/* Cmd/Shift-held scrolling for the right trackball; ordinary bindings stay in Studio. */
#define DT_DRV_COMPAT roi_cmd_scroll

#ifdef CMD_SCROLL_SELF_TEST
#include "../scripts/cmd_scroll_test_stubs.h"
#else
#include <zephyr/kernel.h>
#include <drivers/input_processor.h>
#include <dt-bindings/zmk/modifiers.h>
#include <dt-bindings/zmk/hid_usage_pages.h>
#include <zmk/endpoints.h>
#include <zmk/event_manager.h>
#include <zmk/events/keycode_state_changed.h>
#include <zmk/hid.h>
#endif

#define SCROLL_MOD_MASK (MOD_LGUI | MOD_RGUI | MOD_LSFT | MOD_RSFT)

struct cmd_scroll_config {
    int divisor;
};

static bool scrolling;
static int remainder[2];
K_MUTEX_DEFINE(cmd_scroll_mutex);

/* restore_cmd - releases our mask before the next keyboard event reaches HID. */
static int restore_cmd(const zmk_event_t *event) {
    if (!as_zmk_keycode_state_changed(event)) {
        return ZMK_EV_EVENT_BUBBLE;
    }
    k_mutex_lock(&cmd_scroll_mutex, K_FOREVER);
    if (scrolling) {
        zmk_hid_masked_modifiers_clear();
        scrolling = false;
        remainder[0] = remainder[1] = 0;
        /* HID's following listener sends the updated keyboard report. */
    }
    k_mutex_unlock(&cmd_scroll_mutex);
    return ZMK_EV_EVENT_BUBBLE;
}

ZMK_LISTENER(cmd_scroll, restore_cmd);
ZMK_SUBSCRIPTION(cmd_scroll, zmk_keycode_state_changed);

/* keys_held - avoids interrupting a keyboard shortcut already in progress. */
static bool keys_held(void) {
    const struct zmk_hid_keyboard_report *report = zmk_hid_get_keyboard_report();
    for (size_t i = 0; i < sizeof(report->body.keys); i++) {
        if (report->body.keys[i]) {
            return true;
        }
    }
    return false;
}

/* cmd_scroll_event - masks scroll modifiers before reports, then maps XY to wheel events. */
static int cmd_scroll_event(const struct device *dev, struct input_event *event,
                            uint32_t param1, uint32_t param2,
                            struct zmk_input_processor_state *state) {
    if (event->type != INPUT_EV_REL ||
        (event->code != INPUT_REL_X && event->code != INPUT_REL_Y)) {
        return ZMK_INPUT_PROC_CONTINUE;
    }

    const struct cmd_scroll_config *config = dev->config;
    k_mutex_lock(&cmd_scroll_mutex, K_FOREVER);
    if (!(zmk_hid_get_explicit_mods() & SCROLL_MOD_MASK) || keys_held()) {
        remainder[0] = remainder[1] = 0;
        k_mutex_unlock(&cmd_scroll_mutex);
        return ZMK_INPUT_PROC_CONTINUE;
    }

    if (!scrolling) {
        /* Do not replace a mask already owned by another behavior (e.g. mod-morph). */
        if (!(zmk_hid_get_keyboard_report()->body.modifiers & SCROLL_MOD_MASK)) {
            k_mutex_unlock(&cmd_scroll_mutex);
            return ZMK_INPUT_PROC_CONTINUE;
        }
        zmk_hid_masked_modifiers_set(SCROLL_MOD_MASK);
        int err = zmk_endpoints_send_report(HID_USAGE_KEY);
        if (err < 0) {
            zmk_hid_masked_modifiers_clear();
            k_mutex_unlock(&cmd_scroll_mutex);
            return ZMK_INPUT_PROC_STOP;
        }
        scrolling = true;
    }

    int axis = event->code == INPUT_REL_X ? 0 : 1;
    int total = remainder[axis] + event->value;
    event->value = total / config->divisor;
    remainder[axis] = total % config->divisor;
    event->code = axis == 0 ? INPUT_REL_HWHEEL : INPUT_REL_WHEEL;
    k_mutex_unlock(&cmd_scroll_mutex);
    return ZMK_INPUT_PROC_CONTINUE;
}

static struct zmk_input_processor_driver_api cmd_scroll_api = {
    .handle_event = cmd_scroll_event,
};

static const struct cmd_scroll_config cmd_scroll_config = {
    .divisor = DT_INST_PROP(0, scroll_divisor),
};
BUILD_ASSERT(DT_INST_PROP(0, scroll_divisor) > 0, "scroll-divisor must be positive");
DEVICE_DT_INST_DEFINE(0, NULL, NULL, NULL, &cmd_scroll_config, POST_KERNEL,
                      CONFIG_KERNEL_INIT_PRIORITY_DEFAULT, &cmd_scroll_api);

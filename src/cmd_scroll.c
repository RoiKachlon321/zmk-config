/* Cmd = reading scroll, Shift = fast scroll; runtime speeds are independent. */
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
#include "cmd_scroll.h"
#endif

#define GUI_MASK (MOD_LGUI | MOD_RGUI)
#define SHIFT_MASK (MOD_LSFT | MOD_RSFT)
#define SCROLL_MOD_MASK (GUI_MASK | SHIFT_MASK)

struct cmd_scroll_config {
    int fast_divisor;
    int slow_divisor;
    int multiplier;
};

static bool scrolling;
static int scroll_mode;
static int scroll_remainder[2];
static int pointer_remainder[2];
/* ponytail: session-only tuning; add settings persistence if reboot retention is needed. */
static int pointer_percent = 100;
static int scroll_percent = 100;
K_MUTEX_DEFINE(cmd_scroll_mutex);

/* cosmos_adjust_speed - changes pointer or scroll gain by a bounded percentage step. */
void cosmos_adjust_speed(bool scroll, int delta) {
    k_mutex_lock(&cmd_scroll_mutex, K_FOREVER);
    int *percent = scroll ? &scroll_percent : &pointer_percent;
    int next = *percent + delta;
    *percent = next < 25 ? 25 : next > 300 ? 300 : next;
    int *remainder = scroll ? scroll_remainder : pointer_remainder;
    remainder[0] = remainder[1] = 0;
    k_mutex_unlock(&cmd_scroll_mutex);
}

/* restore_cmd - releases our mask before the next keyboard event reaches HID. */
static int restore_cmd(const zmk_event_t *event) {
    if (!as_zmk_keycode_state_changed(event)) {
        return ZMK_EV_EVENT_BUBBLE;
    }
    k_mutex_lock(&cmd_scroll_mutex, K_FOREVER);
    if (scrolling) {
        zmk_hid_masked_modifiers_clear();
        scrolling = false;
        scroll_mode = 0;
        scroll_remainder[0] = scroll_remainder[1] = 0;
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

/* scale_event - retains fractional counts independently for each axis. */
static void scale_event(struct input_event *event, int axis, int multiplier, int divisor,
                        int remainder[2]) {
    /* The PMW3610 produces signed 12-bit deltas; these bounded gains fit int32_t. */
    int total = remainder[axis] + event->value * multiplier;
    event->value = total / divisor;
    remainder[axis] = total % divisor;
}

/* mask_scroll_mods - sends a modifier release before the first wheel report. */
static int mask_scroll_mods(void) {
    if (scrolling) {
        return ZMK_INPUT_PROC_CONTINUE;
    }
    /* Do not replace a mask owned by another behavior (e.g. mod-morph). */
    if (!(zmk_hid_get_keyboard_report()->body.modifiers & SCROLL_MOD_MASK)) {
        return ZMK_INPUT_PROC_STOP;
    }
    zmk_hid_masked_modifiers_set(SCROLL_MOD_MASK);
    int err = zmk_endpoints_send_report(HID_USAGE_KEY);
    if (err < 0) {
        zmk_hid_masked_modifiers_clear();
        return ZMK_INPUT_PROC_STOP;
    }
    scrolling = true;
    return ZMK_INPUT_PROC_CONTINUE;
}

/* cmd_scroll_event - scales cursor motion or converts it to reversed wheel motion. */
static int cmd_scroll_event(const struct device *dev, struct input_event *event,
                            uint32_t param1, uint32_t param2,
                            struct zmk_input_processor_state *state) {
    if (event->type != INPUT_EV_REL ||
        (event->code != INPUT_REL_X && event->code != INPUT_REL_Y)) {
        return ZMK_INPUT_PROC_CONTINUE;
    }

    const struct cmd_scroll_config *config = dev->config;
    int axis = event->code == INPUT_REL_X ? 0 : 1;
    k_mutex_lock(&cmd_scroll_mutex, K_FOREVER);
    uint8_t mods = zmk_hid_get_explicit_mods();
    int mode = keys_held() ? 0 : (mods & GUI_MASK) ? 1 : (mods & SHIFT_MASK) ? 2 : 0;
    if (mode != scroll_mode) {
        scroll_remainder[0] = scroll_remainder[1] = 0;
        pointer_remainder[0] = pointer_remainder[1] = 0;
        scroll_mode = mode;
    }

    if (mode == 0) {
        scale_event(event, axis, pointer_percent, 100, pointer_remainder);
        k_mutex_unlock(&cmd_scroll_mutex);
        return ZMK_INPUT_PROC_CONTINUE;
    }

    int result = mask_scroll_mods();
    if (result == ZMK_INPUT_PROC_CONTINUE) {
        int divisor = mode == 1 ? config->slow_divisor : config->fast_divisor;
        scale_event(event, axis, -config->multiplier * scroll_percent, divisor * 100,
                    scroll_remainder);
        event->code = axis == 0 ? INPUT_REL_HWHEEL : INPUT_REL_WHEEL;
    }
    k_mutex_unlock(&cmd_scroll_mutex);
    return result;
}

static struct zmk_input_processor_driver_api cmd_scroll_api = {
    .handle_event = cmd_scroll_event,
};

static const struct cmd_scroll_config cmd_scroll_config = {
    .fast_divisor = DT_INST_PROP(0, fast_scroll_divisor),
    .slow_divisor = DT_INST_PROP(0, slow_scroll_divisor),
    .multiplier = DT_INST_PROP(0, scroll_multiplier),
};
BUILD_ASSERT(DT_INST_PROP(0, fast_scroll_divisor) > 0, "fast-scroll-divisor must be positive");
BUILD_ASSERT(DT_INST_PROP(0, slow_scroll_divisor) > 0, "slow-scroll-divisor must be positive");
BUILD_ASSERT(DT_INST_PROP(0, scroll_multiplier) > 0, "scroll-multiplier must be positive");
DEVICE_DT_INST_DEFINE(0, NULL, NULL, NULL, &cmd_scroll_config, POST_KERNEL,
                      CONFIG_KERNEL_INIT_PRIORITY_DEFAULT, &cmd_scroll_api);

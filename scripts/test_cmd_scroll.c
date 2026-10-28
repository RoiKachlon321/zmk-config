/* Run: cc -std=c11 scripts/test_cmd_scroll.c -o firmware/check-cmd-scroll && firmware/check-cmd-scroll */
#define CMD_SCROLL_SELF_TEST
#include "../src/cmd_scroll.c"

static int last_result;

/* move - runs the real processor with one synthetic sensor event. */
static struct input_event move(uint16_t code, int value) {
    const struct device device = { .config = &cmd_scroll_config };
    struct input_event event = { .type = INPUT_EV_REL, .code = code, .value = value };
    last_result = cmd_scroll_event(&device, &event, 0, 0, NULL);
    return event;
}

/* key - mimics our listener followed by HID processing a modifier key event. */
static void key(uint8_t mods) {
    zmk_event_t event = {0};
    restore_cmd(&event);
    test_mods = test_report.body.modifiers = mods;
}

/* main - checks directions, speed ratio, fractional movement, independent tuning and masking. */
int main(void) {
    struct input_event event = move(INPUT_REL_Y, 9);
    assert(event.code == INPUT_REL_Y && event.value == 9 && test_sends == 0);
    key(MOD_LGUI);
    for (int i = 0; i < 3; i++) {
        event = move(INPUT_REL_Y, 16);
        assert(event.code == INPUT_REL_WHEEL && event.value == (i == 2 ? -1 : 0));
    }
    assert(scrolling && test_report.body.modifiers == 0 && test_sends == 1);
    key(MOD_RGUI);
    assert(!scrolling && test_report.body.modifiers == MOD_RGUI);
    int slow = move(INPUT_REL_Y, 128).value;
    assert(slow == -3);
    key(MOD_RSFT);
    int fast = move(INPUT_REL_Y, 128).value;
    assert(fast == slow * 4);
    event = move(INPUT_REL_X, -32);
    assert(event.code == INPUT_REL_HWHEEL && event.value == 3);
    key(MOD_LSFT | MOD_LGUI); /* Cmd takes the slower mode when both are held. */
    assert(move(INPUT_REL_Y, 128).value == slow);
    key(MOD_LSFT);
    assert(move(INPUT_REL_Y, 128).value == fast);

    key(0);
    cosmos_adjust_speed(false, -25);
    assert(pointer_percent == 75 && scroll_percent == 100);
    assert(move(INPUT_REL_X, 8).value == 6);
    cosmos_adjust_speed(false, -25);
    assert(move(INPUT_REL_Y, 1).value == 0);
    assert(move(INPUT_REL_Y, 1).value == 1);
    assert(move(INPUT_REL_X, -1).value == 0);
    assert(move(INPUT_REL_X, -1).value == -1);
    cosmos_adjust_speed(true, -25);
    assert(pointer_percent == 50 && scroll_percent == 75);
    key(MOD_RSFT);
    assert(move(INPUT_REL_Y, 128).value == -9);
    cosmos_adjust_speed(false, 25);
    assert(move(INPUT_REL_Y, 128).value == -9); /* Cursor gain does not alter scroll. */
    key(0);
    assert(move(INPUT_REL_Y, 100).value == 75); /* Scroll gain does not alter cursor. */
    for (int i = 0; i < 20; i++) cosmos_adjust_speed(false, -25);
    assert(pointer_percent == 25);
    for (int i = 0; i < 20; i++) cosmos_adjust_speed(true, 25);
    assert(scroll_percent == 300);
    for (int i = 0; i < 20; i++) cosmos_adjust_speed(false, 25);
    assert(pointer_percent == 300);
    for (int i = 0; i < 20; i++) cosmos_adjust_speed(true, -25);
    assert(scroll_percent == 25);

    key(MOD_LGUI);
    test_report.body.keys[0] = 6; /* Cmd+C must remain a keyboard shortcut. */
    event = move(INPUT_REL_Y, 32);
    assert(event.code == INPUT_REL_Y && event.value == 96);
    assert(test_report.body.modifiers == MOD_LGUI);
    test_report.body.keys[0] = 0;
    test_report.body.modifiers = 0; /* Another behavior owns the mask: don't overwrite it. */
    move(INPUT_REL_Y, 32);
    assert(last_result == ZMK_INPUT_PROC_STOP && !scrolling);
    key(MOD_LGUI);
    test_send_error = -1;
    move(INPUT_REL_Y, 16);
    assert(last_result == ZMK_INPUT_PROC_STOP && !scrolling);
    assert(test_report.body.modifiers == MOD_LGUI);
    return 0;
}

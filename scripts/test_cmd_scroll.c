/* Run: cc -std=c11 scripts/test_cmd_scroll.c -o firmware/check-cmd-scroll && firmware/check-cmd-scroll */
#define CMD_SCROLL_SELF_TEST
#include "../src/cmd_scroll.c"

/* move - runs the real processor with one synthetic sensor event. */
static struct input_event move(uint16_t code, int value) {
    const struct device device = { .config = &cmd_scroll_config };
    struct input_event event = { .type = INPUT_EV_REL, .code = code, .value = value };
    int result = cmd_scroll_event(&device, &event, 0, 0, NULL);
    assert(result == (test_send_error ? ZMK_INPUT_PROC_STOP : ZMK_INPUT_PROC_CONTINUE));
    return event;
}

/* main - checks cursor passthrough, fractional scroll, Cmd restoration and errors. */
int main(void) {
    struct input_event event = move(INPUT_REL_Y, 9);
    assert(event.code == INPUT_REL_Y && event.value == 9 && test_sends == 0);
    test_mods = test_report.body.modifiers = MOD_LGUI;
    event = move(INPUT_REL_Y, 9);
    assert(event.code == INPUT_REL_WHEEL && event.value == 0 && scrolling);
    event = move(INPUT_REL_Y, 9);
    assert(event.value == 1 && test_sends == 1 && test_report.body.modifiers == 0);
    event = move(INPUT_REL_X, -32);
    assert(event.code == INPUT_REL_HWHEEL && event.value == -2);
    zmk_event_t key_event = {0};
    restore_cmd(&key_event);
    assert(!scrolling && test_report.body.modifiers == MOD_LGUI && remainder[1] == 0);
    test_report.body.keys[0] = 6; /* Cmd+C must not be converted into scrolling. */
    event = move(INPUT_REL_Y, 32);
    assert(event.code == INPUT_REL_Y && test_sends == 1);
    test_report.body.keys[0] = 0;
    test_mods = test_report.body.modifiers = MOD_RGUI;
    event = move(INPUT_REL_Y, -16);
    assert(event.code == INPUT_REL_WHEEL && event.value == -1);
    restore_cmd(&key_event); /* runs before HID applies Cmd release */
    test_mods = test_report.body.modifiers = 0;
    event = move(INPUT_REL_Y, 10);
    assert(event.code == INPUT_REL_Y && !scrolling);
    test_mods = MOD_LGUI;
    test_report.body.modifiers = 0; /* Another behavior owns the existing mask. */
    event = move(INPUT_REL_Y, 10);
    assert(event.code == INPUT_REL_Y && !scrolling);
    test_report.body.modifiers = MOD_LGUI;
    test_send_error = -1;
    move(INPUT_REL_Y, 16);
    assert(!scrolling && test_report.body.modifiers == MOD_LGUI);
    return 0;
}

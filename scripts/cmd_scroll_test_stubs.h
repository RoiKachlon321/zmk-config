/* Small host substitute for the ZMK interfaces used by cmd_scroll.c. */
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

#define MOD_LGUI 8
#define MOD_RGUI 128
#define MOD_LSFT 2
#define MOD_RSFT 32
#define HID_USAGE_KEY 7
#define INPUT_EV_REL 2
#define INPUT_REL_X 0
#define INPUT_REL_Y 1
#define INPUT_REL_HWHEEL 6
#define INPUT_REL_WHEEL 8
#define ZMK_INPUT_PROC_CONTINUE 0
#define ZMK_INPUT_PROC_STOP 1
#define ZMK_EV_EVENT_BUBBLE 0
#define K_FOREVER 0
#define K_MUTEX_DEFINE(name) int name
#define ZMK_LISTENER(...)
#define ZMK_SUBSCRIPTION(...)
#define TEST_fast_scroll_divisor 32
#define TEST_slow_scroll_divisor 128
#define TEST_scroll_multiplier 3
#define DT_INST_PROP(inst, prop) TEST_##prop
#define BUILD_ASSERT(condition, message) _Static_assert(condition, message)
#define DEVICE_DT_INST_DEFINE(...)

struct device { const void *config; };
struct input_event { uint8_t type; uint16_t code; int32_t value; };
struct zmk_input_processor_state { int unused; };
struct zmk_input_processor_driver_api { int (*handle_event)(const struct device *, struct input_event *, uint32_t, uint32_t, struct zmk_input_processor_state *); };
struct zmk_hid_keyboard_report { struct { uint8_t modifiers; uint8_t keys[6]; } body; };
typedef struct { int unused; } zmk_event_t;
static struct zmk_hid_keyboard_report test_report;
static uint8_t test_mods;
static int test_send_error;
static int test_sends;

/* lock stubs - host checks are single threaded. */
static void k_mutex_lock(int *mutex, int timeout) {}
static void k_mutex_unlock(int *mutex) {}
/* key event stub - test calls always represent a keyboard event. */
static const void *as_zmk_keycode_state_changed(const zmk_event_t *event) { return event; }
/* HID stubs - retain explicit Cmd even while its host report is masked. */
static uint8_t zmk_hid_get_explicit_mods(void) { return test_mods; }
static struct zmk_hid_keyboard_report *zmk_hid_get_keyboard_report(void) { return &test_report; }
static void zmk_hid_masked_modifiers_set(uint8_t mask) { test_report.body.modifiers = test_mods & ~mask; }
static void zmk_hid_masked_modifiers_clear(void) { test_report.body.modifiers = test_mods; }
/* report stub - verifies Cmd is absent before a mouse report can follow. */
static int zmk_endpoints_send_report(int page) { assert(!(test_report.body.modifiers & (MOD_LGUI | MOD_RGUI | MOD_LSFT | MOD_RSFT))); test_sends++; return test_send_error; }

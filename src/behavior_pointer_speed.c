/* Studio-assignable speed actions; no saved key positions are overwritten. */
#define DT_DRV_COMPAT roi_behavior_pointer_speed
#include <zephyr/device.h>
#include <drivers/behavior.h>
#include <zmk/behavior.h>
#include "cmd_scroll.h"

struct pointer_speed_config {
    bool scroll;
    int delta;
};

/* speed_pressed - applies one speed step when the assigned key is pressed. */
static int speed_pressed(struct zmk_behavior_binding *binding,
                         struct zmk_behavior_binding_event event) {
    const struct device *dev = zmk_behavior_get_binding(binding->behavior_dev);
    const struct pointer_speed_config *config = dev->config;
    cosmos_adjust_speed(config->scroll, config->delta);
    return ZMK_BEHAVIOR_OPAQUE;
}

/* speed_released - consumes release without repeating the speed change. */
static int speed_released(struct zmk_behavior_binding *binding,
                          struct zmk_behavior_binding_event event) {
    return ZMK_BEHAVIOR_OPAQUE;
}

static const struct behavior_driver_api speed_api = {
    .binding_pressed = speed_pressed,
    .binding_released = speed_released,
#if IS_ENABLED(CONFIG_ZMK_BEHAVIOR_METADATA)
    .get_parameter_metadata = zmk_behavior_get_empty_param_metadata,
#endif
};

#define SPEED_INSTANCE(n)                                                                         \
    static const struct pointer_speed_config speed_config_##n = {                                  \
        .scroll = DT_INST_PROP(n, scroll),                                                         \
        .delta = DT_INST_PROP(n, delta),                                                           \
    };                                                                                            \
    BEHAVIOR_DT_INST_DEFINE(n, NULL, NULL, NULL, &speed_config_##n, POST_KERNEL,                     \
                            CONFIG_KERNEL_INIT_PRIORITY_DEFAULT, &speed_api);

DT_INST_FOREACH_STATUS_OKAY(SPEED_INSTANCE)

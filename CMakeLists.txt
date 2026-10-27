# Compile only when the right-half overlay enables the processor.
if(CONFIG_ZMK_POINTING AND CONFIG_DT_HAS_ROI_CMD_SCROLL_ENABLED)
  # Module sources precede ZMK HID sources: restore Cmd before HID handles a key.
  target_sources(app PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/src/cmd_scroll.c)
  # Refuse to ship if linker subscription order changes and breaks Cmd shortcuts.
  add_custom_target(check_cmd_scroll ALL
    COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/scripts/check_cmd_scroll.py
            ${CMAKE_NM} ${CMAKE_BINARY_DIR}/zephyr/${CONFIG_KERNEL_BIN_NAME}.elf
    DEPENDS zephyr_final
    VERBATIM)
endif()

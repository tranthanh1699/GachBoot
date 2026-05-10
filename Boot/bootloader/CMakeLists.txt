add_library(bootloader STATIC
    app/bl_app_jump.c
    app/bl_app_validate.c
    core/bl_boot.c
    core/bl_main.c
    core/bl_session.c
    core/bl_state_machine.c
    log/bl_log.c
    memory/bl_flash.c
    memory/bl_memory.c
    platform/platform_boot_mode.c
    platform/platform_flash.c
    platform/platform_reset.c
    platform/platform_uart.c
    protocol/bl_command.c
    protocol/bl_frame.c
    protocol/bl_protocol.c
    security/bl_checksum.c
    security/bl_signature.c
    transport/bl_transport.c
    transport/bl_uart_transport.c
)

set(BL_BOOTLOADER_VARIANT "Development" CACHE STRING "Bootloader variant: Development or Release")
set_property(CACHE BL_BOOTLOADER_VARIANT PROPERTY STRINGS Development Release)
set(BL_PUBLIC_KEY_PEM "" CACHE FILEPATH "RSA-2048 public key PEM for release signature verification")
option(BL_ENABLE_SECURE_BOOT "Enable boot-time RSA secure boot in Release builds" OFF)

target_include_directories(bootloader PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/app
    ${CMAKE_CURRENT_SOURCE_DIR}/config
    ${CMAKE_CURRENT_SOURCE_DIR}/core
    ${CMAKE_CURRENT_SOURCE_DIR}/log
    ${CMAKE_CURRENT_SOURCE_DIR}/memory
    ${CMAKE_CURRENT_SOURCE_DIR}/platform
    ${CMAKE_CURRENT_SOURCE_DIR}/protocol
    ${CMAKE_CURRENT_SOURCE_DIR}/security
    ${CMAKE_CURRENT_SOURCE_DIR}/transport
)

if(NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/config/bl_build_config.h")
    message(FATAL_ERROR "bl_build_config.h not found. Run make dev or make release first.")
endif()

target_link_libraries(bootloader PUBLIC stm32cubemx)
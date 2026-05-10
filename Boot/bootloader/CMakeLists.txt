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
set(BL_GENERATED_PUBLIC_KEY_HEADER "${CMAKE_BINARY_DIR}/bl_rsa_public_key_generated.h")

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

if(BL_BOOTLOADER_VARIANT STREQUAL "Release")
    if(BL_ENABLE_SECURE_BOOT)
        if(NOT BL_PUBLIC_KEY_PEM)
            message(FATAL_ERROR "BL_PUBLIC_KEY_PEM is required when BL_ENABLE_SECURE_BOOT is ON")
        endif()

        if(NOT EXISTS "${BL_PUBLIC_KEY_PEM}")
            message(FATAL_ERROR "BL_PUBLIC_KEY_PEM does not exist: ${BL_PUBLIC_KEY_PEM}")
        endif()

        find_package(Python3 REQUIRED COMPONENTS Interpreter)

        add_custom_command(
            OUTPUT "${BL_GENERATED_PUBLIC_KEY_HEADER}"
            COMMAND ${Python3_EXECUTABLE}
                    "${CMAKE_CURRENT_SOURCE_DIR}/tools/rsa_public_key_from_pem.py"
                    --pem "${BL_PUBLIC_KEY_PEM}"
                    --out "${BL_GENERATED_PUBLIC_KEY_HEADER}"
            DEPENDS
                    "${BL_PUBLIC_KEY_PEM}"
                    "${CMAKE_CURRENT_SOURCE_DIR}/tools/rsa_public_key_from_pem.py"
            COMMENT "Generating RSA public key header from ${BL_PUBLIC_KEY_PEM}"
            VERBATIM
        )

        add_custom_target(bootloader_public_key DEPENDS "${BL_GENERATED_PUBLIC_KEY_HEADER}")
        add_dependencies(bootloader bootloader_public_key)

        target_compile_definitions(bootloader PRIVATE
            BOOTLOADER_RELEASE=1u
            BOOTLOADER_DEV=0u
            BL_ENABLE_SECURE_BOOT=1u
            BL_ENABLE_SIGNATURE_VERIFY=1u
            BL_RSA_PUBLIC_KEY_HEADER="${BL_GENERATED_PUBLIC_KEY_HEADER}"
        )

        target_include_directories(bootloader PRIVATE
            "${CMAKE_BINARY_DIR}"
        )
    else()
        target_compile_definitions(bootloader PRIVATE
            BOOTLOADER_RELEASE=1u
            BOOTLOADER_DEV=0u
            BL_ENABLE_SECURE_BOOT=0u
            BL_ENABLE_SIGNATURE_VERIFY=0u
        )
    endif()
else()
    target_compile_definitions(bootloader PRIVATE
        BOOTLOADER_DEV=1u
        BOOTLOADER_RELEASE=0u
        BL_ENABLE_SECURE_BOOT=0u
        BL_ENABLE_SIGNATURE_VERIFY=0u
    )
endif()

target_link_libraries(bootloader PUBLIC stm32cubemx)

PUBLIC_KEY_PEM ?= ../RSA_Key/public_key.pem
SECURE_BOOT ?= OFF
STM32_TOOLCHAIN_BIN ?= $(HOME)/.local/share/stm32cube/bundles/gnu-tools-for-stm32/13.3.1+st.9/bin
STM32_NINJA_BIN ?= $(HOME)/.local/share/stm32cube/bundles/ninja/1.13.2+st.1/bin
BOOT_BUILD_PATH := $(PATH)

ifneq ($(wildcard $(STM32_NINJA_BIN)/ninja),)
BOOT_BUILD_PATH := $(STM32_NINJA_BIN):$(BOOT_BUILD_PATH)
endif

ifneq ($(wildcard $(STM32_TOOLCHAIN_BIN)/arm-none-eabi-gcc),)
BOOT_BUILD_PATH := $(STM32_TOOLCHAIN_BIN):$(BOOT_BUILD_PATH)
endif

.PHONY: dev release clean

dev:
	PATH="$(BOOT_BUILD_PATH)" cmake --preset Debug
	PATH="$(BOOT_BUILD_PATH)" cmake --build --preset Debug

release:
	PATH="$(BOOT_BUILD_PATH)" cmake --preset Release -DBL_ENABLE_SECURE_BOOT=$(SECURE_BOOT) -DBL_PUBLIC_KEY_PEM="$(PUBLIC_KEY_PEM)"
	PATH="$(BOOT_BUILD_PATH)" cmake --build --preset Release

clean:
	PATH="$(BOOT_BUILD_PATH)" cmake --build --preset Debug --target clean
	PATH="$(BOOT_BUILD_PATH)" cmake --build --preset Release --target clean

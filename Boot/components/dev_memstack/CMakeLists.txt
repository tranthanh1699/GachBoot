# ==============================================================================
# Memory Stack (AUTOSAR-compliant)
# ==============================================================================
# This module implements a 3-layer non-volatile memory stack:
#   - NvM (NV Manager): Block management, CRC, redundancy
#   - Fee (Flash EEPROM Emulation): Virtual addressing, wear leveling
#   - Fls (Flash Driver): STM32H7 hardware operations (sector info only)
# ==============================================================================

cmake_minimum_required(VERSION 3.22)

# Add all memory stack layers
add_subdirectory(dev_fls)    # Flash Driver (hardware layer)
add_subdirectory(dev_fee)    # Flash EEPROM Emulation (sector management)
add_subdirectory(dev_memif)  # Memory Interface (abstraction)
add_subdirectory(dev_nvm)    # NV Manager (block management)

# Create a combined memory stack library with initialization module
add_library(dev_memstack STATIC
    dev_memstack.c
)

# Link all layers in correct dependency order
target_link_libraries(dev_memstack PUBLIC
    dev_fls     # Bottom layer - hardware
    dev_fee     # Sector management
    dev_memif   # Abstraction layer
    dev_nvm     # Top layer - application interface
)

# Expose include directories from all layers
target_include_directories(dev_memstack PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/dev_fls/include
    ${CMAKE_CURRENT_SOURCE_DIR}/dev_fee/include
    ${CMAKE_CURRENT_SOURCE_DIR}/dev_memif/include
    ${CMAKE_CURRENT_SOURCE_DIR}/dev_nvm/include
)

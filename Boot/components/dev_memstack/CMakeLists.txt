# ==============================================================================
# Memory Stack (AUTOSAR-inspired)
# ==============================================================================
# This module implements a 4-layer non-volatile memory stack:
#   - NvM (NV Manager): Block management, CRC, redundancy
#   - MemIf (Memory Interface): Device abstraction layer
#   - Fee (Flash EEPROM Emulation): Sector management, wear leveling
#   - Fls (Flash Driver): STM32H7 hardware operations
# ==============================================================================

cmake_minimum_required(VERSION 3.22)

# Add all memory stack layers
add_subdirectory(dev_fls)    # Flash Driver (hardware layer)
add_subdirectory(dev_fee)    # Flash EEPROM Emulation (sector management)
add_subdirectory(dev_memif)  # Memory Interface (abstraction)
add_subdirectory(dev_nvm)    # NV Manager (block management)

# Create a combined memory stack library
add_library(dev_memstack INTERFACE)

# Link all layers in correct dependency order
target_link_libraries(dev_memstack INTERFACE
    dev_fls     # Bottom layer - hardware
    dev_fee     # Sector management
    dev_memif   # Abstraction layer
    dev_nvm     # Top layer - application interface
)

# Expose include directories from all layers
target_include_directories(dev_memstack INTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}/dev_fls/include
    ${CMAKE_CURRENT_SOURCE_DIR}/dev_fee/include
    ${CMAKE_CURRENT_SOURCE_DIR}/dev_memif/include
    ${CMAKE_CURRENT_SOURCE_DIR}/dev_nvm/include
)

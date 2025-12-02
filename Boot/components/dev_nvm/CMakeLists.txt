# Automatically find all .c files in the current directory
file(GLOB DEV_NVM_SOURCES CONFIGURE_DEPENDS "*.c")

# Create the dev_nvm library
add_library(dev_nvm STATIC ${DEV_NVM_SOURCES})

# Add include directories for dev_nvm
target_include_directories(dev_nvm PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link to stm32cubemx to get HAL includes and definitions
target_link_libraries(dev_nvm PUBLIC stm32cubemx)
target_link_libraries(dev_nvm PUBLIC dev_app)
target_link_libraries(dev_nvm PUBLIC dev_crc)
target_link_libraries(dev_nvm PUBLIC dev_memif)
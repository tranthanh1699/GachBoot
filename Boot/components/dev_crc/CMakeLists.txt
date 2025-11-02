# Automatically find all .c files in the current directory
file(GLOB DEV_CRC_SOURCES CONFIGURE_DEPENDS "*.c")

# Create the dev_crc library
add_library(dev_crc STATIC ${DEV_CRC_SOURCES})

# Add include directories for dev_crc
target_include_directories(dev_crc PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link to stm32cubemx to get HAL includes and definitions
target_link_libraries(dev_crc PUBLIC stm32cubemx)
target_link_libraries(dev_crc PUBLIC dev_app)

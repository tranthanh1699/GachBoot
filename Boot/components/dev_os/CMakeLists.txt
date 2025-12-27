# Automatically find all .c files in the current directory
file(GLOB DEV_OS_SOURCES CONFIGURE_DEPENDS "*.c")

# Create the dev_os library
add_library(dev_os STATIC ${DEV_OS_SOURCES})

# Add include directories for dev_os
target_include_directories(dev_os PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link to stm32cubemx to get HAL includes and definitions
target_link_libraries(dev_os PUBLIC stm32cubemx)
target_link_libraries(dev_os PUBLIC dev_app)
target_link_libraries(dev_os PUBLIC GenerateCode)

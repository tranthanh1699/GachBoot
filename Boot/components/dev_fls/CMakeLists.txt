# Automatically find all .c files in the current directory
file(GLOB DEV_FLS_SOURCES CONFIGURE_DEPENDS "*.c")

# Create the dev_fls library
add_library(dev_fls STATIC ${DEV_FLS_SOURCES})

# Add include directories for dev_fls
target_include_directories(dev_fls PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link to stm32cubemx to get HAL includes and definitions
target_link_libraries(dev_fls PUBLIC stm32cubemx)
target_link_libraries(dev_fls PUBLIC dev_app)
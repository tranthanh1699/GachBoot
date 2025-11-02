# Automatically find all .c files in the current directory
file(GLOB DEV_APP_SOURCES CONFIGURE_DEPENDS "*.c")

# Create the dev_app library
add_library(dev_app STATIC ${DEV_APP_SOURCES})

# Add include directories for dev_app
target_include_directories(dev_app PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link to stm32cubemx to get HAL includes and definitions
target_link_libraries(dev_app PUBLIC stm32cubemx)

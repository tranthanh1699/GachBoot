# Automatically find all .c files in the current directory
file(GLOB DEV_QUEUE_SOURCES CONFIGURE_DEPENDS "*.c")

# Create the dev_queue library
add_library(dev_queue STATIC ${DEV_QUEUE_SOURCES})

# Add include directories for dev_queue
target_include_directories(dev_queue PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link to stm32cubemx to get HAL includes and definitions
target_link_libraries(dev_queue PUBLIC stm32cubemx)
target_link_libraries(dev_queue PUBLIC dev_app)

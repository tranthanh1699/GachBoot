# Automatically find all .c files in the current directory
file(GLOB DEV_UART_SOURCES CONFIGURE_DEPENDS "*.c")

# Create the dev_uart library
add_library(dev_uart STATIC ${DEV_UART_SOURCES})

# Add include directories for dev_uart
target_include_directories(dev_uart PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link to stm32cubemx to get HAL includes and definitions
target_link_libraries(dev_uart PUBLIC stm32cubemx)
target_link_libraries(dev_uart PUBLIC dev_app)

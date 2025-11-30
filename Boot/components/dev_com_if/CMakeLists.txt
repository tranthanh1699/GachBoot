# Automatically find all .c files in the current directory
file(GLOB DEV_COM_IF_SOURCES CONFIGURE_DEPENDS "*.c")

# Create the dev_com_if library
add_library(dev_com_if STATIC ${DEV_COM_IF_SOURCES})

# Add include directories for dev_com_if
target_include_directories(dev_com_if PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link to stm32cubemx to get HAL includes and definitions
target_link_libraries(dev_com_if PUBLIC stm32cubemx)
target_link_libraries(dev_com_if PUBLIC dev_com)

# Automatically find all .c files in the current directory
file(GLOB DEV_COM_SOURCES CONFIGURE_DEPENDS "*.c")

# Create the dev_com library
add_library(dev_com STATIC ${DEV_COM_SOURCES})

# Add include directories for dev_com
target_include_directories(dev_com PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link to stm32cubemx to get HAL includes and definitions
target_link_libraries(dev_com PUBLIC stm32cubemx)
target_link_libraries(dev_com PUBLIC dev_app)

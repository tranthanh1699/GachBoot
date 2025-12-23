# Automatically find all .c files in the current directory
file(GLOB DEV_FLASHBLOCK_SOURCES CONFIGURE_DEPENDS "*.c")

# Create the dev_flashblock library
add_library(dev_flashblock STATIC ${DEV_FLASHBLOCK_SOURCES})

# Add include directories for dev_flashblock
target_include_directories(dev_flashblock PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link to stm32cubemx to get HAL includes and definitions
target_link_libraries(dev_flashblock PUBLIC stm32cubemx)
target_link_libraries(dev_flashblock PUBLIC dev_app)
target_link_libraries(dev_flashblock PUBLIC GenerateCode)
target_link_libraries(dev_flashblock PUBLIC dev_fls)

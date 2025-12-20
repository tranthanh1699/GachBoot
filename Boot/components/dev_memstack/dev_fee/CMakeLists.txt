# Automatically find all .c files in the current directory
file(GLOB DEV_FEE_SOURCES CONFIGURE_DEPENDS "*.c")

# Create the dev_fee library
add_library(dev_fee STATIC ${DEV_FEE_SOURCES})

# Add include directories for dev_fee
target_include_directories(dev_fee PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link dependencies
target_link_libraries(dev_fee PUBLIC stm32cubemx)
target_link_libraries(dev_fee PUBLIC dev_app)
target_link_libraries(dev_fee PUBLIC dev_fls)
target_link_libraries(dev_fee PUBLIC GenerateCode)

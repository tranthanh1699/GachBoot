# Automatically find all .c files in the current directory
file(GLOB DEV_MEMIF_SOURCES CONFIGURE_DEPENDS "*.c")

# Create the dev_memif library
add_library(dev_memif STATIC ${DEV_MEMIF_SOURCES})

# Add include directories for dev_memif
target_include_directories(dev_memif PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link dependencies
target_link_libraries(dev_memif PUBLIC stm32cubemx)
target_link_libraries(dev_memif PUBLIC dev_app)
target_link_libraries(dev_memif PUBLIC dev_fee)

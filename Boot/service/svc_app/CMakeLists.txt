# Automatically find all .c files in the current directory
file(GLOB SVC_APP_SOURCES CONFIGURE_DEPENDS "*.c")

# Create the svc_app library
add_library(svc_app STATIC ${SVC_APP_SOURCES})

# Add include directories for svc_app
target_include_directories(svc_app PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

# Link to stm32cubemx to get HAL includes and definitions
target_link_libraries(svc_app PUBLIC stm32cubemx)
target_link_libraries(svc_app PUBLIC dev_app)
target_link_libraries(svc_app PUBLIC dev_uart)
target_link_libraries(svc_app PUBLIC dev_com_if)
target_link_libraries(svc_app PUBLIC dev_com_tp)

# Automatically find all .c files in DCM layers
file(GLOB SVC_DCM_SOURCES CONFIGURE_DEPENDS "*.c")
file(GLOB DCMDSL_SOURCES CONFIGURE_DEPENDS "dcmdsl/*.c")
file(GLOB DCMDSD_SOURCES CONFIGURE_DEPENDS "dcmdsd/*.c")
file(GLOB DCMDSP_SOURCES CONFIGURE_DEPENDS "dcmdsp/*.c")

# Find all UDS service sources (service_did will be excluded automatically since it's a subdirectory)
file(GLOB_RECURSE UDS_SERVICES_SOURCES CONFIGURE_DEPENDS "uds_services/**/*.c")

# Add Service_PBCfg.c from GenerateCode (must be compiled with svc_dcm to resolve circular dependency)
set(SERVICE_PBCFG_SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/../../GenerateCode/Service_Gen/Service_PBCfg.c")
if(EXISTS ${SERVICE_PBCFG_SOURCE})
    list(APPEND UDS_SERVICES_SOURCES ${SERVICE_PBCFG_SOURCE})
    message(STATUS "Added Service_PBCfg.c to svc_dcm")
endif()

# Create the svc_dcm library
add_library(svc_dcm STATIC 
    ${SVC_DCM_SOURCES}
    ${DCMDSL_SOURCES}
    ${DCMDSD_SOURCES}
    ${DCMDSP_SOURCES}
    ${UDS_SERVICES_SOURCES}
)

# Add include directories for svc_dcm
target_include_directories(svc_dcm PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# Link to stm32cubemx to get HAL includes and definitions
target_link_libraries(svc_dcm PUBLIC stm32cubemx)
target_link_libraries(svc_dcm PUBLIC dev_com_tp)
target_link_libraries(svc_dcm PUBLIC GenerateCode)
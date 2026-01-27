cmake_minimum_required(VERSION 3.22)

#
# This file is generated only once,
# and is not re-generated if converter is called multiple times.
#
# User is free to modify the file as much as necessary
#

# Setup compiler settings
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(CMAKE_C_EXTENSIONS ON)


# Define the build type
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE "Debug")
endif()

# Set the project name
set(CMAKE_PROJECT_NAME Boot)

# Enable compile command to ease indexing with e.g. clangd
set(CMAKE_EXPORT_COMPILE_COMMANDS TRUE)

# Core project settings
project(${CMAKE_PROJECT_NAME})
message("Build type: " ${CMAKE_BUILD_TYPE})

# Enable CMake support for ASM and C languages
enable_language(C ASM)

# Create an executable object type
add_executable(${CMAKE_PROJECT_NAME})

# Add STM32CubeMX generated sources
add_subdirectory(cmake/stm32cubemx)

# Add user component modules
add_subdirectory(components/dev_app)
add_subdirectory(components/dev_com)
add_subdirectory(components/dev_crc)
add_subdirectory(components/dev_com_if)
add_subdirectory(components/dev_com_tp)
add_subdirectory(components/dev_queue)  # Generic Queue Library
add_subdirectory(components/dev_memstack)  # Memory Stack (Fls, Fee, MemIf, NvM)
add_subdirectory(components/dev_flashblock)  # Flash Block Management
add_subdirectory(components/dev_os)
add_subdirectory(GenerateCode)
# Add user service modules
add_subdirectory(service/svc_app)
add_subdirectory(service/svc_dcm)

# Add generated code from ConfigTool
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/Tool/ConfigTool/GenCode/CMakeLists.txt)
    add_subdirectory(Tool/ConfigTool/GenCode)
    message(STATUS "Added ConfigTool generated code")
endif()

# Link directories setup
target_link_directories(${CMAKE_PROJECT_NAME} PRIVATE
    # Add user defined library search paths
)

# Add sources to executable
target_sources(${CMAKE_PROJECT_NAME} PRIVATE
    # Add user sources here
)

# Add include paths
target_include_directories(${CMAKE_PROJECT_NAME} PRIVATE
    # Add user defined include paths
)

# Add project symbols (macros)
target_compile_definitions(${CMAKE_PROJECT_NAME} PRIVATE
    # Add user defined symbols
)

# Remove wrong libob.a library dependency when using cpp files
list(REMOVE_ITEM CMAKE_C_IMPLICIT_LINK_LIBRARIES ob)

# Add linked libraries
target_link_libraries(${CMAKE_PROJECT_NAME}
    stm32cubemx

    # Add user defined libraries
    dev_app
    dev_com
    dev_crc
    dev_com_if
    dev_com_tp
    dev_queue     # Generic FIFO Queue Library
    dev_memstack  # Memory Stack (includes Fls, Fee, MemIf, NvM)
    dev_flashblock  # Flash Block Management
    dev_os
    
    # Add generated code library (headers and non-circular sources)
    GenerateCode

    # Add service libraries
    svc_app
    svc_dcm  # Includes Service_PBCfg.c and Routine_PBCfg.c from GenerateCode
)

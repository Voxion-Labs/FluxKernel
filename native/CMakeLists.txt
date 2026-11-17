cmake_minimum_required(VERSION 3.20)
project(FluxKernelNative VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Optimization flags
if(MSVC)
    add_compile_options(/W4 /permissive- /O2)
else()
    add_compile_options(-Wall -Wextra -Wpedantic -O3 -fPIC)
endif()

# Include directories
include_directories(include)

# Shared Library Target
add_library(flux_core SHARED
    src/flux_core.cpp
)

target_include_directories(flux_core PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# Test Executable
enable_testing()

add_executable(flux_test_suite
    tests/test_flux_core.cpp
)

target_link_libraries(flux_test_suite PRIVATE flux_core)

add_test(NAME FluxCoreTests COMMAND flux_test_suite)

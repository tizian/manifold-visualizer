cmake_minimum_required (VERSION 2.8.3)
project(manifold-visualizer)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    message(STATUS "Setting build type to 'Release' as none was specified.")
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)
    set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
endif()
string(TOUPPER "${CMAKE_BUILD_TYPE}" U_CMAKE_BUILD_TYPE)

if(NOT IS_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/ext/enoki")
  message(FATAL_ERROR "Dependency repositories (enoki, pybind11, etc.) are missing! "
    "You probably did not clone the project with --recursive. It is possible to recover by calling \"git submodule update --init --recursive\"")
endif()

# Enable folders for projects in Visual Studio
if (CMAKE_GENERATOR MATCHES "Visual Studio")
  set_property(GLOBAL PROPERTY USE_FOLDERS ON)
endif()

# Sanitize build environment for static build with C++11
if (MSVC)
  add_definitions (/D "_CRT_SECURE_NO_WARNINGS")

  # Parallel build on MSVC (all targets)
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /MP")
endif()

# Enable C++17 mode on GCC / Clang
if (CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++17")
endif()

include(CheckCXXCompilerFlag)
include(CheckCXXSourceRuns)

macro(CHECK_CXX_COMPILER_AND_LINKER_FLAGS _RESULT _CXX_FLAGS _LINKER_FLAGS)
    set(CMAKE_REQUIRED_FLAGS ${_CXX_FLAGS})
    set(CMAKE_REQUIRED_LIBRARIES ${_LINKER_FLAGS})
    set(CMAKE_REQUIRED_QUIET TRUE)
    check_cxx_source_runs("#include <iostream>\nint main(int argc, char **argv) { std::cout << \"test\"; return 0; }" ${_RESULT})
    set(CMAKE_REQUIRED_FLAGS "")
    set(CMAKE_REQUIRED_LIBRARIES "")
endmacro()

# Prefer libc++ in conjunction with Clang
if (CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    if (CMAKE_CXX_FLAGS MATCHES "-stdlib=libc\\+\\+")
        message(STATUS "Using libc++.")
    else()
        CHECK_CXX_COMPILER_AND_LINKER_FLAGS(HAS_LIBCPP "-stdlib=libc++" "-stdlib=libc++")
        if (HAS_LIBCPP)
            set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -stdlib=libc++")
            set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -stdlib=libc++")
            set(CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS} -stdlib=libc++")
            message(STATUS "Using libc++.")
        else()
            message(STATUS "NOT using libc++.")
      endif()
    endif()
endif()

# Add enoki
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/ext/enoki)
enoki_set_compile_flags()
enoki_set_native_flags()

# Add nanogui
set(NANOGUI_BUILD_EXAMPLE OFF CACHE BOOL " " FORCE)
set(NANOGUI_BUILD_PYTHON  ON  CACHE BOOL " " FORCE)
set(NANOGUI_INSTALL       ON  CACHE BOOL " " FORCE)
add_subdirectory(ext/nanogui)
set_property(TARGET glfw glfw_objects nanogui PROPERTY FOLDER "dependencies")

# Compiler warnings
if(MSVC)
    if(CMAKE_CXX_FLAGS MATCHES "/W[0-4]")
        string(REGEX REPLACE "/W[0-4]" "/W4" CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
    else()
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /W4")
    endif()
elseif (CMAKE_CXX_COMPILER_ID MATCHES "Clang" OR CMAKE_CXX_COMPILER_ID MATCHES "GNU")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Wno-unused-parameter")
    if (CMAKE_CXX_COMPILER_ID MATCHES "Clang")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wno-gnu-anonymous-struct -Wno-c99-extensions -Wno-nested-anon-types")
    endif()
endif()

include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/ext/enoki/include
    ${CMAKE_CURRENT_SOURCE_DIR}/ext/tinyformat
    ${CMAKE_CURRENT_SOURCE_DIR}/ext/nanogui/ext/nanovg/src
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# add_executable(manifold-visualizer
#     ${CMAKE_CURRENT_SOURCE_DIR}/src/main.cpp
# )

# Python bindings
set(PYBIND11_CPP_STANDARD "-std=c++17")
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/ext/pybind11)
pybind11_add_module(manifolds
    ${CMAKE_CURRENT_SOURCE_DIR}/src/python/python.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/python/interaction.cpp    ${CMAKE_CURRENT_SOURCE_DIR}/src/interaction.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/src/python/shape.cpp          ${CMAKE_CURRENT_SOURCE_DIR}/src/shape.cpp
)

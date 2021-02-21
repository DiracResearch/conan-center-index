cmake_minimum_required(VERSION 3.0)
project(conanunwindllvm)

message(STATUS "Conan CMake Wrapper")
include(conanbuildinfo.cmake)
conan_basic_setup()

set(LIBUNWIND_STANDALONE_BUILD 1)

add_subdirectory("source_subfolder")

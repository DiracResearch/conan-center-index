cmake_minimum_required(VERSION 3.1)
project(test_package)

include("${CMAKE_BINARY_DIR}/conanbuildinfo.cmake")
conan_basic_setup(TARGETS)

add_executable(hello_printf_c hello_printf_c.c)
add_executable(hello_iostream hello_iostream.cpp)
add_executable(hello_printf hello_printf.cpp)

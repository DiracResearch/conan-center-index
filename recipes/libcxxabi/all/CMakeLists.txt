cmake_minimum_required(VERSION 3.0)
project(conanlibcxxabi)

message(STATUS "Conan CMake Wrapper")

# Force this include before to fix:
#  ../libcxx/include/cstddef:44:15: fatal error: 'stddef.h' file not found
#  #include_next <stddef.h>
include_directories(BEFORE "libcxx/include")

include(conanbuildinfo.cmake)
conan_basic_setup()

set(LIBCXXABI_STANDALONE_BUILD 1)

add_subdirectory("source_subfolder")

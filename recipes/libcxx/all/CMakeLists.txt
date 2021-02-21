cmake_minimum_required(VERSION 3.0)
project(conanlibcxx)

# Force this include before to fix:
#  ../libcxx/include/cstddef:44:15: fatal error: 'stddef.h' file not found
#  #include_next <stddef.h>
include_directories(BEFORE "source_subfolder/include")

message(STATUS "Conan CMake Wrapper")
include(conanbuildinfo.cmake)
conan_basic_setup()

set(LIBCXX_STANDALONE_BUILD 1)

add_subdirectory("source_subfolder")

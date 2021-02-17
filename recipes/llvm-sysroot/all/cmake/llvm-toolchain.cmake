# A minimal toolchain
#
# Because the recipe has to work for auto tools most of the logic
# goes through enviromint variables like CFLAGS and LDFLAGS
#  https://cmake.org/cmake/help/latest/manual/cmake-env-variables.7.html

set(CMAKE_SYSROOT $ENV{CONAN_CMAKE_SYSROOT})
set(CMAKE_C_COMPILER_TARGET $ENV{CHOST})
set(CMAKE_CXX_COMPILER_TARGET $ENV{CHOST})

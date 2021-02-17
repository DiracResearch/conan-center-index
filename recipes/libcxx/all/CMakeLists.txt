cmake_minimum_required(VERSION 3.0.0)
project(cmake_wrapper)

include("conanbuildinfo.cmake")
conan_basic_setup()

include_directories(${CONAN_INCLUDE_DIRS})

# Since we wrap the CMakeFile the logic in the clang source
# will think it's not built in "standalone" mode. So we force it here.
set(COMPILER_RT_STANDALONE_BUILD ON)

add_subdirectory(source_subfolder)

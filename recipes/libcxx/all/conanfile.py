import os
import stat
from conans import ConanFile, tools, AutoToolsBuildEnvironment, CMake
from conans.errors import ConanException

class ClangLibcxxConan(ConanFile):
    name = "libcxx"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://libcxx.llvm.org/"
    license = "MIT"
    description = ("todo")
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "rtlib": ["compiler-rt", "libgcc"],
        "unwinder": ["clang", "gcc"],
        "cxxabi": ["clang", "gcc"]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "rtlib": "compiler-rt",
        "unwinder": "clang",
        "cxxabi": "clang"
    }
    topics = ("libc", "libcxx", "clang")

    def requirements(self):
        # TODO: if option libc musl
        self.requires.add(f"musl/1.2.2@dirac/testing")
        # TODO: if option libcxx-abi
        self.requires.add(f"libcxxabi/{self.version}@dirac/testing")

    def config_options(self):
        # TODO: Check options
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        pass

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename(f"{self.name}-{self.version}.src", self.name)

    def build(self):
        # TODO: if unwinder
        # We need to handle the dependencies and flags more "manual" because
        # building this libs is a bit different from the normal stuff.
        with tools.environment_append({"LDFLAGS": f"{os.getenv('LDFLAGS')} -L{self.deps_cpp_info['libunwind-llvm'].rootpath}/lib"}):
            cmake = CMake(self)
            cmake.definitions["CMAKE_SYSROOT"] = self.deps_cpp_info["musl"].rootpath
            cmake.definitions["CMAKE_C_COMPILER_TARGET"] = "armv7-linux-musleabihf"
            cmake.definitions["CMAKE_CXX_COMPILER_TARGET"] = "armv7-linux-musleabihf"
            cmake.definitions["CMAKE_ASM_COMPILER_TARGET"] = "armv7-linux-musleabihf"
            cmake.definitions["CMAKE_TRY_COMPILE_TARGET_TYPE"] = "STATIC_LIBRARY"

            # TODO: base below on options
            cmake.definitions["LIBCXX_HAS_MUSL_LIBC"] = True
            cmake.definitions["LIBCXX_HAS_GCC_S_LIB"] = False
            cmake.definitions["LIBCXX_CXX_ABI"] = "libcxxabi"
            cmake.definitions["LIBCXX_USE_COMPILER_RT"] = True
            cmake.definitions["LIBCXXABI_USE_LLVM_UNWINDER"] = True
            cmake.definitions["LIBCXX_CXX_ABI_INCLUDE_PATHS"] = f"{self.deps_cpp_info['libcxxabi'].rootpath}/include"
            cmake.definitions["LIBCXX_CXX_ABI_LIBRARY_PATH"] = f"{self.deps_cpp_info['libcxxabi'].rootpath}/lib"

            cmake.configure(source_folder=self.name, build_folder=f"{self.name}-bin")
            cmake.build()
            cmake.install()

    def package(self):
        pass

    def package_info(self):
        pass

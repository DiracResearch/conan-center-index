import os
import stat
from conans import ConanFile, tools, CMake
from conans.errors import ConanException


class ClangLibcxxabiConan(ConanFile):
    name = "libcxxabi"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://libcxxabi.llvm.org/"
    license = "MIT"
    description = ("todo")
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True
    }
    topics = ("libc", "libcxxabi", "clang")

    def requirements(self):
        # self.requires.add(f"linux/4.19.176@dirac/testing")
        # TODO: if option libc musl
        self.requires.add(f"musl/1.2.2@dirac/testing")
        # TODO: based on option unwinder
        self.requires.add(f"libunwind-llvm/{self.version}@dirac/testing")

    def config_options(self):
        # TODO: Check options
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        pass

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename(f"{self.name}-{self.version}.src", self.name)

        # We need to fetch the headers for libcc
        tools.get(**self.conan_data["sources-libcxx"][self.version])
        os.rename(f"libcxx-{self.version}.src", "libcxx")

    def build(self):
        # TODO: if unwinder
        # We need to handle the dependencies and flags more "manual" because
        # building this libs is a bit different from the normal stuff.
        with tools.environment_append({"LDFLAGS": f"-fuse-ld=lld -L{self.deps_cpp_info['libunwind-llvm'].rootpath}/lib"}):
            cmake = CMake(self)
            cmake.definitions["CMAKE_SYSROOT"] = self.deps_cpp_info["musl"].rootpath
            cmake.definitions["CMAKE_C_COMPILER_TARGET"] = "armv7-linux-musleabihf"
            cmake.definitions["CMAKE_CXX_COMPILER_TARGET"] = "armv7-linux-musleabihf"
            cmake.definitions["CMAKE_ASM_COMPILER_TARGET"] = "armv7-linux-musleabihf"
            cmake.definitions["CMAKE_TRY_COMPILE_TARGET_TYPE"] = "STATIC_LIBRARY"
            cmake.definitions["LIBCXXABI_TARGET_TRIPLE"] = "armv7-linux-musleabihf"
            # TODO: if unwinder
            cmake.definitions["LIBCXXABI_USE_LLVM_UNWINDER"] = True
            # TODO: if musl compiler rt
            cmake.definitions["LIBCXXABI_USE_COMPILER_RT"] = True
            cmake.definitions["LIBCXXABI_LIBCXX_INCLUDES"] = f"{self.build_folder}/libcxx/include"
            cmake.configure(source_folder=self.name,
                            build_folder=f"{self.name}-bin")
            cmake.build()
            cmake.install()

    def package(self):
        # Headers not installed by CMake, copy manually
        self.copy(pattern="*.h", dst="include", src=f"{self.name}/include")

    def package_info(self):
        pass

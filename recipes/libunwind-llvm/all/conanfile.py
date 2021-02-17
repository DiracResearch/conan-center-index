import os
import stat
from conans import ConanFile, tools, AutoToolsBuildEnvironment, CMake
from conans.errors import ConanException

class ClangUnwindConan(ConanFile):
    name = "libunwind-llvm"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://llvm.org/"
    license = "MIT"
    description = ("todo")
    exports_sources = ["CMakeLists.txt"]
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
    }
    topics = ("libc", "unwinder", "clang", "llvm")

    def requirements(self):
        # TODO: if option libc musl
        self.requires.add(f"musl/1.2.2@dirac/testing")

    def config_options(self):
        # TODO: Check options
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        pass

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename(f"libunwind-{self.version}.src", self.name)

    def build(self):
        cmake = CMake(self)
        # TODO: if musl
        cmake.definitions["CMAKE_SYSROOT"] =  self.deps_cpp_info["musl"].rootpath
        cmake.definitions["CMAKE_C_COMPILER_TARGET"] = "armv7-linux-musleabihf"
        cmake.definitions["CMAKE_CXX_COMPILER_TARGET"] = "armv7-linux-musleabihf"
        cmake.definitions["CMAKE_ASM_COMPILER_TARGET"] = "armv7-linux-musleabihf"
        cmake.definitions["CMAKE_TRY_COMPILE_TARGET_TYPE"] = "STATIC_LIBRARY"
        # TODO: if musl uses complier-rt
        cmake.definitions["LIBUNWIND_USE_COMPILER_RT"] = True
        cmake.definitions["LLVM_ENABLE_LIBCXX"] = True

        cmake.configure(source_folder=self.name, build_folder=f"{self.name}-bin")
        cmake.build()
        cmake.install()

    def package(self):
        pass

    def package_info(self):
        pass

import os
import stat
from conans import ConanFile, tools, AutoToolsBuildEnvironment, CMake
from conans.errors import ConanException

class CompilerRtConan(ConanFile):
    name = "compiler-rt"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://compiler-rt.llvm.org/"
    license = "MIT"
    description = ("todo")
    generators = "cmake"
    exports_sources = ["CMakeLists.txt"]
    settings = "os", "arch", "compiler", "build_type"
    # TODO: option libc, musl or glibc
    options = {
        "shared": [True, False],
        "fPIC": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True
    }
    topics = ("compiler-rt", "clang")

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def requirements(self):
        # TODO: if musl
        self.requires.add(f"musl-headers/1.2.2@dirac/testing")

    def config_options(self):
        # TODO: Check options
        if self.settings.os == "Windows":
            del self.options.fPIC


    def configure(self):
        pass

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename(f"{self.name}-{self.version}.src", self._source_subfolder)

    def build(self):
        # Tips and tricks from: https://llvm.org/docs/HowToCrossCompileBuiltinsOnArm.html
        cmake = CMake(self)

        # TODO: if musl
        # When we are building compiler-rt we don't have a complete sysroot at this point
        # Just add a dummy to make sure any system headers are not used.
        cmake.definitions["CMAKE_SYSROOT"] = "dummy"

        cmake.definitions["CMAKE_C_COMPILER_TARGET"] = "armv7-linux-musleabihf"
        cmake.definitions["CMAKE_ASM_COMPILER_TARGET"] = "armv7-linux-musleabihf"
        cmake.definitions["COMPILER_RT_DEFAULT_TARGET_ONLY"] = True
        cmake.definitions["CMAKE_TRY_COMPILE_TARGET_TYPE"] = "STATIC_LIBRARY"
        # TODO: Try to build sanitizers also
        cmake.definitions["COMPILER_RT_BUILD_SANITIZERS"] = False
        cmake.definitions["COMPILER_RT_BUILD_XRAY"] = False
        cmake.definitions["COMPILER_RT_BUILD_LIBFUZZER"] = False
        cmake.definitions["COMPILER_RT_BUILD_PROFILE"] = False
        cmake.configure(build_folder=self._build_subfolder)
        cmake.build()
        cmake.install()

        # TODO: Fix hard coded `armhf`, regex or similar
        os.rename(f"{self.package_folder}/lib/linux/clang_rt.crtbegin-armhf.o", f"{self.package_folder}/lib/crtbeginS.o")
        os.rename(f"{self.package_folder}/lib/linux/clang_rt.crtend-armhf.o", f"{self.package_folder}/lib/crtendS.o")
        os.rename(f"{self.package_folder}/lib/linux/libclang_rt.builtins-armhf.a", f"{self.package_folder}/lib/libcompiler_rt.a")
        os.rmdir(f"{self.package_folder}/lib/linux")

    def package(self):
        pass

    def package_info(self):
        pass

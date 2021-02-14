import os
import stat
from conans import ConanFile, tools, AutoToolsBuildEnvironment, CMake
from conans.errors import ConanException


class MuslConan(ConanFile):
    name = "musl"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://musl.libc.org"
    license = "MIT"
    description = ("musl is lightweight, fast, simple, free, and strives to be "
                   "correct in the sense of standards-conformance and safety.")
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "rtlib": ["compiler-rt", "libgcc"]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "rtlib": "compiler-rt"
    }

    _source_subfolder = "source_subfolder"
    topics = ("libc")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        pass

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename("{}-{}".format(self.name, self.version), self._source_subfolder)

        # TODO: if rtlib compiler-rt
        # TODO: fetch version based on compiler version.
        # TODO: separate recipe
        clang_version = "10.0.0"
        tools.get(**self.conan_data["sources-compiler-rt"][clang_version])
        os.rename(f"compiler-rt-{clang_version}.src", "compiler-rt")

    def _build_compiler_rt(self):
        # Tips and tricks from: https://llvm.org/docs/HowToCrossCompileBuiltinsOnArm.html
        cmake = CMake(self)
        cmake.definitions["CMAKE_SYSROOT"] = self.package_folder
        cmake.definitions["CMAKE_C_COMPILER_TARGET"] = "armv7-linux-musleabihf"
        cmake.definitions["CMAKE_ASM_COMPILER_TARGET"] = "armv7-linux-musleabihf"
        cmake.definitions["COMPILER_RT_DEFAULT_TARGET_ONLY"] = True
        cmake.definitions["CMAKE_TRY_COMPILE_TARGET_TYPE"] = "STATIC_LIBRARY"
        cmake.configure(source_folder="compiler-rt/lib/builtins", build_folder="compiler-rt-builtins-bin")
        cmake.build()
        cmake.install()

    def _build_musl(self, shared):
        # TODO: Set LIBCC=" " based on self.options.rtlib

        extra_args = []

        if not shared:
            extra_args.append("--disable-shared")

        with tools.chdir(self._source_subfolder):
            autotools = AutoToolsBuildEnvironment(self)
            # TODO: pick out stuff from settings
            autotools.flags.append(f"--target=armv7-linux-musleabihf -mfloat-abi=hard -march=armv7 -mfpu=neon")
            # TODO: Create function to calculate lib name (libclang_rt.builtins-armv7)
            # TODO: Only if compiler-rt
            autotools.link_flags.append(f"-L{self.package_folder}/lib/linux/ -lclang_rt.builtins-armv7")
            # Even if we build shared we first need to build static libs,
            # then compiler-rt, then shared.
            autotools.configure(args=extra_args)
            autotools.make()
            autotools.install()

    def build(self):
        self._build_musl(shared=False)
        self._build_compiler_rt()
        # We can skip this step based on option shared
        self._build_musl(shared=True)

    def package(self):
        pass

    def package_info(self):
        pass
import os
from glob import glob
from conans import ConanFile, tools, CMake
from conans.errors import ConanException


class CompilerRtConan(ConanFile):
    name = "compiler-rt"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://compiler-rt.llvm.org/"
    license = "Apache License v2.0"
    description = ("Compiler runtime components from LLVM")
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}
    topics = ("compiler-rt", "clang", "bulit-ins")

    @property
    def _musl_abi(self):
        # Translate arch to musl abi
        abi = {"armv6": "musleabihf",
               "armv7": "musleabi",
               "armv7hf": "musleabihf"}.get(str(self.settings.arch))
        # Default to just "musl"
        if abi == None:
            abi = "musl"

        return abi

    @property
    def _musl_arch(self):
        # Translate conan arch to musl/clang arch
        arch = {"armv6": "arm",
                "armv8": "aarch64"}.get(str(self.settings.arch))
        # Default to a one-to-one mapping
        if arch == None:
            arch = str(self.settings.arch)
        return arch

    @property
    def _triplet(self):
        return "{}-linux-{}".format(self._musl_arch, self._musl_abi)

    def _force_host_context(self):
        # If this recipe is a "build_requires" in the host profile we force
        # the settings to instead be settings_target.
        # Ideally it should possible to express "force_host_context"
        # under [build_requires] in the profile.
        settings_target = getattr(self, 'settings_target', None)
        if settings_target:
            self.settings = settings_target
            # For some reason we need to populate these manually
            self.settings.arch_build = self.settings_build.arch
            self.settings.os_build = self.settings_build.os
            self.settings.arch_target = settings_target.arch
            self.settings.os_target = settings_target.os

    def configure(self):
        self._force_host_context()
        del self.settings.compiler.cppstd
        del self.settings.compiler.libcxx

    def package_id(self):
        del self.info.settings.arch_target
        del self.info.settings.os_target

    def requirements(self):
        self.requires(f"musl-headers/1.2.2@dirac/testing")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename(f"{self.name}-{self.version}.src", self.name)

    def build(self):
        # Tips and tricks from: https://llvm.org/docs/HowToCrossCompileBuiltinsOnArm.html
        cmake = CMake(self)

        # We use the musl headers as our, temporary, small sysroot
        cmake.definitions["CMAKE_SYSROOT"] = self.deps_cpp_info["musl-headers"].rootpath

        cmake.definitions["CMAKE_C_COMPILER_TARGET"] = self._triplet
        cmake.definitions["CMAKE_ASM_COMPILER_TARGET"] = self._triplet
        cmake.definitions["COMPILER_RT_DEFAULT_TARGET_ONLY"] = True
        cmake.definitions["CMAKE_TRY_COMPILE_TARGET_TYPE"] = "STATIC_LIBRARY"
        # TODO: Try to build sanitizers also
        cmake.definitions["COMPILER_RT_BUILD_SANITIZERS"] = False
        cmake.definitions["COMPILER_RT_BUILD_XRAY"] = False
        cmake.definitions["COMPILER_RT_BUILD_LIBFUZZER"] = False
        cmake.definitions["COMPILER_RT_BUILD_PROFILE"] = False
        cmake.configure(source_folder=self.name,
                        build_folder="compiler-rt-bin")
        cmake.build()
        cmake.install()

    def package(self):
        lib_dir = os.path.join(self.package_folder, "lib")
        linux_dir = os.path.join(lib_dir, "linux")
        crt_begin = glob(os.path.join(linux_dir, "clang_rt.crtbegin*"))[0]
        crt_end = glob(os.path.join(linux_dir, "clang_rt.crtend*"))[0]
        clang_rt = glob(os.path.join(linux_dir, "libclang_rt*"))[0]

        os.rename(crt_begin, os.path.join(lib_dir, "crtbeginS.o"))
        os.rename(crt_end, os.path.join(lib_dir, "crtendS.o"))
        os.rename(clang_rt, os.path.join(lib_dir, "libcompiler_rt.a"))
        os.rmdir(linux_dir)

        # Copy the license files
        self.copy("LICENSE.TXT", src="compiler-rt", dst="licenses")

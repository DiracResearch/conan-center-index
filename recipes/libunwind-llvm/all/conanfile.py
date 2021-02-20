import os
from conans import ConanFile, tools, CMake
from conans.errors import ConanException


class ClangUnwindConan(ConanFile):
    name = "libunwind-llvm"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://llvm.org/"
    license = "Apache License v2.0"
    description = ("Unwind library from LLVM")
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
    topics = ("unwinder", "clang", "llvm")

    @property
    def _host_settings(self):
        settings_target = getattr(self, 'settings_target', None)
        if settings_target is None:
            settings_target = self.settings
        return settings_target

    @property
    def _conan_arch(self):
        settings_target = getattr(self, 'settings_target', None)
        if settings_target is None:
            settings_target = self.settings
        return settings_target.arch

    @property
    def _musl_abi(self):
        # Translate arch to musl abi
        abi = {"armv6": "musleabihf",
               "armv7": "musleabi",
               "armv7hf": "musleabihf"}.get(str(self._conan_arch))
        # Default to just "musl"
        if abi == None:
            abi = "musl"

        return abi

    @property
    def _musl_arch(self):
        # Translate conan arch to musl/clang arch
        arch = {"armv6": "arm",
                "armv8": "aarch64"}.get(str(self._conan_arch))
        # Default to a one-to-one mapping
        if arch == None:
            arch = self._conan_arch
        return arch

    @property
    def _triplet(self):
        return "{}-linux-{}".format(self._musl_arch, self._musl_abi)

    def requirements(self):
        self.requires("musl/1.2.2@dirac/testing")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename("libunwind-{}.src".format(self.version), self.name)

    def build(self):
        with tools.environment_append({"LDFLAGS": "-fuse-ld=lld"}):
            cmake = CMake(self)
            cmake.definitions["CMAKE_SYSROOT"] = self.deps_cpp_info["musl"].rootpath
            cmake.definitions["CMAKE_C_COMPILER_TARGET"] = self._triplet
            cmake.definitions["CMAKE_CXX_COMPILER_TARGET"] = self._triplet
            cmake.definitions["CMAKE_ASM_COMPILER_TARGET"] = self._triplet
            cmake.definitions["CMAKE_TRY_COMPILE_TARGET_TYPE"] = "STATIC_LIBRARY"
            cmake.definitions["LIBUNWIND_USE_COMPILER_RT"] = True
            cmake.definitions["LLVM_ENABLE_LIBCXX"] = True

            cmake.configure(source_folder=self.name,
                            build_folder="{}-bin".format(self.name))
            cmake.build()
            cmake.install()

    def package(self):
        # Copy the license files
        self.copy("LICENSE.TXT", src=self.name, dst="licenses")

    def package_id(self):
        # Copy settings from host env.
        # Need to do this to be able to have llvm-sysroot in "build_requires" in the profile
        self.info.settings.clear()
        self.info.settings.compiler = self._host_settings.compiler
        self.info.settings.compiler.version = self._host_settings.compiler.version
        self.info.settings.compiler.libc = self._host_settings.compiler.libc
        self.info.settings.compiler.libcxx = self._host_settings.compiler.libcxx
        self.info.settings.build_type = self._host_settings.build_type
        self.info.settings.os = self._host_settings.os
        self.info.settings.arch = self._host_settings.arch

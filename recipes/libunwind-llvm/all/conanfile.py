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

    def package_id(self):
        del self.info.settings.arch_target
        del self.info.settings.os_target

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

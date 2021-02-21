import os
from conans import ConanFile, tools, CMake
from conans.errors import ConanException


class ClangLibcxxConan(ConanFile):
    name = "libcxx"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://libcxx.llvm.org/"
    license = "Apache License v2.0"
    description = ("todo")
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}
    topics = ("libc", "libcxx", "clang")

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

    def package_id(self):
        del self.info.settings.arch_target
        del self.info.settings.os_target

    def requirements(self):
        self.requires("musl/1.2.2@dirac/testing")
        self.requires("libcxxabi/{}@dirac/testing".format(self.version))

    def config_options(self):
        # TODO: Check options
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        pass

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename("{}-{}.src".format(self.name, self.version), self.name)

    def build(self):
        # TODO: if unwinder
        # We need to handle the dependencies and flags more "manual" because
        # building this libs is a bit different from the normal stuff.
        with tools.environment_append({"LDFLAGS": "-fuse-ld=lld -lcompiler_rt -L{}/lib".format(self.deps_cpp_info['libunwind-llvm'].rootpath)}):
            cmake = CMake(self)
            cmake.definitions["CMAKE_SYSROOT"] = self.deps_cpp_info["musl"].rootpath
            cmake.definitions["CMAKE_C_COMPILER_TARGET"] = self._triplet
            cmake.definitions["CMAKE_CXX_COMPILER_TARGET"] = self._triplet
            cmake.definitions["CMAKE_ASM_COMPILER_TARGET"] = self._triplet
            cmake.definitions["CMAKE_TRY_COMPILE_TARGET_TYPE"] = "STATIC_LIBRARY"

            # TODO: base below on options
            cmake.definitions["LIBCXX_HAS_MUSL_LIBC"] = True
            cmake.definitions["LIBCXX_HAS_GCC_LIB"] = False
            cmake.definitions["LIBCXX_HAS_GCC_S_LIB"] = False
            cmake.definitions["LIBCXX_USE_COMPILER_RT"] = False
            cmake.definitions["LIBCXX_CXX_ABI"] = "libcxxabi"
            cmake.definitions["LIBCXXABI_USE_LLVM_UNWINDER"] = True
            cmake.definitions["LIBCXX_CXX_ABI_INCLUDE_PATHS"] = os.path.join(
                self.deps_cpp_info['libcxxabi'].rootpath, "include")
            cmake.definitions["LIBCXX_CXX_ABI_LIBRARY_PATH"] = os.path.join(
                self.deps_cpp_info['libcxxabi'].rootpath, "lib")

            cmake.configure(source_folder=self.name,
                            build_folder="{}-bin".format(self.name))
            cmake.build()
            cmake.install()

    def package(self):
        # Copy the license files
        self.copy("LICENSE.TXT", src=self.name, dst="licenses")

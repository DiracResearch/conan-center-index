import os
import stat
from conans import ConanFile, tools, CMake
from conans.errors import ConanException


class ClangLibcxxabiConan(ConanFile):
    name = "libcxxabi"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://libcxxabi.llvm.org/"
    description = (
        "libc++abi is a new implementation of low level support for a standard C++ library.")
    license = "Apache License v2.0"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True
    }
    topics = ("libcxxabi", "clang")

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
        self.requires("libunwind-llvm/{}@dirac/testing".format(self.version))

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename("{}-{}.src".format(self.name, self.version), self.name)

        # We need to fetch the headers for libcxx
        # Had this in "conandata.yml" before but CCI doesn't allow it.
        # Could create a "libcxx-header target maybe..."
        libcxx_url = "https://github.com/llvm/llvm-project/releases/download/llvmorg-10.0.0/libcxx-10.0.0.src.tar.xz"
        libcxx_sha = "270f8a3f176f1981b0f6ab8aa556720988872ec2b48ed3b605d0ced8d09156c7"
        tools.get(url=libcxx_url, sha256=libcxx_sha)
        os.rename("libcxx-{}.src".format(self.version), "libcxx")

    def build(self):
        # We need to handle the dependencies and flags more "manual" because
        # building this libs is a bit different from the normal stuff.
        with tools.environment_append({"LDFLAGS": "-fuse-ld=lld -L{}/lib".format(self.deps_cpp_info['libunwind-llvm'].rootpath)}):
            cmake = CMake(self)
            cmake.definitions["CMAKE_SYSROOT"] = self.deps_cpp_info["musl"].rootpath
            cmake.definitions["CMAKE_C_COMPILER_TARGET"] = self._triplet
            cmake.definitions["CMAKE_CXX_COMPILER_TARGET"] = self._triplet
            cmake.definitions["CMAKE_ASM_COMPILER_TARGET"] = self._triplet
            cmake.definitions["CMAKE_TRY_COMPILE_TARGET_TYPE"] = "STATIC_LIBRARY"
            cmake.definitions["LIBCXXABI_TARGET_TRIPLE"] = self._triplet
            cmake.definitions["LIBCXXABI_USE_LLVM_UNWINDER"] = True
            cmake.definitions["LIBCXXABI_USE_COMPILER_RT"] = True
            cmake.definitions["LIBCXXABI_LIBCXX_INCLUDES"] = "{}/libcxx/include".format(
                self.build_folder)
            cmake.configure(source_folder=self.name,
                            build_folder="{}-bin".format(self.name))
            cmake.build()
            cmake.install()

    def package(self):
        # Headers not installed by CMake, copy manually
        self.copy(pattern="*.h", dst="include",
                  src="{}/include".format(self.name))

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

from conans import ConanFile, tools
from conans.errors import ConanInvalidConfiguration
import os

class LlvmSysrootConan(ConanFile):
    name = "llvm-sysroot"
    description = "todo"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://llvm.org/"
    topics = ("llvm", "clang", "toolchain", "sysroot", "cross compile")
    license = "Apache-2.0"
    settings = "os", "arch", "compiler", "build_type"
    keep_imports = True

    # TODO: Check flags and options and make sure they are sane

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
        abi = {"armv6": "musleabi",
               "armv7": "musleabi",
               "armv7hf": "musleabihf"}.get(str(self._conan_arch))
        # Default to just "musl"
        if abi == None:
            abi = "musl"

        return abi

    @property
    def _musl_arch(self):
        # Translate conan arch to musl/clang arch
        arch = {"armv8": "aarch64"}.get(str(self._conan_arch))
        # Default to a one-to-one mapping
        if arch == None:
            arch = self._conan_arch
        return arch

    @property
    def _triplet(self):
        return "{}-linux-{}".format(self._musl_arch, self._musl_abi)

    def requirements(self):
        self.requires(f"musl-headers/1.2.2@dirac/testing", override=True)
        self.requires(f"musl-headers/1.2.2@dirac/testing", override=True)
        self.requires(f"compiler-rt/{self.version}@dirac/testing", override=True)
        self.requires(f"libcxx/{self.version}@dirac/testing")

    def imports(self):
        # Repackage the sysroot for consumption
        self.copy("*", src="lib", dst=f"{self.package_folder}/lib")
        self.copy("*", src="include", dst=f"{self.package_folder}/include")
        self.copy("*", src="bin", dst=f"{self.package_folder}/bin")
        self.copy("*", src="licenses", dst=f"{self.package_folder}/licenses")

    def source(self):
        pass

    def build(self):
        pass

    def package(self):
        pass

    def package_id(self):
        # Copy settings from host env.
        # Need to do this to be able to have llvm-sysroot in "build_requires" in the profile
        # Could probably be solved if it was possible to express "force_host_context"
        # under [build_requires] in the profile.
        self.info.settings.clear()
        self.info.settings.compiler = self._host_settings.compiler
        self.info.settings.compiler.version = self._host_settings.compiler.version
        self.info.settings.compiler.libc = self._host_settings.compiler.libc
        self.info.settings.compiler.libcxx = self._host_settings.compiler.libcxx
        self.info.settings.build_type = self._host_settings.build_type
        self.info.settings.os = self._host_settings.os
        self.info.settings.arch = self._host_settings.arch

    def package_info(self):
        sysroot = self.package_folder

        self.output.info(f"Creating SYSROOT environment variable: {sysroot}")
        self.env_info.SYSROOT = sysroot
        self.output.info(f"Creating self.cpp_info.sysroot: {sysroot}")
        self.cpp_info.sysroot = sysroot
        self.output.info('Creating CHOST environment variable: %s' % self._triplet)
        self.env_info.CHOST = self._triplet

        self.env_info.CFLAGS = f"-target {self._triplet} --sysroot={sysroot}"
        self.env_info.CXXFLAGS = f"-target {self._triplet} --sysroot={sysroot} -I{sysroot}/include/c++/v1"

        # TODO: static should be and option. Or left up to the consumer?
        # TODO: Distinguish between ldflags for c and c++?
        # TODO: Escape paths? Use ""?
        self.env_info.LDFLAGS = "-fuse-ld=lld -nostdlib -lunwind -lc -lc++abi -lc++ "\
                                "-lcompiler_rt "\
                                f"{sysroot}/lib/crt1.o "\
                                f"{sysroot}/lib/crtendS.o "\
                                f"{sysroot}/lib/crtn.o "\
                                "-static"

        # TODO: Set CC/LD/AR/RANLIB here or is it up to the profile to decide?
        # TODO: Test with auto tools
        # TODO: Test with a bunch of packages

        # TODO: Might have to do RPATH things


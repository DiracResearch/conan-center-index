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
    def _triplet(self):
        return self.deps_cpp_info["musl-headers"].CHOST

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
        # We re-package so no transitive requires
        self.info.requires.clear()

    def requirements(self):
        self.requires("libcxx/{}@dirac/testing".format(self.version))

    def imports(self):
        # Repackage the sysroot for consumption
        self.copy("*", src="lib", dst="lib")
        self.copy("*", src="include", dst="include")
        self.copy("*", src="bin", dst="bin")
        self.copy("*", src="licenses", dst="licenses")

    def package(self):
        self.copy("*")

    def package_info(self):
        # Setup the final sysroot and compiler flags
        sysroot = self.package_folder

        self.output.info(
            'Creating CHOST environment variable: %s' % self._triplet)
        self.env_info.CHOST = self._triplet

        cflags = "-nostdinc -target {0} --sysroot={1} -I{1}/include".format(
            self._triplet, sysroot)
        self.env_info.CFLAGS = cflags
        self.env_info.ASFLAGS = cflags
        self.env_info.ASMFLAGS = cflags
        self.env_info.CXXFLAGS = "-I{}/include/c++/v1 {}".format(
            sysroot, cflags)
        # TODO: asm flags

        # TODO: static should be and option. Or left up to the consumer?
        # TODO: Distinguish between ldflags for c and c++?
        # TODO: Escape paths? Use ""?
        self.env_info.LDFLAGS = "-fuse-ld=lld -nostdlib -lunwind -lc -lc++abi -lc++ "\
                                "-lcompiler_rt "\
                                "{0}/lib/crt1.o " \
                                "{0}/lib/crtendS.o " \
                                "{0}/lib/crtn.o " \
                                "-static".format(sysroot)

        # TODO: Set CC/LD/AR/RANLIB here or is it up to the profile to decide?
        # TODO: Test with auto tools
        # TODO: Test with a bunch of packages

        # TODO: Might have to do RPATH things

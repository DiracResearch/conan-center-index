import os
from conans import ConanFile, tools, AutoToolsBuildEnvironment
from conans.errors import ConanException, ConanInvalidConfiguration


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
        "fPIC": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True
    }
    topics = ("libc", "musl")
    keep_imports = True

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
        del self.settings.compiler.cppstd
        del self.settings.compiler.libcxx

    def package_id(self):
        del self.info.settings.arch_target
        del self.info.settings.os_target

    def requirements(self):
        self.requires(f"compiler-rt/10.0.0@dirac/testing")

    def imports(self):
        # We need the libraries and object files from compile-rt to create a
        # temporary "sysroot" to build the rest of the sysroot (cxx for example)
        self.copy("*", src="lib", dst=f"{self.package_folder}/lib")

        # Copy linux headers to package folder. The package folder is used as
        # the "sysroot"
        self.copy("*.h", src="include", dst=f"{self.package_folder}/include")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename(f"{self.name}-{self.version}", self.name)

    def build(self):
        with tools.chdir(self.name), \
             tools.environment_append({"LIBCC": "-lcompiler_rt"}):
            autotools = AutoToolsBuildEnvironment(self)
            autotools.configure(target=self._triplet)
            autotools.make()
            autotools.install()

    def package(self):
        # Copy the license files
        self.copy("COPYRIGHT", src="musl", dst="licenses")

    def package_info(self):
        # Setup the third sysroot and compiler flags
        # This is a sysroot with libc and linux headers together with compiler rt built-ins and crt
        # and a libc
        sysroot = self.package_folder
        self.cpp_info.CHOST = self._triplet
        flags = ["-nostdinc", "-target", self._triplet, f"--sysroot={sysroot}", f"-I{sysroot}/include"]
        self.cpp_info.cflags = flags
        self.cpp_info.cxxflags = flags

        linker_flags = ["-fuse-ld=lld", "-nostdlib", "-lc", "-lcompiler_rt",
                        f"{sysroot}/lib/crt1.o", f"{sysroot}/lib/crtendS.o", f"{sysroot}/lib/crtn.o", "-static"]
        self.cpp_info.sharedlinkflags = linker_flags
        self.cpp_info.exelinkflags = linker_flags

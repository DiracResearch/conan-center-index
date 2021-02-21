import os
from conans import ConanFile, tools
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
        # Never got it to work with AutoToolsBuildEnvironment.
        # Trick to get the correct logic when settings_target is needed...
        with tools.chdir(self.name), \
                tools.environment_append({"LIBCC": "-lcompiler_rt"}), \
                tools.environment_append({"CFLAGS": f"-target {self._triplet}"}), \
                tools.environment_append({"LDFLAGS": f"-fuse-ld=lld -L{self.deps_cpp_info['compiler-rt'].rootpath}/lib"}):
            self.run(
                f"./configure --target={self._triplet} --prefix={self.package_folder}")
            self.run("make")
            self.run("make install")

    def package(self):
        # Copy the license files
        self.copy("COPYRIGHT", src="musl", dst="licenses")

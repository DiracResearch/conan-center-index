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
        return f"{self._musl_arch}-linux-{self._musl_abi}"

    def requirements(self):
        self.requires(f"compiler-rt/10.0.0@dirac/testing")
        self.requires(f"linux-headers/4.19.176@dirac/testing")

    def imports(self):
        # We need the libraries and object files from compile-rt to create a
        # temporary "sysroot" to build the rest of the sysroot (cxx for example)
        self.copy("*", src="lib", dst=f"{self.package_folder}/lib")

        # Copy linux headers to package folder. The package folder is used as
        # the "sysroot"
        self.copy("*.h", src="include", dst=f"{self.package_folder}/include")

    def configure(self):
        del self.settings.compiler.cppstd
        del self.settings.compiler.libcxx

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

    def package_id(self):
        # Copy settings from host env.
        # Need to do this to be able to have llvm-sysroot in "build_requires" in the profile
        self.info.settings.clear()
        self.info.settings.compiler = self._host_settings.compiler
        self.info.settings.compiler.version = self._host_settings.compiler.version
        self.info.settings.compiler.libc = self._host_settings.compiler.libc
        self.info.settings.build_type = self._host_settings.build_type
        self.info.settings.os = self._host_settings.os
        self.info.settings.arch = self._host_settings.arch

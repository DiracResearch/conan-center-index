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
        "target": "ANY",
        "shared": [True, False],
        "fPIC": [True, False],
        "rtlib": ["compiler-rt", "libgcc"]
    }
    default_options = {
        "target": None,
        "shared": False,
        "fPIC": True,
        "rtlib": "compiler-rt"
    }
    topics = ("libc", "libcxx", "musl", "clang")
    keep_imports = True

    @property
    def _llvm_triplet(self):
        arch = self.settings_target.arch  # Translate names?
        abi = 'musleabihf'  # TODO: base on settings
        return f"{arch}-linux-{abi}"

    def configure(self):
        settings_target = getattr(self, 'settings_target', None)
        if settings_target is None:
            # It is running in 'host', so Conan is compiling this package
            if not self.options.target:
                raise ConanInvalidConfiguration(
                    "A value for option 'target' has to be provided")
        else:
            self.options.target = self._llvm_triplet

    def requirements(self):
        # TODO: if option compiler-rt
        # TODO: use clang version info
        self.requires.add(f"compiler-rt/10.0.0@dirac/testing")

        # TODO: should probably be a "build requires" with host context
        self.requires.add(f"linux-headers/4.19.176@dirac/testing")

    def imports(self):
        # TODO: if compiler-rt
        # We need the libraries and object files from compile-rt to create a
        # temporary "sysroot" to build the rest of the sysroot (cxx for example)
        self.copy("*", src="lib", dst=f"{self.package_folder}/lib")

        # Copy linux headers to package folder. The package folder is used as
        # the "sysroot"
        self.copy("*.h", src="include", dst=f"{self.package_folder}/include")

    def config_options(self):
        # TODO: Check options
        if self.settings.os == "Windows":
            del self.options.fPIC

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename(f"{self.name}-{self.version}", self.name)

    def build(self):
        # Never got it to work with AutoToolsBuildEnvironment.
        # Trick to get the correct logic when settings_target is needed...
        with tools.chdir(self.name), \
                tools.environment_append({"LIBCC": "-lcompiler_rt"}), \
                tools.environment_append({"CFLAGS": f"--target={self.options.target}"}), \
                tools.environment_append({"LDFLAGS": f"-fuse-ld=lld -L{self.deps_cpp_info['compiler-rt'].rootpath}/lib"}):
            self.run(
                f"./configure --target={self.options.target} --prefix={self.package_folder}")
            self.run("make")
            self.run("make install")

    def package(self):
        pass

    def package_info(self):
        pass

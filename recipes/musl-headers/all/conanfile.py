import os
from conans import ConanFile, tools
from conans.errors import ConanException, ConanInvalidConfiguration

class MuslHeadersConan(ConanFile):
    name = "musl-headers"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://musl.libc.org"
    license = "MIT"
    description = ("musl is lightweight, fast, simple, free, and strives to be "
                   "correct in the sense of standards-conformance and safety.")
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "target": "ANY",
        "shared": [True, False],
        "fPIC": [True, False]
    }
    default_options = {
        "target": None,
        "shared": False,
        "fPIC": True,
    }
    topics = ("libc", "musl")
    keep_imports = True

    @property
    def _llvm_triplet(self):
        arch = self.settings_target.arch # TODO: Translate names?
        abi = 'musleabihf' # TODO: base on settings
        return f"{arch}-linux-{abi}"

    def configure(self):
        settings_target = getattr(self, 'settings_target', None)
        if settings_target is None:
            # It is running in 'host', so Conan is compiling this package
            if not self.options.target:
                raise ConanInvalidConfiguration("A value for option 'target' has to be provided")
        else:
            self.options.target = self._llvm_triplet

    def config_options(self):
        # TODO: Check options
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        pass

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename(f"musl-{self.version}", "musl")

    def build(self):
        # TODO: winbash = true?
        with tools.chdir("musl"), \
                tools.environment_append({"CFLAGS": f"--target={self.options.target}"}):
            self.run(
                f"./configure --target={self.options.target} --prefix={self.package_folder}")
            self.run("make install-headers")

    def package(self):
        pass

    def package_info(self):
        pass

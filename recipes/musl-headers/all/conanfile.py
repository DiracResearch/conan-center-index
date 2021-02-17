import os
import stat
from conans import ConanFile, tools, AutoToolsBuildEnvironment, CMake
from conans.errors import ConanException

class MuslHeadersConan(ConanFile):
    name = "musl-headers"
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
        "fPIC": True,
    }
    topics = ("libc", "musl")
    keep_imports = True

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
        with tools.chdir("musl"):
            autotools = AutoToolsBuildEnvironment(self)
            # TODO: pick out stuff from settings
            autotools.flags.append(f"--target=armv7-linux-musleabihf -mfloat-abi=hard -march=armv7 -mfpu=neon")
            autotools.configure()
            autotools.make(target="install-headers")

    def package(self):
        pass

    def package_info(self):
        pass

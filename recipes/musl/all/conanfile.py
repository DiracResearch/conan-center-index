import os
import stat
from conans import ConanFile, tools, AutoToolsBuildEnvironment
from conans.errors import ConanException


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
        "fPIC": [True, False],
        "rtlib": ["compiler-rt", "libgcc"]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "rtlib": "compiler-rt"
    }

    _source_subfolder = "source_subfolder"
    topics = ("libc")

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename("{}-{}".format(self.name, self.version), self._source_subfolder)

    def build(self):
        with tools.chdir(self._source_subfolder):
            autotools = AutoToolsBuildEnvironment(self)
            # TODO: pick out stuff from settings
            autotools.flags.append(f"--target=armv7l-linux-musleabihf -mfloat-abi=hard -march=armv7l -mfpu=neon")
            autotools.link_flags.append(f"--rtlib={self.options.rtlib}")
            # Even if we build shared we first need to build static libs,
            # then compiler-rt, then shared.
            autotools.configure(target="arm", args=["--disable-shared"])
            autotools.make()
            autotools.install()

    def package(self):
        pass

    def package_info(self):
        pass
import os
import stat
from conans import ConanFile, tools, AutoToolsBuildEnvironment
from conans.errors import ConanException

class MuslConan(ConanFile):
    name = "linux"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.kernel.org/"
    license = "GPL"
    description = ("todo")
    settings = "os", "arch", "compiler", "build_type"
    no_copy_source=True
    options = {
        "shared": [True, False],
        "fPIC": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True
    }

    topics = ("linux")

    def config_options(self):
        # TODO: Check options
        pass

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])

    def build(self):
        with tools.chdir(f"{self.source_folder}/{self.name}-{self.version}"):
            autotools = AutoToolsBuildEnvironment(self)
            # We only need the headers from linux so run the 'headers_install' target
            autotools.make(target="headers_install", args=[f"INSTALL_HDR_PATH={self.package_folder}"])

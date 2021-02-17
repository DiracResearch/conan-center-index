import os
import stat
from conans import ConanFile, tools, AutoToolsBuildEnvironment, CMake
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
    topics = ("libc", "libcxx", "musl", "clang")
    keep_imports = True

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

    def configure(self):
        pass

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename(f"{self.name}-{self.version}", self.name)

    def build(self):
        with tools.chdir(self.name):
            autotools = AutoToolsBuildEnvironment(self)
            # TODO: pick out stuff from settings
            autotools.flags.append(f"--target=armv7-linux-musleabihf -mfloat-abi=hard -march=armv7 -mfpu=neon")
            #autotools.link_flags.append(f"-L{self.package_folder}/lib/")
            autotools.configure()
            autotools.make()
            autotools.install()

    def package(self):
        pass

    def package_info(self):
        pass

import os
from conans import ConanFile, tools, AutoToolsBuildEnvironment


class LinuxHeadersConan(ConanFile):
    name = "linux-headers"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.kernel.org/"
    license = "GPLv2"
    description = ("Headers for the Linux Kernel operating system")
    settings = "os", "arch", "compiler", "build_type"
    topics = ("linux", "kernel", "headers")
    no_copy_source = True

    def package_id(self):
        self.info.header_only()

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])

    def build(self):
        with tools.chdir(f"{self.source_folder}/linux-{self.version}"):
            autotools = AutoToolsBuildEnvironment(self)
            # We only want the headers from linux so run the 'headers_install' target
            autotools.make(target="headers_install", args=[
                           f"INSTALL_HDR_PATH={self.build_folder}"])

    def package(self):
        self.copy("*.h", src="include", dst="include")

        # Copy the license files
        self.copy(
            pattern="*", src=os.path.join(f"linux-{self.version}", "LICENSES"), dst="licenses")

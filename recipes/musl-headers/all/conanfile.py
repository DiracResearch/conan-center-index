import os
from conans import ConanFile, tools


class MuslHeadersConan(ConanFile):
    name = "musl-headers"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://musl.libc.org"
    license = "MIT"
    description = ("musl is lightweight, fast, simple, free, and strives to be "
                   "correct in the sense of standards-conformance and safety.")
    settings = "os", "arch", "compiler", "build_type"
    topics = ("libc", "musl")

    @property
    def _target_arch(self):
        # TODO: Need to translate conan/musl arch names?
        settings_target = getattr(self, 'settings_target', None)
        if settings_target is None:
            settings_target = self.settings
        return settings_target.arch

    @property
    def _triplet(self):
        arch = self._target_arch
        abi = 'musleabihf'  # TODO: base on settings
        return f"{arch}-linux-{abi}"

    def configure(self):
        del self.settings.compiler.cppstd
        del self.settings.compiler.libcxx

    def package_id(self):
        # Even though this is a header only recipe the headers generated
        # by make are different based on arch. So we need to include arch in
        # the package id.
        del self.info.settings.compiler
        del self.info.settings.build_type
        del self.info.settings.os
        self.info.arch = self._target_arch

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename(f"musl-{self.version}", "musl")

    def build(self):
        # TODO: winbash = true?
        with tools.chdir("musl"), \
                tools.environment_append({"CFLAGS": f"-target {self._triplet}"}):
            self.run(
                f"./configure --target={self._triplet} --prefix={self.package_folder}")
            self.run("make install-headers")

    def package(self):
        # Copy the license files
        self.copy("COPYRIGHT", src="musl", dst="licenses")

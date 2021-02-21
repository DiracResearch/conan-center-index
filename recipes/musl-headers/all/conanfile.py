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
    keep_imports = True

    @property
    def _conan_arch(self):
        settings_target = getattr(self, 'settings_target', None)
        if settings_target is None:
            settings_target = self.settings
        return settings_target.arch

    @property
    def _musl_abi(self):
        # Translate arch to musl abi
        abi = {"armv6": "musleabihf",
               "armv7": "musleabi",
               "armv7hf": "musleabihf"}.get(str(self._conan_arch))
        # Default to just "musl"
        if abi == None:
            abi = "musl"

        return abi

    @property
    def _musl_arch(self):
        # Translate conan arch to musl/clang arch
        arch = {"armv6": "arm",
                "armv8": "aarch64"}.get(str(self._conan_arch))
        # Default to a one-to-one mapping
        if arch == None:
            arch = self._conan_arch
        return arch

    @property
    def _triplet(self):
        return f"{self._musl_arch}-linux-{self._musl_abi}"

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
        self.info.settings.arch = self._conan_arch

    def requirements(self):
        self.requires(f"linux-headers/4.19.176@dirac/testing")

    def imports(self):
        # Copy linux headers to package folder. The package folder is used as
        # the "sysroot"
        self.copy("*.h", src="include", dst=f"{self.package_folder}/include")

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

    def package_info(self):
        # Setup the first sysroot and compiler flags
        # This is a sysroot with just libc and linux headers
        sysroot = self.package_folder
        self.cpp_info.CHOST = self._triplet
        flags = ["-nostdinc", "-target", self._triplet, f"--sysroot={sysroot}", f"-I{sysroot}/include"]
        self.cpp_info.cflags = flags
        self.cpp_info.cxxflags = flags

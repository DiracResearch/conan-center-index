from conans import ConanFile, tools
from conans.errors import ConanInvalidConfiguration
import os

class LlvmSysrootConan(ConanFile):
    name = "llvm-sysroot"
    description = "The Android NDK is a toolset that lets you implement parts of your app in " \
                  "native code, using languages such as C and C++"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://llvm.org/"
    topics = ("llvm", "clang", "toolchain", "sysroot", "cross compile")
    license = "Apache-2.0"
    exports_sources = ["cmake/llvm-toolchain.cmake"]
    settings = "os", "arch", "compiler", "build_type"
    keep_imports = True

    options = {
        "target": "ANY",
        "libc": ["musl/1.2.2"]
    }
    default_options = {
        "target": None,
        "libc": "musl/1.2.2"
    }

    # TODO: Check flags and options and make sure they are sane

    @property
    def _llvm_triplet(self):
        arch = self.settings_target.arch  # Translate names?
        abi = 'musleabihf'  # TODO: base on options/settings
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
        self.requires(f"{self.options.libc}@dirac/testing")
        self.requires(f"libcxx/{self.version}@dirac/testing")

    def imports(self):
        # Repackage the sysroot for consumption
        self.copy("*", src="lib", dst=f"{self.package_folder}/lib")
        self.copy("*", src="include", dst=f"{self.package_folder}/include")
        self.copy("*", src="bin", dst=f"{self.package_folder}/bin")

    def source(self):
        pass

    def build(self):
        pass

    def package(self):
        self.copy("*", src="cmake", dst=f"{self.package_folder}/cmake")

    def package_id(self):
        self.info.requires.clear()
        self.info.settings.clear()

    def package_info(self):
        sysroot = self.package_folder

        self.output.info(f"Creating CONAN_CMAKE_SYSROOT environment variable: {sysroot}")
        self.env_info.CONAN_CMAKE_SYSROOT = sysroot
        self.output.info(f"Creating SYSROOT environment variable: {sysroot}")
        self.env_info.SYSROOT = sysroot
        self.output.info(f"Creating self.cpp_info.sysroot: {sysroot}")
        self.cpp_info.sysroot = sysroot
        self.output.info('Creating CHOST environment variable: %s' % self._llvm_triplet)
        self.env_info.CHOST = self._llvm_triplet

        # TODO: static should be and option. Or left up to the consumer?
        # TODO: Distinguish between ldflags for c and c++?
        # TODO: Escape paths? Use ""?
        self.env_info.LDFLAGS = "-fuse-ld=lld -nostdlib -lunwind -lc -lc++abi -lc++ "\
                                "-lcompiler_rt "\
                                f"{sysroot}/lib/crt1.o "\
                                f"{sysroot}/lib/crtendS.o "\
                                f"{sysroot}/lib/crtn.o "\
                                "-static"
        self.env_info.CXXFLAGS = f"-I{sysroot}/include/c++/v1"

        # TODO: Set CC/LD/AR/RANLIB here or is it up to the profile to decide?
        # TODO: Test with auto tools
        # TODO: Test with a bunch of packages

        # TODO: Might have to do RPATH things

        toolchain = os.path.join(self.package_folder, "cmake", "llvm-toolchain.cmake")
        self.output.info('Creating CONAN_CMAKE_TOOLCHAIN_FILE environment variable: %s' % toolchain)
        self.env_info.CONAN_CMAKE_TOOLCHAIN_FILE = toolchain

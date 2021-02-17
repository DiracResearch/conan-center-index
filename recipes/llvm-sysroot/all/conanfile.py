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

    options = {"libc": ["musl"]}
    default_options = {"libc": "musl"}

    # TODO: Check flags and options and make sure they are sane

    @property
    def _llvm_triplet(self):
        arch = self.settings.arch # TODO: settings_target? Translate names?
        abi = 'musleabihf' # TODO: base on settings
        return f"{arch}-linux-{abi}"

        # Info on triplets
        # https://llvm.org/doxygen/Triple_8h_source.html
        # https://docs.conan.io/en/latest/reference/config_files/settings.yml.html#architectures
        # https://github.com/richfelker/musl-cross-make/blob/master/README.md#supported-targets

    def build_requirements(self):
        self.build_requires("musl/1.2.2@dirac/testing", force_host_context=True)
        self.build_requires(f"libcxx/{self.version}@dirac/testing", force_host_context=True)

    def imports(self):
        # Repackage the sysroot for consumption
        self.copy("*", src="lib", dst=f"{self.package_folder}/lib")
        self.copy("*", src="include", dst=f"{self.package_folder}/include")
        self.copy("*", src="bin", dst=f"{self.package_folder}/bin")

    def configure(self):
        pass

    def source(self):
        pass

    def build(self):
        pass

    def package(self):
        self.copy("*", src="cmake", dst=f"{self.package_folder}/cmake")

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

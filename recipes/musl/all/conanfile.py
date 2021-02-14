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

    def config_options(self):
        # TODO: Check options
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        pass

    def source(self):
        # TODO: Add version as options or seprate recipes

        linux_version = "4.19.176"
        tools.get(**self.conan_data["sources-linux"][linux_version])
        os.rename(f"linux-{linux_version}", "linux")

        musl_version = "1.2.2"
        tools.get(**self.conan_data["sources-musl"][musl_version])
        os.rename(f"musl-{musl_version}", "musl")

        # Clang stuff
        clang_version = "10.0.0"
        tools.get(**self.conan_data["sources-compiler-rt"][clang_version])
        os.rename(f"compiler-rt-{clang_version}.src", "compiler-rt")
        tools.get(**self.conan_data["sources-libunwind"][clang_version])
        os.rename(f"libunwind-{clang_version}.src", "libunwind")
        tools.get(**self.conan_data["sources-libcxxabi"][clang_version])
        os.rename(f"libcxxabi-{clang_version}.src", "libcxxabi")
        tools.get(**self.conan_data["sources-libcxx"][clang_version])
        os.rename(f"libcxx-{clang_version}.src", "libcxx")

    def build(self):
        # First install linux headers
        self._build_linux()
        # Then build static version of libc and install c header files
        self._build_musl(shared=False)
        # Then build the compiler runtime. Depends on c headers. After this we can link stuff.
        self._build_compiler_rt()
        # Then build dynamic libc. Depends on compiler_rt.
        self._build_musl(shared=True)
        # Now we can build libc++. Starting with libunwind -> libcxxabi -> libcxx.
        self._build_libunwind()
        self._build_libcxxabi()
        self._build_libcxx()

    def _build_linux(self):
        with tools.chdir("linux"):
            autotools = AutoToolsBuildEnvironment(self)
            # We only need the headers from linux so run the 'headers_install' target
            autotools.make(target="headers_install", args=[f"INSTALL_HDR_PATH={self.package_folder}"])

    def _build_musl(self, shared):
        # TODO:
        # LDFLAGS="-fuse-ld=lld"
        # LIBCC="-lcompiler_rt
        # Here instead of in profile
        extra_args = []

        if not shared:
            extra_args.append("--disable-shared")

        with tools.chdir("musl"):
            autotools = AutoToolsBuildEnvironment(self)
            # TODO: pick out stuff from settings
            autotools.flags.append(f"--target=armv7-linux-musleabihf -mfloat-abi=hard -march=armv7 -mfpu=neon")
            autotools.link_flags.append(f"-L{self.package_folder}/lib/")
            autotools.configure(args=extra_args)
            autotools.make()
            autotools.install()

    def _build_compiler_rt(self):
        # Tips and tricks from: https://llvm.org/docs/HowToCrossCompileBuiltinsOnArm.html
        cmake = CMake(self)
        cmake.definitions["CMAKE_SYSROOT"] = self.package_folder
        cmake.definitions["CMAKE_C_COMPILER_TARGET"] = "armv7-linux-musleabihf"
        cmake.definitions["CMAKE_ASM_COMPILER_TARGET"] = "armv7-linux-musleabihf"
        cmake.definitions["COMPILER_RT_DEFAULT_TARGET_ONLY"] = True
        cmake.definitions["CMAKE_TRY_COMPILE_TARGET_TYPE"] = "STATIC_LIBRARY"
        # TODO: Try to build sanitizers also
        cmake.definitions["COMPILER_RT_BUILD_SANITIZERS"] = False
        cmake.definitions["COMPILER_RT_BUILD_XRAY"] = False
        cmake.definitions["COMPILER_RT_BUILD_LIBFUZZER"] = False
        cmake.definitions["COMPILER_RT_BUILD_PROFILE"] = False
        cmake.configure(source_folder="compiler-rt", build_folder="compiler-rt-bin")
        cmake.build()
        cmake.install()

        # TODO: Fix hard coded `armhf`, regex or similar
        os.rename(f"{self.package_folder}/lib/linux/clang_rt.crtbegin-armhf.o", f"{self.package_folder}/lib/crtbeginS.o")
        os.rename(f"{self.package_folder}/lib/linux/clang_rt.crtend-armhf.o", f"{self.package_folder}/lib/crtendS.o")
        os.rename(f"{self.package_folder}/lib/linux/libclang_rt.builtins-armhf.a", f"{self.package_folder}/lib/libcompiler_rt.a")

    def _build_libunwind(self):
        cmake = CMake(self)
        cmake.definitions["CMAKE_SYSROOT"] = self.package_folder
        cmake.definitions["CMAKE_C_COMPILER_TARGET"] = "armv7-linux-musleabihf"
        cmake.definitions["CMAKE_CXX_COMPILER_TARGET"] = "armv7-linux-musleabihf"
        cmake.definitions["CMAKE_ASM_COMPILER_TARGET"] = "armv7-linux-musleabihf"
        cmake.definitions["CMAKE_TRY_COMPILE_TARGET_TYPE"] = "STATIC_LIBRARY"
        cmake.definitions["LIBUNWIND_ENABLE_SHARED"] = False
        cmake.definitions["LLVM_ENABLE_LIBCXX"] = True
        cmake.configure(source_folder="libunwind", build_folder="libunwind-bin")
        cmake.build()
        cmake.install()

    def _build_libcxxabi(self):
        cmake = CMake(self)
        cmake.definitions["CMAKE_SYSROOT"] = self.package_folder
        cmake.definitions["CMAKE_C_COMPILER_TARGET"] = "armv7-linux-musleabihf"
        cmake.definitions["CMAKE_CXX_COMPILER_TARGET"] = "armv7-linux-musleabihf"
        cmake.definitions["CMAKE_ASM_COMPILER_TARGET"] = "armv7-linux-musleabihf"
        cmake.definitions["CMAKE_TRY_COMPILE_TARGET_TYPE"] = "STATIC_LIBRARY"
        cmake.definitions["LIBCXXABI_TARGET_TRIPLE"] = "armv7-linux-musleabihf"
        cmake.definitions["LIBCXXABI_USE_LLVM_UNWINDER"] = True
        cmake.definitions["LIBCXXABI_USE_COMPILER_RT"] = True
        cmake.definitions["LIBCXXABI_LIBCXX_INCLUDES"] = f"{self.build_folder}/libcxx/include"
        cmake.configure(source_folder="libcxxabi", build_folder="libcxxabi-bin")
        cmake.build()
        cmake.install()

    def _build_libcxx(self):
        cmake = CMake(self)
        cmake.definitions["CMAKE_SYSROOT"] = self.package_folder
        cmake.definitions["CMAKE_C_COMPILER_TARGET"] = "armv7-linux-musleabihf"
        cmake.definitions["CMAKE_CXX_COMPILER_TARGET"] = "armv7-linux-musleabihf"
        cmake.definitions["CMAKE_ASM_COMPILER_TARGET"] = "armv7-linux-musleabihf"
        cmake.definitions["CMAKE_TRY_COMPILE_TARGET_TYPE"] = "STATIC_LIBRARY"

        cmake.definitions["LIBCXX_HAS_MUSL_LIBC"] = True
        cmake.definitions["LIBCXX_HAS_GCC_S_LIB"] = False
        cmake.definitions["LIBCXX_CXX_ABI"] = "libcxxabi"
        cmake.definitions["LIBCXX_USE_COMPILER_RT"] = True
        cmake.definitions["LIBCXXABI_USE_LLVM_UNWINDER"] = True
        cmake.definitions["LIBCXX_CXX_ABI_INCLUDE_PATHS"] = f"{self.build_folder}/libcxxabi/include"
        cmake.definitions["LIBCXX_CXX_ABI_LIBRARY_PATH"] = f"{self.package_folder}/lib"

        cmake.configure(source_folder="libcxx", build_folder="libcxx-bin")
        cmake.build()
        cmake.install()

    def package(self):
        pass

    def package_info(self):
        pass
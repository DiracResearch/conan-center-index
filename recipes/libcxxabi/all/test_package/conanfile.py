import os
from conans import ConanFile, tools
from conans.errors import ConanException


class TestLibCxxAbiConan(ConanFile):
    settings = "os", "compiler", "arch", "build_type"

    def test(self):
        file_to_check = os.path.join("lib", "libc++abi.a")
        file_path = os.path.join(
            self.deps_cpp_info['libcxxabi'].rootpath, file_to_check)

        if not os.path.isfile(file_path):
            raise ConanException(
                f"Expected {file_to_check} to exist but it doesn't!")

        print(f"found: {file_to_check}")

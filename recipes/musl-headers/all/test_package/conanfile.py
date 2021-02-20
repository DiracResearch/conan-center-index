import os
from conans import ConanFile, tools
from conans.errors import ConanException


class TestMuslHeadersConan(ConanFile):
    settings = "os", "compiler", "arch", "build_type"

    def test(self):
        file_to_check = os.path.join("include", "stdc-predef.h")
        file_path = os.path.join(
            self.deps_cpp_info['musl-headers'].rootpath, file_to_check)

        if not os.path.isfile(file_path):
            raise ConanException(
                f"Expected {file_to_check} to exist but it doesn't!")

        print(f"found: {file_to_check}")
        with open(file_path, "r") as f:
            print(f.read())

import os
from conans import ConanFile, CMake, tools

class TestLinuxConan(ConanFile):
    settings = "os", "compiler", "arch", "build_type"

    def test(self):
        pass


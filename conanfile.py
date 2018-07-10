#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, CMake, tools
import os


class FollyConan(ConanFile):
    name = "folly"
    version = "0.58.0"
    release = "2018.06.25.00" # check contained cmakelists for version number
    description = "An open-source C++ library developed and used at Facebook"
    url = "https://github.com/bincrafters/conan-folly"
    homepage = "https://github.com/facebook/folly"
    license = "Apache 2.0"
    exports = ["LICENSE.md", "msvc-folly.patch"]
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"
    source_subfolder = "source_subfolder"
    build_subfolder = "build_subfolder"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
    }
    default_options = (
        "shared=False",
        "fPIC=True",
    )
    requires = (
        "boost_context/1.66.0@bincrafters/stable",
        "boost_crc/1.66.0@bincrafters/stable",
        "boost_multi_index/1.66.0@bincrafters/stable",
        "boost_program_options/1.66.0@bincrafters/stable",
        "cmake_findboost_modular/1.66.0@bincrafters/stable",
        "double-conversion/3.0.0@bincrafters/stable",
        "gflags/2.2.1@bincrafters/stable",
        "glog/0.3.5@bincrafters/stable",
        "libevent/2.0.22@bincrafters/stable",
        "lz4/1.8.0@bincrafters/stable",
        "OpenSSL/1.0.2n@conan/stable",
        "zlib/1.2.11@conan/stable",
        "zstd/1.3.4@bincrafters/stable",
    )

    def source(self):
        source_url = "https://github.com/facebook/folly"
        tools.get("{0}/archive/v{1}.tar.gz".format(source_url, self.release))
        extracted_dir = self.name + "-" + self.release
        os.rename(extracted_dir, self.source_subfolder)

        # Fix inconsistent case for gflags so that the package config can be
        # found and used. Otherwise find_package() resorts to module mode, and
        # that might turn up any old junk.
        follyDepsPath = os.path.join(self.source_subfolder, "CMake", "folly-deps.cmake")
        tools.replace_in_file(follyDepsPath,
            "find_package(GFlags CONFIG QUIET)",
            "find_package(gflags CONFIG QUIET)")
        tools.replace_in_file(follyDepsPath,
            "find_package(GFlags MODULE)",
            "find_package(gflags MODULE)")

        # Disable the "maybe uninitialized" warnings from gcc, as they were
        # breaking the Release build (they only show up when optimisations
        # are enabled, as the analysis is only done then). Remove this when
        # fixes make their way upstream.
        if self.settings.compiler == "gcc":
            tools.replace_in_file(os.path.join(self.source_subfolder, "CMake", "FollyCompilerUnix.cmake"),
                "-g -Wall -Wextra",
                "-g -Wall -Wextra -Wno-maybe-uninitialized")

        # GCC 8 has introduced more agressive warnings, and Boost hasn't quite
        # caught up yet, so we simply allow all warnings for now.
        tools.replace_in_file(os.path.join(self.source_subfolder, "CMake", "FollyCompilerUnix.cmake"),
            "-Werror",
            "")

        # folly finds libevent using the 'event' name. This will work fine
        # on Linux (CMake will search for 'libevent' too) but will fail on
        # Windows where the library file happens to be named libevent.lib.
        tools.replace_in_file(os.path.join(self.source_subfolder, "CMake", "FindLibEvent.cmake"),
            'find_library(LIBEVENT_LIB NAMES event PATHS ${LibEvent_LIB_PATHS})',
            'find_library(LIBEVENT_LIB NAMES event libevent PATHS ${LibEvent_LIB_PATHS})')

        # These patches are necessary when building with MSVC, and do no harm
        # otherwise. Remove this when fixes make their way upstream.
        tools.patch(patch_file="msvc-folly.patch", base_path=self.source_subfolder)

    def _configure_cmake(self):
        cmake = CMake(self)
        cmake.definitions["BUILD_SHARED_LIBS"] = self.options.shared
        cmake.configure()
        return cmake
        
    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        cmake = self._configure_cmake()
        cmake.install()
        self.copy(pattern="LICENSE", dst="licenses", src=self.source_subfolder)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

        if self.settings.os == "Linux":
            self.cpp_info.libs.extend(["pthread", "dl"])

        if not self.options.shared:
            if self.settings.compiler == "Visual Studio":
                self.cpp_info.libs.extend(["ws2_32", "Iphlpapi", "Crypt32"])

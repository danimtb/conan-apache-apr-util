# -*- coding: utf-8 -*-

from conans import ConanFile, AutoToolsBuildEnvironment, tools, CMake
import os


class ApacheAPRUtil(ConanFile):
    name = "apache-apr-util"
    version = "1.6.1"
    url = "https://github.com/jgsogo/conan-apache-apr-util"
    homepage = "https://apr.apache.org/"
    license = "http://www.apache.org/LICENSE.txt"
    description = "The mission of the Apache Portable Runtime (APR) project is to create and maintain " \
                  "software libraries that provide a predictable and consistent interface to underlying " \
                  "platform-specific implementations."
    exports_sources = ["LICENSE"]
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = {"shared": False, "fPIC": True}
    generators = "cmake"
    requires = "apache-apr/1.6.3@jgsogo/stable", "Expat/2.2.5@pix4d/stable"
    _lib_name = "apr-util-" + version

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fpic

    def configure(self):
        del self.settings.compiler.libcxx  # It is a C library

    def source(self):
        file_ext = ".tar.gz" if not self.settings.os == "Windows" else "-win32-src.zip"
        tools.get("http://archive.apache.org/dist/apr/apr-util-{v}{ext}".format(v=self.version, ext=file_ext))

    def _patch(self):
        tools.replace_in_file(os.path.join(self._lib_name, 'CMakeLists.txt'),
                              "PROJECT(APR-Util C)",
                              """
                              PROJECT(APR-Util C)
                              include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
                              conan_basic_setup()
                              """)

        # Fix a ¿bug? Maybe it has changed in FindExpat module
        tools.replace_in_file(os.path.join(self._lib_name, 'CMakeLists.txt'),
                              "SET(XMLLIB_INCLUDE_DIR   ${EXPAT_INCLUDE_DIRS})",
                              "SET(XMLLIB_INCLUDE_DIR   ${EXPAT_INCLUDE_DIR})")
        tools.replace_in_file(os.path.join(self._lib_name, 'CMakeLists.txt'),
                              "SET(XMLLIB_LIBRARIES     ${EXPAT_LIBRARIES})",
                              "SET(XMLLIB_LIBRARIES     ${EXPAT_LIBRARY})")

        if self.settings.os == "Windows":
            if self.settings.build_type == "Debug":
                tools.replace_in_file(os.path.join(self._lib_name, 'CMakeLists.txt'),
                                      "SET(install_bin_pdb ${install_bin_pdb} ${PROJECT_BINARY_DIR}/",
                                      "SET(install_bin_pdb ${install_bin_pdb} ${PROJECT_BINARY_DIR}/bin/")
                tools.replace_in_file(os.path.join(self._lib_name, 'CMakeLists.txt'),  # TODO: Do not make it optional, grab the files and copy them.
                                      "          CONFIGURATIONS RelWithDebInfo Debug)",
                                      "          CONFIGURATIONS RelWithDebInfo Debug OPTIONAL)")

    def _cmake_configure(self):
        cmake = CMake(self)
        cmake.definitions["APR_INCLUDE_DIR"] = self.deps_cpp_info["apache-apr"].include_paths[0]
        cmake.definitions["APR_LIBRARIES"] = os.path.join(self.deps_cpp_info["apache-apr"].lib_paths[0], "libapr-1.lib")
        cmake.configure(source_folder=self._lib_name)
        return cmake

    def _autotools_configure(self):
        env_build = AutoToolsBuildEnvironment(self)
        args = ['--with-apr={}'.format(self.deps_cpp_info["apache-apr"].rootpath)]
        env_build.configure(configure_dir=self._lib_name, args=args,)

    def build(self):
        self._patch()
        if self.settings.os == "Windows":
            cmake = self._cmake_configure()
            cmake.build()
        else:
            atools = self._autotools_configure()
            atools.make()

    def package(self):
        # TODO: Copy files from apache-apr, this project expected them side by side
        # self.copy("*.h", dst="include", src=os.path.join(self.deps_cpp_info["apache-apr"].include_paths[0]))
        self.copy("LICENSE", src=self._lib_name)
        if self.settings.os == "Windows":
            cmake = self._cmake_configure()
            cmake.install()
        else:
            atools = self._autotools_configure()
            atools.install()

    def package_id(self):
        self.info.options.shared = "Any"  # Both, shared and static are built always

    def package_info(self):
        if self.settings.os == "Windows":
            if self.options.shared:
                libs = ["libaprutil-1", ]
            else:
                libs = ["aprutil-1", "ws2_32", "Rpcrt4", ]
                self.cpp_info.defines = ["APU_DECLARE_STATIC", ]
        else:
            libs = ["aprutil-1", ]
            if not self.options.shared:
                libs += ["pthread", ]
            self.cpp_info.includedirs = [os.path.join("include", "apr-1"), ]
        self.cpp_info.libs = libs

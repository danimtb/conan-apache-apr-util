# -*- coding: utf-8 -*-

from conans import ConanFile, AutoToolsBuildEnvironment, tools, CMake
import os


class ApacheAPRUtil(ConanFile):
    name = "apache-apr-util"
    version = "1.6.1"
    url = "https://github.com/jgsogo/conan-apache-apr-util"
    homepage = "https://apr.apache.org/"
    license = "http://www.apache.org/LICENSE.txt"
    exports_sources = ["LICENSE",]
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=False"
    generators = "cmake"

    lib_name = "apr-util-" + version

    def requirements(self):
        self.requires("apache-apr/1.6.3@jgsogo/stable")
        self.requires("expat/2.2.5@bincrafters/stable")

    def source(self):
        file_ext = ".tar.gz" if not self.settings.os == "Windows" else "-win32-src.zip"
        tools.get("http://archive.apache.org/dist/apr/apr-util-{v}{ext}".format(v=self.version, ext=file_ext))

    def patch(self):
        tools.replace_in_file(os.path.join(self.lib_name, 'CMakeLists.txt'),
                              "PROJECT(APR-Util C)",
                              """
                              PROJECT(APR-Util C)
                              include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
                              conan_basic_setup()
                              """)

        # Fix a ¿bug? Maybe it has changed in FindExpat module
        tools.replace_in_file(os.path.join(self.lib_name, 'CMakeLists.txt'),
                              "SET(XMLLIB_INCLUDE_DIR   ${EXPAT_INCLUDE_DIRS})",
                              "SET(XMLLIB_INCLUDE_DIR   ${EXPAT_INCLUDE_DIR})")
        tools.replace_in_file(os.path.join(self.lib_name, 'CMakeLists.txt'),
                              "SET(XMLLIB_LIBRARIES     ${EXPAT_LIBRARIES})",
                              "SET(XMLLIB_LIBRARIES     ${EXPAT_LIBRARY})")

        if self.settings.os == "Windows":
            if self.settings.build_type == "Debug":
                tools.replace_in_file(os.path.join(self.lib_name, 'CMakeLists.txt'),
                                      "SET(install_bin_pdb ${install_bin_pdb} ${PROJECT_BINARY_DIR}/",
                                      "SET(install_bin_pdb ${install_bin_pdb} ${PROJECT_BINARY_DIR}/Debug/")

    def build(self):
        self.patch()
        if self.settings.os == "Windows":
            cmake = CMake(self)
            cmake.definitions["APR_INCLUDE_DIR"] = os.path.join(self.deps_cpp_info["apache-apr"].include_paths[0], "apr-1")
            cmake.definitions["APR_LIBRARIES"] = os.path.join(self.deps_cpp_info["apache-apr"].lib_paths[0], "libapr-1.lib")
            cmake.configure(source_folder=self.lib_name)
            cmake.build()
            cmake.install()
        else:
            env_build = AutoToolsBuildEnvironment(self)
            args = ['--prefix', self.package_folder,
                    '--with-apr={}'.format(os.path.join(self.deps_cpp_info["apache-apr"].include_paths[0], "..")),  # TODO: Path to package dir?
                    ]
            env_build.configure(configure_dir=self.lib_name,
                                args=args,
                                build=False)  # TODO: Workaround for https://github.com/conan-io/conan/issues/2552
            env_build.make()
            env_build.make(args=['install'])

    def package(self):
        # TODO: Find a better approach
        # Copy files and libs from apache-apr
        self.copy("*.h", dst="include", src=os.path.join(self.deps_cpp_info["apache-apr"].include_paths[0]))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

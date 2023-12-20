"""A setuptools based setup module.
See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import os
import pathlib

from setuptools.command.develop import develop
from subprocess import check_call


def generate_proto_code():
    proto_interface_dir = "./vendor"
    generated_src_dir = "./dart_sass/proto"
    out_folder = "dart_sass"
    if not os.path.exists(generated_src_dir):
        os.mkdir(generated_src_dir)
    proto_it = pathlib.Path().glob(proto_interface_dir + "/**/*")
    proto_path = "proto=" + proto_interface_dir
    protos = [str(proto) for proto in proto_it if proto.is_file()]
    check_call(
        ["protoc"]
        + protos
        + [
            "--python_out",
            out_folder,
            "--proto_path",
            proto_path,
            "--pyi_out",
            out_folder,
        ]
    )


class CustomDevelopCommand(develop):
    """Wrapper for custom commands to run before package installation."""

    uninstall = False

    def run(self):
        develop.run(self)

    def install_for_development(self):
        develop.install_for_development(self)
        generate_proto_code()


setup(
    install_requires=["protobuf"],
    name="dart_sass",
    description="Simple wrapper around dart-sass-embedded",
    version="0.0.1",
    package_dir={},
    cmdclass={
        "develop": CustomDevelopCommand,  # used for pip install -e ./
    },
    packages=find_packages(where="dart_sass"),
)

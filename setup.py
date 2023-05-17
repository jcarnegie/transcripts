import os
from setuptools import setup, find_namespace_packages


def read_file(fname: str) -> str:
    path = os.path.join(os.path.dirname(__file__), fname)
    with open(path) as f:
        return f.read()


REQUIREMENTS = read_file("requirements.txt").splitlines()[1:]


setup(
    name="me_2.0",
    author="Daniel Reznikov",
    author_email="daniel.reznikov@gmail.com",
    description="Digital Coach",
    packages=find_namespace_packages(
        where="src",
        include=["stovell.*"],
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    package_dir={"": "src"},
    install_requires=REQUIREMENTS,
    include_package_data=True,
)

import os
import re
import setuptools

ROOT = os.path.dirname(__file__)
INIT = open(os.path.join(ROOT, "bingo", "__init__.py")).read()

AUTHOR_RE = re.compile(r"""__author__ = ['"]([A-Za-z]+)['"]""")
VERSION_RE = re.compile(r"""__version__ = ['"]([0-9.]+)['"]""")


def get_author():
    return AUTHOR_RE.search(INIT).group(1)


def get_version():
    return VERSION_RE.search(INIT).group(1)


def get_description():
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()

    return long_description


setuptools.setup(
    name="hbz-bingo",
    version=get_version(),
    author=get_author(),
    description="Python package contains common modules that are shared between packages and services",
    long_description=get_description(),
    long_description_content_type="text/markdown",
    license="MIT",
    packages=setuptools.find_packages(),
    python_requires=">=3.9",
    install_requires=["boto3==1.24.17", "motor==3.0.0", "pydantic==1.9.1"],
)

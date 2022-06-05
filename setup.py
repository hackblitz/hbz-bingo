import setuptools


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setuptools.setup(
    name="bingo",
    version="0.0.1",
    author="Satheesh Kumar",
    author_email="mail@satheesh.dev",
    description="Python package that contain common modules that are shared between packages and services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=["bingo"],
    python_requires=">=3.9",
    install_requires=["motor=3.0.0", "pydantic=1.9.1"],
)

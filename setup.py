import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="opensafely-ckg",
    version="0.1",
    author="Abdullah Faqih",
    author_email="abdulfaqihalm@binomika.kemkes.go.id",
    description="A fork version of OpenSafely CLI for Indonesia MoH MVP",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bgsi-id/opensafely-cli/tree/bgsi_dev",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
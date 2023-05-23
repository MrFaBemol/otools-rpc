from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="otools-rpc",
    version="0.2.6",
    description="A tool to interact with Odoo's external API.",
    packages=find_packages(exclude=["tests"]),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MrFaBemol/otools-rpc",
    author="Gautier Casabona",
    author_email="gcasabona.pro@gmail.com",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Natural Language :: English"
    ],
    install_requires=[
        "loguru >= 0.7.0",
        "requests == 2.29.0" #Higher version can break your docker python lib
    ],
    extras_require={
        "dev": ["pytest>=7.0", "twine>=4.0.2"],
    },
    python_requires=">=3.8",
)

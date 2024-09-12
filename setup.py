from setuptools import setup, find_packages

setup(
    name="laview_dl",
    version="0.1.0",
    description="A Python package for laview_dl",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        # List your package dependencies here, e.g.,
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "laview-cli=laview_dl.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

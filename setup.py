"""PyCentipede - A Python-based word splitter
Copyright (C) 2019-2020  John Hyland
GNU GENERAL PUBLIC LICENSE Version 3"""

from setuptools import find_packages, setup


with open('requirements.txt') as f:
    requirements = f.read().splitlines()


setup(
    name="PyCentipede",
    version="2.1.0",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requirements,
    package_data={
        "": ["*.py", "*.txt", "*.yaml", "*.html"],
        "service": ["*.py", "*.html"],
        "splitter": ["*.py"],
        "tests": ["*.py", "*.txt"],
        "utils": ["*.py"]
    },
    author="John Hyland",
    author_email="jonhyland@hotmail.com",
    description="A Python-based word splitter, wrapped in a Flask HTTP service.",
    keywords="word split splitting splitter text separation",
    license='GNU',
    project_urls={
        "Source Code": "https://github.com/jon-hyland/pycentipede/"
    }
)
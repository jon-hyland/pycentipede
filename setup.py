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
        "": ["*.txt", "*.yaml", "*.html"],
        "service": ["*.txt", "*.html"]
    },
    author="John Hyland",
    author_email="jonhyland@hotmail.com",
    description="A Flask-based word splitting service.",
    keywords="word split splitting splitter text separation"
)
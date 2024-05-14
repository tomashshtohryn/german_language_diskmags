from setuptools import setup, find_packages

setup(
    name='c64_diskmag_converter',
    version='0.1',
    packages=find_packages(),
    package_data={'c64_diskmag_converter': ['data/*.csv']},
)
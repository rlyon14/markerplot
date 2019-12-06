from setuptools import setup, find_packages

setup(
    name='markerplot',
    description='interactive cursor support for matplotlib',
    author='Rick Lyon',
    author_email='rlyon14@gmail.com',
    version='0.1.1',
    packages=['markerplot',],
    install_requires=(
		'matplotlib>=3.1.0',
        'numpy',
        'gorilla'
    ),
)

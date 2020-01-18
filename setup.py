from setuptools import setup, find_packages

setup(
    name='mpl-markers',
    description='interactive marker support for matplotlib',
    author='rlyon',
    author_email='rlyon14@yahoo.com',
    version='0.1.1',
    packages=['mpl-markers',],
    install_requires=(
		'matplotlib>=3.1.0',
        'numpy',
        'gorilla',
        'pyqt5'
    ),
)

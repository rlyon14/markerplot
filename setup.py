from setuptools import setup, find_packages

setup(
    name='markerplot',
    description='interactive marker support for matplotlib',
    author='rlyon',
    author_email='rlyon14@yahoo.com',
    version='0.1.1',
    packages=['markerplot',],
    install_requires=(
		'matplotlib>=3.1.3',
        'numpy',
        'gorilla',
        'pyside2',
        'Pillow',
        'pywin32'
    ),
)

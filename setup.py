from setuptools import setup

setup(
    name='xwiimote',
    version='1',
    py_modules=['xwiimote'],
    setup_requires=['cffi'],
    cffi_modules=['xwiimote_build.py:ffibuilder'],
    install_requires=['cffi'],
)

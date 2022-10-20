# -*- coding: utf-8 -*-
"""
install via

python -m pip install .

or to allow development to be ongoing in the location of the working directory

python -m pip install -e .

"""


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="camcos",
    description="Ethereum simulations",
    version='Fall2022',
    install_requires=['numpy', 'scipy', 'h5py']
)
from distutils.core import setup
from Cython.Build import cythonize

setup(name="TensorOrder", ext_modules=cythonize("*/*.pyx", language_level=3))

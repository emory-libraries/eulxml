from distutils.command.build_py import build_py
import os

from setuptools import setup, find_packages

import eulxml

class build_py_with_ply(build_py):
    def run(self, *args, **kwargs):
        # importing this forces ply to generate parsetab/lextab
        import eulxml.xpath.core
        build_py.run(self, *args, **kwargs)

setup(
    cmdclass={'build_py': build_py_with_ply},

    name='eulxml',
    version=eulxml.__version__,
    author='Emory University Libraries',
    author_email='libsysdev-l@listserv.cc.emory.edu',
    packages=find_packages(),
    install_requires=[
        'ply',
        'lxml',
        'rdflib>=3.0',
    ],
)

from distutils.command.build_py import build_py
import os

from setuptools import setup

from eulxml import __version__

packages = []
for path, dirs, files in os.walk('eulxml'):
    if '__init__.py' in files:
        packages.append(path.replace(os.path.sep, '.'))

class build_py_with_ply(build_py):
    def run(self, *args, **kwargs):
        # importing this forces ply to generate parsetab/lextab
        import eulxml.xpath.core
        build_py.run(self, *args, **kwargs)

setup(
    cmdclass={'build_py': build_py_with_ply},

    name='eulxml',
    version=__version__,
    author='Emory University Libraries',
    author_email='libsysdev-l@listserv.cc.emory.edu',
    packages=packages,
    package_dir={'': '.'},
    install_requires=[
        'ply',
        'lxml',
        'rdflib>=3.0',
    ],
)

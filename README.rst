eulxml
======

**package**
  .. image:: https://img.shields.io/pypi/v/eulxml.svg
    :target: https://pypi.python.org/pypi/eulxml
    :alt: PyPI

  .. image:: https://img.shields.io/github/license/emory-libraries/eulxml.svg
    :alt: License

  .. image:: https://img.shields.io/pypi/dm/eulxml.svg
    :alt: PyPI downloads

**documentation**
  .. image:: https://readthedocs.org/projects/eulxml/badge/?version=latest
    :target: http://eulxml.readthedocs.org/en/latest/?badge=latest
    :alt: Documentation Status

**code**
  .. image:: https://travis-ci.org/emory-libraries/eulxml.svg
    :alt: travis-ci build
    :target: https://travis-ci.org/emory-libraries/eulxml

  .. image:: https://coveralls.io/repos/github/emory-libraries/eulxml/badge.svg
    :target: https://coveralls.io/github/emory-libraries/eulxml
    :alt: Code Coverage

  .. image:: https://codeclimate.com/github/emory-libraries/eulxml/badges/gpa.svg
    :target: https://codeclimate.com/github/emory-libraries/eulxml
    :alt: Code Climate


  .. image:: https://requires.io/github/emory-libraries/eulxml/requirements.svg
    :target: https://requires.io/github/emory-libraries/eulxml/requirements

eulxml is a `Python <http://www.python.org/>`_ module that provides
utilities and classes for interacting with XML that allow the
definition of re-usable XML objects that can be accessed, updated and
created as standard Python types, and a form component for editing XML
with `Django <https://www.djangoproject.com/>`_ forms.

**eulxml.xpath** provides functions and classes for parsing XPath
expressions using `PLY <http://www.dabeaz.com/ply/>`_.

**eulxml.xmlmap** makes it easier to map XML to Python objects in a
nicer, more pythonic and object-oriented way than typical DOM access
usually provides.  XML can be read, modified, and even created from
scratch (in cases where the configured XPath is simple enough to
determine the nodes that should be constructed).

**eulxml.forms** provides Django Form objects that use
**eulxml.xmlmap.XmlObject** instances as the basis and data instance
for the form, with the goal of making it easy to edit XML content
via web forms.

Dependencies
------------

**eulxml** depends on `PLY <http://www.dabeaz.com/ply/>`_ and `lxml
<http://lxml.de/>`_.

**eulxml.forms** requires and was designed to be used with
`Django <https://www.djangoproject.com/>`_, although Django is not
required for installation and use of the non-form components of
**eulxml**.


Contact Information
-------------------

**eulxml** was created by the Digital Programs and Systems Software
Team of `Emory University Libraries <http://web.library.emory.edu/>`_.

libsysdev-l@listserv.cc.emory.edu


License
-------
**eulxml** is distributed under the Apache 2.0 License.


Development History
-------------------

For instructions on how to see and interact with the full development
history of **eulxml**, see
`eulcore-history <https://github.com/emory-libraries/eulcore-history>`_.

Developer notes
---------------

As of version 1.1, eulxml provides an `XML catalog <http://lxml.de/resolvers.html#xml-catalogs>`_
for loading schemas referenced by included XmlObject instances. `Requests <https://github.com/kennethreitz/requests>`_ is required for downloading schemas, but it is not a dependency of eulxml. The
catalog and schemas will be included in distributed releases, but if you
want to use the catalog when installing directly from GitHub you can
use a normal pip install and then run::

  python -c 'from eulxml.catalog import generate_catalog; generate_catalog()'


To install dependencies for your local check out of the code, run ``pip install``
in the ``eulxml`` directory (the use of `virtualenv`_ is recommended)::

    pip install -e .

.. _virtualenv: http://www.virtualenv.org/en/latest/

If you want to run unit tests or build sphinx documentation, you will also
need to install development dependencies::

    pip install -e . "eulxml[dev]"

To run all unit tests::

    nosetests   # for normal development
    nosetests --with-coverage --cover-package=eulxml --cover-xml --with-xunit   # for continuous integration

To run unit tests for a specific module, use syntax like this::

    nosetests test/test_xpath.py


To generate sphinx documentation::

    cd doc
    make html


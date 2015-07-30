EULxml
======

.. image:: https://api.travis-ci.org/emory-libraries/eulxml.png
   :alt: current build status for namedropper-py
   :target: https://travis-ci.org/emory-libraries/eulxml

.. image:: https://pypip.in/version/eulxml/badge.png
   :target: https://pypi.python.org/pypi/eulxml

.. image:: https://pypip.in/license/eulxml/badge.png

.. image:: https://pypip.in/download/eulxml/badge.png


EULxml is a `Python <http://www.python.org/>`_ module that provides
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

Local settings
--------------

EULxml provides the option to override the default namespaces and schemas
for datastreams in the case of locally hosted schemas. Add your datastream setting
to your local settings to override the defaults:

**MODS**

    ``MODS_NAMESPACE`` (defaults to 'http://www.loc.gov/mods/v3')

    ``MODS_SCHEMA`` (defaults to 'http://www.loc.gov/standards/mods/mods.xsd')

    ``MODSv34_SCHEMA`` (defaults to 'http://www.loc.gov/standards/mods/v3/mods-3-4.xsd')


**PREMIS**

    ``PREMIS_NAMESPACE`` (defaults to 'info:lc/xmlns/premis-v2')

    ``PREMIS_SCHEMA`` (defaults to 'http://www.loc.gov/standards/premis/v2/premis-v2-1.xsd')

**Dublin Core**
    ``OAI_DC_NAMESPACE`` (defaults to 'http://www.openarchives.org/OAI/2.0/oai_dc/')

    ``DC_NAMESPACES`` (defaults to 'http://purl.org/dc/elements/1.1/')

    ``DC_SCHEMA`` (defaults to 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd')


Dependencies
------------

**eulxml** depends on `PLY <http://www.dabeaz.com/ply/>`_ and `lxml
<http://lxml.de/>`_.

**eulxml.forms** requires and was designed       to be used with
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

EULxml
======

EULxml is an extensible library for reading and writing XML documents in
idiomatic Python. It allows developers to `map predictable XML node
structures <xmlmap.html#general-usage>`_ to
:class:`~eulxml.xmlmap.XmlObject` subclasses, using field definitions to map
`XPath <http://www.w3.org/TR/xpath/>`_ expressions directly to Python
attributes.

For projects using `Django <http://www.djangoproject.com/>`_, it also
provides utilities for exposing :class:`~eulxml.xmlmap.XmlObject` instances
to web users with :class:`~eulxml.forms.XmlObjectForm`. As a bonus, EULxml
happens to include an XPath parser in :mod:`eulxml.xpath`.

Contents
--------

.. toctree::
   :maxdepth: 3
   
   changelog
   xmlmap
   forms
   xpath

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

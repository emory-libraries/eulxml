:mod:`eulxml.xmlmap.cerp` - Collaborative Electronic Records Project
=====================================================================

.. module:: eulxml.xmlmap.cerp

General Information
-------------------

The Collaborative Celectronic Records Project, or `CERP
<http://siarchives.si.edu/cerp/>`_ is a digital preservation project from
the `Smithsonian Institution Archives <http://siarchives.si.edu/>`_ and the
`Rockefeller Archive Center <http://www.rockarch.org/>`_. One particular
product of that project was an `XML format for email accounts
<http://www.records.ncdcr.gov/emailpreservation/mail-account/mail-account_docs.html>`_.
This module maps those XML objects to Python objects.

The schema produced by the project will validate only :class:`Account`
objects, though this module also allows the creation of subelements.

:class:`Account` and Associated Objects
---------------------------------------

.. autoclass:: Account
   :members:
   :undoc-members:
   :inherited-members:

   http://www.records.ncdcr.gov/emailpreservation/mail-account/mail-account_docs.html#element_Account

.. autoclass:: ReferencesAccount
   :members:
   :undoc-members:
   :inherited-members:

   http://www.records.ncdcr.gov/emailpreservation/mail-account/mail-account_docs.html#type_ref-account-type

:class:`Folder` and Associated Objects
--------------------------------------

.. autoclass:: Folder
   :members:
   :undoc-members:
   :inherited-members:

   http://www.records.ncdcr.gov/emailpreservation/mail-account/mail-account_docs.html#type_folder-type

.. autoclass:: Mbox
   :members:
   :undoc-members:
   :inherited-members:

   http://www.records.ncdcr.gov/emailpreservation/mail-account/mail-account_docs.html#type_mbox-type

:class:`Message` and Associated Objects
---------------------------------------

.. autoclass:: Message
   :members:
   :undoc-members:
   :inherited-members:

   http://www.records.ncdcr.gov/emailpreservation/mail-account/mail-account_docs.html#type_message-type

.. autoclass:: ChildMessage
   :members:
   :undoc-members:
   :inherited-members:

   http://www.records.ncdcr.gov/emailpreservation/mail-account/mail-account_docs.html#type_child-message-type

.. autoclass:: SingleBody
   :members:
   :undoc-members:
   :inherited-members:

   http://www.records.ncdcr.gov/emailpreservation/mail-account/mail-account_docs.html#type_single-body-type

.. autoclass:: MultiBody
   :members:
   :undoc-members:
   :inherited-members:

   http://www.records.ncdcr.gov/emailpreservation/mail-account/mail-account_docs.html#type_multi-body-type

.. autoclass:: Incomplete
   :members:
   :undoc-members:
   :inherited-members:

   http://www.records.ncdcr.gov/emailpreservation/mail-account/mail-account_docs.html#type_incomplete-parse-type

.. autoclass:: BodyContent
   :members:
   :undoc-members:
   :inherited-members:

   http://www.records.ncdcr.gov/emailpreservation/mail-account/mail-account_docs.html#type_int-body-content-type

.. autoclass:: ExtBodyContent
   :members:
   :undoc-members:
   :inherited-members:

   http://www.records.ncdcr.gov/emailpreservation/mail-account/mail-account_docs.html#type_ext-body-content-type

Additional Utility Objects
--------------------------

.. autoclass:: Parameter
   :members:
   :undoc-members:
   :inherited-members:

   http://www.records.ncdcr.gov/emailpreservation/mail-account/mail-account_docs.html#type_parameter-type

.. autoclass:: Header
   :members:
   :undoc-members:
   :inherited-members:

   http://www.records.ncdcr.gov/emailpreservation/mail-account/mail-account_docs.html#type_header-type

.. autoclass:: Hash
   :members:
   :undoc-members:
   :inherited-members:

   http://www.records.ncdcr.gov/emailpreservation/mail-account/mail-account_docs.html#type_hash-type

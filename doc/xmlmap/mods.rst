:mod:`eulxml.xmlmap.mods` - Metadata Object Description Schema (MODS)
=====================================================================

.. module:: eulxml.xmlmap.mods

General Information
-------------------

The Metadata Object Description Standard, or `MODS
<http://www.loc.gov/standards/mods/>`_ is a schema developed and maintained
by the Library of Congress for bibliographic records.

This module defines classes to handle common use cases for MODS metadata,
rooted in the :class:`MODSv34` object. It is not a complete mapping, though
it will likely grow closer to one as development progresses according to
user needs.

Root Classes: MODS and Friends
------------------------------

.. autoclass:: MODS
   :members:
   :undoc-members:
   :inherited-members:

.. autoclass:: MODSv34
   :members:
   :undoc-members:
   :inherited-members:

Title Info
----------
MODS `titleInfo <http://www.loc.gov/standards/mods/userguide/titleinfo.html>`_

.. autoclass:: TitleInfo
   :members:
   :undoc-members:

Name
----
MODS `name <http://www.loc.gov/standards/mods/userguide/name.html>`_

.. autoclass:: Name
   :members:
   :undoc-members:

.. autoclass:: NamePart
   :members:
   :undoc-members:

.. autoclass:: Role
   :members:
   :undoc-members:

Genre
-----
MODS `genre <http://www.loc.gov/standards/mods/userguide/genre.html>`_

.. autoclass:: Genre
   :members:
   :undoc-members:

Origin Info
-----------
MODS `originInfo <http://www.loc.gov/standards/mods/userguide/origininfo.html>`_

.. autoclass:: OriginInfo
   :members:
   :undoc-members:

.. autoclass:: DateCreated
   :members:
   :undoc-members:

.. autoclass:: DateIssued
   :members:
   :undoc-members:

Language
--------
MODS `language <http://www.loc.gov/standards/mods/userguide/language.html>`_

.. autoclass:: Language
   :members:
   :undoc-members:

.. autoclass:: LanguageTerm
   :members:
   :undoc-members:

Physical Description
--------------------
MODS `physicalDescription <http://www.loc.gov/standards/mods/userguide/physicaldescription.html>`_

.. autoclass:: PhysicalDescription
   :members:
   :undoc-members:

Abstract
--------
MODS `abstract <http://www.loc.gov/standards/mods/userguide/abstract.html>`_

.. autoclass:: Abstract
   :members:
   :undoc-members:

Note
----
MODS `note <http://www.loc.gov/standards/mods/userguide/note.html>`_

.. autoclass:: Note
   :members:
   :undoc-members:

.. autoclass:: TypedNote

Subject
-------
MODS `subject <http://www.loc.gov/standards/mods/userguide/subject.html>`_

.. autoclass:: Subject
   :members:
   :undoc-members:

Related Item
------------
MODS `relatedItem <http://www.loc.gov/standards/mods/userguide/relateditem.html>`_

.. autoclass:: RelatedItem
   :members:
   :undoc-members:

Identifer
---------
MODS `identifier <http://www.loc.gov/standards/mods/userguide/identifier.html>`_

.. autoclass:: Identifier
   :members:
   :undoc-members:

Location
--------
MODS `location <http://www.loc.gov/standards/mods/userguide/location.html>`_

.. autoclass:: Location
   :members:
   :undoc-members:

Access Condition
----------------
MODS `accessCondition <http://www.loc.gov/standards/mods/userguide/accesscondition.html>`_

.. autoclass:: AccessCondition
   :members:
   :undoc-members:

Part
----
MODS `part <http://www.loc.gov/standards/mods/userguide/part.html>`_

.. autoclass:: Part
   :members:
   :undoc-members:

.. autoclass:: PartDetail
   :members:
   :undoc-members:

.. autoclass:: PartExtent
   :members:
   :undoc-members:

Record Info
-----------
MODS `recordInfo <http://www.loc.gov/standards/mods/userguide/recordinfo.html>`_

.. autoclass:: RecordInfo
   :members:
   :undoc-members:

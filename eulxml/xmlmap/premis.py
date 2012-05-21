# file eulxml/xmlmap/premis.py
# 
#   Copyright 2010,2011 Emory University Libraries
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

'''
:mod:`eulxml.xmlmap` classes for dealing with the `PREMIS
<http://www.loc.gov/standards/premis/>`_ metadata format for
preservation metadata.

-----
'''

from eulxml import xmlmap

PREMIS_NAMESPACE = 'info:lc/xmlns/premis-v2'
'authoritative namespace for PREMIS'
PREMIS_SCHEMA = 'http://www.loc.gov/standards/premis/v2/premis-v2-1.xsd'
'authoritative schema location for PREMIS'

class BasePremis(xmlmap.XmlObject):
    '''Base PREMIS class with namespace declaration common to all PREMIS
    XmlObjects.

    .. Note::

       This class is intended mostly for internal use, but could be
       useful when extending or adding additional PREMIS
       :class:`~eulxml.xmlmap.XmlObject` classes.  The
       :attr:`PREMIS_NAMESPACE` is mapped to the prefix **p**.
    '''
    ROOT_NS = PREMIS_NAMESPACE
    ROOT_NAMESPACES = {
        'p': PREMIS_NAMESPACE,
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }

class PremisRoot(BasePremis):
    '''Base class with a schema declaration for any of the
    root/stand-alone PREMIS elements:
    
     * ``<premis>`` - :class:`Premis`
     * ``<object>`` - :class:`Object`
     * ``<event>``  - :class:`Event`
     * ``<agent>``
     * ``<rights>``
    
    '''
    XSD_SCHEMA = PREMIS_SCHEMA
    
class Object(PremisRoot):
    '''Preliminary :class:`~eulxml.xmlmap.XmlObject` for a PREMIS
    object.

    Curently only includes the minimal required fields.
    '''
    ROOT_NAME = 'object'
    type = xmlmap.StringField('@xsi:type') # file, representation, bitstream
    '''type of object (e.g., file, representation, bitstream).

    .. Note::
      To be schema valid, object types must be in the PREMIS namespace, e.g.::

        from eulxml.xmlmap import premis
        obj = premis.Object()
        obj.type = "p:file"
    '''
    id_type = xmlmap.StringField('p:objectIdentifier/p:objectIdentifierType')
    'identifier type (`objectIdentifier/objectIdentifierType`)'
    id = xmlmap.StringField('p:objectIdentifier/p:objectIdentifierValue')
    'identifier value (`objectIdentifier/objectIdentifierValue`)'

class Event(PremisRoot):
    '''Preliminary :class:`~eulxml.xmlmap.XmlObject` for a PREMIS
    event.

    .. Note::

      The PREMIS schema requires that elements occur in a specified
      order, which :mod:`eulxml` does not currently handle or manage.
      As a work-around, when creating a new :class:`Event` from
      scratch, you should set the following required fields in this
      order: identifier (:attr:`id` and :attr:`ad_type`
    
    '''
    ROOT_NAME = 'event'
    type = xmlmap.StringField('p:eventType')
    'event type  (``eventType``)'
    id_type = xmlmap.StringField('p:eventIdentifier/p:eventIdentifierType')
    'identifier type (`eventIdentifier/eventIdentifierType`)'
    id = xmlmap.StringField('p:eventIdentifier/p:eventIdentifierValue')
    'identifier value (`eventIdentifier/eventIdentifierValue`)'
    date = xmlmap.StringField('p:eventDateTime')
    'date/time for the event (`eventDateTime`)'
    detail = xmlmap.StringField('p:eventDetail', required=False)
    'event detail (`eventDetail`)'
    outcome = xmlmap.StringField('p:eventOutcomeInformation/p:eventOutcome', required=False)
    '''outcome of the event (`eventOutcomeInformation/eventOutcome`).
    
    .. Note::
      In this preliminary implementation, the outcome detail fields
      are not mapped.
    '''
    # leaving out outcome detail for now...

    # agent (optional, could be repeated)
    agent_type = xmlmap.StringField('p:linkingAgentIdentifier/p:linkingAgentIdentifierType')
    agent_id = xmlmap.StringField('p:linkingAgentIdentifier/p:linkingAgentIdentifierValue')

    # object (optional, could be repeated)
    object_type = xmlmap.StringField('p:linkingObjectIdentifier/p:linkingObjectIdentifierType')
    object_id = xmlmap.StringField('p:linkingObjectIdentifier/p:linkingObjectIdentifierValue')


class Premis(PremisRoot):
    '''Preliminary :class:`~eulxml.xmlmap.XmlObject` for a PREMIS
    container element that can contain any of the other top-level
    PREMIS elements.

    Curently only includes mappings for a single object and list of
    events.
    '''
    ROOT_NAME = 'premis'

    version = xmlmap.StringField('@version')
    '''Version of PREMIS in use; by default, new instances of
    :class:`Premis` will be initialized with a version of 2.1'''
    object = xmlmap.NodeField('p:object', Object)
    'a single PREMIS :class:`object`'
    events = xmlmap.NodeListField('p:event', Event)
    'list of PREMIS events, as instances of :class:`Event`'

    def __init__(self, *args, **kwargs):
        # version is required for schema-validity; don't override a
        # user-supplied version, but otherwise default to 2.1
        if 'version' not in kwargs:
            kwargs['version'] = '2.1'
        super(Premis, self).__init__(*args, **kwargs)

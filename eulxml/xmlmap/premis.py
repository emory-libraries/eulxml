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
:mod:`eulxml.xmlmap` classes for dealing with the
`PREMIS <http://www.loc.gov/standards/premis/>`_ metadata format
for preservation metadta and maintenance.
'''

from eulxml import xmlmap

PREMIS_NAMESPACE = 'info:lc/xmlns/premis-v2'
PREMIS_SCHEMA = 'http://www.loc.gov/standards/premis/premis.xsd'

class BasePremis(xmlmap.XmlObject):
    "Base PREMIS class with namespace declaration common to all PREMIS XmlObjects."
    ROOT_NS = PREMIS_NAMESPACE
    ROOT_NAMESPACES = {
        'p': PREMIS_NAMESPACE,
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }

class Object(BasePremis):
    'PREMIS object'
    ROOT_NAME = 'object'
    type = xmlmap.StringField('@xsi:type') # file, representation, bitstream
    id_type = xmlmap.StringField('p:objectIdentifier/p:objectIdentifierType')
    id = xmlmap.StringField('p:objectIdentifier/p:objectIdentifierValue')

class EventIdentifier(BasePremis):
    ROOT_NAME = 'eventIdentifier'
    type = xmlmap.StringField('p:eventIdentifierType')
    value = xmlmap.StringField('p:eventIdentifierValue')
    
class Event(BasePremis):
    'PREMIS Event'
    ROOT_NAME = 'event'
    type = xmlmap.StringField('p:eventType')
    identifier = xmlmap.NodeField('p:eventIdentifier', EventIdentifier)
    date = xmlmap.StringField('p:eventDateTime')
    detail = xmlmap.StringField('p:eventDetail', required=False)
    outcome = xmlmap.StringField('p:eventOutcomeInformation/p:eventOutcome', required=False)
    # leaving out outcome detail for now...

    # agent (optional, could be repeated)
    agent_type = xmlmap.StringField('p:linkingAgentIdentifier/p:linkingAgentIdentifierType')
    agent_id = xmlmap.StringField('p:linkingAgentIdentifier/p:linkingAgentIdentifierValue')

    # object (optional, could be repeated)
    object_type = xmlmap.StringField('p:linkingObjectIdentifier/p:linkingObjectIdentifierType')
    object_id = xmlmap.StringField('p:linkingObjectIdentifier/p:linkingObjectIdentifierValue')


class Premis(BasePremis):
    'PREMIS container record'
    ROOT_NAME = 'premis'
    xmlschema = xmlmap.loadSchema(PREMIS_SCHEMA)

    _schema_loc = 'info:lc/xmlns/premis-v2 http://www.loc.gov/standards/premis/v2/premis-v2-1.xsd'

    version = xmlmap.StringField('@version')
    schema_location = xmlmap.StringField('@xsi:schemaLocation')
    object = xmlmap.NodeField('p:object', Object)
    events = xmlmap.NodeListField('p:event', Event)

    def __init__(self, *args, **kwargs):
        super(Premis, self).__init__(version='2.1', schema_location=self._schema_loc,
                                     *args, **kwargs)

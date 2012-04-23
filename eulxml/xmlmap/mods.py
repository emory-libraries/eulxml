# file eulxml/xmlmap/mods.py
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
`MODS <http://www.loc.gov/standards/mods/>`_ metadata format
(Metadata Object Description Schema).
'''

from eulxml import xmlmap

MODS_NAMESPACE = 'http://www.loc.gov/mods/v3'
MODS_SCHEMA = "http://www.loc.gov/standards/mods/mods.xsd"
MODSv34_SCHEMA = "http://www.loc.gov/standards/mods/v3/mods-3-4.xsd"

class Common(xmlmap.XmlObject):
    '''MODS class with namespace declaration common to all MODS
    XmlObjects.  Defines the MODS schema (e.g., for use with
    :class:`xmlmap.SchemaField`), but by sets ``schema_validate`` to
    False.
    '''
    ROOT_NS = MODS_NAMESPACE
    ROOT_NAMESPACES = {'mods': MODS_NAMESPACE }
    XSD_SCHEMA = MODS_SCHEMA
    schema_validate = False

class Date(Common):
    ''':class:`~eulxml.xmlmap.XmlObject` for MODS date element (common fields
    for the dates under mods:originInfo).'''
    # this class not meant for direct use; should be extended for specific dates.

    date = xmlmap.StringField('text()')
    key_date = xmlmap.SimpleBooleanField('@keyDate', 'yes', false=None)
    encoding = xmlmap.SchemaField('@encoding', 'dateEncodingAttributeDefinition')
    point = xmlmap.SchemaField('@point', 'datePointAttributeDefinition')
    qualifier = xmlmap.SchemaField('@qualifier', 'dateQualifierAttributeDefinition')

    def is_empty(self):
        '''Returns False if no date value is set; returns True if any date value
        is set.  Attributes are ignored for determining whether or not the
        date should be considered empty, as they are only meaningful in
        reference to a date value.'''
        return not self.node.text

class DateCreated(Date):
    ROOT_NAME = 'dateCreated'

class DateIssued(Date):
    ROOT_NAME = 'dateIssued'

class OriginInfo(Common):
    ":class:`~eulxml.xmlmap.XmlObject` for MODS originInfo element (incomplete)"
    ROOT_NAME = 'originInfo'
    created = xmlmap.NodeListField('mods:dateCreated', DateCreated,
        verbose_name='Date Created',
        help_text='Date the resource was first created (e.g., date of recording,' +
            ' photograph taken, or letter written)')
    issued = xmlmap.NodeListField('mods:dateIssued', DateIssued,
        verbose_name='Date Issued',
        help_text='Date the resource was published, released, or issued')
    publisher = xmlmap.StringField('mods:publisher')

    def is_empty(self):
        """Returns True if all child date elements present are empty
        and other nodes are not set.  Returns False if any child date
        elements are not empty or other nodes are set."""
        return all(date.is_empty() for date in set.union(set(self.created), set(self.issued))) \
               and not self.publisher

class RecordInfo(Common):
    ROOT_NAME = 'recordInfo'
    record_id = xmlmap.StringField('mods:recordIdentifier')
    record_origin = xmlmap.StringField('mods:recordOrigin')
    creation_date = xmlmap.StringField('mods:recordCreationDate[@encoding="w3cdtf"]')
    change_date = xmlmap.StringField('mods:recordChangeDate[@encoding="w3cdtf"]')

class Note(Common):
    ":class:`~eulxml.xmlmap.XmlObject` for MODS note element"
    ROOT_NAME = 'note'
    label = xmlmap.StringField('@displayLabel')
    type = xmlmap.StringField('@type')
    text = xmlmap.StringField('text()')      # actual text value of the note

class TypedNote(Note):
    '''Extends :class:`Note` to modify :meth:`is_empty` behavior-- considered
    empty when a type attribute is set without any text.'''
    
    def is_empty(self):
        """Returns True if the root node contains no child elements, no text,
        and no attributes other than **type**. Returns False if any are present."""
        non_type_attributes = [attr for attr in self.node.attrib.keys() if attr != 'type']
        return len(self.node) == 0 and len(non_type_attributes) == 0 \
            and not self.node.text and not self.node.tail


class Identifier(Common):
    ':class:`~eulxml.xmlmap.XmlObject` for MODS identifier'
    ROOT_NAME = 'identifier'
    type = xmlmap.StringField('@type')
    text = xmlmap.StringField('text()')
    label = xmlmap.StringField('@displayLabel')

class AccessCondition(Common):
    ':class:`~eulxml.xmlmap.XmlObject` for MODS accessCondition'
    ROOT_NAME = 'accessCondition'
    type = xmlmap.StringField('@type',
            choices=['restrictions on access', 'use and reproduction'])
    text = xmlmap.StringField('text()')

class NamePart(Common):
    ':class:`~eulxml.xmlmap.XmlObject` for MODS namePart'
    ROOT_NAME = 'namePart'
    # FIXME: schema required here for schemafields; this should be refactored

    type = xmlmap.SchemaField('@type', 'namePartTypeAttributeDefinition',
                              required=False) # type is optional
    text = xmlmap.StringField('text()')

class Role(Common):
    ':class:`~eulxml.xmlmap.XmlObject` for MODS role'
    ROOT_NAME = 'role'
    type = xmlmap.StringField('mods:roleTerm/@type')
    authority = xmlmap.StringField('mods:roleTerm/@authority', choices=['', 'marcrelator', 'local'])
    text = xmlmap.StringField('mods:roleTerm')

class Name(Common):
    ':class:`~eulxml.xmlmap.XmlObject` for MODS name'
    ROOT_NAME = 'name'

    type = xmlmap.SchemaField('@type', 'nameTypeAttributeDefinition', required=False)
    authority = xmlmap.StringField('@authority', choices=['', 'local', 'naf'], required=False) # naf = NACO authority file
    id = xmlmap.StringField('@ID', required=False)  # optional
    name_parts = xmlmap.NodeListField('mods:namePart', NamePart)
    display_form = xmlmap.StringField('mods:displayForm')
    affiliation = xmlmap.StringField('mods:affiliation')
    roles = xmlmap.NodeListField('mods:role', Role)

    def __unicode__(self):
        # default text display of a name (excluding roles for now)
        # TODO: improve logic for converting to plain-text name
        # (e.g., for template display, setting as dc:creator, etc)
        return ' '.join([unicode(part) for part in self.name_parts])

class Genre(Common):
    ROOT_NAME = 'genre'
    authority = xmlmap.StringField('@authority')
    text = xmlmap.StringField('text()')

class LanguageTerm(Common):
    ROOT_NAME = 'languageTerm'
    type = xmlmap.StringField('@type')
    authority = xmlmap.StringField('@authority')
    text = xmlmap.StringField('text()')

class Language(Common):
    ROOT_NAME = 'language'
    terms = xmlmap.NodeListField('mods:languageTerm', LanguageTerm)

class Location(Common):
    ROOT_NAME = 'location'
    physical = xmlmap.StringField('mods:physicalLocation')
    url = xmlmap.StringField('mods:url')
    # NOTE: mods:location subfields are ordered;
    # setting them in the wrong order could currently generate invalid mods...

class Subject(Common):
    ROOT_NAME = 'subject'
    authority = xmlmap.StringField('@authority')
    id = xmlmap.StringField('@ID')

    # and one of the following:
    geographic = xmlmap.StringField('mods:geographic')
    name = xmlmap.NodeField('mods:name', Name)
    topic = xmlmap.StringField('mods:topic')
    title = xmlmap.StringField('mods:titleInfo/mods:title')

class TitleInfo(Common):
    ROOT_NAME = 'titleInfo'

    title = xmlmap.StringField('mods:title')
    subtitle = xmlmap.StringField('mods:subTitle')
    part_number = xmlmap.StringField('mods:partNumber')
    part_name = xmlmap.StringField('mods:partName')
    non_sort = xmlmap.StringField('mods:nonSort')
    type  = xmlmap.SchemaField('@type', 'titleInfoTypeAttributeDefinition')


    def is_empty(self):
        '''Returns True if all titleInfo subfields are not set or
        empty; returns False if any of the fields are not empty.'''
        return not bool(self.title or self.subtitle or self.part_number \
                        or self.part_name or self.non_sort or self.type)

class Abstract(Common):
    ROOT_NAME = 'abstract'
    text = xmlmap.StringField('text()')
    type = xmlmap.StringField('@type')
    label = xmlmap.StringField('@displayLabel')

class PhysicalDescription(Common):
    ROOT_NAME = 'physicalDescription'
    media_type = xmlmap.StringField('mods:internetMediaType')
    extent = xmlmap.StringField('mods:extent')

class PartDetail(Common):
    ROOT_NAME = 'detail'
    type = xmlmap.StringField('@type')
    number = xmlmap.StringField('mods:number')

    def is_empty(self):
        '''Returns False if no number value is set; returns True if
        any number value is set.  Type attribute is ignored for
        determining whether or not this node should be considered
        empty.'''
        # disregard type attribute when checking if empty
        return not self.number

class PartExtent(Common):
    ROOT_NAME = 'extent'
    unit = xmlmap.StringField('@unit')
    start = xmlmap.StringField('mods:start')
    end = xmlmap.StringField('mods:end')
    total = xmlmap.StringField('mods:total')

    def is_empty(self):
        '''Returns False if no extent value is set; returns True if
        any extent value is set.  Unit attribute is ignored for
        determining whether or not this node should be considered
        empty.'''
        # disregard type attribute when checking if empty
        return not bool(self.start or self.end or self.total)


class Part(Common):
    ROOT_NAME = 'part'
    type = xmlmap.StringField('@type')
    details = xmlmap.NodeListField('mods:detail', PartDetail)
    extent = xmlmap.NodeField('mods:extent', PartExtent)

    def is_empty(self):
        '''Returns True if details, extent, and type are not set or
        return True for ``is_empty``; returns False if any of the
        fields are not empty.'''
        return all(field.is_empty() for field in [self.details, self.extent]
                   			if field is not None) \
               and not self.type

class BaseMods(Common):
    ''':class:`~eulxml.xmlmap.XmlObject` with common field declarations for all
    top-level MODS elements; base class for :class:`MODS` and :class:`RelatedItem`.'''
    schema_validate = True

    title = xmlmap.StringField("mods:titleInfo/mods:title")
    title_info = xmlmap.NodeField('mods:titleInfo', TitleInfo)
    resource_type  = xmlmap.SchemaField("mods:typeOfResource", "resourceTypeDefinition")
    name = xmlmap.NodeField('mods:name', Name)  # DEPRECATED: use names instead
    names = xmlmap.NodeListField('mods:name', Name)
    note = xmlmap.NodeField('mods:note', Note)
    notes = xmlmap.NodeListField('mods:note', Note)
    origin_info = xmlmap.NodeField('mods:originInfo', OriginInfo)
    record_info = xmlmap.NodeField('mods:recordInfo', RecordInfo)
    identifiers = xmlmap.NodeListField('mods:identifier', Identifier)
    access_conditions = xmlmap.NodeListField('mods:accessCondition', AccessCondition)
    genres = xmlmap.NodeListField('mods:genre', Genre)
    languages = xmlmap.NodeListField('mods:language', Language)
    location = xmlmap.StringField('mods:location/mods:physicalLocation',
                                  required=False)
    locations = xmlmap.NodeListField('mods:location', Location)
    subjects = xmlmap.NodeListField('mods:subject', Subject)
    physical_description = xmlmap.NodeField('mods:physicalDescription', PhysicalDescription)
    abstract = xmlmap.NodeField('mods:abstract', Abstract)
    parts = xmlmap.NodeListField('mods:part', Part)

class RelatedItem(BaseMods):
    ''':class:`~eulxml.xmlmap.XmlObject` for MODS relatedItem: contains all the
    top-level MODS fields defined by :class:`BaseMods`, plus a type attribute.'''
    ROOT_NAME = 'relatedItem'
    type = xmlmap.SchemaField("@type", 'relatedItemTypeAttributeDefinition')
    label = xmlmap.StringField('@displayLabel')
    
class MODS(BaseMods):
    '''Top-level :class:`~eulxml.xmlmap.XmlObject` for a MODS metadata record.
    Inherits all standard top-level MODS fields from :class:`BaseMods` and adds
    a mapping for :class:`RelatedItem`.
    '''
    ROOT_NAME = 'mods'
    related_items = xmlmap.NodeListField('mods:relatedItem', RelatedItem)


class MODSv34(MODS):
    ''':class:`~eulxml.xmlmap.XmlObject` for MODS version 3.4.  Currently
    consists of all the same fields as :class:`MODS`, but loads the MODS version
    3.4 schema for validation.
    '''
    XSD_SCHEMA = MODSv34_SCHEMA
    # FIXME: how to set version attribute when creating from scratch?

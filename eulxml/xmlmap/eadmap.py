# file eulxml/xmlmap/eadmap.py
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

from copy import deepcopy

from eulxml import xmlmap

# xmlmap objects for various sections of an ead
# organized from smallest/lowest level to highest level

EAD_NAMESPACE = 'urn:isbn:1-931666-22-9'

class _EadBase(xmlmap.XmlObject):
    '''Common EAD namespace declarations, for use by all EAD XmlObject instances.'''
    ROOT_NS = EAD_NAMESPACE
    ROOT_NAME = 'ead'
    ROOT_NAMESPACES = {
        'e' : ROOT_NS,
        'xlink': 'http://www.w3.org/1999/xlink',
        'exist': 'http://exist.sourceforge.net/NS/exist'
    }
    # TODO: if there are any universal EAD attributes, they should be added here

    # NOTE: this is not an EAD field, but simplifies using EAD objects with eXist
    # by making exist match-count totals available at any level
    match_count = xmlmap.IntegerField("count(.//exist:match)")
    'Count of exist matches under the current field - for use with EAD and eXist-db'

class Note(_EadBase):
    """EAD note."""
    content = xmlmap.StringListField("e:p")
    "list of paragraphs - `p`"

class Section(_EadBase):
    """Generic EAD section.  Currently only has mappings for head, paragraph, and note."""
    head   = xmlmap.NodeField("e:head", xmlmap.XmlObject)
    "heading - `head`"
    content = xmlmap.NodeListField("e:p", xmlmap.XmlObject)       # ??
    "list of paragraphs - `p`"
    note = xmlmap.NodeField("e:note", Note)
    ":class:`Note`"


class Heading(_EadBase):
    """Generic xml object for headings used under `controlaccess`"""
    source = xmlmap.StringField("@source")
    "source vocabulary for controlled term - `@source`"
    value  = xmlmap.StringField(".", normalize=True)
    "controlled term text value (content of the heading element)"

    def __unicode__(self):
        return self.value


class ControlledAccessHeadings(Section):
    """
    Controlled access headings, such as subject terms, family and corporate
    names, etc.

    Expected node element passed to constructor: `contolaccess`.
    """
    person_name = xmlmap.NodeListField("e:persname", Heading)
    "person name :class:`Heading` list - `persname`"
    family_name = xmlmap.NodeListField("e:famname", Heading)
    "family name :class:`Heading` list  - `famname`"
    corporate_name = xmlmap.NodeListField("e:corpname", Heading)
    "corporate name :class:`Heading` list  - `corpname`"
    subject = xmlmap.NodeListField("e:subject", Heading)
    "subject :class:`Heading` list - `subject`"
    geographic_name = xmlmap.NodeListField("e:geogname", Heading)
    "geographic name :class:`Heading` list - `geogname`"
    genre_form = xmlmap.NodeListField("e:genreform", Heading)
    "genre or form :class:`Heading` list - `genreform`"
    occupation = xmlmap.NodeListField("e:occupation", Heading)
    "occupation :class:`Heading` list - `occupation`"
    function = xmlmap.NodeListField("e:function", Heading)
    "function :class:`Heading` list - `function`"
    title = xmlmap.NodeListField("e:title", Heading)
    "title :class:`Heading` list - `title`"
    # catch-all to get any of these, in order
    terms = xmlmap.NodeListField("e:corpname|e:famname|e:function|e:genreform|e:geogname|e:occupation|e:persname|e:subject|e:title", Heading)
    "list of :class:`Heading` - any allowed control access terms, in whatever order they appear"

    controlaccess = xmlmap.NodeListField("e:controlaccess", "self")
    "list of :class:`ControlledAccessHeadings` - recursive mapping to `controlaccess`"


class Container(_EadBase):
    """
    Container - :class:`DescriptiveIdentification` subelement for locating materials.

    Expected node element passed to constructor: `did/container`.
    """
    type = xmlmap.StringField("@type")
    "type - `@type`"
    value = xmlmap.StringField(".")
    "text value - (contents of the container element)"

    def __unicode__(self):
        return self.value

class DateField(_EadBase):
    """
    DateField - for access to date and unitdate elements value and attributes.
    When converted to unicode, will be the non-normalized version of the date
    in the text content of the element.
    """
    normalized = xmlmap.StringField("@normal")
    "normalized form of the date - `@normal`"
    calendar = xmlmap.StringField("@calendar")
    "calendar (e.g. gregorian) - `@calendar`"
    era = xmlmap.StringField("@era")
    "era (e.g. ce) - `@era`"
    value = xmlmap.StringField(".")
    "human-readable date - (contents of the date element)"

    def __unicode__(self):
        return self.value
    
class Unitid(_EadBase):
    '''Unitid element'''
    identifier = xmlmap.IntegerField('@identifier')
    'machine-readable identifier - `@identifier`'
    country_code = xmlmap.StringField('@countrycode')
    'country code - `@countrycode`'
    repository_code = xmlmap.StringField('@repositorycode')
    'repository code - `@repositorycode`'
    value = xmlmap.StringField('.')
    "human-readable unitid - (contents of the element)"

class UnitTitle(_EadBase):
    unitdate = xmlmap.NodeField("e:unitdate", DateField)
    "unit date"
    
    @property
    def short(self):
        '''Short-form of the unit title, excluding any unit date, as an instance
        of :class:`~eulxml.xmlmap.eadmap.UnitTitle` . Can be used with formatting
        anywhere the full form of the unittitle can be used.'''
        # if there is no unitdate to remove, just return the current object
        if not self.unitdate:
            return self

        # preserve any child elements (e.g., title or emph) 
        # initialize a unittitle with a *copy* of the current node
        ut = UnitTitle(node=deepcopy(self.node))
        # remove the unitdate node and return
        ut.node.remove(ut.unitdate.node)
        return ut
        # not caching the modified node because the main node could be modified
        # and the short version should reflect any changes made


class DescriptiveIdentification(_EadBase):
    """Descriptive Information (`did` element) for materials in a component"""
    unitid = xmlmap.NodeField("e:unitid", Unitid)
    ":class:`Unitid` - `unitid`"
    unittitle = xmlmap.NodeField("e:unittitle", UnitTitle)
    "unit title - `unittitle`"
    unitdate = xmlmap.NodeField(".//e:unitdate", DateField)
    "unit date - `.//unitdate` can be anywhere under the DescriptiveIdentification"
    physdesc = xmlmap.StringField("e:physdesc")
    "physical description - `physdesc`"
    abstract = xmlmap.NodeField('e:abstract', xmlmap.XmlObject)
    "abstract - `abstract`"
    langmaterial = xmlmap.StringField("e:langmaterial")
    "language of materials - `langmaterial`"
    origination = xmlmap.StringField("e:origination", normalize=True)
    "origination - `origination`"
    location = xmlmap.StringField("e:physloc")
    "physical location - `physloc`"
    container = xmlmap.NodeListField("e:container", Container)
    ":class:`Container` - `container`"    


class Component(_EadBase):
    """Generic component `cN` (`c1`-`c12`) element - a subordinate component of the materials"""
    level = xmlmap.StringField("@level")
    "level of the component - `@level`"
    id = xmlmap.StringField("@id")
    "component id - `@id`"
    did = xmlmap.NodeField("e:did", DescriptiveIdentification)
    ":class:`DescriptiveIdentification` - `did`"
    # FIXME: these sections overlap significantly with those in archdesc; share/inherit?
    use_restriction = xmlmap.NodeField("e:userestrict", Section)
    "usage restrictions :class:`Section` - `userestrict`"
    alternate_form = xmlmap.NodeField("e:altformavail", Section)
    "alternative form available :class:`Section` - `altformavail`"
    originals_location = xmlmap.NodeField("e:originalsloc", Section)
    "location of originals :class:`Section` - `originalsloc`"
    related_material = xmlmap.NodeField("e:relatedmaterial", Section)
    "related material :class:`Section` - `relatedmaterial`"
    separated_material = xmlmap.NodeField("e:separatedmaterial", Section)
    "separated material :class:`Section` - `separatedmaterial`"
    acquisition_info = xmlmap.NodeField("e:acqinfo", Section)
    "acquistion info :class:`Section` - `acqinfo`"
    custodial_history = xmlmap.NodeField("e:custodhist", Section)
    "custodial history :class:`Section` - `custodhist`"
    preferred_citation = xmlmap.NodeField("e:prefercite", Section)
    "preferred citation :class:`Section` - `prefercite`"
    biography_history = xmlmap.NodeField("e:bioghist", Section)
    "biography or history :class:`Section` - `bioghist`"
    bibliography = xmlmap.NodeField("e:bibliography", Section)
    "bibliography :class:`Section` - `bibliograhy`"
    scope_content  = xmlmap.NodeField("e:scopecontent", Section)
    "scope and content :class:`Section` - `scopecontent`"
    arrangement = xmlmap.NodeField("e:arrangement", Section)
    "arrangement :class:`Section` - `arrangement`"
    other = xmlmap.NodeField("e:otherfindaid", Section)
    "other finding aid :class:`Section` - `otherfindaid`"
    use_restriction = xmlmap.NodeField("e:userestrict", Section)
    "use restrictions :class:`Section` - `userestrict`"
    access_restriction = xmlmap.NodeField("e:accessrestrict", Section)
    "access restrictions :class:`Section` - `accessrestrict`"

    c = xmlmap.NodeListField("e:c02|e:c03|e:c04|e:c05|e:c06|e:c07|e:c08|e:c09|e:c10|e:c11|e:c12", "self")
    "list of :class:`Component` - recursive mapping to any c-level 2-12; `c02|c03|c04|c05|c06|c07|c08|c09|c10|c11|c12`"
    
    # using un-numbered mapping for c-series or container lists
    def hasSubseries(self):
        """Check if this component has subseries or not.

           Determined based on level of first subcomponent (series or subseries)
           or if first component has subcomponents present.

            :rtype: boolean
        """
        if self.c and self.c[0] and ((self.c[0].level in ('series', 'subseries')) or
            (self.c[0].c and self.c[0].c[0])):            
            return True
        else:
            return False


class SubordinateComponents(Section):
    """Description of Subordinate Components (dsc element); container lists and series.
    
       Expected node element passed to constructor: `ead/archdesc/dsc`.
    """

    type = xmlmap.StringField("@type")
    "type of component - `@type`"
    c = xmlmap.NodeListField("e:c01", Component)
    "list of :class:`Component` - `c01`; list of c01 elements directly under this section"
    
    def hasSeries(self):
        """Check if this finding aid has series/subseries.

           Determined based on level of first component (series) or if first
           component has subcomponents present.

           :rtype: boolean
        """
        if len(self.c) and (self.c[0].level == 'series' or (self.c[0].c and self.c[0].c[0])):
            return True
        else:
            return False

class Reference(_EadBase):
    """Internal linking element that may contain text.

    Expected node element passed to constructor: `ref`.
    """
    type = xmlmap.StringField("@xlink:type")
    "link type - `xlink:type`"
    target = xmlmap.StringField("@target")
    "link target"
    value = xmlmap.NodeField(".", xmlmap.XmlObject)
    "text content of the reference"
    # TODO: add mappings for other relevant reference and link attributes

    def __unicode__(self):
        return self.value


class PointerGroup(_EadBase):
    """Group of pointer or reference elements in an index entry
    
    Expected node element passed to constructor: `ptrgrp`.
    """
    ref = xmlmap.NodeListField("e:ref", Reference)
    "list of :class:`Reference` - references"


class IndexEntry(_EadBase):
    "Index entry in an archival description index."
    name = xmlmap.NodeField("e:corpname|e:famname|e:function|e:genreform|e:geogname|e:name|e:namegrp|e:occupation|e:persname|e:title|e:subject",
                            xmlmap.XmlObject)
    "access element, e.g. name or subject"
    ptrgroup = xmlmap.NodeField("e:ptrgrp", PointerGroup)
    ":class:`PointerGroup` - group of references for this index entry"


class Index(Section):
    """Index (index element); list of key terms and reference information.

       Expected node element passed to constructor: `ead/archdesc/index`.
    """
    entry = xmlmap.NodeListField("e:indexentry", IndexEntry)
    "list of :class:`IndexEntry` - `indexentry`; entry in the index"
    id = xmlmap.StringField("@id")


class ArchivalDescription(_EadBase):
    """Archival description, contains the bulk of the information in an EAD document.

      Expected node element passed to constructor: `ead/archdesc`.
      """
    did = xmlmap.NodeField("e:did", DescriptiveIdentification)
    'descriptive identification :class:`DescriptiveIdentification` - `did`'
    origination = xmlmap.StringField("e:did/e:origination", normalize=True)
    "origination - `did/origination`"
    unitid = xmlmap.NodeField("e:did/e:unitid", Unitid)
    ":class:`Unitid` - `did/unitid`"
    extent = xmlmap.StringListField("e:did/e:physdesc/e:extent")
    "extent from the physical description - `did/physdesc/extent`"
    langmaterial = xmlmap.StringField("e:did/e:langmaterial")
    "language of the materials - `did/langmaterial`"
    location = xmlmap.StringField("e:did/e:physloc")
    "physical location - `did/physloc`"
    access_restriction = xmlmap.NodeField("e:accessrestrict", Section)
    "access restrictions :class:`Section` - `accessrestrict`"
    use_restriction = xmlmap.NodeField("e:userestrict", Section)
    "use restrictions :class:`Section` - `userestrict`"
    alternate_form = xmlmap.NodeField("e:altformavail", Section)
    "alternative form available :class:`Section` - `altformavail`"
    originals_location = xmlmap.NodeField("e:originalsloc", Section)
    "location of originals :class:`Section` - `originalsloc`"
    related_material = xmlmap.NodeField("e:relatedmaterial", Section)
    "related material :class:`Section` - `relatedmaterial`"
    separated_material = xmlmap.NodeField("e:separatedmaterial", Section)
    "separated material :class:`Section` - `separatedmaterial`"
    acquisition_info = xmlmap.NodeField("e:acqinfo", Section)
    "acquistion info :class:`Section` - `acqinfo`"
    custodial_history = xmlmap.NodeField("e:custodhist", Section)
    "custodial history :class:`Section` - `custodhist`"
    preferred_citation = xmlmap.NodeField("e:prefercite", Section)
    "preferred citation :class:`Section` - `prefercite`"
    biography_history = xmlmap.NodeField("e:bioghist", Section)
    "biography or history :class:`Section` - `bioghist`"
    bibliography = xmlmap.NodeField("e:bibliography", Section)
    "bibliography :class:`Section` - `bibliograhy`"
    scope_content  = xmlmap.NodeField("e:scopecontent", Section)
    "scope and content :class:`Section` - `scopecontent`"
    arrangement = xmlmap.NodeField("e:arrangement", Section)
    "arrangement :class:`Section` - `arrangement`"
    other = xmlmap.NodeField("e:otherfindaid", Section)
    "other finding aid :class:`Section` - `otherfindaid`"
    controlaccess = xmlmap.NodeField("e:controlaccess", ControlledAccessHeadings)
    ":class:`ControlledAccessHeadings` - `controlaccess`; subject terms, names, etc."
    index = xmlmap.NodeListField("e:index", Index)
    "list of :class:`Index` - `index`; e.g., index of selected correspondents"

class Address(_EadBase):
    """Address information.

      Expected node element passed to constructor: `address`.
    """
    lines = xmlmap.StringListField("e:addressline")
    "list of lines in an address - `line`"

class PublicationStatement(_EadBase):
    """Publication information for an EAD document.

    Expected node element passed to constructor: `ead/eadheader/filedesc/publicationstmt`.
    """
    date = xmlmap.NodeField("e:date", DateField)
    ":class:`DateField` - `date`"
    publisher = xmlmap.StringField("e:publisher")
    "publisher - `publisher`"
    address = xmlmap.NodeField("e:address", Address)
    "address of publication/publisher - `address`"

class ProfileDescription(_EadBase):
    """Profile Descriptor for an EAD document.
       Expected node element passed to constructor: 'ead/eadheader/profiledesc'.
    """
    date = xmlmap.NodeField("e:creation/e:date", DateField)
    ":class:`DateField` - `creation/date`"
    languages = xmlmap.StringListField("e:langusage/e:language")
    "language information - `langusage/language`"
    language_codes = xmlmap.StringListField("e:langusage/e:language/@langcode")
    "language codes - `langusage/language/@langcode`"
    
class FileDescription(_EadBase):
    """Bibliographic information about this EAD document.

      Expected node element passed to constructor: `ead/eadheader/filedesc`.
      """
    publication = xmlmap.NodeField("e:publicationstmt", PublicationStatement)
    "publication information - `publicationstmt`"

class EadId(_EadBase):
    """EAD identifier for a single EAD finding aid document.

    Expected element passed to constructor: `ead/eadheader/eadid`.
    """
    country = xmlmap.StringField('@countrycode')
    "country code - `@countrycode`"
    maintenance_agency = xmlmap.StringField('@mainagencycode')
    "maintenance agency - `@mainagencycode`"
    url = xmlmap.StringField('@url')
    "url - `@url`"
    identifier = xmlmap.StringField('@identifier')
    "identifier - `@identifier`"
    value = xmlmap.StringField(".")
    "text content of the eadid node"

class EncodedArchivalDescription(_EadBase):
    """:class:`~eulxml.xmlmap.XmlObject` for an Encoded Archival Description
    (EAD) Finding Aid (Schema-based).  All XPaths use the EAD namespace; this
    class can not be used with non-namespaced, DTD-based EAD.

    Expects node passed to constructor to be top-level `ead` element.
    """

    XSD_SCHEMA = 'http://www.loc.gov/ead/ead.xsd'

    id = xmlmap.StringField('@id')
    "top-level id attribute - `@id`; preferable to use eadid"
    eadid = xmlmap.NodeField('e:eadheader/e:eadid', EadId)
    "ead id :class:`EadId` - `eadheader/eadid`"
    # mappings for fields common to access or display as top-level information
    title = xmlmap.NodeField('e:eadheader/e:filedesc/e:titlestmt/e:titleproper', xmlmap.XmlObject)
    "record title - `eadheader/filedesc/titlestmt/titleproper`"
    author = xmlmap.StringField('e:eadheader/e:filedesc/e:titlestmt/e:author')
    "record author - `eadheader/filedesc/titlestmt/author`"
    unittitle = xmlmap.NodeField('e:archdesc[@level="collection"]/e:did/e:unittitle', UnitTitle)
    """unit title for the archive - `archdesc[@level="collection"]/did/unittitle`"""
    physical_desc = xmlmap.StringField('e:archdesc[@level="collection"]/e:did/e:physdesc')
    """collection level physical description - `archdesc[@level="collection"]/did/physdesc`"""
    abstract = xmlmap.NodeField('e:archdesc[@level="collection"]/e:did/e:abstract', xmlmap.XmlObject)
    """collection level abstract - `archdesc[@level="collection"]/did/abstract`"""
    
    archdesc  = xmlmap.NodeField("e:archdesc", ArchivalDescription)
    ":class:`ArchivalDescription` - `archdesc`"
    # dsc is under archdesc, but is a major section - mapping at top-level for convenience
    dsc = xmlmap.NodeField("e:archdesc/e:dsc", SubordinateComponents)
    ":class:`SubordinateComponents` `archdesc/dsc`; accessible at top-level for convenience"
    file_desc = xmlmap.NodeField("e:eadheader/e:filedesc", FileDescription)
    ":class:`FileDescription` - `filedesc`"
    profiledesc = xmlmap.NodeField("e:eadheader/e:profiledesc", ProfileDescription)
    ":class:`ProfileDescription` - `profiledesc`"


# file eulxml/xmlmap/teimap.py
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

from eulxml import xmlmap

# TODO: generic/base tei xml object with common attributes?

TEI_NAMESPACE = 'http://www.tei-c.org/ns/1.0'

class _TeiBase(xmlmap.XmlObject):
    '''Common TEI namespace declarations, for use by all TEI XmlObject instances.'''
    ROOT_NS = TEI_NAMESPACE
    ROOT_NAME = 'tei'
    ROOT_NAMESPACES = {
        'tei' : ROOT_NS,
    }

class TeiLine(_TeiBase):
    rend        = xmlmap.StringField("@rend")

    """set up indents for lines with @rend=indent plus some number. Handle default indent in css."""
    def indent(self):
        if self.rend.startswith("indent"):
            indentation = self.rend[len("indent"):]
            if indentation:
                return int(indentation)
            else:
                return 0

class TeiLineGroup(_TeiBase):
    head        = xmlmap.StringField('tei:head')
    linegroup   = xmlmap.NodeListField('tei:lg', 'self')
    line        = xmlmap.NodeListField('tei:l', TeiLine)

            
class TeiQuote(_TeiBase):
    line    = xmlmap.NodeListField('tei:l', TeiLine)
    linegroup = xmlmap.NodeListField('tei:lg', TeiLineGroup)
    
class TeiEpigraph(_TeiBase):
    quote = xmlmap.NodeListField('tei:q|tei:quote|tei:cit/tei:q|tei:cit/tei:quote', TeiQuote)
    bibl  = xmlmap.StringField('tei:bibl')


class TeiDiv(_TeiBase):
    id       = xmlmap.StringField('@xml:id')
    type     = xmlmap.StringField('@type')
    author   = xmlmap.StringField('tei:docAuthor/tei:name/tei:choice/tei:sic')
    docauthor = xmlmap.StringField('tei:docAuthor')
    title     = xmlmap.StringField('tei:head[1]') # easy access to FIRST head
    title_list = xmlmap.StringListField('tei:head')   # access to all heads when there are multiple
    text     = xmlmap.StringField('.')   # short-hand mapping for full text of a div (e.g., for short divs)
    linegroup = xmlmap.NodeListField('tei:lg', TeiLineGroup)
    div      = xmlmap.NodeListField('tei:div', 'self')
    byline   = xmlmap.StringField('tei:byline')
    epigraph = xmlmap.NodeListField('tei:epigraph', TeiEpigraph)
    p        = xmlmap.StringListField('tei:p')
    q        = xmlmap.StringListField('tei:q')
    quote    = xmlmap.StringListField('tei:quote')
    floatingText = xmlmap.NodeListField('tei:floatingText/tei:body/tei:div', 'self')

class TeiFloatingText(_TeiBase):
    head = xmlmap.StringField("./tei:body/tei:head")
    line_group = xmlmap.NodeListField('.//tei:lg', TeiLineGroup)
    line = xmlmap.NodeListField('.//tei:l', TeiLine)


# note: not currently mapped to any of the existing tei objects...  where to add?
class TeiFigure(_TeiBase):
    #entity      = xmlmap.StringField("@entity") #not used in P5
    # TODO: ana should be a more generic attribute, common to many elements...
    ana         = xmlmap.StringField("@ana")    # FIXME: how to split on spaces? should be a list...
    head        = xmlmap.StringField("tei:head")
    description = xmlmap.StringField("tei:figDesc")
    entity      = xmlmap.StringField("tei:graphic/@url") #graphic replaces entity in p5.
    floatingText = xmlmap.NodeListField('tei:floatingText', TeiFloatingText)

# currently not mapped... should it be mapped by default? at what level?
class TeiInterp(_TeiBase):
    id          = xmlmap.StringField("@xml:id")
    value       = xmlmap.StringField("@value")

class TeiSection(_TeiBase):
    # top-level sections -- front/body/back
    div = xmlmap.NodeListField('tei:div', TeiDiv)
    all_figures = xmlmap.NodeListField('.//tei:figure', TeiFigure)

class TeiInterpGroup(_TeiBase):
    type        = xmlmap.StringField("@type")
    interp      = xmlmap.NodeListField("tei:interp", TeiInterp)

class TeiName(_TeiBase):
    type = xmlmap.StringField('@person')
    reg = xmlmap.StringField('tei:choice/tei:reg')
    'regularized value for a name'
    value = xmlmap.StringField('tei:choice/tei:sic')
    'name as displayed in the text'

class TeiHeader(_TeiBase):
    '''xmlmap object for a TEI (Text Encoding Initiative) header'''
    title  = xmlmap.StringField('tei:fileDesc/tei:titleStmt/tei:title')
    author_list = xmlmap.NodeListField('tei:fileDesc/tei:titleStmt/tei:author/tei:name',
        TeiName)
    editor_list = xmlmap.NodeListField('tei:fileDesc/tei:titleStmt/tei:editor/tei:name',
        TeiName)
    publisher = xmlmap.StringField('tei:fileDesc/tei:publicationStmt/tei:publisher')
    publication_date = xmlmap.StringField('tei:fileDesc/tei:publicationStmt/tei:date')
    availability = xmlmap.StringField('tei:fileDesc/tei:publicationStmt/tei:availability')
    source_description = xmlmap.StringField('tei:fileDesc/tei:sourceDesc')
    series_statement = xmlmap.StringField('tei:fileDesc/tei:seriesStmt')


class Tei(_TeiBase):
    """xmlmap object for a TEI (Text Encoding Initiative) XML document """
    id     = xmlmap.StringField('@xml:id')
    title  = xmlmap.StringField('tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title')
    author = xmlmap.StringField('tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:author/tei:name/tei:choice/tei:sic')
    editor = xmlmap.StringField('tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:editor/tei:name/tei:choice/tei:sic')

    header = xmlmap.NodeField('tei:teiHeader', TeiHeader)
    front  = xmlmap.NodeField('tei:text/tei:front', TeiSection)
    body   = xmlmap.NodeField('tei:text/tei:body', TeiSection)
    back   = xmlmap.NodeField('tei:text/tei:back', TeiSection)


# file eulxml/xmlmap/dc.py
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

try:
    import rdflib
except ImportError:
    # use rdflib if it's available, but it's ok if it's not
    rdflib = None

from eulxml import xmlmap

class _BaseDublinCore(xmlmap.XmlObject):
    'Base Dublin Core class for common namespace declarations'
    ROOT_NS = 'http://www.openarchives.org/OAI/2.0/oai_dc/'
    ROOT_NAMESPACES = { 'oai_dc' : ROOT_NS,
                        'dc': 'http://purl.org/dc/elements/1.1/'}

class DublinCoreElement(_BaseDublinCore):
    'Generic Dublin Core element with access to element name and value'
    name = xmlmap.StringField('local-name(.)')
    value = xmlmap.StringField('.')

class DublinCore(_BaseDublinCore):
    """
    XmlObject for Simple (unqualified) Dublin Core metadata.

    If no node is specified when initialized, a new, empty Dublin Core
    XmlObject will be created.
    """    

    ROOT_NAME = 'dc'

    XSD_SCHEMA = "http://www.openarchives.org/OAI/2.0/oai_dc.xsd"

    contributor = xmlmap.StringField("dc:contributor", required=False)
    contributor_list = xmlmap.StringListField("dc:contributor",
                                              verbose_name='Contributors')

    coverage = xmlmap.StringField("dc:coverage", required=False)
    coverage_list = xmlmap.StringListField("dc:coverage",
                                           verbose_name='Coverage') #?

    creator = xmlmap.StringField("dc:creator", required=False)
    creator_list = xmlmap.StringListField("dc:creator",
                                          verbose_name='Creators')

    date = xmlmap.StringField("dc:date", required=False)
    date_list = xmlmap.StringListField("dc:date",
                                       verbose_name='Dates')

    description = xmlmap.StringField("dc:description", required=False)
    description_list = xmlmap.StringListField("dc:description",
                                              verbose_name='Descriptions')

    format = xmlmap.StringField("dc:format", required=False)
    format_list = xmlmap.StringListField("dc:format",
                                         verbose_name='Formats')

    identifier = xmlmap.StringField("dc:identifier", required=False)
    identifier_list = xmlmap.StringListField("dc:identifier",
                                             verbose_name='Identifiers')

    language = xmlmap.StringField("dc:language", required=False)
    language_list = xmlmap.StringListField("dc:language",
                                           verbose_name='Languages')

    publisher = xmlmap.StringField("dc:publisher", required=False)
    publisher_list = xmlmap.StringListField("dc:publisher",
                                            verbose_name='Publishers')

    relation = xmlmap.StringField("dc:relation", required=False)
    relation_list = xmlmap.StringListField("dc:relation",
                                           verbose_name='Relations')

    rights = xmlmap.StringField("dc:rights", required=False)
    rights_list = xmlmap.StringListField("dc:rights",
                                         verbose_name='Rights')

    source = xmlmap.StringField("dc:source", required=False)
    source_list = xmlmap.StringListField("dc:source",
                                         verbose_name='Sources')

    subject = xmlmap.StringField("dc:subject", required=False)
    subject_list = xmlmap.StringListField("dc:subject",
                                          verbose_name='Subjects')

    title = xmlmap.StringField("dc:title", required=False)
    title_list = xmlmap.StringListField("dc:title",
                                        verbose_name='Titles')

    type = xmlmap.StringField("dc:type", required=False)
    type_list = xmlmap.StringListField("dc:type",
                                       verbose_name='Types')

    elements = xmlmap.NodeListField('dc:*', DublinCoreElement)
    'list of all DC elements as instances of :class:`DublinCoreElement`'

    # RDF declaration of the Recommended DCMI types
    DCMI_TYPES_RDF = 'http://dublincore.org/2010/10/11/dctype.rdf'
    DCMI_TYPE_URI = 'http://purl.org/dc/dcmitype/'
    if rdflib:
        DCMI_TYPE_URI = rdflib.URIRef(DCMI_TYPE_URI)

        _dcmi_types_graph = None
        @property
        def dcmi_types_graph(self):
            'DCMI Types Vocabulary as an :class:`rdflib.Graph`'
            # only initialize if requested; then save the result
            if self._dcmi_types_graph is None:
                self._dcmi_types_graph = rdflib.Graph()
                self._dcmi_types_graph.parse(self.DCMI_TYPES_RDF)
            return self._dcmi_types_graph

        _dcmi_types = None
        @property
        def dcmi_types(self):
            '''DCMI Type Vocabulary (recommended), as documented at
            http://dublincore.org/documents/dcmi-type-vocabulary/'''
            if self._dcmi_types is None:
                # generate a list of DCMI types based on the RDF dctype document
                self._dcmi_types = []
                # get all items with rdf:type of rdfs:Clas
                items = self.dcmi_types_graph.subjects(rdflib.RDF.type, rdflib.RDFS.Class)
                for item in items:
                    # check that this item is defined by dcmitype
                    if (item, rdflib.RDFS.isDefinedBy, self.DCMI_TYPE_URI) in self.dcmi_types_graph:
                        # add the label to the list
                        self._dcmi_types.append(str(self.dcmi_types_graph.label(subject=item)))
            return self._dcmi_types
    else:
        # no rdflib
        dcmi_types_graph = None
        dcmi_types = None

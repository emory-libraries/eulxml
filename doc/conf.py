# eulcore documentation build configuration file

import eulxml

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx']

#templates_path = ['templates']
exclude_trees = ['build']
source_suffix = '.rst'
master_doc = 'index'

project = 'eulxml'
copyright = '2011, Emory University Libraries'
version = '%d.%d' % eulxml.__version_info__[:2]
release = eulxml.__version__
#modindex_common_prefix = ['eulxml.', 'eulxml.django.']
modindex_common_prefix = ['eulxml.']

pygments_style = 'sphinx'

html_style = 'default.css'
#html_static_path = ['static']
htmlhelp_basename = 'eulxmldoc'

latex_documents = [
  ('index', 'eulxml.tex', 'EULxml Documentation',
   'Emory University Libraries', 'manual'),
]

# configuration for intersphinx: refer to the Python standard library, django, eulfedora
intersphinx_mapping = {
    'python': ('http://docs.python.org/', None),
    'django': ('http://django.readthedocs.org/en/latest/', None),
}

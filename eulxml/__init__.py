
# file eulxml/__init__.py
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

import os
import pkg_resources

__version_info__ = (1, 1, 3, None)

# Dot-connect all but the last. Last is dash-connected if not None.
__version__ = '.'.join([str(i) for i in __version_info__[:-1]])
if __version_info__[-1] is not None:
    __version__ += ('-%s' % (__version_info__[-1],))

# Paths for XML catalog file & directory

# NOTE: these paths are defined here so they can easily be included
# without requiring the import of other parts of the code (e.g.
# in setup.py, which could be run when eulxml isn't fully installed)

#: relative path for schema data directory
SCHEMA_DATA_DIR = 'schema_data'

# use package resources if possible, so this will work from an egg
# http://peak.telecommunity.com/DevCenter/PythonEggs#accessing-package-resources
if pkg_resources.resource_isdir(__name__, SCHEMA_DATA_DIR):
    XMLCATALOG_DIR = pkg_resources.resource_filename(__name__,
                                                     SCHEMA_DATA_DIR)
    XMLCATALOG_FILE = pkg_resources.\
        resource_filename(__name__,
                          '%s/catalog.xml' % SCHEMA_DATA_DIR)
else:
    XMLCATALOG_DIR = os.path.join(os.path.dirname(__file__),
                                  SCHEMA_DATA_DIR)
    XMLCATALOG_FILE = os.path.join(XMLCATALOG_DIR, 'catalog.xml')

# Add local XML catalog file to the environment variable so
# it will automatically be used by libxml to resolve URIs.
# See http://xmlsoft.org/catalog.html for more details.
# Only add once, even if eulxml is loaded multiple times.
if XMLCATALOG_FILE not in os.environ.get('XML_CATALOG_FILES', ''):
    os.environ['XML_CATALOG_FILES'] = ":".join(
        [path for path in (os.environ.get('XML_CATALOG_FILES'), XMLCATALOG_FILE)
         if path])

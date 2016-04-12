
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

__version_info__ = (1, 1, 0, 'dev')

# Dot-connect all but the last. Last is dash-connected if not None.
__version__ = '.'.join([str(i) for i in __version_info__[:-1]])
if __version_info__[-1] is not None:
    __version__ += ('-%s' % (__version_info__[-1],))

# paths to xml schema catalog file & directory
# use package resources if possible, so this will work from an egg
# http://peak.telecommunity.com/DevCenter/PythonEggs#accessing-package-resources
if pkg_resources.resource_isdir(__name__, "schema_data"):
    XMLCATALOG_DIR = pkg_resources.resource_filename(__name__,
                                                     'schema_data')
    XMLCATALOG_FILE = pkg_resources.resource_filename(__name__,
                                                      'schema_data/catalog.xml')
else:
    XMLCATALOG_DIR = os.path.join(os.path.dirname(__file__), 'schema_data')
    XMLCATALOG_FILE = os.path.join(XMLCATALOG_DIR, 'catalog.xml')


print XMLCATALOG_DIR
print XMLCATALOG_FILE

# FIXME: should add to any existing xml catalog files
os.environ['XML_CATALOG_FILES'] = XMLCATALOG_FILE

# file eulxml/xpath/__init__.py
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

"""Functions and classes for parsing XPath expressions into abstract syntax
trees and serializing them back to strings.

This module exports two key functions, :func:`parse` and :func:`serialize`.

.. function:: parse(xpath_str)

   Parse a string XPath expression into an abstract syntax tree. The AST
   will be built from the classes defined in :mod:`eulxml.xpath.ast`.

.. function:: serialize(xpath_ast)

   Serialize an XPath AST expressed in terms of :mod:`eulxml.xpath.ast`
   objects into a valid XPath string.

This module does not support evaluating XPath expressions.
"""

from eulxml.xpath.core import parse, serialize

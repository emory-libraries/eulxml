# file eulxml/xpath/lexrules.py
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

"""XPath lexing rules.

To understand how this module works, it is valuable to have a strong
understanding of the `ply <http://www.dabeaz.com/ply/>` module.
"""

from ply.lex import TOKEN

operator_names = {
    'or': 'OR_OP',
    'and': 'AND_OP',
    'div': 'DIV_OP',
    'mod': 'MOD_OP',
}

tokens = [
        'PATH_SEP',
        'ABBREV_PATH_SEP',
        'ABBREV_STEP_SELF',
        'ABBREV_STEP_PARENT',
        'AXIS_SEP',
        'ABBREV_AXIS_AT',
        'OPEN_PAREN',
        'CLOSE_PAREN',
        'OPEN_BRACKET',
        'CLOSE_BRACKET',
        'UNION_OP',
        'EQUAL_OP',
        'REL_OP',
        'PLUS_OP',
        'MINUS_OP',
        'MULT_OP',
        'STAR_OP',
        'COMMA',
        'LITERAL',
        'FLOAT',
        'INTEGER',
        'NCNAME',
        'NODETYPE',
        'FUNCNAME',
        'AXISNAME',
        'COLON',
        'DOLLAR',
    ] + list(operator_names.values())

t_PATH_SEP = r'/'
t_ABBREV_PATH_SEP = r'//'
t_ABBREV_STEP_SELF = r'\.'
t_ABBREV_STEP_PARENT = r'\.\.'
t_AXIS_SEP = r'::'
t_ABBREV_AXIS_AT = r'@'
t_OPEN_PAREN = r'\('
t_CLOSE_PAREN = r'\)'
t_OPEN_BRACKET = r'\['
t_CLOSE_BRACKET = r'\]'
t_UNION_OP = r'\|'
t_EQUAL_OP = r'!?='
t_REL_OP = r'[<>]=?'
t_PLUS_OP = r'\+'
t_MINUS_OP = r'-'
t_COMMA = r','
t_COLON = r':'
t_DOLLAR = r'\$'
t_STAR_OP = r'\*'

t_ignore = ' \t\r\n'

# NOTE: some versions of python cannot compile regular expressions that
# contain unicode characters above U+FFFF, which are allowable in NCNames.
# These characters can be used in Python 2.6.4, but can NOT be used in 2.6.2
# (status in 2.6.3 is unknown).  The code below accounts for that and excludes
# the higher character range if Python can't handle it.

# Monster regex derived from:
#  http://www.w3.org/TR/REC-xml/#NT-NameStartChar
#  http://www.w3.org/TR/REC-xml/#NT-NameChar
# EXCEPT:
# Technically those productions allow ':'. NCName, on the other hand:
#  http://www.w3.org/TR/REC-xml-names/#NT-NCName
# explicitly excludes those names that have ':'. We implement this by
# simply removing ':' from our regexes.

# NameStartChar regex without characters about U+FFFF
NameStartChar = ur'[A-Z]|_|[a-z]|\xc0-\xd6]|[\xd8-\xf6]|[\xf8-\u02ff]|' + \
    ur'[\u0370-\u037d]|[\u037f-\u1fff]|[\u200c-\u200d]|[\u2070-\u218f]|' + \
    ur'[\u2c00-\u2fef]|[\u3001-\uD7FF]|[\uF900-\uFDCF]|[\uFDF0-\uFFFD]'
# complete NameStartChar regex
Full_NameStartChar = ur'(' + NameStartChar + ur'|[\U00010000-\U000EFFFF]' + r')'
# additional characters allowed in NCNames after the first character
NameChar_extras = ur'[-.0-9\xb7\u0300-\u036f\u203f-\u2040]'

try:
    import re
    # test whether or not re can compile unicode characters above U+FFFF
    re.compile(ur'[\U00010000-\U00010001]')
    # if that worked, then use the full ncname regex
    NameStartChar = Full_NameStartChar
except:
    # if compilation failed, leave NameStartChar regex as is, which does not
    # include the unicode character ranges above U+FFFF
    pass

NCNAME_REGEX = r'(' + NameStartChar + r')(' + \
                      NameStartChar + r'|' + NameChar_extras + r')*'
                      
NODE_TYPES = set(['comment', 'text', 'processing-instruction', 'node'])

t_NCNAME = NCNAME_REGEX

def t_LITERAL(t):
    r""""[^"]*"|'[^']*'"""
    t.value = t.value[1:-1]
    return t

def t_FLOAT(t):
    r'\d+\.\d*|\.\d+'
    t.value = float(t.value)
    return t
    
def t_INTEGER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_error(t):
    raise TypeError("Unknown text '%s'" % (t.value,))

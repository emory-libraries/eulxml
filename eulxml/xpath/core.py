# file eulxml/xpath/core.py
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

"""Core XPath parsing glue.

This module builds a lexer and parser for XPath expressions for import into
eulxml.xpath. To understand how this module builds the lexer and parser, it
is helpful to understand how the `ply <http://www.dabeaz.com/ply/>`_ module
works.

Note that most client applications will import htese objects from
eulxml.xpath, not directly from here."""

import os
import re
from ply import lex, yacc

from eulxml.xpath import lexrules
from eulxml.xpath import parserules
from eulxml.xpath.ast import serialize

__all__ = [ 'lexer', 'parser', 'parse', 'serialize' ]

# build the lexer. This will generate a lextab.py in the eulxml.xpath
# directory. Unfortunately, xpath requires some wonky lexing.
# Per http://www.w3.org/TR/xpath/#exprlex : 
#  1 If there is a preceding token and the preceding token is not one of @,
#    ::, (, [, , or an Operator, then a * must be recognized as a
#    MultiplyOperator and an NCName must be recognized as an OperatorName.
#  2 If the character following an NCName (possibly after intervening
#    ExprWhitespace) is (, then the token must be recognized as a NodeType
#    or a FunctionName.
#  3 If the two characters following an NCName (possibly after intervening
#    ExprWhitespace) are ::, then the token must be recognized as an
#    AxisName.
#  4 Otherwise, the token must not be recognized as a MultiplyOperator, an
#    OperatorName, a NodeType, a FunctionName, or an AxisName.
#
# To implement this, we create a wrapper class that extends token() for the
# described lookahead/lookback lexing, and we dynamically set the lexer's
# __class__ to this wrapper. That's pretty weird and ugly, but Python allows
# it. If you can find a prettier solution to the problem then I welcome a
# fix.

OPERATOR_FORCERS = set([
    # @, ::, (, [
    'ABBREV_AXIS_AT', 'AXIS_SEP', 'OPEN_PAREN', 'OPEN_BRACKET',
    # Operators: OperatorName
    'AND_OP', 'OR_OP', 'MOD_OP', 'DIV_OP', 'MULT_OP',
    # Operators: MultiplyOperator
    'PATH_SEP',
    # Operators: /, //, |, +, -
    'ABBREV_PATH_SEP', 'UNION_OP', 'PLUS_OP', 'MINUS_OP',
    # Operators: =. !=, <, <=, >, >=
    'EQUAL_OP', 'REL_OP',

    # Also need to add : . Official XPath lexing rules are in terms of
    # QNames, but we produce QNames in the parse layer. We need to include :
    # here to force foo:div to be a single step, otherwise that last div
    # would be interpreted as an operator (where standard xpath would just
    # call it part of the qname)
    'COLON',
])
NODE_TYPES = set(['comment', 'text', 'processing-instruction', 'node'])
class LexerWrapper(lex.Lexer):
    def token(self):
        tok = lex.Lexer.token(self)
        if tok is not None:
            if tok.type == 'STAR_OP':
                if self.last is not None and self.last.type not in OPERATOR_FORCERS:
                    # first half of point 1
                    tok.type = 'MULT_OP'

            if tok.type == 'NCNAME':
                if self.last is not None and self.last.type not in OPERATOR_FORCERS:
                    # second half of point 1
                    operator = lexrules.operator_names.get(tok.value, None)
                    if operator is not None:
                        tok.type = operator
                else:
                    next = self.peek()
                    if next is not None:
                        if next.type == 'OPEN_PAREN':
                            # point 2
                            if tok.value in NODE_TYPES:
                                tok.type = 'NODETYPE'
                            else:
                                tok.type = 'FUNCNAME'
                        elif next.type == 'AXIS_SEP':
                            # point 3
                            tok.type = 'AXISNAME'

        self.last = tok
        return tok

    def peek(self):
        clone = self.clone()
        return clone.token()

# try to build the lexer with cached lex table generation. this will fail if
# the user doesn't have write perms on the source directory. in that case,
# try again without lex table generation.
lexdir = os.path.dirname(lexrules.__file__)
lexer = None
try:
    lexer = lex.lex(module=lexrules, optimize=1, outputdir=lexdir, 
        reflags=re.UNICODE)
except IOError, e:
    import errno
    if e.errno != errno.EACCES:
        raise
if lexer is None:
    lexer = lex.lex(module=lexrules, reflags=re.UNICODE)
# then dynamically rewrite the lexer class to use the wonky override logic
# above
lexer.__class__ = LexerWrapper
lexer.last = None

# build the parser. This will generate a parsetab.py in the eulxml.xpath
# directory. Unlike lex, though, this just logs a complaint when it fails
# (contrast lex's explosion). Other than that, it's much less exciting
# than the lexer wackiness.
parsedir = os.path.dirname(parserules.__file__)
parser = yacc.yacc(module=parserules, outputdir=parsedir, debug=0)

def parse(xpath):
    '''Parse an xpath.'''
    # Expose the parse method of the constructed parser,
    # but explicitly specify the lexer created here,
    # since otherwise parse will use the most-recently created lexer. 
    return parser.parse(xpath, lexer=lexer)

def ptokens(s):
    '''Lex a string as XPath tokens, and print each token as it is lexed.
    This is used primarily for debugging. You probably don't want this
    function.'''

    lexer.input(s)
    for tok in lexer:
            print tok

# file eulxml/xpath/parserules.py
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

"""XPath parsing rules.

To understand how this module works, it is valuable to have a strong
understanding of the `ply <http://www.dabeaz.com/ply/>` module.
"""

from eulxml.xpath import ast
from eulxml.xpath.lexrules import tokens

precedence = (
    ('left', 'OR_OP'),
    ('left', 'AND_OP'),
    ('left', 'EQUAL_OP'),
    ('left', 'REL_OP'),
    ('left', 'PLUS_OP', 'MINUS_OP'),
    ('left', 'MULT_OP', 'DIV_OP', 'MOD_OP'),
    ('right', 'UMINUS_OP'),
    ('left', 'UNION_OP'),
)

#
# basic expressions
#

def p_expr_boolean(p):
    """
    Expr : Expr OR_OP Expr
         | Expr AND_OP Expr
         | Expr EQUAL_OP Expr
         | Expr REL_OP Expr
         | Expr PLUS_OP Expr
         | Expr MINUS_OP Expr
         | Expr MULT_OP Expr
         | Expr DIV_OP Expr
         | Expr MOD_OP Expr
         | Expr UNION_OP Expr
    """
    p[0] = ast.BinaryExpression(p[1], p[2], p[3])

def p_expr_unary(p):
    """
    Expr : MINUS_OP Expr %prec UMINUS_OP
    """
    p[0] = ast.UnaryExpression(p[1], p[2])

#
# path expressions
#

def p_path_expr_binary(p):
    """
    Expr : FilterExpr PATH_SEP RelativeLocationPath
         | FilterExpr ABBREV_PATH_SEP RelativeLocationPath
    """
    p[0] = ast.BinaryExpression(p[1], p[2], p[3])

def p_path_expr_unary(p):
    """
    Expr : RelativeLocationPath
         | AbsoluteLocationPath
         | AbbreviatedAbsoluteLocationPath
         | FilterExpr
    """
    p[0] = p[1]

#
# paths
#

def p_absolute_location_path_rootonly(p):
    """
    AbsoluteLocationPath : PATH_SEP
    """
    p[0] = ast.AbsolutePath(p[1])

def p_absolute_location_path_subpath(p):
    """
    AbsoluteLocationPath : PATH_SEP RelativeLocationPath
    """
    p[0] = ast.AbsolutePath(p[1], p[2])

def p_abbreviated_absolute_location_path(p):
    """
    AbbreviatedAbsoluteLocationPath : ABBREV_PATH_SEP RelativeLocationPath
    """
    p[0] = ast.AbsolutePath(p[1], p[2])

def p_relative_location_path_simple(p):
    """
    RelativeLocationPath : Step
    """
    p[0] = p[1]

def p_relative_location_path_binary(p):
    """
    RelativeLocationPath : RelativeLocationPath PATH_SEP Step
                         | RelativeLocationPath ABBREV_PATH_SEP Step
    """
    p[0] = ast.BinaryExpression(p[1], p[2], p[3])

#
# path steps
#

def p_step_nodetest(p):
    """
    Step : NodeTest
    """
    p[0] = ast.Step(None, p[1], [])

def p_step_nodetest_predicates(p):
    """
    Step : NodeTest PredicateList
    """
    p[0] = ast.Step(None, p[1], p[2])

def p_step_axis_nodetest(p):
    """
    Step : AxisSpecifier NodeTest
    """
    p[0] = ast.Step(p[1], p[2], [])

def p_step_axis_nodetest_predicates(p):
    """
    Step : AxisSpecifier NodeTest PredicateList
    """
    p[0] = ast.Step(p[1], p[2], p[3])

def p_step_abbrev(p):
    """
    Step : ABBREV_STEP_SELF
         | ABBREV_STEP_PARENT
    """
    p[0] = ast.AbbreviatedStep(p[1])

#
# axis specifier
#

def p_axis_specifier_full(p):
    """
    AxisSpecifier : AXISNAME AXIS_SEP
    """
    p[0] = p[1]

def p_axis_specifier_abbrev(p):
    """
    AxisSpecifier : ABBREV_AXIS_AT
    """
    p[0] = '@'

#
# node test
#

def p_node_test_name_test(p):
    """
    NodeTest : NameTest
    """
    p[0] = p[1]

def p_node_test_type_simple(p):
    """
    NodeTest : NODETYPE OPEN_PAREN CLOSE_PAREN
    """
    # NOTE: Strictly speaking p[1] must come from a list of recognized
    # NodeTypes. Since we don't actually do anything with them, we don't
    # need to recognize them. 
    p[0] = ast.NodeType(p[1])

def p_node_test_type_literal(p):
    """
    NodeTest : NODETYPE OPEN_PAREN LITERAL CLOSE_PAREN
    """
    # NOTE: Technically this only allows 'processing-instruction' for p[1].
    # We'll go light on that restriction since we don't actually need it for
    # processing.
    p[0] = ast.NodeType(p[1], p[3])

#
# name test
#

def p_name_test_star(p):
    """
    NameTest : STAR_OP
    """
    p[0] = ast.NameTest(None, p[1])

def p_name_test_prefix_star(p):
    """
    NameTest : NCNAME COLON STAR_OP
    """
    p[0] = ast.NameTest(p[1], p[3])

def p_name_test_qname(p):
    """
    NameTest : QName
    """
    qname = p[1]
    p[0] = ast.NameTest(qname[0], qname[1])


#
# qname
#

def p_qname_prefixed(p):
    """
    QName : NCNAME COLON NCNAME
    """
    p[0] = (p[1], p[3])

def p_qname_unprefixed(p):
    """
    QName : NCNAME
    """
    p[0] = (None, p[1])

def p_funcqname_prefixed(p):
    """
    FuncQName : NCNAME COLON FUNCNAME
    """
    p[0] = (p[1], p[3])

def p_funcqname_unprefixed(p):
    """
    FuncQName : FUNCNAME
    """
    p[0] = (None, p[1])

#
# filter expressions
#
    
def p_filter_expr_simple(p):
    """
    FilterExpr : VariableReference
               | LITERAL
               | Number
               | FunctionCall
    """
    # FIXME: | FunctionCall moved so as not to conflict with NodeTest :
    # FunctionCall
    p[0] = p[1]

def p_filter_expr_grouped(p):
    """
    FilterExpr : OPEN_PAREN Expr CLOSE_PAREN
    """
    p[0] = p[2]

def p_filter_expr_predicate(p):
    """
    FilterExpr : FilterExpr Predicate
    """
    if not hasattr(p[1], 'append_predicate'):
        p[1] = ast.PredicatedExpression(p[1])
    p[1].append_predicate(p[2])
    p[0] = p[1]

#
# predicates
#

def p_predicate_list_single(p):
    """
    PredicateList : Predicate
    """
    p[0] = [p[1]]

def p_predicate_list_recursive(p):
    """
    PredicateList : PredicateList Predicate
    """
    p[0] = p[1]
    p[0].append(p[2])

def p_predicate(p):
    """
    Predicate : OPEN_BRACKET Expr CLOSE_BRACKET
    """
    p[0] = p[2]

#
# variable
#

def p_variable_reference(p):
    """
    VariableReference : DOLLAR QName
    """
    p[0] = ast.VariableReference(p[2])

#
# number
#

def p_number(p):
    """
    Number : FLOAT
           | INTEGER
    """
    p[0] = p[1]

#
# funcall
#

def p_function_call(p):
    """
    FunctionCall : FuncQName FormalArguments
    """
    # FIXME: This production also matches NodeType() or
    # processing-instruction("foo"), which are technically NodeTest
    qname = p[1]
    p[0] = ast.FunctionCall(qname[0], qname[1], p[2])

def p_formal_arguments_empty(p):
    """
    FormalArguments : OPEN_PAREN CLOSE_PAREN
    """
    p[0] = []

def p_formal_arguments_list(p):
    """
    FormalArguments : OPEN_PAREN ArgumentList CLOSE_PAREN
    """
    p[0] = p[2]

def p_argument_list_single(p):
    """
    ArgumentList : Expr
    """
    p[0] = [p[1]]

def p_argument_list_recursive(p):
    """
    ArgumentList : ArgumentList COMMA Expr
    """
    p[0] = p[1]
    p[0].append(p[3])

#
# error handling
#

def p_error(p):
    # In some cases, p could actually be None.
    # However, stack trace should have enough information to identify the problem.
    raise RuntimeError("Syntax error at '%s'" % repr(p))

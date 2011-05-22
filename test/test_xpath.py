#!/usr/bin/env python

# file test_xpath.py
# 
#   Copyright 2011 Emory University Libraries
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


import unittest

from eulxml import xpath
from eulxml.xpath import ast, serialize

from testcore import main

class ParseTest(unittest.TestCase):
    def test_nametest_step(self):
        xp = xpath.parse('''author''')
        self.assert_(isinstance(xp, ast.Step))
        self.assert_(xp.axis is None) # or should this be 'child', the default?
        self.assert_(isinstance(xp.node_test, ast.NameTest))
        self.assert_(xp.node_test.prefix is None)
        self.assertEqual('author', xp.node_test.name)
        self.assertEqual(0, len(xp.predicates))

    def test_nodetype_step(self):
        xp = xpath.parse('''text()''')
        self.assert_(isinstance(xp, ast.Step))
        self.assert_(isinstance(xp.node_test, ast.NodeType))
        self.assertEqual('text', xp.node_test.name)

    def test_axis(self):
        xp = xpath.parse('''ancestor::lib:book''')
        self.assert_(isinstance(xp, ast.Step))
        self.assertEqual('ancestor', xp.axis)
        self.assertEqual('lib', xp.node_test.prefix)
        self.assertEqual('book', xp.node_test.name)

    def test_relative_path(self):
        xp = xpath.parse('''book//author/first-name''')
        self.assert_(isinstance(xp, ast.BinaryExpression))
        self.assert_(isinstance(xp.left, ast.BinaryExpression))
        self.assertEqual('book', xp.left.left.node_test.name)
        self.assertEqual('//', xp.left.op)
        self.assertEqual('author', xp.left.right.node_test.name)
        self.assertEqual('/', xp.op)
        self.assertEqual('first-name', xp.right.node_test.name)

    def test_absolute_path(self):
        xp = xpath.parse('''/book//author''')
        self.assert_(isinstance(xp, ast.AbsolutePath))
        self.assertEqual('/', xp.op)
        self.assertEqual('book', xp.relative.left.node_test.name)

    def test_step_predicate(self):
        xp = xpath.parse('''book[author]''')
        self.assertEqual('book', xp.node_test.name)
        self.assertEqual(1, len(xp.predicates))
        self.assertEqual('author', xp.predicates[0].node_test.name)

    def test_function(self):
        xp = xpath.parse('''author[position() = 1]''')
        self.assert_(isinstance(xp.predicates[0], ast.BinaryExpression))
        self.assertEqual('=', xp.predicates[0].op)
        self.assert_(isinstance(xp.predicates[0].left, ast.FunctionCall))
        self.assertEqual('position', xp.predicates[0].left.name)
        self.assertEqual(0, len(xp.predicates[0].left.args))
        self.assertEqual(1, xp.predicates[0].right)

    def test_variable(self):
        xp = xpath.parse('''title[substring-after(text(), $pre:separator) = "world"]''')
        self.assertEqual('title', xp.node_test.name)
        self.assert_(isinstance(xp.predicates[0], ast.BinaryExpression))
        self.assertEqual('=', xp.predicates[0].op)
        self.assertEqual('world', xp.predicates[0].right) # no quotes, just a string
        self.assert_(isinstance(xp.predicates[0].left, ast.FunctionCall))
        self.assertEqual('substring-after', xp.predicates[0].left.name)
        self.assertEqual(2, len(xp.predicates[0].left.args))
        self.assert_(isinstance(xp.predicates[0].left.args[0], ast.Step))
        self.assertEqual('text', xp.predicates[0].left.args[0].node_test.name)
        self.assert_(isinstance(xp.predicates[0].left.args[1], ast.VariableReference))
        self.assertEqual(('pre', 'separator'), xp.predicates[0].left.args[1].name)

    def test_predicated_expression(self):
        xp = xpath.parse('''(book or article)[author/last-name = "Jones"]''')
        self.assert_(isinstance(xp, ast.PredicatedExpression))
        self.assert_(isinstance(xp.base, ast.BinaryExpression))
        self.assertEqual('book', xp.base.left.node_test.name)
        self.assertEqual('or', xp.base.op)
        self.assertEqual('article', xp.base.right.node_test.name)

        self.assertEqual(1, len(xp.predicates))
        self.assertEqual('=', xp.predicates[0].op)
        self.assertEqual('Jones', xp.predicates[0].right)
        self.assertEqual('/', xp.predicates[0].left.op)
        self.assertEqual('author', xp.predicates[0].left.left.node_test.name)
        self.assertEqual('last-name', xp.predicates[0].left.right.node_test.name)

    def test_lex_exceptions(self):
        # http://www.w3.org/TR/xpath/#exprlex describes several unusual
        # lexing rules. Verify them here.
        xp = xpath.parse('''***''')
        self.assert_(isinstance(xp, ast.BinaryExpression))
        self.assertEqual('*', xp.op)
        self.assert_(isinstance(xp.left, ast.Step))
        self.assert_(isinstance(xp.left.node_test, ast.NameTest))
        self.assertEqual('*', xp.left.node_test.name)
        self.assert_(isinstance(xp.right, ast.Step))
        self.assert_(isinstance(xp.right.node_test, ast.NameTest))
        self.assertEqual('*', xp.right.node_test.name)

        xp = xpath.parse('''div div div''')
        self.assert_(isinstance(xp, ast.BinaryExpression))
        self.assertEqual('div', xp.op)
        self.assert_(isinstance(xp.left, ast.Step))
        self.assert_(isinstance(xp.left.node_test, ast.NameTest))
        self.assertEqual('div', xp.left.node_test.name)
        self.assert_(isinstance(xp.right, ast.Step))
        self.assert_(isinstance(xp.right.node_test, ast.NameTest))
        self.assertEqual('div', xp.right.node_test.name)

        xp = xpath.parse('''div:div''')
        self.assert_(isinstance(xp, ast.Step))
        self.assertEqual('div', xp.node_test.prefix)
        self.assertEqual('div', xp.node_test.name)

        xp = xpath.parse('''node/node()''')
        self.assert_(isinstance(xp, ast.BinaryExpression))
        self.assertEqual('/', xp.op)
        self.assert_(isinstance(xp.left, ast.Step))
        self.assert_(isinstance(xp.left.node_test, ast.NameTest))
        self.assertEqual('node', xp.left.node_test.name)
        self.assert_(isinstance(xp.right, ast.Step))
        self.assert_(isinstance(xp.right.node_test, ast.NodeType))
        self.assertEqual('node', xp.right.node_test.name)

        xp = xpath.parse('''boolean(boolean)''')
        self.assert_(isinstance(xp, ast.FunctionCall))
        self.assertEqual('boolean', xp.name)
        self.assertEqual(1, len(xp.args))
        self.assert_(isinstance(xp.args[0], ast.Step))
        self.assertEqual('boolean', xp.args[0].node_test.name)

        xp = xpath.parse('''parent::parent/parent:parent''')
        self.assertEqual('parent', xp.left.axis)
        self.assertEqual('parent', xp.left.node_test.name)
        self.assertEqual('parent', xp.right.node_test.prefix)
        self.assertEqual('parent', xp.right.node_test.name)

    def test_syntax_error(self):
        # try to parse invalid xpath and make sure we get an exception
        self.assertRaises(RuntimeError, xpath.parse, '''bogus-(''')
        self.assertRaises(RuntimeError, xpath.parse, '''/bogus-(''')


class TestSerializeRoundTrip(unittest.TestCase):
    def round_trip(self, xpath_str):
        xp = xpath.parse(xpath_str)
        self.assertEqual(xpath_str, serialize(xp))

    def test_nametest(self):
        self.round_trip('''ancestor::lib:book''')

    def test_attr_nametest(self):
        self.round_trip('''@xml:lang''')

    def test_nodetype(self):
        self.round_trip('''node()''')

    def test_predicates(self):
        self.round_trip('''a[b][1]''')

    def test_relative_path(self):
        self.round_trip('''a/b//c/*/..//@d''')

    def test_absolute_path(self):
        self.round_trip('''//a/b/c''')

    def test_unary(self):
        self.round_trip('''.//a/@val[0]*-5''')

    def test_predicated_expr(self):
        self.round_trip('''(a or b)[2]''')

    def test_variable(self):
        self.round_trip('''a[@b<$threshold]''')

    def test_function(self):
        self.round_trip('''*[position() mod 2=1]''')

    def test_function_multi_args(self):
        self.round_trip('''substring-after(.,':')''')

if __name__ == '__main__':
    main()

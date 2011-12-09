#!/usr/bin/env python

# file test_xmlmap/test_premis.py
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
from os import path

from eulxml.xmlmap  import load_xmlobject_from_file
from eulxml.xmlmap import premis
from testcore import main

class TestPremis(unittest.TestCase):
    # LOC PREMIS v2.1 example document taken from:
    # http://www.loc.gov/standards/premis/louis-2-1.xml
    FIXTURE_FILE = path.join(path.dirname(path.abspath(__file__)),
                             'fixtures', 'loc-premis-2.1.xml')

    def setUp(self):
        self.premis = load_xmlobject_from_file(self.FIXTURE_FILE, premis.Premis)

    def test_init(self):
        self.assert_(isinstance(self.premis, premis.Premis))
        self.assert_(isinstance(self.premis.object, premis.Object))
        self.assert_(self.premis.events) # list should be non-empty
        self.assert_(isinstance(self.premis.events[0], premis.Event))

        self.assertTrue(self.premis.is_valid())

    def test_object(self):
        self.assertEqual('file', self.premis.object.type)
        self.assertEqual('hdl', self.premis.object.id_type)
        self.assertEqual('loc.music/gottlieb.09601', self.premis.object.id)

    def test_event(self):
        ev = self.premis.events[0]
        self.assertEqual('validation', ev.type)
        self.assertEqual('LocalRepository', ev.id_type)
        self.assertEqual('e001.1', ev.id)
        self.assertEqual('2006-06-06T00:00:00.001', ev.date)
        self.assertEqual('jhove1_1e', ev.detail)
        self.assertEqual('successful', ev.outcome)
        self.assertEqual('AgentID', ev.agent_type)
        self.assertEqual('na12345', ev.agent_id)
        self.assertEqual('hdl', ev.object_type)
        self.assertEqual('loc.music/gottlieb.09601', ev.object_id)


    def test_create_valid_premis(self):
        # test creating a premis xml object from scratch - should be valid
        pr = premis.Premis()
        pr.create_object()
        pr.object.type = 'p:representation'  # needs to be in premis namespace
        pr.object.id_type = 'ark'
        pr.object.id = 'ark:/1234/56789'
        # object can be schema-validated by itself
        self.assertTrue(pr.object.schema_valid())
        ev = premis.Event()
        ev.id_type = 'local'
        ev.id = '0101'
        ev.type = 'automated test'
        ev.date = '2011-11-23'
        ev.detail = 'python unittest'
        ev.outcome = 'successful'
        ev.agent_type = 'code'
        ev.agent_id = 'eulxml'
        # event can be schema-validated by itself
        self.assertTrue(ev.schema_valid())
        pr.events.append(ev)

        # if changes cause validation errors, uncomment the next 2 lines to debug
        #pr.is_valid()
        #print pr.validation_errors()
        self.assertTrue(pr.is_valid())

        
if __name__ == '__main__':
    main()

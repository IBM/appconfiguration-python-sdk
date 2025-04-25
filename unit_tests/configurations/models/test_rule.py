# Copyright 2021 IBM All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import

import unittest
from ibm_appconfiguration.configurations.models import Rule


class MyTestCase(unittest.TestCase):
    sut = None

    def set_up_email(self, value, attribute, operator):
        values = [value]
        rules = {
            'values': values,
            'operator': operator,
            'attribute_name': attribute
        }
        self.sut = Rule(rules)

    def test_test_rules(self):
        self.set_up_email('in.ibm.com', 'email', "endsWith")
        self.assertEqual(self.sut.get_attributes(), 'email')
        self.assertEqual(self.sut.get_operator(), 'endsWith')
        self.assertEqual(len(self.sut.get_values()), 1)
        self.assertNotEqual(self.sut.get_values()[0], 'in.test.com')
        self.assertEqual(self.sut.get_values()[0], 'in.ibm.com')

    def testNoEntity(self):
        self.set_up_email('in.ibm.com', 'email', "endsWith")
        client_attributes = {
            'email1': 'tester@in.ibm.com'
        }
        self.assertFalse(self.sut.evaluate_rule(client_attributes))

    def test_evaluation_ends_with_string(self):
        self.set_up_email('in.ibm.com', 'email', 'endsWith')
        client_attributes = {
            'email': 'tester@in.ibm.com'
        }
        self.assertTrue(self.sut.evaluate_rule(client_attributes))
        client_attributes = {
            'email': 'tester@in.ibm.error'
        }
        self.assertFalse(self.sut.evaluate_rule(client_attributes))

    def test_evaluation_not_ends_with_string(self):
        self.set_up_email('google.com', 'email', 'notEndsWith')
        client_attributes = {
            'email': 'tester@in.ibm.com'
        }
        self.assertTrue(self.sut.evaluate_rule(client_attributes))
        client_attributes = {
            'email': 'tester@google.com'
        }
        self.assertFalse(self.sut.evaluate_rule(client_attributes))

    def test_evaluation_is(self):
        self.set_up_email("123", "creditValues", "is")
        client_attributes = {
            'creditValues': '123'
        }
        self.assertTrue(self.sut.evaluate_rule(client_attributes))

        self.set_up_email("123", "creditValues", "is")
        client_attributes = {
            'creditValues': 123
        }
        self.assertTrue(self.sut.evaluate_rule(client_attributes))

        client_attributes = {
            'creditValues': 123
        }
        self.set_up_email(123, "creditValues", "is")
        self.assertTrue(self.sut.evaluate_rule(client_attributes))

        client_attributes = {
            'creditValues': False
        }
        self.set_up_email(False, "creditValues", "is")
        self.assertTrue(self.sut.evaluate_rule(client_attributes))

        client_attributes = {
            'creditValues': False
        }
        self.set_up_email("123", "creditValues", "is")
        self.assertFalse(self.sut.evaluate_rule(client_attributes))

        self.set_up_email(123, "creditValues", "is")
        self.assertFalse(self.sut.evaluate_rule(client_attributes))

        client_attributes = {
            'creditValues': False
        }
        self.set_up_email(True, "creditValues", "is")
        self.assertFalse(self.sut.evaluate_rule(client_attributes))

        self.set_up_email(False, "creditValues", "is")
        self.assertTrue(self.sut.evaluate_rule(client_attributes))

    def test_evaluation_is_not(self):
        self.set_up_email("123", "creditValues", "isNot")
        client_attributes = {
            'creditValues': '1234'
        }
        self.assertTrue(self.sut.evaluate_rule(client_attributes))

        self.set_up_email("1234", "creditValues", "isNot")
        client_attributes = {
            'creditValues': 123
        }
        self.assertTrue(self.sut.evaluate_rule(client_attributes))

        client_attributes = {
            'creditValues': 123
        }
        self.set_up_email(5123, "creditValues", "isNot")
        self.assertTrue(self.sut.evaluate_rule(client_attributes))

        client_attributes = {
            'creditValues': False
        }
        self.set_up_email(True, "creditValues", "isNot")
        self.assertTrue(self.sut.evaluate_rule(client_attributes))

    def test_evaluation_startswith(self):
        self.set_up_email('user1', 'email', 'startsWith')
        client_attributes = {
            'email': 'user1@gm.com'
        }
        self.assertTrue(self.sut.evaluate_rule(client_attributes))

    def test_evaluation_not_startswith(self):
        self.set_up_email('user2', 'email', 'notStartsWith')
        client_attributes = {
            'email': 'user1@gm.com'
        }
        self.assertTrue(self.sut.evaluate_rule(client_attributes))

    def test_evaluation_contains(self):
        self.set_up_email('+91', 'mobile', 'contains')
        client_attributes = {
            'mobile': '+91xxxxxxxxxx'
        }
        self.assertTrue(self.sut.evaluate_rule(client_attributes))

        client_attributes = {
            'mobile': '+01xxxxxxxxxx'
        }
        self.assertFalse(self.sut.evaluate_rule(client_attributes))

    def test_evaluation_not_contains(self):
        self.set_up_email('+91', 'mobile', 'notContains')
        client_attributes = {
            'mobile': '+81xxxxxxxxxx'
        }
        self.assertTrue(self.sut.evaluate_rule(client_attributes))

        client_attributes = {
            'mobile': '+91xxxxxxxxxx'
        }
        self.assertFalse(self.sut.evaluate_rule(client_attributes))

    def evaluation_common(self, type, val1, val2):
        self.set_up_email(val1, 'balance', type)
        client_attributes = {
            'balance': val2
        }
        self.assertTrue(self.sut.evaluate_rule(client_attributes))

        self.set_up_email(val2, 'balance', type)

        client_attributes = {
            'balance': val1
        }
        self.assertFalse(self.sut.evaluate_rule(client_attributes))

        client_attributes = {
            'balance': '{0}'.format(val1)
        }
        self.assertFalse(self.sut.evaluate_rule(client_attributes))

        client_attributes = {
            'balance': True
        }
        self.assertFalse(self.sut.evaluate_rule(client_attributes))

    def test_evaluation_greater_than(self):
        self.evaluation_common('greaterThan', 100, 200)

    def test_evaluation_lesser_than(self):
        self.evaluation_common('lesserThan', 200, 100)

    def test_evaluation_greater_than_equals(self):
        self.evaluation_common('greaterThanEquals', 100, 200)

    def test_evaluation_lesser_than_equals(self):
        self.evaluation_common('lesserThanEquals', 200, 100)

if __name__ == '__main__':
    unittest.main()

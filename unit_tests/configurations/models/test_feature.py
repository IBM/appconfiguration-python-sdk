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

import unittest

from ibm_appconfiguration.configurations.internal.utils.metering import Metering
from ibm_appconfiguration.configurations.models import Feature, ConfigurationType


class MyTestCase(unittest.TestCase):
    sut = None

    def test_empty_object(self):
        sut = Feature(dict())
        self.assertFalse(sut.is_enabled())
        self.assertEqual(sut.get_feature_name(), "")
        self.assertEqual(sut.get_feature_id(), "")
        self.assertEqual(len(sut.get_segment_rules()), 0)
        self.assertEqual(sut.get_feature_data_type(), ConfigurationType.NUMERIC)
        self.assertIsNotNone(sut.get_disabled_value())
        self.assertIsNotNone(sut.get_enabled_value())

    def test_feature(self):
        feature = {
            "name": "testF5",
            "feature_id": "testf5",
            "description": "Feature flags to enable testing",
            "type": "BOOLEAN",
            "enabled": True,
            "enabled_value": True,
            "disabled_value": False,
            "tags": "version: 1.1, pre-release",
            "segment_rules": [{
                "rules": [
                    {
                        "segments": [
                            "300"
                        ]
                    }
                ],
                "value": "$default",
                "order": 1
            }
            ]
        }

        sut = Feature(feature)
        self.assertTrue(sut.is_enabled())
        self.assertEqual(sut.get_feature_name(), "testF5")
        self.assertEqual(sut.get_feature_id(), "testf5")
        Metering.get_instance().set_repeat_calls(False)

        value = sut.get_current_value("id1", {"email": "test.dev@tester.com"})
        self.assertEqual(value, True)

    # enabled and disabled value contains valid yaml
    def test_feature_yaml1(self):
        feature = {
            "name": "testF5",
            "feature_id": "testf5",
            "description": "Feature flags to enable testing",
            "type": "STRING",
            "format": "YAML",
            "enabled": True,
            "enabled_value": "key1: enabled_value",
            "disabled_value": "key2: disabled_value\n---\nkey22: disabled_value22",
            "tags": "version: 1.1, pre-release",
            "segment_rules": [{
                "rules": [
                    {
                        "segments": [
                            "300"
                        ]
                    }
                ],
                "value": "$default",
                "order": 1
            }
            ]
        }

        sut = Feature(feature)
        self.assertTrue(sut.is_enabled())
        self.assertEqual(sut.get_feature_name(), "testF5")
        self.assertEqual(sut.get_feature_id(), "testf5")
        self.assertEqual(sut.get_feature_data_format(), "YAML")
        self.assertEqual(sut.get_enabled_value()['key1'], "enabled_value")
        self.assertEqual(sut.get_disabled_value()[1]['key22'], "disabled_value22")
        Metering.get_instance().set_repeat_calls(False)

        value = sut.get_current_value("id1", {"email": "test.dev@tester.com"})
        self.assertEqual(value['key1'], "enabled_value")

    # enabled and disabled value contains invalid yaml documents and invalid entity id is passed
    def test_feature_yaml2(self):
        feature = {
            "name": "testF5",
            "feature_id": "testf5",
            "description": "Feature flags to enable testing",
            "type": "STRING",
            "format": "YAML",
            "enabled": True,
            "enabled_value": "key1: enabled_value1\n--\n",
            "disabled_value": "key2: disabled_value2\n--\n",
            "tags": "version: 1.1, pre-release"
        }

        sut = Feature(feature)
        self.assertTrue(sut.is_enabled())
        self.assertEqual(sut.get_feature_name(), "testF5")
        self.assertEqual(sut.get_feature_id(), "testf5")
        self.assertEqual(sut.get_feature_data_format(), "YAML")
        self.assertEqual(sut.get_enabled_value(), None)
        self.assertEqual(sut.get_disabled_value(), None)
        Metering.get_instance().set_repeat_calls(False)

        value = sut.get_current_value("", {"email": "test.dev@tester.com"})
        self.assertEqual(value, None)

    # enabled and disabled value contains valid json
    def test_feature_json(self):
        feature = {
            "name": "testF5",
            "feature_id": "testf5",
            "description": "Feature flags to enable testing",
            "type": "STRING",
            "format": "JSON",
            "enabled": True,
            "enabled_value": {
                "key1": "value is enabled"
            },
            "disabled_value": {
                "key2": "value is disabled"
            },
            "tags": "version: 1.1, pre-release"
        }

        sut = Feature(feature)
        self.assertTrue(sut.is_enabled())
        self.assertEqual(sut.get_feature_name(), "testF5")
        self.assertEqual(sut.get_feature_id(), "testf5")
        self.assertEqual(sut.get_feature_data_format(), "JSON")
        self.assertEqual(sut.get_enabled_value()['key1'], "value is enabled")
        self.assertEqual(sut.get_disabled_value()['key2'], "value is disabled")
        Metering.get_instance().set_repeat_calls(False)



if __name__ == '__main__':
    unittest.main()

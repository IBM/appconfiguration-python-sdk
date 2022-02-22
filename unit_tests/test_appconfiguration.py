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

import time
import unittest
import os
from ibm_appconfiguration import AppConfiguration
from ibm_appconfiguration.configurations.internal.utils.url_builder import URLBuilder


class MyTestCase(unittest.TestCase):

    def setUp(self):
        URLBuilder.set_auth_type(False)

    def test_configuration(self):
        sut1 = AppConfiguration.get_instance()
        sut2 = AppConfiguration.get_instance()
        self.assertEqual(sut1, sut2)

    def test_configuration_values(self):
        sut1 = AppConfiguration.get_instance()

        sut1.init(None, "guid_value", "apikey_value")
        self.assertIsNotNone(sut1.get_region())

        sut1.init('region', None, "apikey_value")
        self.assertIsNotNone(sut1.get_guid())

        sut1.init('region', "guid_value", None)
        self.assertIsNotNone(sut1.get_apikey())

        sut1.init('region', "guid_value", "apikey_value")
        self.assertEqual(sut1.get_guid(), "guid_value")
        self.assertEqual(sut1.get_apikey(), "apikey_value")
        self.assertEqual(sut1.get_region(), "region")

    def test_configuration_fetch(self):
        sut1 = AppConfiguration.get_instance()
        sut1.set_context("", "")
        self.assertIsNotNone(sut1.get_apikey())

    def test_configuration_fetch_feature_data(self):
        sut1 = AppConfiguration.get_instance()
        sut1.fetch_configurations()

    def response(self):
        print('Get your Feature value NOW')

    def test_configuration_register_features_update_listener(self):
        sut1 = AppConfiguration.get_instance()
        sut1.register_configuration_update_listener(self.response)

    def test_configuration_get_feature(self):
        sut1 = AppConfiguration.get_instance()
        self.assertIsNone(sut1.get_feature("FeatureId"))

    def test_configuration_get_features(self):
        sut1 = AppConfiguration.get_instance()
        sut1.init('region', "guid_value", "apikey_value")
        sut1.enable_debug(True)

        FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user.json')
        sut1.set_context("collectionId", "environmentId", configuration_file=FILE, live_config_update_enabled=False)
        time.sleep(2.5)

        self.assertEqual(len(sut1.get_features()), 3)

    def test_configuration_get_features_Dict(self):
        sut1 = AppConfiguration.get_instance()
        self.assertIsNotNone(sut1.get_features())


if __name__ == '__main__':
    unittest.main()

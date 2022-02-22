import unittest
import os
import time
from os.path import join, dirname
from dotenv import load_dotenv

from ibm_appconfiguration import AppConfiguration, Feature, Property

DEFAULT_SERVICE_NAME = 'appconfiguration'


class MyTestCase(unittest.TestCase):

    def setUp(self):
        dotenv_path = join(dirname(__file__), '.env')
        load_dotenv(dotenv_path)
        self.guid = os.environ.get("GUID")
        self.apikey = os.environ.get("APIKEY")
        self.region = os.environ.get("REGION")
        self.collection_id = os.environ.get("COLLECTION_ID")
        self.environment_id = os.environ.get("ENVIRONMENT_ID")

        self.sut = AppConfiguration.get_instance()
        self.sut.init(self.region, self.guid, self.apikey)
        self.sut.enable_debug(True)

    def app_configuration_actions(self):
        features_list = self.sut.get_features()
        feature: Feature = self.sut.get_feature("defaultfeature")

        self.assertEqual(len(features_list), 3)
        self.assertEqual(feature.get_feature_id(), "defaultfeature")

        property_list = self.sut.get_properties()
        property_obj = self.sut.get_property("numericproperty")

        self.assertEqual(len(property_list), 1)
        self.assertEqual(property_obj.get_property_id(), "numericproperty")

        entity_id = "developer_entity"
        entity_attributes = {
            'email': 'tommartin@company.dev'
        }
        current_value = feature.get_current_value(entity_id, entity_attributes)
        self.assertEqual(current_value, "Welcome")

        entity_attributes = {
            'email': 'laila@company.test'
        }
        current_value = feature.get_current_value(entity_id, entity_attributes)
        self.assertEqual(current_value, "Hello")

        entity_attributes = {
            'email': 'tommartin@tester.com'
        }
        current_value = property_obj.get_current_value(entity_id, entity_attributes)
        self.assertEqual(current_value, 81)

        entity_attributes = {
            'email': 'laila@company.test'
        }
        current_value = property_obj.get_current_value(entity_id, entity_attributes)
        self.assertEqual(current_value, 25)

    def test_app_configuration_with_file(self):
        FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user.json')

        self.sut.set_context(self.collection_id, self.environment_id, options={
            'bootstrap_file': FILE,
            'live_config_update_enabled': False
        })
        time.sleep(2.0)
        self.app_configuration_actions()

    def test_app_configuration_online(self):

        try:
            self.sut.set_context(self.collection_id, self.environment_id)
            self.app_configuration_actions()
            unittest.installHandler()
        except Exception as e:
            print(f'Error {e}')
            unittest.installHandler()


if __name__ == '__main__':
    unittest.main()

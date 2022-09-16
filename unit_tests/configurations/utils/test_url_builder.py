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
from ibm_appconfiguration.configurations.internal.utils.url_builder import URLBuilder


class MyTestCase(unittest.TestCase):

    def test_url_builder(self):
        # Test prod url
        URLBuilder.init_with_collection_id(collection_id="collection_id",
                                           environment_id="environment_id",
                                           region="region",
                                           guid="guid",
                                           apikey="",
                                           override_service_url="",
                                           use_private_endpoint=False)

        self.assertEqual(URLBuilder.get_base_url(), 'https://region.apprapp.cloud.ibm.com')
        self.assertEqual(URLBuilder.get_iam_url(), 'https://iam.cloud.ibm.com')
        self.assertEqual(URLBuilder.get_config_path(),
                         '/apprapp/feature/v1/instances/guid/collections/collection_id/config?environment_id=environment_id')
        self.assertEqual(URLBuilder.get_metering_path(), '/apprapp/events/v1/instances/guid/usage')
        self.assertEqual(URLBuilder.get_web_socket_url(),
                         'wss://region.apprapp.cloud.ibm.com/apprapp/wsfeature?instance_id=guid&collection_id=collection_id&environment_id=environment_id')

        # Test prod url with private endpoint
        URLBuilder.init_with_collection_id(collection_id="collection_id",
                                           environment_id="environment_id",
                                           region="region",
                                           guid="guid",
                                           apikey="",
                                           override_service_url="",
                                           use_private_endpoint=True)

        self.assertEqual(URLBuilder.get_base_url(), 'https://private.region.apprapp.cloud.ibm.com')
        self.assertEqual(URLBuilder.get_iam_url(), 'https://private.iam.cloud.ibm.com')
        self.assertEqual(URLBuilder.get_config_path(),
                         '/apprapp/feature/v1/instances/guid/collections/collection_id/config?environment_id=environment_id')
        self.assertEqual(URLBuilder.get_metering_path(), '/apprapp/events/v1/instances/guid/usage')
        self.assertEqual(URLBuilder.get_web_socket_url(),
                         'wss://private.region.apprapp.cloud.ibm.com/apprapp/wsfeature?instance_id=guid&collection_id=collection_id&environment_id=environment_id')

        # Test dev & stage url
        URLBuilder.init_with_collection_id(collection_id="collection_id",
                                           environment_id="environment_id",
                                           region="region",
                                           guid="guid",
                                           apikey="",
                                           override_service_url="https://region.apprapp.test.cloud.ibm.com",
                                           use_private_endpoint=False)

        self.assertEqual(URLBuilder.get_base_url(), 'https://region.apprapp.test.cloud.ibm.com')
        self.assertEqual(URLBuilder.get_iam_url(), 'https://iam.test.cloud.ibm.com')
        self.assertEqual(URLBuilder.get_config_path(),
                         '/apprapp/feature/v1/instances/guid/collections/collection_id/config?environment_id=environment_id')
        self.assertEqual(URLBuilder.get_metering_path(), '/apprapp/events/v1/instances/guid/usage')
        self.assertEqual(URLBuilder.get_web_socket_url(),
                         'wss://region.apprapp.test.cloud.ibm.com/apprapp/wsfeature?instance_id=guid&collection_id=collection_id&environment_id=environment_id')

        # Test dev & stage url with private endpoint
        URLBuilder.init_with_collection_id(collection_id="collection_id",
                                           environment_id="environment_id",
                                           region="region",
                                           guid="guid",
                                           apikey="",
                                           override_service_url="https://region.apprapp.test.cloud.ibm.com",
                                           use_private_endpoint=True)

        self.assertEqual(URLBuilder.get_base_url(), 'https://private.region.apprapp.test.cloud.ibm.com')
        self.assertEqual(URLBuilder.get_iam_url(), 'https://private.iam.test.cloud.ibm.com')
        self.assertEqual(URLBuilder.get_config_path(),
                         '/apprapp/feature/v1/instances/guid/collections/collection_id/config?environment_id=environment_id')
        self.assertEqual(URLBuilder.get_metering_path(), '/apprapp/events/v1/instances/guid/usage')
        self.assertEqual(URLBuilder.get_web_socket_url(),
                         'wss://private.region.apprapp.test.cloud.ibm.com/apprapp/wsfeature?instance_id=guid&collection_id=collection_id&environment_id=environment_id')


if __name__ == '__main__':
    unittest.main()

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
        URLBuilder.init_with_collection_id(collection_id="collection_id",
                                           guid="guid",
                                           environment_id="environment_id",
                                           region="region",
                                           override_service_url="",
                                           apikey="")
        expected_config_url = '/feature/v1/instances/guid/collections/collection_id/config?environment_id=environment_id'
        expected_socket_url = 'wss://region.apprapp.cloud.ibm.com/apprapp/wsfeature?instance_id=guid&collection_id=collection_id&environment_id=environment_id'
        expected_metering_url = '/events/v1/instances/'

        self.assertEqual(URLBuilder.get_config_url(), expected_config_url)
        self.assertEqual(URLBuilder.get_web_socket_url(), expected_socket_url)
        self.assertEqual(URLBuilder.get_metering_url(), expected_metering_url)


if __name__ == '__main__':
    unittest.main()

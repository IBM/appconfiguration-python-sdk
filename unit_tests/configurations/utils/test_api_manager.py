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
import responses
from ibm_appconfiguration.configurations.internal.utils.api_manager import APIManager
from ibm_appconfiguration.configurations.internal.utils.url_builder import URLBuilder

base_url = 'https://cloud.ibm.com'


class MyTestCase(unittest.TestCase):

    def setUp(self) -> None:

        self.responses = responses.RequestsMock()
        self.responses.start()
        self.addCleanup(self.responses.stop)
        self.addCleanup(self.responses.reset)

        URLBuilder.init_with_collection_id(collection_id="collection_id",
                                           environment_id="environment_id",
                                           region="region",
                                           guid="guid",
                                           apikey="apikey",
                                           override_service_url=base_url,
                                           use_private_endpoint=False)
        URLBuilder.set_auth_type(False)
        self.api_manager = APIManager.get_instance()

    def test_get_call(self):
        mock_response = '{ "features": [], "properties": [], "segments": []}'
        url = 'https://region.apprapp.cloud.ibm.com/apprapp/feature/v1/instances/guid/collections/collection_id/config?environment_id=environment_id'
        self.responses.add(responses.GET,
                           url,
                           body=mock_response,
                           content_type='application/json',
                           status=200)

        resp = self.api_manager.prepare_api_request(method="GET", url=URLBuilder.get_config_path())
        self.assertEqual(resp.get_status_code(), 200)

        try:
            response_data = dict(resp.get_result())
            self.assertEqual(len(response_data), 3)
        except Exception as exception:
            self.fail("Issues with API request")


if __name__ == '__main__':
    unittest.main()

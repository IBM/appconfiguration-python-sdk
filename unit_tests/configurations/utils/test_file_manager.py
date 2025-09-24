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
import json
import unittest
import os
from ibm_appconfiguration.configurations.internal.utils.file_manager import FileManager


class MyTestCase(unittest.TestCase):
    file_path = ''

    def setUp(self) -> None:
        self.file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'list.json')

    def test_file_store(self):
        data = {
            "features": [
                {
                    "name": "defaultFeature123",
                    "feature_id": "defaultfeature",
                    "type": "BOOLEAN",
                    "enabled_value": True,
                    "disabled_value": False,
                    "segment_rules": [
                        {
                            "rules": [
                                {
                                    "segments": [
                                        "kg92d3wa"
                                    ]
                                }
                            ],
                            "value": False,
                            "order": 1
                        }
                    ],
                    "segment_exists": True,
                    "isEnabled": True
                }
            ],
            "collection": {
                "name": "appCrash",
                "collection_id": "appcrash"
            },
            "segments": [
                {
                    "name": "defaultSeg",
                    "segment_id": "kg92d3wa",
                    "rules": [
                        {
                            "values": [
                                "dev"
                            ],
                            "operator": "contains",
                            "attribute_name": "email"
                        }
                    ]
                }
            ]
        }
        self.assertTrue(FileManager.store_files(json.dumps(data), self.file_path))

        expected_data = FileManager.read_files(self.file_path)

        self.assertIsNotNone(expected_data)


if __name__ == '__main__':
    unittest.main()

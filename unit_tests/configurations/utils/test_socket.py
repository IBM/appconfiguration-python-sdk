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
from ibm_appconfiguration.configurations.internal.utils.socket import Socket


class MyTestCase(unittest.TestCase):

    expected_message = ''
    expected_error = ''
    expected_closed_state = ''
    expected_open_state = ''

    def callback(self, message=None, error_state=None, closed_state=None, open_state=None):
        self.expected_message = message
        self.expected_error = error_state
        self.expected_closed_state = closed_state
        self.expected_open_state = open_state

    def test_socket(self):
        self.__socket = Socket()
        self.__socket.setup(
            url="ws://testurl.com",
            headers=[],
            callback=self.callback
        )

        self.assertIsNotNone(self.__socket)

        self.__socket.on_message(self.__socket.ws_client,"Socket message")
        self.assertEqual(self.expected_message, "Socket message")

        self.__socket.on_error(self.__socket.ws_client, "Error message")
        self.assertEqual(self.expected_error, "Error message")

        self.__socket.on_open(self.__socket.ws_client)
        self.assertEqual(self.expected_open_state, "Opened the web_socket")

        self.__socket.on_close(self.__socket.ws_client, 1000, "normal closure")
        self.assertEqual(self.expected_closed_state, "Closed the web_socket")




if __name__ == '__main__':
    unittest.main()

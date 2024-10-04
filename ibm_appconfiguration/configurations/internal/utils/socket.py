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

"""
This module provides methods to perform operations on the websocket connection to the server.
"""
import ssl
import websocket


class Socket:
    """Class to handle the Web socket"""
    def __init__(self):
        self.__callback = None
        self.ws_client = None

    def setup(self, url, headers, callback):
        """ Setup the socket.

        Args:
            url: Url for the socket
            headers: Headers for the socket.
            callback: Callback for the socket.
        """
        self.__callback = callback
        self.ws_client = websocket.WebSocketApp(
            url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            header=headers
        )
        self.ws_client.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    def on_message(self, _, message):
        """Socket on-message

        Args:
            message: Message object from the socket
        """
        if message == 'test message':
            return
        self.__callback(message=message)

    def on_error(self, _, error):
        """Socket on-error

        Args:
            error: Error object from the socket
        """
        self.__callback(error_state=error)
        self.ws_client.close()

    def on_close(self, _, close_status_code, close_msg):
        """Socket on-close call"""
        self.__callback(closed_state='Closed the web_socket')

    def on_open(self, _):
        """Socket on-open call"""
        self.__callback(open_state='Opened the web_socket')

    def cancel(self):
        """
        Socket cancel.
        """
        self.ws_client.close()

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
import threading
from time import sleep

from ibm_cloud_sdk_core import ApiException

from .logger import Logger
from ..common import config_constants
from ..common.config_constants import WEBSOCKET_RECONNECT_DELAY


class Socket:
    """
    Class to handle the Web socket connection.

    Example usage:
        # Create socket instance
        socket = Socket()

        # Setup and connect
        socket.setup(url="wss://example.com", headers={"Authorization": "Bearer token"}, callback=my_callback)

        # Check connection status
        is_connected = socket.is_connected()

        # Disconnect and reconnect
        socket.disconnect()
        socket.connect()

        # Clean up when done
        socket.cancel()
    """

    def __init__(self):
        self.__callback = None
        self.ws_client = None
        self.__url = None
        self.__headers_provider = None
        self.__should_reconnect = False
        self.__is_connected = False
        self.__websocket_thread = None

    def setup(self, url: str, headers_provider, callback) -> None:
        """
        Setup the socket with connection parameters. If already connected, will disconnect first.

        Args:
            url: Websocket URL to connect to
            headers_provider: Callable that returns fresh headers dict for the websocket connection
            callback: Callback function for websocket events
        """
        if not callable(headers_provider):
            Logger.error("headers_provider must be a callable")
            return

        # If already connected with same parameters, do nothing
        if (self.__url == url and
                self.__headers_provider == headers_provider and
                self.__callback == callback and
                self.__is_connected):
            return

        # Store new parameters
        self.__url = url
        self.__headers_provider = headers_provider
        self.__callback = callback

        # Disconnect if already connected
        self.disconnect()

        # Start new connection
        self.connect()

    def connect(self) -> None:
        """
        Explicitly start/restart the websocket connection.
        Safe to call multiple times - will disconnect existing connection first.
        """
        # Disconnect any existing connection
        self.disconnect()

        # Start new connection
        self.__should_reconnect = True
        if not self.__websocket_thread or not self.__websocket_thread.is_alive():
            self.__websocket_thread = threading.Thread(target=self.__websocket_run)
            self.__websocket_thread.daemon = True
            self.__websocket_thread.start()

    def disconnect(self) -> None:
        """
        Disconnect the websocket without canceling. Can be reconnected later.
        """
        self.__should_reconnect = False
        self.__is_connected = False
        if self.ws_client:
            try:
                self.ws_client.close(status=config_constants.CUSTOM_SOCKET_CLOSE_REASON_CODE)
            except Exception:
                pass
            self.ws_client = None

    def cancel(self) -> None:
        """
        Permanently cancel the websocket. Cannot be reconnected after this.
        """
        self.disconnect()
        self.__url = None
        self.__headers_provider = None
        self.__callback = None

    def is_connected(self) -> bool:
        """
        Check if websocket is currently connected.

        Returns:
            bool: True if connected, False otherwise
        """
        return self.__is_connected

    def __websocket_run(self):
        """Main websocket thread that handles connection and reconnection"""
        while self.__should_reconnect:
            try:
                if not self.__url or not self.__headers_provider:
                    Logger.error("URL or headers_provider not configured")
                    break

                # Get fresh headers for each connection attempt
                try:
                    current_headers = self.__headers_provider()
                    if not isinstance(current_headers, dict):
                        Logger.error("headers_provider must return a dictionary")
                        break
                except ApiException as e:
                    Logger.error(f"Error getting headers: {str(e)}")
                    # Check if the exception is due to a client error (4xx) from IAM
                    if self.__is_token_client_error(e):
                        Logger.error("Token retrieval failed with client error (4xx). Stopping WebSocket reconnection.")
                        self.__should_reconnect = False
                        break

                    # For other errors (5xx, network issues), retry after delay
                    if self.__should_reconnect:
                        Logger.debug(f"Reconnecting to websocket in {WEBSOCKET_RECONNECT_DELAY} seconds...")
                        sleep(WEBSOCKET_RECONNECT_DELAY)
                    continue

                self.ws_client = websocket.WebSocketApp(
                    self.__url,
                    on_open=self.on_open,
                    on_message=self.on_message,
                    on_error=self.on_error,
                    on_close=self.on_close,
                    header=current_headers
                )

                self.ws_client.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

                if self.__should_reconnect:
                    Logger.debug(f"Reconnecting to websocket in {WEBSOCKET_RECONNECT_DELAY} seconds...")
                    sleep(WEBSOCKET_RECONNECT_DELAY)

            except Exception as e:
                Logger.error(f"WebSocket error: {str(e)}")
                if self.__should_reconnect:
                    Logger.debug(f"Reconnecting to websocket in {WEBSOCKET_RECONNECT_DELAY} seconds...")
                    sleep(WEBSOCKET_RECONNECT_DELAY)

    def __is_token_client_error(self, error) -> bool:
        """Check if the error from token retrieval is a client-side error (4xx)"""
        # Check for various IBM SDK exception types that might contain status codes
        error_str = str(error).lower()

        # Common patterns for 4xx errors in IBM SDK exceptions
        if any(code in error_str for code in ['400', '401', '403', '404']):
            return True

        # Check if exception has a status_code or code attribute
        status_code = getattr(error, 'status_code', None) or getattr(error, 'code', None)
        if status_code is not None:
            try:
                status_code = int(status_code)
                if 400 <= status_code < 500 and status_code != 429 and status_code != 499:
                    return True
            except (ValueError, TypeError):
                pass

        # Check if it's an ApiException from ibm_cloud_sdk_core
        if hasattr(error, 'message') and hasattr(error, 'http_response'):
            http_response = getattr(error, 'http_response', None)
            if http_response and hasattr(http_response, 'status_code'):
                status_code = http_response.status_code
                if 400 <= status_code < 500 and status_code != 429 and status_code != 499:
                    return True

        return False

    def __is_client_error(self, error) -> bool:
        """Check if the error is a client-side error (4xx)"""
        if isinstance(error, websocket.WebSocketBadStatusException):
            status_code = getattr(error, 'status_code', None)
            if status_code is not None and 400 <= status_code < 500 and status_code != 429 and status_code != 499:
                return True
        return False

    def on_message(self, _, message):
        """Socket on-message callback"""
        if message == 'test message':
            Logger.debug("Received test message from server")
            return

        if self.__callback:
            self.__callback(message=message)

    def on_error(self, _, error):
        """Socket on-error callback"""
        self.__is_connected = False
        if self.__is_client_error(error):
            # Stop reconnecting on client-side errors
            Logger.error(f"Websocket connect failed due to client error: {error}")
            self.__should_reconnect = False
        else:
            Logger.error(f"Websocket connect failed due to server error: {error}. Reconnecting...")

        if self.__callback:
            self.__callback(error_state=error)

    def on_close(self, _, close_status_code, close_msg):
        """Socket on-close callback"""
        self.__is_connected = False
        if close_status_code is not None and close_status_code == config_constants.CUSTOM_SOCKET_CLOSE_REASON_CODE:
            self.__should_reconnect = False

        Logger.error(f"Websocket closed with code: {close_status_code} and message: {close_msg}. Reconnecting...")
        if self.__callback:
            self.__callback(closed_state='Closed the web_socket')

    def on_open(self, _):
        """Socket on-open callback"""
        self.__is_connected = True

        if self.__callback:
            self.__callback(open_state='Opened the web_socket')

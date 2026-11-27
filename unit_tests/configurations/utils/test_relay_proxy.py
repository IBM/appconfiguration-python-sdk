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

"""Relay proxy unit tests: no IAM call, the apikey is sent as the Authorization header."""

import unittest
from unittest.mock import patch

import responses
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator, NoAuthAuthenticator

from ibm_appconfiguration import AppConfiguration
from ibm_appconfiguration.configurations.internal.utils.api_manager import APIManager
from ibm_appconfiguration.configurations.internal.utils.url_builder import URLBuilder

RELAY_URL = 'https://relay-proxy.example.com'
APIKEY = 'my-apikey'


def init_url_builder(override_service_url=RELAY_URL, use_private_endpoint=False):
    URLBuilder.init_with_collection_id(collection_id="collection_id",
                                       environment_id="environment_id",
                                       region="region",
                                       guid="guid",
                                       apikey=APIKEY,
                                       override_service_url=override_service_url,
                                       use_private_endpoint=use_private_endpoint)


class TestRelayProxyUrlBuilder(unittest.TestCase):

    def setUp(self):
        # other test modules leave auth disabled on the shared class, so set it explicitly
        self._has_auth = URLBuilder._URLBuilder__hasAuth
        URLBuilder.set_auth_type(True)

    def tearDown(self):
        URLBuilder.set_relay_proxy_configured(False)
        URLBuilder.set_auth_type(self._has_auth)

    def test_relay_proxy_is_disabled_by_default(self):
        self.assertFalse(URLBuilder.is_relay_proxy_configured())
        init_url_builder(override_service_url="")
        self.assertIsInstance(URLBuilder.get_iam_authenticator(), IAMAuthenticator)

    def test_no_iam_authenticator_in_relay_proxy_mode(self):
        URLBuilder.set_relay_proxy_configured(True)
        init_url_builder()
        self.assertIsInstance(URLBuilder.get_iam_authenticator(), NoAuthAuthenticator)

    def test_apikey_is_stored(self):
        URLBuilder.set_relay_proxy_configured(True)
        init_url_builder()
        self.assertEqual(URLBuilder.get_apikey(), APIKEY)

    def test_relay_url_is_used_as_is_with_private_endpoint(self):
        URLBuilder.set_relay_proxy_configured(True)
        init_url_builder(use_private_endpoint=True)
        self.assertEqual(URLBuilder.get_base_url(), RELAY_URL)
        self.assertTrue(URLBuilder.get_web_socket_url().startswith('wss://relay-proxy.example.com/'))

    def test_private_endpoint_prefix_still_applies_without_relay_proxy(self):
        init_url_builder(use_private_endpoint=True)
        self.assertEqual(URLBuilder.get_base_url(), 'https://private.relay-proxy.example.com')

    def test_disabling_relay_proxy_restores_iam_authenticator(self):
        URLBuilder.set_relay_proxy_configured(True)
        URLBuilder.set_relay_proxy_configured(False)
        init_url_builder()
        self.assertIsInstance(URLBuilder.get_iam_authenticator(), IAMAuthenticator)


class TestRelayProxyApiManager(unittest.TestCase):

    def setUp(self):
        self.responses = responses.RequestsMock()
        self.responses.start()
        self.addCleanup(self.responses.stop)
        self.addCleanup(self.responses.reset)
        URLBuilder.set_relay_proxy_configured(True)
        init_url_builder()
        self.api_manager = APIManager()

    def tearDown(self):
        URLBuilder.set_relay_proxy_configured(False)

    def test_request_sends_apikey_as_authorization_header_without_iam_call(self):
        self.responses.add(responses.GET, RELAY_URL + URLBuilder.get_config_path(),
                           json={}, status=200)
        resp = self.api_manager.prepare_api_request(method="GET", url=URLBuilder.get_config_path())
        self.assertEqual(200, resp.get_status_code())
        # only the relay proxy call was made, there was no IAM token request
        self.assertEqual(len(self.responses.calls), 1)
        self.assertEqual(self.responses.calls[0].request.headers['Authorization'], APIKEY)

    def test_websocket_headers_use_apikey_without_token_generation(self):
        with patch.object(IAMAuthenticator, 'token_manager', create=True) as token_manager:
            headers = self.api_manager.get_websocket_headers()
        token_manager.get_token.assert_not_called()
        self.assertEqual(headers['Authorization'], APIKEY)
        self.assertIn('User-Agent', headers)


class TestRelayProxyEndpoint(unittest.TestCase):

    def setUp(self):
        self._url = AppConfiguration._AppConfiguration__override_service_url

    def tearDown(self):
        URLBuilder.set_relay_proxy_configured(False)
        AppConfiguration._AppConfiguration__override_service_url = self._url

    def test_sets_url_and_relay_proxy_flag(self):
        AppConfiguration.set_relay_proxy_endpoint(RELAY_URL)
        self.assertTrue(URLBuilder.is_relay_proxy_configured())
        self.assertEqual(AppConfiguration._AppConfiguration__override_service_url, RELAY_URL)

    def test_empty_url_is_ignored(self):
        AppConfiguration.set_relay_proxy_endpoint('')
        self.assertFalse(URLBuilder.is_relay_proxy_configured())

    def test_none_url_is_ignored(self):
        AppConfiguration.set_relay_proxy_endpoint(None)
        self.assertFalse(URLBuilder.is_relay_proxy_configured())


if __name__ == '__main__':
    unittest.main()

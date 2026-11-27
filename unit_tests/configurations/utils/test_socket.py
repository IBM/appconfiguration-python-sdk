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

import os
import shutil
import socket as net
import ssl
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import MagicMock, patch

from ibm_appconfiguration.configurations.internal.utils import socket as socket_module
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

    def headers_provider(self):
        return {}

    def test_socket(self):
        self.__socket = Socket()
        self.__socket.setup(
            url="ws://testurl.com",
            headers_provider=self.headers_provider,
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


class TestSocketTlsVerification(unittest.TestCase):
    """The websocket must verify the server certificate: no sslopt may be passed to run_forever."""

    URL = "wss://example.com/feed"

    def _run_one_connection(self):
        """Run the websocket loop once with a mocked WebSocketApp. Returns the mocked app."""
        socket = Socket()
        app = MagicMock()
        socket._Socket__url = self.URL
        socket._Socket__headers_provider = lambda: {"Authorization": "key"}
        socket._Socket__should_reconnect = True

        def stop_after_run(*args, **kwargs):
            socket._Socket__should_reconnect = False

        app.run_forever.side_effect = stop_after_run
        with patch.object(socket_module.websocket, "WebSocketApp", return_value=app) as app_class:
            socket._Socket__websocket_run()
        return app_class, app

    def test_run_forever_is_called_without_sslopt(self):
        _, app = self._run_one_connection()
        app.run_forever.assert_called_once_with()

    def test_run_forever_never_disables_certificate_verification(self):
        _, app = self._run_one_connection()
        args, kwargs = app.run_forever.call_args
        self.assertNotIn("sslopt", kwargs)
        self.assertEqual(args, ())

    def test_module_does_not_use_cert_none(self):
        with open(socket_module.__file__, encoding="utf-8") as source:
            code = source.read()
        self.assertNotIn("CERT_NONE", code)
        self.assertNotIn("cert_reqs", code)

    def test_websocket_app_still_gets_url_and_headers(self):
        app_class, _ = self._run_one_connection()
        args, kwargs = app_class.call_args
        self.assertEqual(args[0], self.URL)
        self.assertEqual(kwargs["header"], {"Authorization": "key"})


@unittest.skipUnless(shutil.which("openssl"), "openssl is needed to create a test certificate")
class TestSocketRejectsUntrustedCertificate(unittest.TestCase):
    """Real TLS handshake against a local server that uses a self-signed certificate."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)
        cert = os.path.join(self.tmp_dir, "cert.pem")
        key = os.path.join(self.tmp_dir, "key.pem")
        subprocess.run(
            ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", cert,
             "-days", "1", "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost"],
            check=True, capture_output=True)

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        self.server = net.socket(net.AF_INET, net.SOCK_STREAM)
        self.server.bind(("127.0.0.1", 0))
        self.server.listen(1)
        self.server.settimeout(10)
        self.port = self.server.getsockname()[1]
        self.handshake_completed = threading.Event()
        self.handshake_finished = threading.Event()

        def serve():
            try:
                connection, _ = self.server.accept()
                try:
                    with context.wrap_socket(connection, server_side=True):
                        self.handshake_completed.set()
                except (ssl.SSLError, OSError):
                    pass
            except OSError:
                pass
            finally:
                self.handshake_finished.set()

        self.server_thread = threading.Thread(target=serve, daemon=True)
        self.server_thread.start()
        self.addCleanup(self.server.close)

        self.error_received = threading.Event()
        self.error_text = []

    def callback(self, message=None, error_state=None, closed_state=None, open_state=None):
        if error_state is not None:
            self.error_text.append(str(error_state))
            self.error_received.set()

    def test_connection_to_self_signed_server_fails_verification(self):
        client = Socket()
        client.setup(url="wss://localhost:{0}".format(self.port),
                     headers_provider=lambda: {},
                     callback=self.callback)
        self.addCleanup(client.cancel)

        self.assertTrue(self.error_received.wait(15), "the websocket did not report an error")
        self.assertTrue(self.handshake_finished.wait(15))
        self.assertFalse(self.handshake_completed.is_set(), "TLS handshake succeeded with an untrusted certificate")
        self.assertIn("CERTIFICATE_VERIFY_FAILED", self.error_text[0])


if __name__ == '__main__':
    unittest.main()

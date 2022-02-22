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
Package to perform the connectivity check.
"""

from threading import Timer
import requests
from .url_builder import URLBuilder


class Connectivity:
    """Connectivity checker"""
    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method. """
        if Connectivity.__instance is None:
            return Connectivity()
        return Connectivity.__instance

    def __init__(self):
        if Connectivity.__instance is not None:
            print("Connectivity class must be initialized using the get_instance() method")
        else:
            self.__listeners = list()
            Connectivity.__instance = self

    def add_connectivity_listener(self, listener):
        """ Listener for the the internet

        Args:
            listener: Listener for the the internet
        """
        if callable(listener) and not self.__listeners.__contains__(listener):
            self.__listeners.append(listener)

    def check_connection(self):
        """Check the connection"""
        url = URLBuilder.get_network_check_url()
        if url:
            self.__check_network(url)
            timer = Timer(30, self.check_connection)
            timer.daemon = True
            timer.start()

    def __check_network(self, url):
        try:
            _ = requests.head(url, timeout=3)
            for listener in self.__listeners:
                listener(True)
        except Exception as _:
            for listener in self.__listeners:
                listener(False)

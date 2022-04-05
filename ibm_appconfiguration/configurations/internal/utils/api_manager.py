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
This module provides the methods to facilitate the API requests to the App Configuration service.
"""
import json as json_import
from typing import Optional, Union
from ibm_cloud_sdk_core import BaseService, DetailedResponse, ApiException
from requests.exceptions import RetryError
from .url_builder import URLBuilder
from ibm_appconfiguration.version import __version__
from ..common import config_constants


class APIManager(BaseService):
    """The API Manager for the library"""

    __instance = None

    @staticmethod
    def get_instance():
        """ Static access method. """
        if APIManager.__instance is None:
            return APIManager()
        return APIManager.__instance

    def __init__(self):
        super().__init__(service_url=URLBuilder.get_base_url(),
                         authenticator=URLBuilder.get_iam_authenticator())
        self.enable_retries(config_constants.MAX_NUMBER_OF_RETRIES)
        APIManager.__instance = self

    def prepare_api_request(self,
                            method: str,
                            url: str,
                            data: Optional[Union[str, dict]] = None) -> DetailedResponse:
        """ Prepare the API call request

        Args:
            method: Method for the request
            url: Url of the request
            data: data to be send.
        Returns:
            return the DetailedResponse.
        """

        headers = {'Content-Type': 'application/json',
                   'User-Agent': '{0}/{1}'.format(config_constants.SDK_NAME, __version__)}
        if data and isinstance(data, dict):
            data = self.__remove_null_values(data)
            data = json_import.dumps(data)

        try:
            request = self.prepare_request(method=method,
                                           url=url,
                                           headers=headers,
                                           data=data)
            response = self.send(request)
            return response
        except ApiException as api_exception:
            return DetailedResponse(response=api_exception.message,
                                    headers=None,
                                    status_code=api_exception.code)
        except RetryError as retry_error:
            """
                Because the RetryError doesn't give the status_code in its exception object, we are uncertain for which status code
                the request was failed. The status_code will be initialised as None in the DetailedResponse class and sent back to the caller.
                The caller has to assume the None value status_code was due to one of [429, 500, 502, 503, 504]. As RetryError exception is
                thrown for those status codes.
            """
            return DetailedResponse(response=retry_error)
        except Exception as exception:
            """
                General exception in-case above exceptions are not matched.
            """
            return DetailedResponse(response=exception)

    def __remove_null_values(self, dictionary: dict) -> dict:
        """Create a new dictionary without keys mapped to null values.

        Args:
            dictionary: The dictionary potentially containing keys mapped to values of None.

        Returns:
            A dict with no keys mapped to None.
        """
        if isinstance(dictionary, dict):
            return {k: v for (k, v) in dictionary.items() if v is not None}
        return dictionary

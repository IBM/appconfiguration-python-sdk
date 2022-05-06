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
This module provides methods to construct different url used by the SDK.
"""
from typing import Optional
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator, NoAuthAuthenticator, Authenticator
from .validators import Validators
from ..common import config_constants


class URLBuilder:
    """URLBuilder class to create different urls for the library """
    __wsurl = "/wsfeature"
    __path = "/feature/v1/instances/"
    __service = "/apprapp"
    __events = "/events/v1/instances/"
    __config = "config"
    __override_service_url = ''
    __region = ''
    __http_base = ''
    __web_socket_base = ''
    __config_base = ''
    __iam_authenticator = None
    __hasAuth = True
    __network_check_url = 'https://cloud.ibm.com'

    @classmethod
    def init_with_collection_id(cls, collection_id='', region='', guid='', environment_id='', override_service_url='',
                                apikey=''):
        """Initialise the URLBuilder

        Args:
            collection_id: Id of the collection created in App Configuration service instance.
            region: Region name where the service instance is created.
            guid: GUID of the App Configuration service. Get it from the service credentials section of the dashboard
            environment_id: Id of the environment created in App Configuration service instance.
            override_service_url: Use for testing purpose
            apikey: ApiKey of the App Configuration service. Get it from the service credentials section of the dashboard
        """
        if Validators.validate_string(collection_id) \
                and Validators.validate_string(region) \
                and Validators.validate_string(guid) \
                and Validators.validate_string(environment_id):
            cls.__override_service_url = override_service_url
            cls.__region = region
            cls.__web_socket_base = config_constants.DEFAULT_WSS_TYPE
            cls.__http_base = config_constants.DEFAULT_HTTP_TYPE
            if Validators.validate_string(cls.__override_service_url):
                cls.__iam_authenticator = IAMAuthenticator(apikey, url=config_constants.IAM_TEST_URL)
                cls.__http_base = cls.__override_service_url
                cls.__web_socket_base += (cls.__override_service_url.replace("https://", "").replace("http://", ""))
            else:
                cls.__http_base += region
                cls.__http_base += config_constants.DEFAULT_BASE_URL
                cls.__web_socket_base += region
                cls.__web_socket_base += config_constants.DEFAULT_BASE_URL
                cls.__iam_authenticator = IAMAuthenticator(apikey, url=config_constants.IAM_PROD_URL)

        cls.__http_base += '{0}'.format(cls.__service)
        cls.__config_base = '{0}{1}/collections/{2}/{3}?environment_id={4}'.format(cls.__path,
                                                                                   guid,
                                                                                   collection_id,
                                                                                   cls.__config,
                                                                                   environment_id)

        cls.__web_socket_base += "{0}{1}?instance_id={2}&collection_id={3}&environment_id={4}".format(cls.__service,
                                                                                                      cls.__wsurl,
                                                                                                      guid,
                                                                                                      collection_id,
                                                                                                      environment_id)

    @classmethod
    def set_auth_type(cls, has_auth=True):
        """Set the auth type"""
        cls.__hasAuth = has_auth

    @classmethod
    def get_base_url(cls) -> str:
        """Get the config url"""
        return cls.__http_base

    @classmethod
    def get_config_url(cls) -> str:
        """Get the config url"""
        return cls.__config_base

    @classmethod
    def get_web_socket_url(cls) -> str:
        """Get the web-socket url"""
        return cls.__web_socket_base

    @classmethod
    def get_metering_url(cls) -> str:
        """Get the metering URL"""
        return '{0}'.format(cls.__events)

    @classmethod
    def get_iam_authenticator(cls) -> Authenticator:
        """Get the IAM Authenticator

        Returns:
            Authenticator object
        """
        if cls.__hasAuth:
            return cls.__iam_authenticator
        return NoAuthAuthenticator()

    @classmethod
    def get_network_check_url(cls) -> Optional[str]:
        """Return the the network check url"""
        if cls.__hasAuth:
            return cls.__network_check_url
        return None

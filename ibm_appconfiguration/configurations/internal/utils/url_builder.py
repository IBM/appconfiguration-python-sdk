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


class URLBuilder:
    """URLBuilder class to create different urls for the library """
    __https = 'https://'
    __wss = "wss://"
    __base_url = ".apprapp.cloud.ibm.com"
    __private_endpoint_prefix = "private."
    __wspath = "/wsfeature"
    __service = "/apprapp"
    __feature_path = "/feature/v1/instances/"
    __events_path = "/events/v1/instances/"
    __config = "config"
    __usage = "usage"
    __http_base = ''
    __web_socket_base = ''
    __web_socket_url = ''
    __config_path = ''
    __metering_path = ''
    __iam_url = ''
    __iam_authenticator = None
    __hasAuth = True
    __network_check_url = 'https://cloud.ibm.com'

    @classmethod
    def init_with_collection_id(cls, collection_id='', environment_id='', region='', guid='', apikey='',
                                override_service_url='',
                                use_private_endpoint=False):
        """Initialise the URLBuilder

        Args:
            collection_id: Id of the collection created in App Configuration service instance.
            region: Region name where the service instance is created.
            guid: GUID of the App Configuration service. Get it from the service credentials section of the dashboard
            environment_id: Id of the environment created in App Configuration service instance.
            override_service_url: Use for testing purpose
            apikey: ApiKey of the App Configuration service. Get it from the service credentials section of the dashboard
            use_private_endpoint: If true, use private endpoint to connect to App Configuration service instance.
        """
        if Validators.validate_string(collection_id) \
                and Validators.validate_string(region) \
                and Validators.validate_string(guid) \
                and Validators.validate_string(environment_id):

            # for dev & stage
            if Validators.validate_string(override_service_url):
                temp = override_service_url.split("://")
                if use_private_endpoint:
                    cls.__http_base = temp[0] + "://" + cls.__private_endpoint_prefix + temp[1]
                    cls.__iam_url = "https://private.iam.test.cloud.ibm.com"
                    cls.__web_socket_base = cls.__wss + cls.__private_endpoint_prefix + temp[1]
                else:
                    cls.__http_base = override_service_url
                    cls.__iam_url = "https://iam.test.cloud.ibm.com"
                    cls.__web_socket_base = cls.__wss + temp[1]
            # for prod
            else:
                if use_private_endpoint:
                    cls.__http_base = cls.__https + cls.__private_endpoint_prefix + region + cls.__base_url
                    cls.__iam_url = "https://private.iam.cloud.ibm.com"
                    cls.__web_socket_base = cls.__wss + cls.__private_endpoint_prefix + region + cls.__base_url
                else:
                    cls.__http_base = cls.__https + region + cls.__base_url
                    cls.__iam_url = "https://iam.cloud.ibm.com"
                    cls.__web_socket_base = cls.__wss + region + cls.__base_url

            cls.__config_path = '{0}{1}{2}/collections/{3}/{4}?environment_id={5}'.format(
                cls.__service,
                cls.__feature_path,
                guid,
                collection_id,
                cls.__config,
                environment_id)
            cls.__metering_path = '{0}{1}{2}/usage'.format(cls.__service,
                                                           cls.__events_path,
                                                           guid,
                                                           cls.__usage)
            cls.__web_socket_url = cls.__web_socket_base + '{0}{1}?instance_id={2}&collection_id={3}&environment_id={4}'.format(
                cls.__service,
                cls.__wspath,
                guid,
                collection_id,
                environment_id)

            # create authenticator
            cls.__iam_authenticator = IAMAuthenticator(apikey, url=cls.__iam_url)

    @classmethod
    def set_auth_type(cls, has_auth=True):
        """Set the auth type"""
        cls.__hasAuth = has_auth

    @classmethod
    def get_iam_url(cls) -> str:
        """Get the IAM url"""
        return cls.__iam_url

    @classmethod
    def get_base_url(cls) -> str:
        """Get the config url"""
        return cls.__http_base

    @classmethod
    def get_config_path(cls) -> str:
        """Get the config path"""
        return cls.__config_path

    @classmethod
    def get_web_socket_url(cls) -> str:
        """Get the web-socket url"""
        return cls.__web_socket_url

    @classmethod
    def get_metering_path(cls) -> str:
        """Get the metering path"""
        return cls.__metering_path

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

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
IBM Cloud App Configuration is a centralized feature management and configuration service on IBM Cloud
for use with web and mobile applications, microservices, and distributed environments.

Instrument your applications with App Configuration Python SDK, and use the App Configuration dashboard,
CLI or API to define feature flags or properties, organized into collections and targeted to segments.
Toggle feature flag states in the cloud to activate or deactivate features in your application or environment, when required.
You can also manage the properties for distributed applications centrally.
"""
from typing import Dict, Optional
from .configurations.internal.utils.validators import Validators
from .configurations.models import Feature, Property
from .configurations.internal.utils.logger import Logger
from .configurations.internal.common import config_messages
from .configurations.configuration_handler import ConfigurationHandler


class AppConfiguration:
    """ AppConfiguration class"""
    __instance = None

    # regions
    REGION_US_SOUTH = "us-south"
    REGION_EU_GB = "eu-gb"
    REGION_AU_SYD = "au-syd"
    REGION_US_EAST = "us-east"
    REGION_EU_DE = "eu-de"
    __override_service_url = None
    __use_private_endpoint = False

    @staticmethod
    def get_instance():
        """ Static access method. """
        if AppConfiguration.__instance is None:
            return AppConfiguration()
        return AppConfiguration.__instance

    @staticmethod
    def override_service_url(url: str):
        """Override the default App Configuration URL.
        This method should be invoked before the SDK initialization.

        Example:
            AppConfiguration.override_service_url("https://testurl.com")

        NOTE: To be used for development purposes only.

        Args:
            url: The base url
        """
        if len(url) > 0:
            AppConfiguration.__override_service_url = url

    @staticmethod
    def enable_debug(enable: bool):
        """Set the logger in debug mode

        Args:
            enable: A boolean value to set the logger debug mode
        """
        Logger.set_debug(enable)

    def __init__(self):
        """ Virtually private constructor. """

        if AppConfiguration.__instance is not None:
            raise Exception("AppConfiguration " + config_messages.SINGLETON_EXCEPTION)

        self.__apikey = ''
        self.__region = ''
        self.__configuration_handler_instance = None
        self.__guid = ''
        self.__is_initialized = False
        self.__is_initialized_configuration = False
        self.__is_loading = False
        AppConfiguration.__instance = self

    def use_private_endpoint(self, use_private_endpoint_param: bool):
        """Method to set the SDK to connect to App Configuration service by using a private endpoint
        that is accessible only through the IBM Cloud private network.

        Args:
            use_private_endpoint_param: Set it to true if the SDK should connect to App Configuration using private endpoint.
            Be default, it is set to false.

        NOTE: This method must be called before calling the `init` function on the SDK.
        """
        if type(use_private_endpoint_param) is bool:
            self.__use_private_endpoint = use_private_endpoint_param
            return
        Logger.error(config_messages.INPUT_PARAMETER_NOT_BOOLEAN)

    def init(self, region: str, guid: str, apikey: str):
        """Initialise the AppConfiguration

           Args:
               region: Region Region name where the service instance is created.
               guid : GUID of the App Configuration service.\
               Get it from the service credentials section of the dashboard
               apikey : ApiKey of the App Configuration service.\
               Get it from the service credentials section of the dashboard
        """

        if not Validators.validate_string(region):
            Logger.error(config_messages.REGION_ERROR)
            return
        if not Validators.validate_string(apikey):
            Logger.error(config_messages.APIKEY_ERROR)
            return
        if not Validators.validate_string(guid):
            Logger.error(config_messages.GUID_ERROR)
            return
        self.__apikey = apikey
        self.__region = region
        self.__guid = guid
        self.__is_initialized = True
        self.__is_loading = False
        self.__setup_configuration_handler()

    def get_region(self) -> str:
        """Get the region currently used by the service.

        Returns:
            The region string currently used by the service.
        """
        return self.__region

    def get_guid(self) -> str:
        """Get the guid currently used by the service.

        Returns:
            The guid string currently used by the service.
        """
        return self.__guid

    def get_apikey(self) -> str:
        """Get the apikey currently used by the service.

        Returns:
            The apikey string currently used by the service.
        """
        return self.__apikey

    def set_context(self, collection_id: str, environment_id: str, configuration_file: Optional[str] = None,
                    live_config_update_enabled: Optional[bool] = True, options: Optional[dict] = None):

        """Set the collection and environment value of the service.
        Args:

            collection_id (str): Id of the collection created in App Configuration service instance.
            environment_id (str): Id of the environment created in App Configuration service instance.
            configuration_file (str): [DEPRECATED]. Use the 'bootstrap_file' parameter in the options dict. Path to the JSON file which contains configuration details.
            live_config_update_enabled (bool): [DEPRECATED]. Use this kwarg as part of `options` dict. Set this value to false if the new configuration values shouldn't be fetched from the server. Make sure to provide a proper JSON file in the configuration_file path. By default, this value is enabled.
            options (dict): Dictionary object containing the optional arguments. See below for their usage.

        Optional arguments:
            persistent_cache_dir (str): Absolute path to a directory having write permission. The SDK will create a file - 'appconfiguration.json' file in the specified directory and it will be used as the persistent cache to store the App Configuration service information.
            bootstrap_file (str): Absolute path of configuration file. This parameter when passed along with `live_config_update_enabled` value will drive the SDK to use the configurations present in this file to perform feature & property evaluations.
            live_config_update_enabled (bool): live configurations update from the server. Set this value to `false` if the new configuration values shouldn't be fetched from the server.
        """

        if not self.__is_initialized:
            Logger.error(config_messages.COLLECTION_INIT_ERROR)
            return

        if not Validators.validate_string(collection_id):
            Logger.error(config_messages.COLLECTION_ID_VALUE_ERROR)
            return

        if not Validators.validate_string(environment_id):
            Logger.error(config_messages.ENVIRONMENT_ID_VALUE_ERROR)
            return

        default_options = {
            'persistent_cache_dir': None,
            'bootstrap_file': None,
            'live_config_update_enabled': live_config_update_enabled
        }

        if configuration_file is not None:
            Logger.info(config_messages.DEPRECATION_WARNING_SETCONTEXT)
            default_options['bootstrap_file'] = configuration_file

        if options is not None:
            if Validators.validate_set_context_options(options):
                for key in default_options:
                    if key in options:
                        default_options[key] = options[key]
            else:
                Logger.error(config_messages.SET_CONTEXT_OPTIONAL_ARGUMENTS_ERROR)
                return

        if not default_options['live_config_update_enabled'] and \
                (default_options['bootstrap_file'] is None or not Validators.validate_string(
                    default_options['bootstrap_file'])):
            Logger.error(config_messages.BOOTSTRAP_FILE_NOT_FOUND_ERROR)
            return

        self.__is_initialized_configuration = True

        self.__configuration_handler_instance.set_context(collection_id, environment_id, default_options)
        self.__load_data_now()

    def fetch_configurations(self):
        """Fetch the latest configurations"""
        if self.__is_initialized and self.__is_initialized_configuration:
            self.__load_data_now()
        else:
            Logger.error(config_messages.COLLECTION_INIT_ERROR)

    def __setup_configuration_handler(self):
        self.__configuration_handler_instance = ConfigurationHandler.get_instance()
        self.__configuration_handler_instance.init(region=self.__region, guid=self.__guid, apikey=self.__apikey,
                                                   override_service_url=self.__override_service_url,
                                                   use_private_endpoint=self.__use_private_endpoint)

    def __load_data_now(self):
        if self.__is_loading:
            return
        self.__is_loading = True
        self.__configuration_handler_instance.load_data()
        self.__is_loading = False

    def register_configuration_update_listener(self, listener):
        """Register a listener for the Configuration changes.

        Args:
            listener: A method for listening to the Configuration changes
        """
        if self.__is_initialized and self.__is_initialized_configuration:
            self.__configuration_handler_instance.register_configuration_update_listener(listener)
        else:
            Logger.error(config_messages.COLLECTION_INIT_ERROR)

    def get_feature(self, feature_id: str) -> Feature:
        """Get the Feature with give Feature Id

        Args:
            feature_id: The Feature ID value.
        Returns:
            Feature object with the given feature_id. If the Feature is not available \
            then expect `None`.
        """
        if self.__is_initialized and self.__is_initialized_configuration:
            return self.__configuration_handler_instance.get_feature(feature_id)
        Logger.error(config_messages.COLLECTION_INIT_ERROR)
        return None

    def get_features(self) -> Dict[str, Feature]:
        """Get the list of Feature objects

        Returns:
            List of Feature objects
        """
        if self.__is_initialized and self.__is_initialized_configuration:
            return self.__configuration_handler_instance.get_features()
        Logger.error(config_messages.COLLECTION_INIT_ERROR)
        return None

    def get_properties(self) -> Dict[str, Property]:
        """Get the list of Property objects

        Returns:
            List of Property objects
        """
        if self.__is_initialized and self.__is_initialized_configuration:
            return self.__configuration_handler_instance.get_properties()
        Logger.error(config_messages.COLLECTION_INIT_ERROR)
        return None

    def get_property(self, property_id: str) -> Property:
        """Get the Property with give Property Id

        Args:
            property_id: The Property ID value.
        Returns:
            Property object with the given property_id. If the Property is \
            not available then expect `None`.
        """
        if self.__is_initialized and self.__is_initialized_configuration:
            return self.__configuration_handler_instance.get_property(property_id)
        Logger.error(config_messages.COLLECTION_INIT_ERROR)
        return None

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
This file defines the various messages used by the SDK.
"""

REGION_ERROR = "Provide a valid region in App Configuration init"
GUID_ERROR = "Provide a valid guid in App Configuration init"
APIKEY_ERROR = "Provide a valid apiKey in App Configuration init"
COLLECTION_ID_VALUE_ERROR = "Provide a valid collection_id in App Configuration set_context method"
ENVIRONMENT_ID_VALUE_ERROR = "Provide a valid environment_id in App Configuration set_context method"
COLLECTION_INIT_ERROR = "Invalid action in App Configuration. This action can be performed only after a successful " \
                        "initialization operation. Please check the initialization section for errors. "
SET_CONTEXT_OPTIONAL_ARGUMENTS_ERROR = "Invalid optional parameters passed to set_context method. Either wrong arguments keys or invalid value of arguments passed. " \
                                       "The only available arguments are persistent_cache_dir(string), bootstrap_file(string) & live_config_update_enabled(bool)." \
                                       "Please check the sdk initialization section in the readme."
DEPRECATION_WARNING_SETCONTEXT = "Deprecated: With v0.2.3 onwards, the optional arguments `configuration_file` & `live_config_update_enabled` of set_context method have been deprecated. " \
                                 "Use the options argument instead."
ERROR_NO_WRITE_PERMISSION = "Persistent cache directory provided does not have write permission. Make sure the directory has required access",
BOOTSTRAP_FILE_NOT_FOUND_ERROR = "Provide a valid bootstrap_file path while live_config_update_enabled is false in set_context method."
CONFIGURATION_HANDLER_INIT_ERROR = 'Invalid action in ConfigurationHandler. This action can be performed only after a ' \
                                   'successful initialization. Please check the initialization section for errors. '
CONFIGURATION_HANDLER_METHOD_ERROR = "Invalid action in ConfigurationHandler. Should be a method/function"
SINGLETON_EXCEPTION = "class must be initialized using the get_instance() method."
FEATURE_INVALID = "Invalid feature_id - "
NO_INTERNET_CONNECTION_ERROR = 'No connection to internet. Please re-connect.'
PROPERTY_INVALID = "Invalid property_id - "
CONFIGURATIONS_FETCH_SUCCESS = "Successfully fetched the configurations."
RETRY_AFTER_TWO_MINUTES = "Failed to fetch the configurations. Retrying after 2 minutes."
INPUT_PARAMETER_NOT_BOOLEAN = "Input parameter passed to use_private_endpoint() method is not boolean. Default value will be used."

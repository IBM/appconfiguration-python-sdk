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
This module defines the model of a feature flag defined in App Configuration service.
"""

from typing import Any
from ..internal.utils.logger import Logger
from ..internal.utils.validators import Validators
from .configuration_type import ConfigurationType


class Feature:
    """Feature object"""

    def __init__(self, feature_list=dict):
        """
        @type feature_list: dict
        """
        self.__enabled = feature_list.get('enabled', False)
        self.__name = feature_list.get('name', '')
        self.__feature_id = feature_list.get('feature_id', '')
        self.__segment_rules = feature_list.get('segment_rules', list())
        self.__feature_data = feature_list
        self.__type = ConfigurationType(
            feature_list.get('type') if feature_list.get('type') is not None else ConfigurationType.NUMERIC)
        self.__format = feature_list.get('format', None)
        self.__disabled_value = feature_list.get('disabled_value', object)
        self.__enabled_value = feature_list.get('enabled_value', object)
        self.__rollout_percentage = feature_list.get('rollout_percentage', 100)

    def get_feature_name(self) -> str:
        """Get the Feature name"""
        return self.__name

    def get_disabled_value(self) -> Any:
        """Get the Feature disabled value"""
        if self.__format == "YAML":
            return Validators.validate_yaml_string(self.__disabled_value)
        return self.__disabled_value

    def get_enabled_value(self) -> Any:
        """Get the Feature enabled value"""
        if self.__format == "YAML":
            return Validators.validate_yaml_string(self.__enabled_value)
        return self.__enabled_value

    def get_feature_id(self) -> str:
        """Get the Feature Id"""
        return self.__feature_id

    def get_feature_data_type(self) -> ConfigurationType:
        """Get the Feature data type"""
        return self.__type

    def get_feature_data_format(self) -> str:
        """Get the Feature data format"""
        if self.__type == ConfigurationType.STRING and self.__format is None:
            return 'TEXT'
        return self.__format

    def get_rollout_percentage(self) -> int:
        """Get the Feature flag's rollout percentage"""
        return self.__rollout_percentage

    def is_enabled(self) -> bool:
        """
        Return the state of the feature flag.
        Returns True, if the feature flag is enabled, otherwise returns False.
        """
        return self.__enabled

    def get_segment_rules(self) -> list:
        """Get the Feature segment_rules"""
        return self.__segment_rules

    def get_current_value(self, entity_id: str, entity_attributes=None) -> Any:
        """Get the evaluated value of the feature flag.

        Args:
            entity_id (str): Id of the Entity. This will be a string identifier related to the Entity against which the
            feature is evaluated. For example, an entity might be an instance of an app that runs on a mobile device,
            a microservice that runs on the cloud, or a component of infrastructure that runs that microservice. For
            any entity to interact with App Configuration, it must provide a unique entity ID.

            entity_attributes (dict): A dictionary consisting of the attribute name and their values that defines the
            specified entity. This is an optional parameter if the feature flag is not configured with any targeting
            definition. If the targeting is configured, then entity_attributes should be provided for the rule
            evaluation. An attribute is a parameter that is used to define a segment. The SDK uses the attribute values
            to determine if the specified entity satisfies the targeting rules, and returns the appropriate
            feature flag value.

        Returns:
            Returns one of the Enabled/Disabled/Overridden value based on the evaluation.
            The data type of returned value matches that of feature flag.
        """
        if not entity_id or entity_id == "":
            Logger.error("Feature flag evaluation: Invalid entity_id passed to get_current_value")
            return None
        from ibm_appconfiguration.configurations.configuration_handler import ConfigurationHandler
        feature_handler = ConfigurationHandler.get_instance()
        value, __ = feature_handler.feature_evaluation(feature=self, is_enabled=self.__enabled, entity_id=entity_id,
                                                       entity_attributes=entity_attributes)
        return value

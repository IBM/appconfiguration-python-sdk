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
from ..internal.common import config_constants
from .segment_rules import SegmentRules


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
        self.__parsed_segment_rules = self.__parse_segment_rules()
        self.__feature_data = feature_list
        self.__type = ConfigurationType(
            feature_list.get('type') if feature_list.get('type') is not None else ConfigurationType.NUMERIC)
        self.__format = feature_list.get('format', None)
        self.__disabled_value = feature_list.get('disabled_value', object)
        self.__enabled_value = feature_list.get('enabled_value', object)
        self.__rollout_type = feature_list.get('rollout_type', config_constants.MANUAL)
        if feature_list.get('rollout_configuration', None) is not None:
            self.__rollout_configuration = feature_list.get('rollout_configuration')
            self.__rollout_percentage = None
        else:
            self.__rollout_percentage = feature_list.get('rollout_percentage', 100)
            self.__rollout_configuration = None
        self.__rollout_id = feature_list.get('rollout_id', None)
        self.__metric_map = feature_list.get('metric_map', {})

    def __parse_segment_rules(self) -> list:
        """Parse the raw segment rules into SegmentRules objects sorted by order"""
        parsed_rules = []
        for rule_json in self.__segment_rules:
            try:
                parsed_rules.append(SegmentRules(rule_json))
            except Exception as err:
                Logger.debug(err)
        return sorted(parsed_rules, key=lambda rule: rule.get_order())

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

    def get_rollout_type(self) -> str:
        """Get the Feature flag's rollout type"""
        return self.__rollout_type

    def get_rollout_configuration(self) -> Any:
        """Get the Feature flag's rollout configuration"""
        return self.__rollout_configuration

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
        if not isinstance(entity_id, str) or entity_id.strip() == '':
            Logger.error("Feature flag evaluation: Invalid entity_id passed to get_current_value")
            return None
        from ibm_appconfiguration.configurations.configuration_handler import ConfigurationHandler
        feature_handler = ConfigurationHandler.get_instance()
        value, __ = feature_handler.feature_evaluation(feature=self, is_enabled=self.__enabled, entity_id=entity_id,
                                                       entity_attributes=entity_attributes)
        return value

    def get_rollout_id(self) -> str:
        """Get the rollout id for this feature if guarded is configured for this flag"""
        return self.__rollout_id if self.__rollout_id is not None else ''

    def get_metric_map(self) -> dict[str, list[dict[str, str]]]:
        """Get the metric map for this feature"""
        return self.__metric_map

    def get_matched_segment_rule(self, entity_attributes: dict):
        """Get the first segment rule (by order) whose segments match the entity attributes.

        Only matches the rules, no rollout, analytics or metering is performed.

        Args:
            entity_attributes (dict): Entity attributes object.

        Returns:
            The matching SegmentRules object, or None if no rule matches.
        """
        from ibm_appconfiguration.configurations.configuration_handler import ConfigurationHandler
        handler = ConfigurationHandler.get_instance()
        for segment_rule in self.__parsed_segment_rules:
            for rule in segment_rule.get_rules():
                for segment_key in rule.get('segments', []):
                    if handler.evaluate_segment(segment_key, entity_attributes):
                        return segment_rule
        return None

    def track(self, event_key, entity_id, entity_attributes=None):
        """Record a metric event for an entity of a guarded rollout.

        Args:
            event_key (str): Event key configured for the metric.
            entity_id (str): Id of the Entity used in get_current_value.
            entity_attributes (dict): Entity attributes used in get_current_value. If they match a segment
            rule, that rule alone decides the guarded rollout and metric map, otherwise the feature level
            guarded rollout is used.
        """
        if not isinstance(event_key, str) or event_key.strip() == '':
            Logger.error("track: eventKey must be a non-empty string")
            return
        if not isinstance(entity_id, str) or entity_id.strip() == '':
            Logger.error("track: entityId must be a non-empty string")
            return
        if entity_attributes is not None and not isinstance(entity_attributes, dict):
            Logger.error("track: entityAttributes must be a dictionary")
            return

        from ibm_appconfiguration.configurations.configuration_handler import ConfigurationHandler
        matched_rule = None
        if self.__segment_rules and entity_attributes:
            matched_rule = self.get_matched_segment_rule(entity_attributes)

        if matched_rule is not None:
            if matched_rule.get_rollout_type() != config_constants.GUARDED:
                Logger.warning("The segment rule matched for these entity attributes is not configured for guarded rollout")
                return
            metric_map = matched_rule.get_metric_map()
            rollout_id = matched_rule.get_rollout_id()
            rollout_percentage = int(matched_rule.get_rollout_percentage())

        else:
            if self.get_rollout_type() != config_constants.GUARDED:
                Logger.warning("This feature is not configured for guarded rollout")
                return
            metric_map = self.get_metric_map()
            rollout_id = self.get_rollout_id()
            rollout_percentage = self.get_rollout_percentage()

        if event_key not in metric_map:
            Logger.warning(f'The event key:{event_key} was not found for this feature:{self.get_feature_id()}')
            return

        ConfigurationHandler.get_instance().add_guarded_metric_entry(
            entity_id,
            self.get_feature_id(),
            rollout_id,
            event_key,
            metric_map[event_key],
            rollout_percentage
        )
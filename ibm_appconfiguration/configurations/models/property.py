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
This module defines the model of a Property defined in App Configuration service.
"""

from typing import Any
from ..internal.utils.logger import Logger
from ..internal.utils.validators import Validators
from .configuration_type import ConfigurationType


class Property:
    """Property object"""
    def __init__(self, property_list=dict):
        """
        @type property_list: dict
        """
        self.__name = property_list.get('name', '')
        self.__property_id = property_list.get('property_id', '')
        self.__segment_rules = property_list.get('segment_rules', list())
        self.__property_data = property_list
        self.__type = ConfigurationType(property_list.get('type') if property_list.get('type') is not None else ConfigurationType.NUMERIC)
        self.__format = property_list.get('format', None)
        self.__value = property_list.get('value', object)

    def get_property_name(self) -> str:
        """Get the Property name

        Returns:
            Return the Property name
        """
        return self.__name

    def get_value(self) -> Any:
        """Get the Property value

        Returns:
            Return the Property value
        """
        if self.__format == "YAML":
            return Validators.validate_yaml_string(self.__value)
        return self.__value

    def get_property_id(self) -> str:
        """Get the Property Id

        Returns:
            Return the Property Id
        """
        return self.__property_id

    def get_property_data_type(self) -> ConfigurationType:
        """Get the Property data type

        Returns:
            Return the Property data type
        """
        return self.__type

    def get_property_data_format(self) -> str:
        """Get the Property format type

        Returns:
            Return the Property format type
        """
        if self.__type == ConfigurationType.STRING and self.__format is None:
            return 'TEXT'
        return self.__format

    def get_segment_rules(self) -> list:
        """Get the Property segment rules

        Returns:
            Return the list of Property segment rules
        """
        return self.__segment_rules

    def get_current_value(self, entity_id: str, entity_attributes: {}) -> Any:
        """Get the evaluated value of the Property

        Args:
            entity_id: Id of the Entity
            entity_attributes: Entity attributes object
        Returns:
            Return the evaluated Property value
        """

        if not entity_id or entity_id == "":
            Logger.error("A valid entity id should be passed for this method.")
            return None
        from ibm_appconfiguration.configurations.configuration_handler import ConfigurationHandler
        configuration_handler = ConfigurationHandler.get_instance()
        return configuration_handler.property_evaluation(property_obj=self, entity_id=entity_id,
                                                         entity_attributes=entity_attributes)

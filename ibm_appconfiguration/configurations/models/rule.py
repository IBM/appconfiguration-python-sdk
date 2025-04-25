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
This module defines the model of a rule defined for a segment in App Configuration service.
"""

from typing import Tuple


class Rule:
    """
        Attributes:
           rules (dict): rules JSON object that contains all the Rules.
    """

    def __init__(self, rules: {}):
        self.__attribute_name = rules.get("attribute_name", "")
        self.__operator = rules.get("operator", "")
        self.__values = rules.get("values", list())

    def get_attributes(self) -> str:
        """Get the Rule attributes"""
        return self.__attribute_name

    def get_operator(self) -> str:
        """Get the Rule operator"""
        return self.__operator

    def get_values(self) -> list:
        """Get the Rule values"""
        return self.__values

    def __ends_with(self, key, value) -> bool:
        return key.endswith(value)

    def __not_ends_with(self, key, value) -> bool:
        return not key.endswith(value)

    def __starts_with(self, key, value) -> bool:
        return key.startswith(value)

    def __not_starts_with(self, key, value) -> bool:
        return not key.startswith(value)

    def __contains(self, key, value) -> bool:
        return value in key

    def __not_contains(self, key, value) -> bool:
        return not value in key

    def __is(self, key, value) -> bool:
        if type(key) is type(value):
            return key == value
        return str(key) == str(value)

    def __is_not(self, key, value) -> bool:
        if type(key) is type(value):
            return key != value
        return str(key) != str(value)

    def __greater_than(self, key, value) -> bool:

        key_obj = self.__number_conversion(key)
        value_obj = self.__number_conversion(value)

        if key_obj[0] and value_obj[0]:
            return key_obj[1] > value_obj[1]
        return False

    def __lesser_than(self, key, value) -> bool:
        key_obj = self.__number_conversion(key)
        value_obj = self.__number_conversion(value)

        if key_obj[0] and value_obj[0]:
            return key_obj[1] < value_obj[1]
        return False

    def __greater_than_equals(self, key, value) -> bool:
        key_obj = self.__number_conversion(key)
        value_obj = self.__number_conversion(value)

        if key_obj[0] and value_obj[0]:
            return key_obj[1] >= value_obj[1]
        return False

    def __lesser_than_equals(self, key, value) -> bool:
        key_obj = self.__number_conversion(key)
        value_obj = self.__number_conversion(value)

        if key_obj[0] and value_obj[0]:
            return key_obj[1] <= value_obj[1]
        return False

    def __operator_check(self, key_data=None, value_data=None) -> bool:
        key = key_data
        value = value_data

        result = False

        if key is None or value is None:
            return result

        case_checker = {
            "endsWith": self.__ends_with,
            "notEndsWith": self.__not_ends_with,
            "startsWith": self.__starts_with,
            "notStartsWith": self.__not_starts_with,
            "contains": self.__contains,
            "notContains": self.__not_contains,
            "is": self.__is,
            "isNot": self.__is_not,
            "greaterThan": self.__greater_than,
            "lesserThan": self.__lesser_than,
            "greaterThanEquals": self.__greater_than_equals,
            "lesserThanEquals": self.__lesser_than_equals
        }
        return case_checker.get(self.__operator, False)(key, value)

    def __number_conversion(self, value) -> Tuple[bool, float]:
        if isinstance(value, bool):
            return False, 0
        if isinstance(float(value), float):
            return True, float(value)
        return False, 0

    def evaluate_rule(self, entity_attributes: dict) -> bool:
        """Evaluate the the Rule

        Args:
            entity_attributes: Entity attributes object
        """
        result = False
        if self.__attribute_name in entity_attributes:
            key = entity_attributes.get(self.__attribute_name)
        else:
            return result

        if self.__operator in ["isNot", "notContains", "notStartsWith", "notEndsWith"]:
            result = True
            for i in range(0, len(self.__values)):
                value = self.__values[i]
                if not self.__operator_check(key, value):
                    result = False
        else:
            for i in range(0, len(self.__values)):
                value = self.__values[i]
                if self.__operator_check(key, value):
                    result = True

        return result

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
This module defines the model of a segment rule defined in App Configuration service.
"""

from ..internal.common import config_constants


class SegmentRules:
    """
       Attributes:
        segment_rules (dict): segment_rules JSON object that contains all the SegmentRules
   """

    def __init__(self, segment_rules: {}):
        self.__order = segment_rules.get("order", 1)
        self.__value = segment_rules.get("value", object)
        self.__rules = segment_rules.get("rules", list())
        self.__rule_id = segment_rules.get("rule_id", None)
        self.__rollout_type = segment_rules.get("rollout_type", config_constants.MANUAL)
        if segment_rules.get("rollout_configuration", None) is not None:
            self.__rollout_configuration = segment_rules.get("rollout_configuration")
            self.__rollout_percentage = None
        else:
            self.__rollout_percentage = segment_rules.get("rollout_percentage", 100)
            self.__rollout_configuration = None

    def get_order(self) -> int:
        """Get the SegmentRule order"""
        return self.__order

    def get_rules(self) -> list:
        """Get the SegmentRule rules list"""
        return self.__rules

    def get_value(self):
        """Get the SegmentRule value"""
        return self.__value

    def get_rollout_percentage(self) -> int:
        """Get the rollout percentage for SegmentRule"""
        return self.__rollout_percentage
    
    def get_rule_id(self) -> str:
        """Get the rule ID for SegmentRule"""
        return self.__rule_id
    
    def get_rollout_type(self) -> str:
        """Get the rollout type for SegmentRule"""
        return self.__rollout_type
    
    def get_rollout_configuration(self) -> dict:
        """Get the rollout configuration for SegmentRule"""
        return self.__rollout_configuration

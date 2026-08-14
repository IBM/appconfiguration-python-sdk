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
This module defines the model of a segment defined in App Configuration service.
"""

from ..internal.utils.logger import Logger
from .rule import Rule


class Segment:
    """
      Attributes:
         segment_rules (dict): segments JSON object that contains all the Segments
   """

    def __init__(self, segments: {}):
        self.__name = segments.get("name", "")
        self.__segment_id = segments.get("segment_id", "")
        self.__rules = segments.get("rules", list())

    def get_name(self) -> str:
        """Get the Segment name"""
        return self.__name

    def get_segment_id(self) -> str:
        """Get the Segment Id"""
        return self.__segment_id

    def get_rules(self) -> list:
        """Get the Segment rules"""
        return self.__rules

    def evaluate_rule(self, entity_attributes: dict) -> bool:
        """Evaluate the Segment rules

        Args:
            entity_attributes: Entity attributes object
        """
        for index in range(0, len(self.__rules)):
            try:
                dict_sec = self.__rules[index]
                rule = Rule(dict_sec)

                if not rule.evaluate_rule(entity_attributes):
                    return False
            except Exception as exception:
                Logger.debug(f'Invalid action in Segment class, {exception}')
                return False
        return True

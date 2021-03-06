# (C) Copyright IBM Corp. 2021.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.

from .rule import Rule
from ibm_appconfiguration.core.internal import Logger


class Segment:
    """
      Attributes:
         segment_rules (dict): segments JSON object that contains all the Segments
   """

    def __init__(self, segments=dict()):
        self.__name = segments.get("name", "")
        self.__segment_id = segments.get("segment_id", "")
        self.__rules = segments.get("rules", list())

    def get_name(self) -> str:
        return self.__name

    def get_segment_id(self) -> str:
        return self.__segment_id

    def get_rules(self) -> list:
        return self.__rules

    def evaluate_rule(self, identity_attributes: dict) -> bool:
        for index in range(0, len(self.__rules)):
            try:
                dict_sec = self.__rules[index]
                rule = Rule(dict_sec)

                if not rule.evaluate_rule(identity_attributes):
                    return False
            except:
                Logger.debug('Invalid action in Segment class.')
        return True

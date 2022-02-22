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
This module provides methods to perform the input validations.
"""
import yaml
from schema import Schema, Optional, SchemaError, And
from .logger import Logger


class Validators:
    """Validator class"""

    @classmethod
    def validate_string(cls, value: str) -> bool:
        """Validate the string

        Args:
            value: value to be checked
        """
        return bool(value and value.strip())

    @classmethod
    def validate_yaml_string(cls, value: str):
        """Validate the yaml string and returns parsed yaml

        Args:
            value: yaml string to be checked and parsed
        """
        try:
            parsed_values = list(yaml.safe_load_all(value))
            if len(parsed_values) == 1:
                return parsed_values[0]
            return parsed_values
        except Exception as err:
            Logger.error("Error while parsing yaml string")
            Logger.error(err)
            return None

    @classmethod
    def validate_set_context_options(cls, options) -> bool:
        """Validates the options

        Args:
            options: optional keys to be checked
        """
        try:
            Schema({
                Optional('persistent_cache_dir'): And(str, lambda s: len(s) > 0),
                Optional('bootstrap_file'): And(str, lambda s: len(s) > 0),
                Optional('live_config_update_enabled'): bool
            }).validate(options)
            return True
        except SchemaError:
            return False

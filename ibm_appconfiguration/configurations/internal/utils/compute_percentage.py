# Copyright 2022 IBM All Rights Reserved.
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
This module contains the methods related to string hashing
"""

import mmh3


def compute_hash(string: str):
    seed = 0
    return mmh3.hash(key=string, seed=seed, signed=False)


def get_normalized_value(string: str) -> int:
    max_hash_value = pow(2, 32)
    normalizer = 100
    return int((compute_hash(string) / max_hash_value) * normalizer)

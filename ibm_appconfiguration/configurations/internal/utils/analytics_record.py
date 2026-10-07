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
This module provides methods that perform analytics related operations.
"""
from copy import deepcopy
from enum import Enum
from typing import Any

from ibm_appconfiguration.configurations.internal.common.config_constants import DELIMITER


class EventType(Enum):
    GUARDED_METRIC = 1
    GUARDED_EVALUATION = 2


class AnalyticsRecord:
    """In-memory store for analytics usages.

    NOT thread-safe on its own. All concurrent access must be serialised
    by the caller (Analytics) holding its own lock before calling any method.
    """

    def __init__(self):
        self._usages: list[dict[str, Any]] = []
        self._history_map: dict[str, int] = {}

    @staticmethod
    def _build_key(*args) -> str:
        return DELIMITER.join(args)

    @staticmethod
    def _build_metric_key(metric: dict[str, Any], metric_type: EventType) -> str:
        match metric_type:
            case EventType.GUARDED_EVALUATION:
                return AnalyticsRecord._build_key(
                    metric["rollout_id"],
                    metric["entity_id"],
                    metric["value_served"],
                )
            case EventType.GUARDED_METRIC:
                return AnalyticsRecord._build_key(
                    metric["rollout_id"],
                    metric["entity_id"],
                    metric["value_served"],
                    metric["event_key"],
                )
            case _:
                raise ValueError(f"Unsupported metric type: {metric_type}")

    def _insert_or_create_record(self, index: int, metric: dict[str, Any], metric_type: EventType):
        # Attach the metadata block.
        match metric_type:
            case EventType.GUARDED_EVALUATION:
                metric["metadata"] = {"feature": "guarded", "event_type": "evaluation"}
            case EventType.GUARDED_METRIC:
                metric["metadata"] = {"feature": "guarded", "event_type": "metric"}

        if index == -1:
            # New entry.
            if metric_type == EventType.GUARDED_METRIC:
                metric["count"] = 1
            self._usages.append(metric)
            self._history_map[self._build_metric_key(metric, metric_type)] = len(self._usages) - 1
            return

        # Existing entry — only metric types are aggregated (count + latest timestamp).
        if metric_type == EventType.GUARDED_METRIC:
            self._usages[index]["count"] += 1
            self._usages[index]["timestamp"] = max(self._usages[index]["timestamp"], metric["timestamp"])

    def add(self, metric: dict[str, Any], metric_type: EventType):
        key = self._build_metric_key(metric, metric_type)
        self._insert_or_create_record(self._history_map.get(key, -1), metric, metric_type)

    def get_request_body(self, environment_id: str, collection_id: str) -> dict[str, Any]:
        usages = []
        for usage in self._usages:
            usage_copy = deepcopy(usage)
            usage_copy.pop('event_key', None)
            usages.append(usage_copy)
        return {
            "environment_id": environment_id,
            "collection_id": collection_id,
            "usages": usages,
        }

    def __len__(self) -> int:
        return len(self._usages)

    def get_record_length(self) -> int:
        return len(self._usages)

    def exceeds_limit(self, limit: int) -> bool:
        return len(self._usages) >= limit

    def split_head(self, n: int) -> 'AnalyticsRecord':
        """Remove and return the first *n* usages as a new AnalyticsRecord.

        The caller must hold the outer Analytics lock before calling this.
        Insertion order is preserved — oldest entries are returned first.
        """
        head = AnalyticsRecord()
        head._usages = self._usages[:n]
        for i, usage in enumerate(head._usages):
            metric_type = AnalyticsRecord._get_metric_type(usage)
            key = AnalyticsRecord._build_metric_key(usage, metric_type)
            head._history_map[key] = i

        self._usages = self._usages[n:]
        self._history_map = {}
        for i, usage in enumerate(self._usages):
            metric_type = AnalyticsRecord._get_metric_type(usage)
            key = AnalyticsRecord._build_metric_key(usage, metric_type)
            self._history_map[key] = i

        return head

    @staticmethod
    def _get_metric_type(metric: dict[str, Any]) -> EventType:
        feature = metric["metadata"]["feature"]
        event_type = metric["metadata"]["event_type"]
        return EventType.GUARDED_EVALUATION if event_type == "evaluation" else EventType.GUARDED_METRIC

    def merge(self, other: 'AnalyticsRecord'):
        """Merge all usages from *other* into self.

        The caller must hold the outer Analytics lock before calling this.
        """
        if not isinstance(other, AnalyticsRecord):
            return
        for usage in other._usages:
            metric_type = AnalyticsRecord._get_metric_type(usage)
            key = self._build_metric_key(usage, metric_type)
            index = self._history_map.get(key, -1)
            if index == -1:
                self._usages.append(usage)
                self._history_map[key] = len(self._usages) - 1
            elif metric_type == EventType.GUARDED_METRIC:
                self._usages[index]["count"] += usage["count"]
                self._usages[index]["timestamp"] = max(
                    self._usages[index]["timestamp"], usage["timestamp"]
                )

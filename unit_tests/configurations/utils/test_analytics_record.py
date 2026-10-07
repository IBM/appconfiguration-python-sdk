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

import unittest
from ibm_appconfiguration.configurations.internal.utils.analytics_record import AnalyticsRecord, EventType


def make_guarded_eval(rollout_id, entity_id, value_served):
    return {"rollout_id": rollout_id, "entity_id": entity_id, "value_served": value_served}


def make_guarded_metric(rollout_id, entity_id, value_served, event_key, timestamp="2024-01-01T00:00:00Z"):
    return {"rollout_id": rollout_id, "entity_id": entity_id,
            "value_served": value_served, "event_key": event_key, "timestamp": timestamp}


class TestAnalyticsRecordGuardedEvaluation(unittest.TestCase):

    def test_add_new_evaluation_entry(self):
        record = AnalyticsRecord()
        record.add(make_guarded_eval("rid-1", "u17", "target"), EventType.GUARDED_EVALUATION)
        self.assertEqual(record.get_record_length(), 1)

    def test_deduplicates_identical_evaluation_entries(self):
        record = AnalyticsRecord()
        record.add(make_guarded_eval("rid-1", "u17", "target"), EventType.GUARDED_EVALUATION)
        record.add(make_guarded_eval("rid-1", "u17", "target"), EventType.GUARDED_EVALUATION)
        self.assertEqual(record.get_record_length(), 1)

    def test_target_and_original_are_distinct_entries(self):
        record = AnalyticsRecord()
        record.add(make_guarded_eval("rid-1", "u1", "target"), EventType.GUARDED_EVALUATION)
        record.add(make_guarded_eval("rid-1", "u1", "original"), EventType.GUARDED_EVALUATION)
        self.assertEqual(record.get_record_length(), 2)

    def test_different_entity_ids_are_distinct(self):
        record = AnalyticsRecord()
        record.add(make_guarded_eval("rid-1", "u17", "target"), EventType.GUARDED_EVALUATION)
        record.add(make_guarded_eval("rid-1", "u19", "target"), EventType.GUARDED_EVALUATION)
        self.assertEqual(record.get_record_length(), 2)

    def test_stamps_correct_metadata_on_evaluation(self):
        record = AnalyticsRecord()
        record.add(make_guarded_eval("rid-1", "u17", "target"), EventType.GUARDED_EVALUATION)
        body = record.get_request_body("env-1", "col-1")
        self.assertEqual(body["usages"][0]["metadata"],
                         {"feature": "guarded", "event_type": "evaluation"})

    def test_evaluation_entry_has_no_count_field(self):
        record = AnalyticsRecord()
        record.add(make_guarded_eval("rid-1", "u17", "target"), EventType.GUARDED_EVALUATION)
        body = record.get_request_body("env-1", "col-1")
        self.assertNotIn("count", body["usages"][0])


class TestAnalyticsRecordGuardedMetric(unittest.TestCase):

    def test_add_new_metric_entry_with_count_one(self):
        record = AnalyticsRecord()
        record.add(make_guarded_metric("rid-1", "u17", "target", "click"), EventType.GUARDED_METRIC)
        body = record.get_request_body("env-1", "col-1")
        self.assertEqual(body["usages"][0]["count"], 1)

    def test_aggregates_count_on_duplicate_metrics(self):
        record = AnalyticsRecord()
        record.add(make_guarded_metric("rid-1", "u17", "target", "click"), EventType.GUARDED_METRIC)
        record.add(make_guarded_metric("rid-1", "u17", "target", "click"), EventType.GUARDED_METRIC)
        body = record.get_request_body("env-1", "col-1")
        self.assertEqual(body["usages"][0]["count"], 2)
        self.assertEqual(len(body["usages"]), 1)

    def test_different_event_keys_are_distinct(self):
        record = AnalyticsRecord()
        record.add(make_guarded_metric("rid-1", "u17", "target", "click"), EventType.GUARDED_METRIC)
        record.add(make_guarded_metric("rid-1", "u17", "target", "purchase"), EventType.GUARDED_METRIC)
        self.assertEqual(record.get_record_length(), 2)

    def test_stamps_correct_metadata_on_metric(self):
        record = AnalyticsRecord()
        record.add(make_guarded_metric("rid-1", "u17", "target", "click"), EventType.GUARDED_METRIC)
        body = record.get_request_body("env-1", "col-1")
        self.assertEqual(body["usages"][0]["metadata"],
                         {"feature": "guarded", "event_type": "metric"})


class TestAnalyticsRecordGetRequestBody(unittest.TestCase):

    def test_returns_correct_envelope(self):
        record = AnalyticsRecord()
        record.add(make_guarded_eval("rid-1", "u17", "target"), EventType.GUARDED_EVALUATION)
        body = record.get_request_body("my-env", "my-col")
        self.assertEqual(body["environment_id"], "my-env")
        self.assertEqual(body["collection_id"], "my-col")
        self.assertIsInstance(body["usages"], list)

    def test_strips_event_key_from_usages_in_body(self):
        record = AnalyticsRecord()
        record.add(make_guarded_metric("rid-1", "u17", "target", "click"), EventType.GUARDED_METRIC)
        body = record.get_request_body("env-1", "col-1")
        self.assertNotIn("event_key", body["usages"][0])

    def test_does_not_mutate_internal_state_when_stripping_event_key(self):
        record = AnalyticsRecord()
        record.add(make_guarded_metric("rid-1", "u17", "target", "click"), EventType.GUARDED_METRIC)
        record.get_request_body("env-1", "col-1")  # strip once
        # add again — dedup must still work (internal event_key still present)
        record.add(make_guarded_metric("rid-1", "u17", "target", "click"), EventType.GUARDED_METRIC)
        body = record.get_request_body("env-1", "col-1")
        self.assertEqual(body["usages"][0]["count"], 2)


class TestAnalyticsRecordGetRecordLength(unittest.TestCase):

    def test_returns_zero_on_new_record(self):
        self.assertEqual(AnalyticsRecord().get_record_length(), 0)

    def test_returns_correct_count_after_distinct_adds(self):
        record = AnalyticsRecord()
        record.add(make_guarded_eval("rid-1", "u17", "target"), EventType.GUARDED_EVALUATION)
        record.add(make_guarded_eval("rid-1", "u1", "original"), EventType.GUARDED_EVALUATION)
        record.add(make_guarded_metric("rid-1", "u17", "target", "click"), EventType.GUARDED_METRIC)
        self.assertEqual(record.get_record_length(), 3)


class TestAnalyticsRecordMerge(unittest.TestCase):

    def test_merges_entries_from_another_record(self):
        a = AnalyticsRecord()
        a.add(make_guarded_eval("rid-1", "u17", "target"), EventType.GUARDED_EVALUATION)
        b = AnalyticsRecord()
        b.add(make_guarded_eval("rid-1", "u19", "target"), EventType.GUARDED_EVALUATION)
        a.merge(b)
        self.assertEqual(a.get_record_length(), 2)

    def test_aggregates_counts_for_overlapping_metrics_during_merge(self):
        a = AnalyticsRecord()
        a.add(make_guarded_metric("rid-1", "u17", "target", "click"), EventType.GUARDED_METRIC)
        b = AnalyticsRecord()
        b.add(make_guarded_metric("rid-1", "u17", "target", "click"), EventType.GUARDED_METRIC)
        b.add(make_guarded_metric("rid-1", "u17", "target", "click"), EventType.GUARDED_METRIC)
        a.merge(b)
        self.assertEqual(a.get_record_length(), 1)
        self.assertEqual(a.get_request_body("e", "c")["usages"][0]["count"], 3)

    def test_ignores_non_analytics_record_values_silently(self):
        a = AnalyticsRecord()
        a.add(make_guarded_eval("rid-1", "u17", "target"), EventType.GUARDED_EVALUATION)
        a.merge(None)
        a.merge({})
        self.assertEqual(a.get_record_length(), 1)

    def test_does_not_add_duplicate_evaluation_entries_during_merge(self):
        a = AnalyticsRecord()
        a.add(make_guarded_eval("rid-1", "u17", "target"), EventType.GUARDED_EVALUATION)
        b = AnalyticsRecord()
        b.add(make_guarded_eval("rid-1", "u17", "target"), EventType.GUARDED_EVALUATION)
        a.merge(b)
        self.assertEqual(a.get_record_length(), 1)


class TestAnalyticsRecordExceedsLimit(unittest.TestCase):

    def test_returns_false_when_below_limit(self):
        record = AnalyticsRecord()
        record.add(make_guarded_eval("rid-1", "u1", "target"), EventType.GUARDED_EVALUATION)
        self.assertFalse(record.exceeds_limit(30))

    def test_returns_true_when_at_limit(self):
        record = AnalyticsRecord()
        for i in range(30):
            record.add(make_guarded_eval("rid-1", f"u{i}", "target"), EventType.GUARDED_EVALUATION)
        self.assertTrue(record.exceeds_limit(30))

    def test_returns_true_when_above_limit(self):
        record = AnalyticsRecord()
        for i in range(35):
            record.add(make_guarded_eval("rid-1", f"u{i}", "target"), EventType.GUARDED_EVALUATION)
        self.assertTrue(record.exceeds_limit(30))

    def test_returns_false_on_empty_record(self):
        self.assertFalse(AnalyticsRecord().exceeds_limit(30))


class TestAnalyticsRecordSplitHead(unittest.TestCase):

    def _make_record(self, count):
        record = AnalyticsRecord()
        for i in range(count):
            record.add(make_guarded_eval("rid-1", f"u{i}", "target"), EventType.GUARDED_EVALUATION)
        return record

    def test_head_has_n_entries(self):
        record = self._make_record(35)
        head = record.split_head(30)
        self.assertEqual(head.get_record_length(), 30)

    def test_remainder_has_correct_entries(self):
        record = self._make_record(35)
        record.split_head(30)
        self.assertEqual(record.get_record_length(), 5)

    def test_head_contains_oldest_entries_in_order(self):
        record = self._make_record(35)
        head = record.split_head(30)
        body = head.get_request_body("e", "c")
        entity_ids = [u["entity_id"] for u in body["usages"]]
        self.assertEqual(entity_ids, [f"u{i}" for i in range(30)])

    def test_remainder_contains_newest_entries_in_order(self):
        record = self._make_record(35)
        record.split_head(30)
        body = record.get_request_body("e", "c")
        entity_ids = [u["entity_id"] for u in body["usages"]]
        self.assertEqual(entity_ids, [f"u{i}" for i in range(30, 35)])

    def test_remainder_deduplication_still_works_after_split(self):
        """history_map must be rebuilt correctly so new adds still deduplicate."""
        record = self._make_record(35)
        record.split_head(30)
        # u30 is already in the remainder — adding it again must NOT grow the record.
        record.add(make_guarded_eval("rid-1", "u30", "target"), EventType.GUARDED_EVALUATION)
        self.assertEqual(record.get_record_length(), 5)

    def test_head_deduplication_still_works_after_split(self):
        """history_map in head must be intact so head behaves as a normal record."""
        record = self._make_record(35)
        head = record.split_head(30)
        # u0 is in the head — adding it again must NOT grow the head.
        head.add(make_guarded_eval("rid-1", "u0", "target"), EventType.GUARDED_EVALUATION)
        self.assertEqual(head.get_record_length(), 30)

    def test_split_entire_record(self):
        record = self._make_record(10)
        head = record.split_head(10)
        self.assertEqual(head.get_record_length(), 10)
        self.assertEqual(record.get_record_length(), 0)

    def test_split_produces_independent_records(self):
        """Mutating the head must not affect the remainder and vice-versa."""
        record = self._make_record(35)
        head = record.split_head(30)
        # Add a new entry to the remainder.
        record.add(make_guarded_eval("rid-2", "new", "target"), EventType.GUARDED_EVALUATION)
        # The head must be unaffected.
        self.assertEqual(head.get_record_length(), 30)
        self.assertFalse(any(
            u["entity_id"] == "new"
            for u in head.get_request_body("e", "c")["usages"]
        ))


if __name__ == "__main__":
    unittest.main()

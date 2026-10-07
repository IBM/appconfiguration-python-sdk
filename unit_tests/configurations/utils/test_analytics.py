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
from unittest.mock import patch, MagicMock
from ibm_appconfiguration.configurations.internal.utils.analytics import Analytics
from ibm_appconfiguration.configurations.internal.utils.analytics_record import AnalyticsRecord, EventType

# ── helpers ───────────────────────────────────────────────────────────────────

def make_guarded_eval(rollout_id="rid-1", entity_id="u1"):
    return {"rollout_id": rollout_id, "entity_id": entity_id, "value_served": "target"}


def fill_record(analytics, count=30):
    """Push *count* distinct entries into the analytics record."""
    for i in range(count):
        analytics.add_metric(make_guarded_eval("rid-1", f"u{i}"), EventType.GUARDED_EVALUATION)


SEND_TO_SERVER = "_Analytics__send_to_server"
SEND_ANALYTIC_JOB = "_Analytics__send_analytic_job"
FLUSH_EVENT = "_Analytics__flush_event"


class AnalyticsJobTest(unittest.TestCase):

    def setUp(self):
        Analytics._Analytics__instance = None
        self.analytics = Analytics.get_instance()
        self.analytics.set_context("env-1", "col-1")

    def tearDown(self):
        Analytics._Analytics__instance = None

    # ── helper: run the job loop synchronously ────────────────────────────────

    def _run_drain_chunks(self, response_sequence):
        """
        Call __drain_chunks() directly with a mocked __send_to_server.
        Returns the list of AnalyticsRecord batches passed to __send_to_server.
        """
        sent = []
        idx = [0]

        def send_side_effect(record, previous_delay=0):
            sent.append(record)
            result = response_sequence[idx[0]]
            idx[0] = min(idx[0] + 1, len(response_sequence) - 1)
            return result

        with patch.object(self.analytics, SEND_TO_SERVER, side_effect=send_side_effect):
            # __flush_event.wait must not block — patch it to return immediately.
            self.analytics._Analytics__flush_event.set()
            self.analytics._Analytics__drain_chunks()

        return sent

    # ── start / stop ──────────────────────────────────────────────────────────

    def test_start_sets_job_flag(self):
        self.analytics.start()
        self.assertTrue(self.analytics._Analytics__job_flag)
        self.analytics.stop()

    def test_start_twice_does_not_launch_second_job(self):
        self.analytics.start()
        flag_before = self.analytics._Analytics__job_flag
        self.analytics.start()
        self.assertEqual(self.analytics._Analytics__job_flag, flag_before)
        self.analytics.stop()

    def test_stop_clears_job_flag(self):
        self.analytics._Analytics__job_flag = True
        self.analytics.stop()
        self.assertFalse(self.analytics._Analytics__job_flag)

    def test_stop_sets_flush_event_to_unblock_thread(self):
        self.analytics._Analytics__job_flag = True
        self.analytics._Analytics__flush_event.clear()
        self.analytics.stop()
        self.assertTrue(self.analytics._Analytics__flush_event.is_set())

    # ── add_metric sets flush event when limit is reached ────────────────────

    def test_add_metric_sets_flush_event_on_30th_entry(self):
        self.analytics._Analytics__flush_event.clear()
        # 29 entries — event must NOT be set yet.
        fill_record(self.analytics, 29)
        self.assertFalse(self.analytics._Analytics__flush_event.is_set())
        # 30th entry — event MUST be set.
        self.analytics.add_metric(make_guarded_eval("rid-1", "u29"), EventType.GUARDED_EVALUATION)
        self.assertTrue(self.analytics._Analytics__flush_event.is_set())

    def test_add_metric_does_not_set_flush_event_below_limit(self):
        self.analytics._Analytics__flush_event.clear()
        fill_record(self.analytics, 5)
        self.assertFalse(self.analytics._Analytics__flush_event.is_set())

    # ── drain_chunks: batch splitting ─────────────────────────────────────────

    def test_drain_sends_one_batch_of_30_when_exactly_30_entries(self):
        fill_record(self.analytics, 30)
        sent = self._run_drain_chunks([0])
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0].get_record_length(), 30)

    def test_drain_sends_two_batches_for_60_entries(self):
        fill_record(self.analytics, 60)
        sent = self._run_drain_chunks([0, 0])
        self.assertEqual(len(sent), 2)
        self.assertEqual(sent[0].get_record_length(), 30)
        self.assertEqual(sent[1].get_record_length(), 30)

    def test_drain_sends_two_batches_for_45_entries_leaving_15_in_record(self):
        # 45 entries → first batch of 30 sent, 15 remain (below limit → stop draining).
        fill_record(self.analytics, 45)
        sent = self._run_drain_chunks([0, 0])
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0].get_record_length(), 30)
        # 15 entries remain in the live record for the 5-min flusher.
        self.assertEqual(self.analytics._Analytics__record.get_record_length(), 15)

    def test_drain_sends_oldest_entries_first(self):
        """Insertion order must be preserved — lower-index entries go out first."""
        fill_record(self.analytics, 35)
        sent = self._run_drain_chunks([0])
        body = sent[0].get_request_body("e", "c")
        entity_ids = [u["entity_id"] for u in body["usages"]]
        # Oldest 30: u0 … u29 (in insertion order).
        self.assertEqual(entity_ids, [f"u{i}" for i in range(30)])

    def test_drain_stops_when_record_drops_below_30(self):
        fill_record(self.analytics, 31)
        sent = self._run_drain_chunks([0])
        # Only one batch of 30; the remaining 1 entry stays in the record.
        self.assertEqual(len(sent), 1)
        self.assertEqual(self.analytics._Analytics__record.get_record_length(), 1)

    # ── retry inside __send_batch ─────────────────────────────────────────────

    def test_retries_after_failure_and_succeeds_on_second_attempt(self):
        fill_record(self.analytics, 30)
        sent = self._run_drain_chunks([60, 0])
        self.assertEqual(len(sent), 2)

    def test_failed_batch_is_merged_back_before_retry(self):
        """After a failure the detached batch is merged back so no data is lost."""
        fill_record(self.analytics, 30)
        lengths = []

        def send_side_effect(record, previous_delay=0):
            lengths.append(record.get_record_length())
            return 60 if len(lengths) == 1 else 0

        with patch.object(self.analytics, SEND_TO_SERVER, side_effect=send_side_effect):
            self.analytics._Analytics__flush_event.set()
            self.analytics._Analytics__drain_chunks()

        self.assertEqual(len(lengths), 2)
        # Both attempts carry the same 30 entries.
        self.assertEqual(lengths[0], lengths[1])
        self.assertEqual(lengths[0], 30)

    def test_metrics_added_during_retry_are_included_in_next_attempt(self):
        """Entries added while waiting for retry must appear in the next batch."""
        fill_record(self.analytics, 30)
        sent = []

        def send_side_effect(record, previous_delay=0):
            sent.append(record)
            if len(sent) == 1:
                # Simulate a new metric arriving during the retry wait.
                self.analytics.add_metric(
                    make_guarded_eval("rid-extra", "extra"), EventType.GUARDED_EVALUATION
                )
                return 60
            return 0

        with patch.object(self.analytics, SEND_TO_SERVER, side_effect=send_side_effect):
            self.analytics._Analytics__flush_event.set()
            self.analytics._Analytics__drain_chunks()

        self.assertEqual(len(sent), 2)
        second_body = sent[1].get_request_body("e", "c")["usages"]
        self.assertTrue(any(
            u.get("rollout_id") == "rid-extra" and u.get("entity_id") == "extra"
            for u in second_body
        ))

    def test_exponential_backoff_sequence_is_60_120_240_480_600(self):
        fill_record(self.analytics, 30)
        wait_calls = []
        send_call_count = [0]
        delays = [60, 120, 240, 480, 600, 0]

        def send_side_effect(record, previous_delay=0):
            result = delays[min(send_call_count[0], len(delays) - 1)]
            send_call_count[0] += 1
            return result

        def event_wait_side_effect(timeout=None):
            if timeout and timeout > 0:
                wait_calls.append(timeout)
            return False  # simulate timeout (event not set)

        with patch.object(self.analytics, SEND_TO_SERVER, side_effect=send_side_effect), \
             patch.object(self.analytics._Analytics__flush_event, 'wait',
                          side_effect=event_wait_side_effect):
            self.analytics._Analytics__drain_chunks()

        self.assertEqual(wait_calls, [60, 120, 240, 480, 600])

    def test_backoff_is_capped_at_600(self):
        fill_record(self.analytics, 30)
        wait_calls = []
        send_call_count = [0]
        delays = [60, 120, 240, 480, 600, 600, 0]

        def send_side_effect(record, previous_delay=0):
            result = delays[min(send_call_count[0], len(delays) - 1)]
            send_call_count[0] += 1
            return result

        def event_wait_side_effect(timeout=None):
            if timeout and timeout > 0:
                wait_calls.append(timeout)
            return False

        with patch.object(self.analytics, SEND_TO_SERVER, side_effect=send_side_effect), \
             patch.object(self.analytics._Analytics__flush_event, 'wait',
                          side_effect=event_wait_side_effect):
            self.analytics._Analytics__drain_chunks()

        self.assertEqual(wait_calls[-1], 600)
        self.assertEqual(len(wait_calls), 6)

    def test_429_retry_delay_is_30_seconds(self):
        fill_record(self.analytics, 30)
        wait_calls = []
        responses = iter([30, 0])

        def send_side_effect(record, previous_delay=0):
            return next(responses)

        def event_wait_side_effect(timeout=None):
            if timeout and timeout > 0:
                wait_calls.append(timeout)
            return False

        with patch.object(self.analytics, SEND_TO_SERVER, side_effect=send_side_effect), \
             patch.object(self.analytics._Analytics__flush_event, 'wait',
                          side_effect=event_wait_side_effect):
            self.analytics._Analytics__drain_chunks()

        self.assertEqual(wait_calls, [30])

    # ── flush_remainder (5-min mandatory flusher) ─────────────────────────────

    def test_flush_remainder_sends_partial_record_below_30(self):
        fill_record(self.analytics, 10)
        sent = []

        def send_side_effect(record, previous_delay=0):
            sent.append(record)
            return 0

        with patch.object(self.analytics, SEND_TO_SERVER, side_effect=send_side_effect):
            self.analytics._Analytics__flush_remainder()

        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0].get_record_length(), 10)

    def test_flush_remainder_does_nothing_on_empty_record(self):
        sent = []

        with patch.object(self.analytics, SEND_TO_SERVER,
                          side_effect=lambda r, previous_delay=0: sent.append(r) or 0):
            self.analytics._Analytics__flush_remainder()

        self.assertEqual(len(sent), 0)

    def test_flush_remainder_clears_record_after_send(self):
        fill_record(self.analytics, 5)
        with patch.object(self.analytics, SEND_TO_SERVER, return_value=0):
            self.analytics._Analytics__flush_remainder()
        self.assertEqual(self.analytics._Analytics__record.get_record_length(), 0)

    # ── request body envelope ─────────────────────────────────────────────────

    def test_request_body_has_correct_envelope(self):
        fill_record(self.analytics, 30)
        sent = self._run_drain_chunks([0])
        body = sent[0].get_request_body("env-1", "col-1")
        self.assertEqual(body["environment_id"], "env-1")
        self.assertEqual(body["collection_id"], "col-1")
        self.assertIsInstance(body["usages"], list)

    def test_each_batch_contains_at_most_30_usages(self):
        fill_record(self.analytics, 90)
        sent = self._run_drain_chunks([0, 0, 0])
        for batch in sent:
            self.assertLessEqual(batch.get_record_length(), 30)


if __name__ == "__main__":
    unittest.main()

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
Guarded Rollout unit tests.

Hash values (get_normalized_value) are deterministic via murmurhash v3.
Key format for guarded: "entityId:featureId:rolloutId"

Boundary: target=[0, pct)  original=[100-pct, 100)  outside=[pct, 100-pct)
                            i.e. >= 100 - rollout_percentage

Feature gf-1, rollout_id rid-1, rollout_percentage 30:
  target   (0-29):   u17=19, u19=2,  u21=4,  u22=22, u25=9
  original (70-99):  u2=91,  u4=75,  u7=95,  u9=97,  u12=86
  outside  (30-69):  u1=32,  u3=65,  u5=41,  u6=67,  u8=33

Segment gf-1, rollout_id seg-rid-1, rollout_percentage 30:
  target   (0-29):   u2=11,  u13=16, u14=24, u16=9,  u17=6
  original (70-99):  u1=79,  u4=88,  u5=94,  u9=92,  u27=98
  outside  (30-69):  u3=53,  u6=42,  u7=30,  u8=58,  u10=30
"""

import unittest
from unittest.mock import MagicMock

from ibm_appconfiguration.configurations.models.feature import Feature
from ibm_appconfiguration.configurations.models.segment_rules import SegmentRules
from ibm_appconfiguration.configurations.internal.utils.analytics import Analytics
from ibm_appconfiguration.configurations.internal.utils.analytics_record import AnalyticsRecord, EventType
from ibm_appconfiguration.configurations.internal.utils.url_builder import URLBuilder
from ibm_appconfiguration.configurations.configuration_handler import ConfigurationHandler

FEATURE_ID = "gf-1"
ROLLOUT_ID = "rid-1"
SEG_ROLLOUT_ID = "seg-rid-1"
ROLLOUT_PCT = 30
SEGMENT_ID = "seg-1"


def make_guarded_feature(**overrides):
    base = {
        "name": "Guarded Feature",
        "feature_id": FEATURE_ID,
        "type": "BOOLEAN",
        "enabled_value": True,
        "disabled_value": False,
        "enabled": True,
        "rollout_type": "GUARDED",
        "rollout_percentage": ROLLOUT_PCT,
        "rollout_id": ROLLOUT_ID,
        "segment_rules": [],
        "metric_map": {"purchase": [{"id": "m1", "type": "count"}]},
    }
    base.update(overrides)
    return Feature(base)


# ─── URLBuilder ──────────────────────────────────────────────────────────────

class TestURLBuilderAnalyticsPath(unittest.TestCase):

    def test_analytics_path(self):
        URLBuilder.init_with_collection_id(
            collection_id="col", environment_id="env",
            region="region", guid="test-guid", apikey="",
            override_service_url="", use_private_endpoint=False,
        )
        self.assertEqual(
            URLBuilder.get_analytics_path(),
            "/apprapp/metrics/v1/instances/test-guid/analytics",
        )


# ─── SegmentRules ─────────────────────────────────────────────────────────────

class TestSegmentRulesGuarded(unittest.TestCase):

    def test_reads_rollout_id(self):
        sr = SegmentRules({
            "rules": [], "value": "$default", "order": 1,
            "rollout_type": "GUARDED", "rollout_percentage": ROLLOUT_PCT,
            "rollout_id": SEG_ROLLOUT_ID,
        })
        self.assertEqual(sr.get_rollout_id(), SEG_ROLLOUT_ID)

    def test_rollout_id_defaults_to_empty_string_when_absent(self):
        sr = SegmentRules({"rules": [], "value": "$default", "order": 1})
        self.assertEqual(sr.get_rollout_id(), "")

    def test_rollout_type_is_preserved(self):
        sr = SegmentRules({
            "rules": [], "value": "$default", "order": 1,
            "rollout_type": "GUARDED",
        })
        self.assertEqual(sr.get_rollout_type(), "GUARDED")


# ─── Feature model ───────────────────────────────────────────────────────────

class TestFeatureGuardedModel(unittest.TestCase):

    def test_reads_rollout_id(self):
        f = make_guarded_feature()
        self.assertEqual(f.get_rollout_id(), ROLLOUT_ID)

    def test_rollout_id_defaults_to_empty_string_when_absent(self):
        f = Feature({
            "name": "f", "feature_id": "f", "type": "BOOLEAN",
            "enabled_value": True, "disabled_value": False, "enabled": True,
            "segment_rules": [],
        })
        self.assertEqual(f.get_rollout_id(), "")

    def test_reads_metric_map(self):
        f = make_guarded_feature()
        self.assertEqual(f.get_metric_map(),
                         {"purchase": [{"id": "m1", "type": "count"}]})

    def test_metric_map_defaults_to_empty_dict_when_absent(self):
        f = Feature({
            "name": "f", "feature_id": "f", "type": "BOOLEAN",
            "enabled_value": True, "disabled_value": False, "enabled": True,
            "segment_rules": [],
        })
        self.assertEqual(f.get_metric_map(), {})


# ─── Feature.track() ─────────────────────────────────────────────────────────

class TestFeatureTrack(unittest.TestCase):
    """
    Call the real Analytics singleton and inspect get_request_body, following
    the same pattern as test_metering.py.
    """

    def setUp(self):
        # Swap in a fresh AnalyticsRecord so each test starts clean
        self._analytics = Analytics.get_instance()
        self._original_record = self._analytics._Analytics__record
        self._analytics._Analytics__record = AnalyticsRecord()

    def tearDown(self):
        self._analytics._Analytics__record = self._original_record

    def _usages(self):
        return self._analytics._Analytics__record.get_request_body("e", "c")["usages"]

    def test_emits_guarded_metric_target_for_entity_in_target_range(self):
        # u17: norm=19 < 30 -> target
        f = make_guarded_feature()
        f.track("purchase", "u17")
        usages = self._usages()
        self.assertEqual(len(usages), 1)
        self.assertEqual(usages[0]["value_served"], "target")
        self.assertEqual(usages[0]["rollout_id"], ROLLOUT_ID)
        self.assertEqual(usages[0]["entity_id"], "u17")
        self.assertEqual(usages[0]["metadata"]["feature"], "guarded")
        self.assertEqual(usages[0]["metadata"]["event_type"], "metric")

    def test_emits_guarded_metric_original_for_entity_in_original_range(self):
        # u2: norm=91 >= 100-30=70 -> original
        f = make_guarded_feature()
        f.track("purchase", "u2")
        usages = self._usages()
        self.assertEqual(len(usages), 1)
        self.assertEqual(usages[0]["value_served"], "original")

    def test_emits_nothing_for_entity_outside_both_ranges(self):
        # u1: norm=32 -> 30 <= 32 < 70 -> outside
        f = make_guarded_feature()
        f.track("purchase", "u1")
        self.assertEqual(len(self._usages()), 0)

    def test_skips_when_entity_id_is_empty(self):
        f = make_guarded_feature()
        f.track("purchase", "")
        self.assertEqual(len(self._usages()), 0)

    def test_skips_when_event_key_not_in_metric_map(self):
        f = make_guarded_feature()
        f.track("unknown-event", "u17")
        self.assertEqual(len(self._usages()), 0)

    def test_skips_when_feature_not_configured_for_guarded(self):
        f = Feature({
            "name": "f", "feature_id": FEATURE_ID, "type": "BOOLEAN",
            "enabled_value": True, "disabled_value": False, "enabled": True,
            "rollout_type": "MANUAL", "rollout_percentage": 100, "rollout_id": None,
            "segment_rules": [],
            "metric_map": {"purchase": [{"id": "m1", "type": "count"}]},
        })
        f.track("purchase", "u17")
        self.assertEqual(len(self._usages()), 0)

    def test_uses_segment_level_rollout_id_when_segment_is_guarded(self):
        # u2: seg norm=11 < 30 -> target
        f = Feature({
            "name": "f", "feature_id": FEATURE_ID, "type": "BOOLEAN",
            "enabled_value": True, "disabled_value": False, "enabled": True,
            "rollout_type": "MANUAL", "rollout_percentage": ROLLOUT_PCT, "rollout_id": None,
            "segment_rules": [{
                "rules": [{"segments": [SEGMENT_ID]}], "value": "$default", "order": 1,
                "rollout_type": "GUARDED", "rollout_percentage": ROLLOUT_PCT,
                "rollout_id": SEG_ROLLOUT_ID,
            }],
            "metric_map": {"purchase": [{"id": "m1", "type": "count"}]},
        })
        f.track("purchase", "u2")
        usages = self._usages()
        self.assertEqual(len(usages), 1)
        self.assertEqual(usages[0]["value_served"], "target")
        self.assertEqual(usages[0]["rollout_id"], SEG_ROLLOUT_ID)

    def test_track_includes_metrics_array_in_event_body(self):
        f = make_guarded_feature()
        f.track("purchase", "u17")
        # event_key is stripped from request body, but metrics list remains
        usages = self._usages()
        self.assertNotIn("event_key", usages[0])
        self.assertEqual(usages[0]["metrics"], [{"id": "m1", "type": "count"}])


# ─── ConfigurationHandler – add_guarded_evaluation_entry ─────────────────────

class TestAddGuardedEvaluationEntry(unittest.TestCase):
    """
    Test the static helper directly against the real Analytics record.
    """

    def setUp(self):
        self._analytics = Analytics.get_instance()
        self._original_record = self._analytics._Analytics__record
        self._analytics._Analytics__record = AnalyticsRecord()

    def tearDown(self):
        self._analytics._Analytics__record = self._original_record

    def _usages(self):
        return self._analytics._Analytics__record.get_request_body("e", "c")["usages"]

    def test_records_target_when_norm_below_percentage(self):
        # norm=19, pct=30 -> target
        ConfigurationHandler.add_guarded_evaluation_entry(ROLLOUT_ID, "u17", 30, 19)
        usages = self._usages()
        self.assertEqual(len(usages), 1)
        self.assertEqual(usages[0]["value_served"], "target")
        self.assertEqual(usages[0]["rollout_id"], ROLLOUT_ID)
        self.assertEqual(usages[0]["entity_id"], "u17")
        self.assertEqual(usages[0]["metadata"]["event_type"], "evaluation")

    def test_records_original_when_norm_in_original_range(self):
        # norm=91, pct=30 -> 91 >= 100-30=70 -> original
        ConfigurationHandler.add_guarded_evaluation_entry(ROLLOUT_ID, "u2", 30, 91)
        self.assertEqual(self._usages()[0]["value_served"], "original")

    def test_records_nothing_when_norm_outside_both_ranges(self):
        # norm=32, pct=30 -> 30 <= 32 < 70 -> outside
        ConfigurationHandler.add_guarded_evaluation_entry(ROLLOUT_ID, "u1", 30, 32)
        self.assertEqual(len(self._usages()), 0)

    def test_argument_order_rollout_percentage_before_normalised_value(self):
        # Verify the bug-1 fix: (rollout_id, entity_id, rollout_percentage, normalised_value)
        # With pct=30, norm=19 should be TARGET; swapped (norm=30, pct=19) would be ORIGINAL
        ConfigurationHandler.add_guarded_evaluation_entry(ROLLOUT_ID, "u17", 30, 19)
        self.assertEqual(self._usages()[0]["value_served"], "target")


# ─── ConfigurationHandler evaluation (feature-level, no targeting) ────────────

class TestConfigurationHandlerFeatureLevelGuarded(unittest.TestCase):
    """
    Test feature_evaluation return values for guarded rollout.
    We don't assert on Analytics calls here — that is covered by
    TestAddGuardedEvaluationEntry above. We just verify the served values.
    """

    def setUp(self):
        self.handler = ConfigurationHandler.get_instance()

    def test_serves_enabled_for_entity_in_target_range(self):
        # u17: norm=19 < 30
        f = make_guarded_feature()
        value, is_enabled = self.handler.feature_evaluation(f, True, "u17")
        self.assertTrue(value)
        self.assertTrue(is_enabled)

    def test_serves_disabled_for_entity_in_original_range(self):
        # u2: norm=91 >= 100-30=70 -> original -> disabled value
        f = make_guarded_feature()
        value, is_enabled = self.handler.feature_evaluation(f, True, "u2")
        self.assertFalse(value)
        self.assertFalse(is_enabled)

    def test_serves_disabled_for_entity_outside_both_ranges(self):
        # u1: norm=32 -> 30 <= 32 < 70 -> outside -> disabled value
        f = make_guarded_feature()
        value, is_enabled = self.handler.feature_evaluation(f, True, "u1")
        self.assertFalse(value)
        self.assertFalse(is_enabled)

    def test_serves_disabled_when_feature_flag_is_disabled(self):
        f = make_guarded_feature()
        value, is_enabled = self.handler.feature_evaluation(f, False, "u17")
        self.assertFalse(value)
        self.assertFalse(is_enabled)

    def test_rollout_100_always_serves_enabled(self):
        f = make_guarded_feature(rollout_percentage=100)
        value, is_enabled = self.handler.feature_evaluation(f, True, "u2")
        self.assertTrue(value)
        self.assertTrue(is_enabled)


# ─── ConfigurationHandler evaluation (segment-level guarded) ─────────────────

class TestConfigurationHandlerSegmentLevelGuarded(unittest.TestCase):
    """
    Inject a mock open segment and verify served values for segment-level
    guarded rollout. Analytics assertion is done via AnalyticsRecord directly.
    """

    def setUp(self):
        self.handler = ConfigurationHandler.get_instance()
        self.handler._ConfigurationHandler__segment_map = {
            SEGMENT_ID: MagicMock(
                evaluate_rule=MagicMock(return_value=True),
                name="Open Seg",
            ),
        }
        self._analytics = Analytics.get_instance()
        self._original_record = self._analytics._Analytics__record
        self._analytics._Analytics__record = AnalyticsRecord()

    def tearDown(self):
        self._analytics._Analytics__record = self._original_record

    def _usages(self):
        return self._analytics._Analytics__record.get_request_body("e", "c")["usages"]

    def _guarded_seg_feature(self):
        return Feature({
            "name": "f", "feature_id": FEATURE_ID, "type": "BOOLEAN",
            "enabled_value": True, "disabled_value": False, "enabled": True,
            "rollout_type": "MANUAL", "rollout_percentage": 100, "rollout_id": None,
            "segment_rules": [{
                "rules": [{"segments": [SEGMENT_ID]}], "value": "$default", "order": 1,
                "rollout_type": "GUARDED", "rollout_percentage": ROLLOUT_PCT,
                "rollout_id": SEG_ROLLOUT_ID,
            }],
        })

    def test_serves_enabled_and_records_target_for_entity_in_target_range(self):
        # u2: seg norm=11 < 30 -> target
        value, is_enabled = self.handler.feature_evaluation(
            self._guarded_seg_feature(), True, "u2", {"any": "attr"})
        self.assertTrue(value)
        self.assertTrue(is_enabled)
        usages = self._usages()
        self.assertEqual(len(usages), 1)
        self.assertEqual(usages[0]["value_served"], "target")
        self.assertEqual(usages[0]["rollout_id"], SEG_ROLLOUT_ID)

    def test_serves_disabled_and_records_original_for_entity_in_original_range(self):
        # u1: seg norm=79 >= 100-30=70 -> original -> disabled value
        value, is_enabled = self.handler.feature_evaluation(
            self._guarded_seg_feature(), True, "u1", {"any": "attr"})
        self.assertFalse(value)
        self.assertFalse(is_enabled)
        self.assertEqual(self._usages()[0]["value_served"], "original")

    def test_serves_disabled_and_emits_no_entry_outside_both_ranges(self):
        # u3: seg norm=53 -> 30 <= 53 < 70 -> outside
        value, is_enabled = self.handler.feature_evaluation(
            self._guarded_seg_feature(), True, "u3", {"any": "attr"})
        self.assertFalse(value)
        self.assertFalse(is_enabled)
        self.assertEqual(len(self._usages()), 0)


# ─── Feature.get_current_value() entity_id validation ───────────────────────

class TestGetCurrentValueEntityIdValidation(unittest.TestCase):

    def test_returns_none_for_whitespace_only_entity_id(self):
        f = make_guarded_feature()
        self.assertIsNone(f.get_current_value("   "))

    def test_returns_none_for_none_entity_id(self):
        f = make_guarded_feature()
        self.assertIsNone(f.get_current_value(None))

    def test_returns_none_for_integer_entity_id(self):
        f = make_guarded_feature()
        self.assertIsNone(f.get_current_value(123))


# ─── Feature.track() — additional edge cases ─────────────────────────────────

class TestFeatureTrackEdgeCases(unittest.TestCase):

    def setUp(self):
        self._analytics = Analytics.get_instance()
        self._original_record = self._analytics._Analytics__record
        self._analytics._Analytics__record = AnalyticsRecord()

    def tearDown(self):
        self._analytics._Analytics__record = self._original_record

    def _usages(self):
        return self._analytics._Analytics__record.get_request_body("e", "c")["usages"]

    def test_skips_when_event_key_is_none(self):
        f = make_guarded_feature()
        f.track(None, "u17")
        self.assertEqual(len(self._usages()), 0)

    def test_skips_when_entity_id_is_whitespace(self):
        f = make_guarded_feature()
        f.track("purchase", "   ")
        self.assertEqual(len(self._usages()), 0)

    def test_skips_when_event_key_is_whitespace(self):
        f = make_guarded_feature()
        f.track("   ", "u17")
        self.assertEqual(len(self._usages()), 0)

    def test_segment_metric_map_takes_priority_over_feature_metric_map(self):
        # The segment rule has its own metric_map for "purchase" with a
        # different metric id. track() must resolve from the segment, not
        # the feature-level map.
        f = Feature({
            "name": "f", "feature_id": FEATURE_ID, "type": "BOOLEAN",
            "enabled_value": True, "disabled_value": False, "enabled": True,
            "rollout_type": "MANUAL", "rollout_percentage": ROLLOUT_PCT,
            "rollout_id": None,
            "segment_rules": [{
                "rules": [{"segments": [SEGMENT_ID]}], "value": "$default", "order": 1,
                "rollout_type": "GUARDED", "rollout_percentage": ROLLOUT_PCT,
                "rollout_id": SEG_ROLLOUT_ID,
                "metric_map": {"purchase": [{"id": "seg-metric", "type": "count"}]},
            }],
            "metric_map": {"purchase": [{"id": "feat-metric", "type": "count"}]},
        })
        # u2: seg norm=11 < 30 -> target
        f.track("purchase", "u2")
        usages = self._usages()
        self.assertEqual(len(usages), 1)
        self.assertEqual(usages[0]["metrics"][0]["id"], "seg-metric")

    def test_segment_level_guarded_original_range(self):
        # u1: seg norm=79 >= 100-30=70 -> original
        f = Feature({
            "name": "f", "feature_id": FEATURE_ID, "type": "BOOLEAN",
            "enabled_value": True, "disabled_value": False, "enabled": True,
            "rollout_type": "MANUAL", "rollout_percentage": ROLLOUT_PCT, "rollout_id": None,
            "segment_rules": [{
                "rules": [], "value": "$default", "order": 1,
                "rollout_type": "GUARDED", "rollout_percentage": ROLLOUT_PCT,
                "rollout_id": SEG_ROLLOUT_ID,
            }],
            "metric_map": {"purchase": [{"id": "m1", "type": "count"}]},
        })
        f.track("purchase", "u1")
        usages = self._usages()
        self.assertEqual(len(usages), 1)
        self.assertEqual(usages[0]["value_served"], "original")
        self.assertEqual(usages[0]["rollout_id"], SEG_ROLLOUT_ID)

    def test_segment_level_guarded_outside_range_emits_nothing(self):
        # u3: seg norm=53 -> 30 <= 53 < 70 -> outside
        f = Feature({
            "name": "f", "feature_id": FEATURE_ID, "type": "BOOLEAN",
            "enabled_value": True, "disabled_value": False, "enabled": True,
            "rollout_type": "MANUAL", "rollout_percentage": ROLLOUT_PCT, "rollout_id": None,
            "segment_rules": [{
                "rules": [], "value": "$default", "order": 1,
                "rollout_type": "GUARDED", "rollout_percentage": ROLLOUT_PCT,
                "rollout_id": SEG_ROLLOUT_ID,
            }],
            "metric_map": {"purchase": [{"id": "m1", "type": "count"}]},
        })
        f.track("purchase", "u3")
        self.assertEqual(len(self._usages()), 0)

    def test_segment_rule_default_rollout_pct_inherits_feature_pct(self):
        # Segment rollout_percentage is '$default' → inherits feature rollout_percentage (30).
        # u2: seg norm=11 < 30 -> target with inherited pct
        f = Feature({
            "name": "f", "feature_id": FEATURE_ID, "type": "BOOLEAN",
            "enabled_value": True, "disabled_value": False, "enabled": True,
            "rollout_type": "MANUAL", "rollout_percentage": ROLLOUT_PCT, "rollout_id": None,
            "segment_rules": [{
                "rules": [], "value": "$default", "order": 1,
                "rollout_type": "GUARDED", "rollout_percentage": "$default",
                "rollout_id": SEG_ROLLOUT_ID,
            }],
            "metric_map": {"purchase": [{"id": "m1", "type": "count"}]},
        })
        f.track("purchase", "u2")
        usages = self._usages()
        self.assertEqual(len(usages), 1)
        self.assertEqual(usages[0]["value_served"], "target")


# ─── add_guarded_evaluation_entry — boundary and edge cases ──────────────────

class TestAddGuardedEvaluationEntryBoundaries(unittest.TestCase):

    def setUp(self):
        self._analytics = Analytics.get_instance()
        self._original_record = self._analytics._Analytics__record
        self._analytics._Analytics__record = AnalyticsRecord()

    def tearDown(self):
        self._analytics._Analytics__record = self._original_record

    def _usages(self):
        return self._analytics._Analytics__record.get_request_body("e", "c")["usages"]

    def test_boundary_at_exactly_100_minus_pct_is_original(self):
        # norm == 100-pct (70) with pct=30 -> 70 >= 70 -> original
        ConfigurationHandler.add_guarded_evaluation_entry(ROLLOUT_ID, "u-exact", 30, 70)
        self.assertEqual(self._usages()[0]["value_served"], "original")

    def test_boundary_at_pct_is_outside(self):
        # norm == pct (30) with pct=30 -> 30 < 70 and 30 >= 30 -> outside
        ConfigurationHandler.add_guarded_evaluation_entry(ROLLOUT_ID, "u-pct", 30, 30)
        self.assertEqual(len(self._usages()), 0)

    def test_rollout_percentage_100_makes_everyone_target(self):
        # pct=100: target=[0,100), original=[0,100) overlaps entirely with target
        # norm=0 -> 0 < 100 -> target (target wins as it is checked first)
        ConfigurationHandler.add_guarded_evaluation_entry(ROLLOUT_ID, "u-all", 100, 0)
        self.assertEqual(self._usages()[0]["value_served"], "target")

    def test_rollout_percentage_0_emits_nothing(self):
        # pct=0: target=[0,0) empty, original=[100,100) empty -> everything outside
        ConfigurationHandler.add_guarded_evaluation_entry(ROLLOUT_ID, "u-zero", 0, 50)
        self.assertEqual(len(self._usages()), 0)

    def test_norm_zero_with_nonzero_pct_is_target(self):
        # norm=0, pct=30 -> 0 < 30 -> target
        ConfigurationHandler.add_guarded_evaluation_entry(ROLLOUT_ID, "u-n0", 30, 0)
        self.assertEqual(self._usages()[0]["value_served"], "target")

    def test_evaluation_entry_carries_correct_metadata(self):
        ConfigurationHandler.add_guarded_evaluation_entry(ROLLOUT_ID, "u17", 30, 19)
        usage = self._usages()[0]
        self.assertEqual(usage["metadata"]["feature"], "guarded")
        self.assertEqual(usage["metadata"]["event_type"], "evaluation")
        self.assertNotIn("count", usage)


# ─── feature_evaluation — evaluation entry is emitted at feature level ────────

class TestFeatureLevelGuardedEvaluationEntry(unittest.TestCase):
    """
    Verify that feature_evaluation emits the correct GUARDED_EVALUATION
    entry via add_guarded_evaluation_entry.
    """

    def setUp(self):
        self.handler = ConfigurationHandler.get_instance()
        self._analytics = Analytics.get_instance()
        self._original_record = self._analytics._Analytics__record
        self._analytics._Analytics__record = AnalyticsRecord()

    def tearDown(self):
        self._analytics._Analytics__record = self._original_record

    def _usages(self):
        return self._analytics._Analytics__record.get_request_body("e", "c")["usages"]

    def test_emits_target_evaluation_entry_for_entity_in_target_range(self):
        # u17: norm=19 < 30 -> target
        self.handler.feature_evaluation(make_guarded_feature(), True, "u17")
        usages = self._usages()
        self.assertEqual(len(usages), 1)
        self.assertEqual(usages[0]["value_served"], "target")
        self.assertEqual(usages[0]["rollout_id"], ROLLOUT_ID)
        self.assertEqual(usages[0]["metadata"]["event_type"], "evaluation")

    def test_emits_original_evaluation_entry_for_entity_in_original_range(self):
        # u2: norm=91 >= 100-30=70 -> original
        self.handler.feature_evaluation(make_guarded_feature(), True, "u2")
        self.assertEqual(self._usages()[0]["value_served"], "original")

    def test_emits_no_evaluation_entry_for_entity_outside_both_ranges(self):
        # u1: norm=32 -> 30 <= 32 < 70 -> outside
        self.handler.feature_evaluation(make_guarded_feature(), True, "u1")
        self.assertEqual(len(self._usages()), 0)

    def test_emits_no_evaluation_entry_when_feature_is_disabled(self):
        # is_enabled=False short-circuits before any rollout check
        self.handler.feature_evaluation(make_guarded_feature(), False, "u17")
        self.assertEqual(len(self._usages()), 0)

    def test_no_analytics_when_entity_attributes_absent_and_segment_guarded(self):
        # Feature has a guarded segment rule, but entity_attributes is None
        # → falls through to feature-level rollout (MANUAL/100%) → no guarded emit
        f = Feature({
            "name": "f", "feature_id": FEATURE_ID, "type": "BOOLEAN",
            "enabled_value": True, "disabled_value": False, "enabled": True,
            "rollout_type": "MANUAL", "rollout_percentage": 100, "rollout_id": None,
            "segment_rules": [{
                "rules": [{"segments": [SEGMENT_ID]}], "value": "$default", "order": 1,
                "rollout_type": "GUARDED", "rollout_percentage": ROLLOUT_PCT,
                "rollout_id": SEG_ROLLOUT_ID,
            }],
        })
        self.handler.feature_evaluation(f, True, "u2", None)
        self.assertEqual(len(self._usages()), 0)


# ─── segment-level evaluation — rollout_percentage == $default ───────────────

class TestSegmentLevelGuardedDefaultPct(unittest.TestCase):
    """
    When a segment rule has rollout_percentage == '$default', it inherits
    the feature-level rollout_percentage for the guarded evaluation.
    """

    def setUp(self):
        self.handler = ConfigurationHandler.get_instance()
        self.handler._ConfigurationHandler__segment_map = {
            SEGMENT_ID: MagicMock(evaluate_rule=MagicMock(return_value=True)),
        }
        self._analytics = Analytics.get_instance()
        self._original_record = self._analytics._Analytics__record
        self._analytics._Analytics__record = AnalyticsRecord()

    def tearDown(self):
        self._analytics._Analytics__record = self._original_record

    def _usages(self):
        return self._analytics._Analytics__record.get_request_body("e", "c")["usages"]

    def _feature_with_default_seg_pct(self):
        return Feature({
            "name": "f", "feature_id": FEATURE_ID, "type": "BOOLEAN",
            "enabled_value": True, "disabled_value": False, "enabled": True,
            "rollout_type": "MANUAL", "rollout_percentage": ROLLOUT_PCT, "rollout_id": None,
            "segment_rules": [{
                "rules": [{"segments": [SEGMENT_ID]}], "value": "$default", "order": 1,
                "rollout_type": "GUARDED", "rollout_percentage": "$default",
                "rollout_id": SEG_ROLLOUT_ID,
            }],
        })

    def test_inherits_feature_pct_and_serves_enabled_for_target_entity(self):
        # u2: seg norm=11 < 30 (inherited) -> target -> enabled value
        value, is_enabled = self.handler.feature_evaluation(
            self._feature_with_default_seg_pct(), True, "u2", {"any": "attr"})
        self.assertTrue(value)
        self.assertTrue(is_enabled)
        self.assertEqual(self._usages()[0]["value_served"], "target")

    def test_inherits_feature_pct_and_serves_disabled_for_original_entity(self):
        # u1: seg norm=79 >= 100-30=70 (inherited pct=30) -> original -> disabled
        value, is_enabled = self.handler.feature_evaluation(
            self._feature_with_default_seg_pct(), True, "u1", {"any": "attr"})
        self.assertFalse(value)
        self.assertFalse(is_enabled)
        self.assertEqual(self._usages()[0]["value_served"], "original")


if __name__ == "__main__":
    unittest.main()

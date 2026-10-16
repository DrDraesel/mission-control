"""Tests for labflow.workflow — parsing, validation, ordering, defaults."""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from labflow.workflow import (  # noqa: E402
    CAPTURE_TYPES,
    DEFAULT_WORKFLOW,
    LAUNCH_TYPES,
    SORT_RULES,
    Station,
    Workflow,
)

EXPECTED_IDS = [
    "intake", "vitals", "hrv", "inbody", "blood_panels",
    "squats_strength", "eeg_baseline", "balance", "treadmill_form",
]


def make_station(**over):
    base = dict(
        id="a",
        name="A",
        app="app-a",
        description="Do A.",
        typical_minutes=5,
        launch={"type": "manual", "value": "manual"},
        capture={"type": "manual", "fields": ["x"], "probe": None},
    )
    base.update(over)
    return Station(**base)


class StationTests(unittest.TestCase):
    def test_post_init_normalises_launch_capture_requires(self):
        station = Station(
            id="s", name="S", app="app", description="d", typical_minutes=1,
            launch=None, capture=None, requires=None,
        )
        self.assertEqual(station.launch, {"type": "manual", "value": ""})
        self.assertEqual(station.capture, {"type": "manual", "fields": [], "probe": None})
        self.assertEqual(station.requires, [])
        self.assertFalse(station.pinned)
        self.assertEqual(station.notes, "")
        self.assertEqual(station.alert_text, "")

    def test_requires_string_becomes_list(self):
        self.assertEqual(make_station(requires="vitals").requires, ["vitals"])

    def test_launch_and_capture_dicts_are_copied(self):
        launch = {"type": "url", "value": "http://x"}
        station = make_station(launch=launch)
        launch["value"] = "mutated"
        self.assertEqual(station.launch["value"], "http://x")

    def test_to_dict_from_dict_roundtrip(self):
        station = make_station(id="eeg", name="EEG", app="neurosync", typical_minutes=20,
                               pinned=True, notes="n", alert_text="a", requires=["vitals"],
                               launch={"type": "command", "value": "neurosync record"},
                               capture={"type": "auto", "fields": ["recording_id"],
                                        "probe": "neurosync recordings"})
        clone = Station.from_dict(station.to_dict())
        self.assertEqual(clone, station)
        self.assertEqual(station.to_dict()["capture"]["probe"], "neurosync recordings")

    def test_launch_hint_variants(self):
        self.assertEqual(make_station(launch={"type": "url", "value": "http://h"}).launch_hint(),
                         "Open http://h")
        self.assertEqual(make_station(launch={"type": "command", "value": "run me"}).launch_hint(),
                         "Run: run me")
        self.assertEqual(make_station(launch={"type": "manual", "value": "cart"}).launch_hint(),
                         "Manual: cart")
        self.assertEqual(make_station(launch={"type": "manual", "value": ""}).launch_hint(),
                         "Manual step")

    def test_capture_prompt_variants(self):
        self.assertEqual(
            make_station(capture={"type": "manual", "fields": ["a", "b"]}).capture_prompt(),
            "Enter: a, b")
        self.assertEqual(
            make_station(capture={"type": "auto", "fields": ["sid"],
                                  "probe": "probe name"}).capture_prompt(),
            "Auto-capture from 'probe name' (fields: sid)")
        self.assertEqual(
            make_station(capture={"type": "auto", "fields": [], "probe": None}).capture_prompt(),
            "Auto-capture")
        self.assertEqual(
            make_station(capture={"type": "ref", "fields": ["panel"]}).capture_prompt(),
            "External reference (record: panel)")

    def test_minutes_text_defensive(self):
        self.assertEqual(make_station(typical_minutes=15).minutes_text(), "15 min")
        self.assertEqual(make_station(typical_minutes=7.5).minutes_text(), "7.5 min")
        self.assertEqual(make_station(typical_minutes=None).minutes_text(), "duration unknown")


class WorkflowConstructionTests(unittest.TestCase):
    def test_from_dict_accepts_station_dicts_and_defaults(self):
        wf = Workflow.from_dict({"name": "W", "version": "2", "stations": [
            {"id": "a", "name": "A", "app": "x", "description": "d",
             "typical_minutes": 3, "launch": {"type": "manual", "value": ""},
             "capture": {"type": "manual", "fields": ["f"]}},
        ]})
        self.assertEqual(wf.name, "W")
        self.assertEqual(wf.version, "2")
        self.assertEqual(wf.sort_rule, "longest_last")
        self.assertIsInstance(wf.stations[0], Station)
        self.assertEqual(wf.stations[0].id, "a")

    def test_from_dict_accepts_wrapped_workflow_key(self):
        wf = Workflow.from_dict({"workflow": {"name": "Wrapped", "stations": []}})
        self.assertEqual(wf.name, "Wrapped")

    def test_to_json_roundtrips(self):
        clone = Workflow.from_dict(json.loads(DEFAULT_WORKFLOW.to_json()))
        self.assertEqual(clone.name, DEFAULT_WORKFLOW.name)
        self.assertEqual(clone.sort_rule, DEFAULT_WORKFLOW.sort_rule)
        self.assertEqual(len(clone.stations), len(DEFAULT_WORKFLOW.stations))
        self.assertEqual(clone.stations[0], DEFAULT_WORKFLOW.stations[0])
        self.assertEqual(clone.ordered_stations()[0].id, "intake")

    def test_empty_stations_list_ok_but_flagged(self):
        wf = Workflow(name="empty", version="1")
        self.assertEqual(wf.ordered_stations(), [])
        self.assertIn("workflow has no stations", wf.validation_errors())


class FromYamlTests(unittest.TestCase):
    def test_from_yaml_reads_json_compatible_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "workflow.yaml"
            path.write_text(DEFAULT_WORKFLOW.to_json(), encoding="utf-8")
            wf = Workflow.from_yaml(path)
        self.assertEqual(wf.name, DEFAULT_WORKFLOW.name)
        self.assertEqual([s.id for s in wf.ordered_stations()], [s.id for s in DEFAULT_WORKFLOW.ordered_stations()])

    def test_from_yaml_wrapped_document(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "workflow.yaml"
            path.write_text(json.dumps({"workflow": {"name": "Wrapped", "stations": []}}), encoding="utf-8")
            wf = Workflow.from_yaml(path)
        self.assertEqual(wf.name, "Wrapped")

    def test_from_yaml_bad_yaml_raises_value_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "workflow.yaml"
            path.write_text("name: W\nstations:\n  - id: a\n", encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                Workflow.from_yaml(path)
        self.assertIn("JSON-compatible YAML", str(ctx.exception))

    def test_from_yaml_missing_file_raises(self):
        with self.assertRaises(ValueError):
            Workflow.from_yaml("does-not-exist/workflow.yaml")

    def test_from_yaml_non_object_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "workflow.yaml"
            path.write_text("[1, 2, 3]", encoding="utf-8")
            with self.assertRaises(ValueError):
                Workflow.from_yaml(path)


class ValidationTests(unittest.TestCase):
    def test_default_workflow_is_valid(self):
        self.assertEqual(DEFAULT_WORKFLOW.validation_errors(), [])

    def test_duplicate_ids_flagged(self):
        wf = Workflow(name="w", version="1", stations=[
            make_station(id="dup"), make_station(id="dup"),
        ])
        errors = wf.validation_errors()
        self.assertTrue(any("duplicate station id" in e and "dup" in e for e in errors), errors)

    def test_negative_minutes_flagged(self):
        wf = Workflow(name="w", version="1", stations=[make_station(typical_minutes=-5)])
        self.assertTrue(any("negative typical_minutes" in e for e in wf.validation_errors()))

    def test_missing_minutes_flagged(self):
        wf = Workflow(name="w", version="1", stations=[make_station(typical_minutes=None)])
        self.assertTrue(any("missing typical_minutes" in e for e in wf.validation_errors()))

    def test_non_numeric_minutes_flagged(self):
        wf = Workflow(name="w", version="1", stations=[make_station(typical_minutes="ten")])
        self.assertTrue(any("must be a number" in e for e in wf.validation_errors()))

    def test_unknown_capture_type_flagged(self):
        wf = Workflow(name="w", version="1", stations=[
            make_station(capture={"type": "telepathy", "fields": [], "probe": None}),
        ])
        self.assertTrue(any("unknown capture.type" in e for e in wf.validation_errors()))

    def test_missing_capture_fields_flagged(self):
        manual = Workflow(name="w", version="1", stations=[
            make_station(capture={"type": "manual", "fields": [], "probe": None}),
        ])
        self.assertTrue(any("manual capture requires fields" in e for e in manual.validation_errors()))
        auto = Workflow(name="w", version="1", stations=[
            make_station(capture={"type": "auto", "fields": [], "probe": None}),
        ])
        self.assertTrue(any("auto capture requires probe" in e for e in auto.validation_errors()))

    def test_missing_id_and_name_flagged(self):
        wf = Workflow(name="w", version="1", stations=[make_station(id="", name="")])
        errors = wf.validation_errors()
        self.assertTrue(any("missing id" in e for e in errors))
        self.assertTrue(any("missing name" in e for e in errors))

    def test_unknown_launch_type_flagged(self):
        wf = Workflow(name="w", version="1", stations=[
            make_station(launch={"type": "teleport", "value": "x"}),
        ])
        self.assertTrue(any("unknown launch.type" in e for e in wf.validation_errors()))

    def test_launch_value_required_for_url_and_command(self):
        wf = Workflow(name="w", version="1", stations=[
            make_station(launch={"type": "url", "value": ""}),
        ])
        self.assertTrue(any("launch.value required" in e for e in wf.validation_errors()))

    def test_unknown_sort_rule_flagged(self):
        wf = Workflow(name="w", version="1", sort_rule="weird", stations=[make_station()])
        self.assertTrue(any("unknown sort_rule" in e for e in wf.validation_errors()))

    def test_constants_expose_allowed_values(self):
        self.assertIn("url", LAUNCH_TYPES)
        self.assertIn("manual", CAPTURE_TYPES)
        self.assertIn("ref", CAPTURE_TYPES)
        self.assertIn("longest_last", SORT_RULES)
        self.assertIn("config", SORT_RULES)


class OrderingTests(unittest.TestCase):
    def test_longest_last_sorts_ascending(self):
        wf = Workflow(name="w", version="1", sort_rule="longest_last", stations=[
            make_station(id="long", typical_minutes=30),
            make_station(id="short", typical_minutes=5),
            make_station(id="mid", typical_minutes=15),
        ])
        self.assertEqual([s.id for s in wf.ordered_stations()], ["short", "mid", "long"])

    def test_longest_last_stable_ties_keep_config_order(self):
        wf = Workflow(name="w", version="1", stations=[
            make_station(id="b", typical_minutes=10),
            make_station(id="a", typical_minutes=10),
        ])
        self.assertEqual([s.id for s in wf.ordered_stations()], ["b", "a"])

    def test_pinned_stations_keep_config_order_at_front(self):
        wf = Workflow(name="w", version="1", stations=[
            make_station(id="p1", typical_minutes=20, pinned=True),
            make_station(id="n1", typical_minutes=5),
            make_station(id="p2", typical_minutes=25, pinned=True),
            make_station(id="n2", typical_minutes=10),
        ])
        self.assertEqual([s.id for s in wf.ordered_stations()], ["p1", "p2", "n1", "n2"])

    def test_config_rule_keeps_file_order(self):
        wf = Workflow(name="w", version="1", sort_rule="config", stations=[
            make_station(id="c", typical_minutes=30),
            make_station(id="a", typical_minutes=5),
            make_station(id="b", typical_minutes=15),
        ])
        self.assertEqual([s.id for s in wf.ordered_stations()], ["c", "a", "b"])

    def test_unknown_rule_falls_back_to_config_order(self):
        wf = Workflow(name="w", version="1", sort_rule="nope", stations=[
            make_station(id="c", typical_minutes=30),
            make_station(id="a", typical_minutes=5),
        ])
        self.assertEqual([s.id for s in wf.ordered_stations()], ["c", "a"])


class DefaultWorkflowTests(unittest.TestCase):
    def test_has_expected_station_ids(self):
        ids = [s.id for s in DEFAULT_WORKFLOW.stations]
        self.assertEqual(sorted(ids), sorted(EXPECTED_IDS))
        self.assertEqual(len(ids), len(set(ids)))

    def test_sort_rule_is_longest_last(self):
        self.assertEqual(DEFAULT_WORKFLOW.sort_rule, "longest_last")

    def test_intake_is_pinned_and_first(self):
        ordered = DEFAULT_WORKFLOW.ordered_stations()
        self.assertEqual(ordered[0].id, "intake")
        self.assertTrue(ordered[0].pinned)
        self.assertEqual(DEFAULT_WORKFLOW.stations[0].id, "intake")

    def test_balance_and_treadmill_at_the_tail(self):
        ordered = DEFAULT_WORKFLOW.ordered_stations()
        self.assertEqual([s.id for s in ordered[-2:]], ["balance", "treadmill_form"])

    def test_longest_test_is_last(self):
        ordered = DEFAULT_WORKFLOW.ordered_stations()
        longest = max(DEFAULT_WORKFLOW.stations, key=lambda s: s.typical_minutes)
        self.assertEqual(longest.id, "treadmill_form")
        self.assertEqual(ordered[-1].id, longest.id)
        self.assertEqual(longest.typical_minutes, 30)

    def test_minutes_ascending_after_pinned_block(self):
        ordered = DEFAULT_WORKFLOW.ordered_stations()
        minutes = [s.typical_minutes for s in ordered if not s.pinned]
        self.assertEqual(minutes, sorted(minutes))

    def test_station_payloads_match_the_seed(self):
        intake = DEFAULT_WORKFLOW.get_station("intake")
        self.assertEqual(intake.typical_minutes, 15)
        self.assertEqual(intake.capture["type"], "manual")
        self.assertTrue(intake.capture["fields"])
        self.assertIsNone(intake.capture["probe"])

        blood = DEFAULT_WORKFLOW.get_station("blood_panels")
        self.assertEqual(blood.capture["type"], "ref")
        self.assertEqual(blood.typical_minutes, 10)

        eeg = DEFAULT_WORKFLOW.get_station("eeg_baseline")
        self.assertEqual(eeg.launch["type"], "command")
        self.assertIn("neurosync", eeg.launch["value"])
        self.assertEqual(eeg.capture["type"], "auto")
        self.assertEqual(eeg.capture["probe"], "neurosync recordings")
        self.assertEqual(eeg.typical_minutes, 20)

        balance = DEFAULT_WORKFLOW.get_station("balance")
        self.assertEqual(balance.launch, {"type": "url", "value": "http://127.0.0.1:8765"})
        self.assertEqual(balance.capture["probe"], "bertec protocol sessions")
        self.assertEqual(balance.typical_minutes, 25)

        treadmill = DEFAULT_WORKFLOW.get_station("treadmill_form")
        self.assertEqual(treadmill.launch, {"type": "url", "value": "http://127.0.0.1:8780"})
        self.assertEqual(treadmill.capture["probe"], "runtrack sessions")
        self.assertEqual(treadmill.typical_minutes, 30)

        vitals = DEFAULT_WORKFLOW.get_station("vitals")
        self.assertEqual(vitals.typical_minutes, 5)
        hrv = DEFAULT_WORKFLOW.get_station("hrv")
        self.assertEqual(hrv.typical_minutes, 5)

    def test_every_station_has_app_description_and_minutes(self):
        for station in DEFAULT_WORKFLOW.stations:
            self.assertTrue(station.app)
            self.assertTrue(station.description)
            self.assertGreater(station.typical_minutes, 0)
            self.assertIn(station.capture["type"], CAPTURE_TYPES)
            self.assertIn(station.launch["type"], LAUNCH_TYPES)

    def test_get_station_unknown_returns_none(self):
        self.assertIsNone(DEFAULT_WORKFLOW.get_station("nope"))


if __name__ == "__main__":
    unittest.main()

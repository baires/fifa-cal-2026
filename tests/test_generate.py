import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "generate.py"
SPEC = importlib.util.spec_from_file_location("generate", MODULE_PATH)
generate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = generate
SPEC.loader.exec_module(generate)


MATCH = {
    "round": "Matchday 1",
    "date": "2026-06-11",
    "time": "13:00 UTC-6",
    "team1": "Mexico",
    "team2": "South Africa",
    "group": "Group A",
    "ground": "Mexico City",
}


class EventUpdateTests(unittest.TestCase):
    def test_unchanged_event_keeps_revision_timestamp(self):
        state = {}
        first_run = datetime(2026, 6, 11, 21, 0, tzinfo=timezone.utc)
        second_run = datetime(2026, 6, 11, 22, 0, tzinfo=timezone.utc)

        first = generate.create_event(MATCH, "en", state, first_run)
        second = generate.create_event(MATCH, "en", state, second_run)

        self.assertEqual(first["SEQUENCE"], 0)
        self.assertEqual(second["SEQUENCE"], 0)
        self.assertEqual(first["DTSTAMP"].dt, first_run)
        self.assertEqual(second["DTSTAMP"].dt, first_run)

    def test_score_update_increments_sequence_and_timestamp(self):
        state = {}
        first_run = datetime(2026, 6, 11, 21, 0, tzinfo=timezone.utc)
        second_run = datetime(2026, 6, 11, 22, 0, tzinfo=timezone.utc)

        generate.create_event(MATCH, "en", state, first_run)
        scored_match = {**MATCH, "score": {"ft": [2, 0]}}
        updated = generate.create_event(scored_match, "en", state, second_run)

        self.assertEqual(updated["SEQUENCE"], 1)
        self.assertEqual(updated["DTSTAMP"].dt, second_run)
        self.assertEqual(updated["LAST-MODIFIED"].dt, second_run)
        self.assertIn("2-0", str(updated["SUMMARY"]))


if __name__ == "__main__":
    unittest.main()

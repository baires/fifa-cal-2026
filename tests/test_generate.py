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

    def test_placeholder_replacement_updates_existing_event(self):
        state = {}
        first_run = datetime(2026, 6, 28, 8, 0, tzinfo=timezone.utc)
        second_run = datetime(2026, 6, 28, 9, 0, tzinfo=timezone.utc)
        placeholder_match = {
            **MATCH,
            "round": "Round of 32",
            "team1": "1H",
            "team2": "2J",
        }

        placeholder = generate.create_event(placeholder_match, "en", state, first_run)
        resolved = generate.create_event(
            {**placeholder_match, "team1": "Spain", "team2": "Austria"},
            "en",
            state,
            second_run,
        )

        self.assertEqual(placeholder["UID"], resolved["UID"])
        self.assertEqual(resolved["SEQUENCE"], 1)
        self.assertEqual(resolved["DTSTAMP"].dt, second_run)
        self.assertIn("Spain", str(resolved["SUMMARY"]))
        self.assertNotIn("1H", str(resolved["SUMMARY"]))


class CalendarMetadataTests(unittest.TestCase):
    def test_calendar_requests_30_minute_subscription_refresh(self):
        generated_at = datetime(2026, 6, 28, 9, 0, tzinfo=timezone.utc)

        calendar = generate.generate_calendar([MATCH], "en", {}, generated_at)
        serialized = calendar.to_ical().decode("utf-8")

        self.assertIn("REFRESH-INTERVAL;VALUE=DURATION:PT30M", serialized)
        self.assertIn("X-PUBLISHED-TTL:PT30M", serialized)


if __name__ == "__main__":
    unittest.main()

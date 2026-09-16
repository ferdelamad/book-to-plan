#!/usr/bin/env python3
"""Tests for bin/due.py.

Plan files are hand-edited by readers, so the parser is tested against a
deliberately messy fixture: hyphens instead of em dashes, capitalised
statuses, reordered fields, wrapped values, a non-numeric chapter, and a
commitment with no review date.
"""

import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DUE = ROOT / "bin" / "due.py"
MESSY = ROOT / "tests" / "fixtures" / "hand-edited-plan.md"
DEMO = ROOT / "examples" / "million-dollar-weekend-plan.md"


def run(*args: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(DUE), "--json", *args],
        capture_output=True, text=True, check=False)
    return proc.returncode, json.loads(proc.stdout)


class TestMessyPlan(unittest.TestCase):
    def setUp(self) -> None:
        _, self.data = run("--today", "2026-09-16", str(MESSY))

    def test_due_commitment_found(self) -> None:
        self.assertEqual(len(self.data["due"]), 1)
        self.assertEqual(self.data["due"][0]["chapter"], "2")

    def test_plain_hyphen_heading_parses(self) -> None:
        """`## Ch 2 - Title` must parse the same as an em dash."""
        self.assertEqual(self.data["due"][0]["title"], "The Freedom Number")

    def test_status_is_case_insensitive(self) -> None:
        """A reader typing `Committed` should not silently drop the item."""
        self.assertEqual(self.data["due"][0]["status"], "Committed")

    def test_done_is_excluded(self) -> None:
        chapters = [r["chapter"] for r in self.data["due"] + self.data["upcoming"]]
        self.assertNotIn("1", chapters)

    def test_undated_is_surfaced_not_dropped(self) -> None:
        """An undated commitment is the core failure mode; it must stay visible."""
        self.assertEqual(len(self.data["undated"]), 1)
        self.assertEqual(self.data["undated"][0]["chapter"], "Intro")

    def test_future_review_is_upcoming(self) -> None:
        self.assertEqual([r["chapter"] for r in self.data["upcoming"]], ["3"])


class TestDemoPlan(unittest.TestCase):
    def test_wrapped_commitment_is_not_truncated(self) -> None:
        """Hand-wrapped values span lines and must be joined, not cut."""
        _, data = run("--today", "2026-09-16", str(DEMO))
        commitment = data["due"][0]["commitment"]
        self.assertTrue(commitment.endswith("without the phone in hand."),
                        f"truncated: {commitment!r}")
        self.assertNotIn("\n", commitment)

    def test_due_today_counts_as_due(self) -> None:
        _, data = run("--today", "2026-09-16", str(DEMO))
        self.assertEqual(len(data["due"]), 1)

    def test_not_yet_due_the_day_before(self) -> None:
        _, data = run("--today", "2026-09-15", str(DEMO))
        self.assertEqual(data["due"], [])
        self.assertEqual(len(data["upcoming"]), 1)


class TestExitCodes(unittest.TestCase):
    def test_nonzero_when_action_needed(self) -> None:
        code, _ = run("--today", "2026-09-16", str(DEMO))
        self.assertEqual(code, 1)

    def test_zero_when_nothing_open(self) -> None:
        code, _ = run("--today", "2026-01-01", str(DEMO))
        self.assertEqual(code, 0)

    def test_directory_scan_finds_plans(self) -> None:
        _, data = run("--today", "2026-09-16", str(ROOT / "examples"))
        self.assertEqual(len(data["due"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

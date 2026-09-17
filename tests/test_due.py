#!/usr/bin/env python3
"""Tests for bin/due.py.

Plan files are hand-edited by readers, so the parser is tested against a
deliberately messy fixture: hyphens instead of em dashes, capitalised
statuses, reordered fields, wrapped values, a non-numeric chapter, and a
commitment with no review date.
"""

import json
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DUE = ROOT / "bin" / "due.py"
MESSY = ROOT / "tests" / "fixtures" / "hand-edited-plan.md"
STATES = ROOT / "tests" / "fixtures" / "states-plan.md"
QUIET = ROOT / "tests" / "fixtures" / "stale-plan.md"
EXAMPLES = ROOT / "examples"
DEMO = EXAMPLES / "million-dollar-weekend-plan.md"
ATOMIC = EXAMPLES / "atomic-habits-plan.md"


def run(*args: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(DUE), "--json", *args],
        capture_output=True, text=True, check=False)
    return proc.returncode, json.loads(proc.stdout)


def run_text(*args: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(DUE), *args],
        capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout


def run_lint(*args: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(DUE), "--lint", *args],
        capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout


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


class TestStates(unittest.TestCase):
    """Behaviour tests point at a fixture, never at the shipped examples —
    editing an example should not break the suite."""

    def test_wrapped_commitment_is_not_truncated(self) -> None:
        _, data = run("--today", "2026-09-16", str(STATES))
        commitment = data["due"][0]["commitment"]
        self.assertTrue(commitment.endswith("truncate at the first newline."),
                        f"truncated: {commitment!r}")
        self.assertNotIn("\n", commitment)

    def test_due_today_counts_as_due(self) -> None:
        _, data = run("--today", "2026-09-16", str(STATES))
        self.assertEqual([r["chapter"] for r in data["due"]], ["1"])

    def test_not_yet_due_the_day_before(self) -> None:
        _, data = run("--today", "2026-09-15", str(STATES))
        self.assertEqual(data["due"], [])
        self.assertEqual({r["chapter"] for r in data["upcoming"]}, {"1", "2"})

    def test_every_resolved_state_is_excluded(self) -> None:
        """done, partial, skipped and dropped are all finished business."""
        _, data = run("--today", "2026-12-31", str(STATES))
        open_chapters = {r["chapter"] for r in data["due"] + data["upcoming"]}
        self.assertEqual(open_chapters, {"1", "2"})


class TestStale(unittest.TestCase):
    """A plan the reader stopped returning to. The quiet fixture's oldest
    commitment came due 2026-08-25 and the file was last written 2026-08-20."""

    def variant(self, tmp: str, **edits: str) -> str:
        """The quiet fixture with frontmatter lines swapped, for the cases
        that differ from it by one field."""
        text = QUIET.read_text(encoding="utf-8")
        for key, value in edits.items():
            text = re.sub(rf"^{key}: .*$", f"{key}: {value}",
                          text, count=1, flags=re.M)
        path = pathlib.Path(tmp) / "variant-plan.md"
        path.write_text(text, encoding="utf-8")
        return str(path)

    def test_gone_quiet_is_reported(self) -> None:
        _, data = run("--today", "2026-09-16", str(QUIET))
        self.assertEqual(len(data["stale"]), 1)
        entry = data["stale"][0]
        self.assertEqual(entry["days"], 22)  # since 2026-08-25
        self.assertEqual(entry["open"], 2)
        self.assertEqual(entry["oldest_review"], "2026-08-25")

    def test_threshold_is_days_waiting_not_days_since_edit(self) -> None:
        """Fourteen days after the review date, not after the last write —
        which was five days earlier."""
        _, on = run("--today", "2026-09-08", str(QUIET))
        _, before = run("--today", "2026-09-07", str(QUIET))
        self.assertEqual(len(on["stale"]), 1)
        self.assertEqual(before["stale"], [])

    def test_an_untouched_plan_with_future_reviews_is_not_stale(self) -> None:
        """The false positive worth avoiding: a commitment reviewed months
        out leaves the file untouched for months and nothing is wrong."""
        with tempfile.TemporaryDirectory() as tmp:
            path = self.variant(tmp, updated="2026-01-01")
            text = pathlib.Path(path).read_text(encoding="utf-8")
            text = text.replace("2026-08-25", "2027-08-25")
            text = text.replace("**Review on:** 2026-08-29",
                                "**Review on:** 2027-08-29")
            pathlib.Path(path).write_text(text, encoding="utf-8")
            _, data = run("--today", "2026-09-16", path)
        self.assertEqual(data["stale"], [])
        self.assertEqual(len(data["upcoming"]), 2)

    def test_coming_back_after_it_came_due_clears_stale(self) -> None:
        """Overdue and engaged is a different problem from overdue and gone;
        three skipped commitments is what answers the first one."""
        with tempfile.TemporaryDirectory() as tmp:
            path = self.variant(tmp, updated="2026-09-14")
            _, data = run("--today", "2026-09-16", path)
        self.assertEqual(data["stale"], [])
        self.assertEqual(len(data["due"]), 2)

    def test_finished_plan_never_goes_stale(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.variant(tmp, status="completed")
            _, data = run("--today", "2026-12-31", path)
        self.assertEqual(data["stale"], [])

    def test_no_updated_field_means_no_guessing(self) -> None:
        """Without `updated:` there is nothing to measure; the linter says so
        instead of the report inventing a date."""
        _, data = run("--today", "2026-12-31", str(MESSY))
        self.assertEqual(data["stale"], [])

    def test_stale_replaces_the_overdue_listing(self) -> None:
        """The whole point: not another day count on the same commitments."""
        _, out = run_text("--today", "2026-09-16", str(QUIET))
        self.assertIn("[stale]", out)
        self.assertIn("waiting 22 days", out)
        self.assertNotIn("overdue", out)

    def test_stale_after_zero_disables_it(self) -> None:
        _, data = run("--today", "2026-09-16", "--stale-after", "0", str(QUIET))
        self.assertEqual(data["stale"], [])
        _, out = run_text("--today", "2026-09-16", "--stale-after", "0",
                          str(QUIET))
        self.assertIn("22d overdue", out)

    def test_exit_code_signals_action_needed(self) -> None:
        code, _ = run("--today", "2026-09-16", str(QUIET))
        self.assertEqual(code, 1)

    def test_quiet_fixture_lints_clean(self) -> None:
        code, out = run_lint(str(QUIET))
        self.assertEqual(code, 0, out)


class TestShippedExamples(unittest.TestCase):
    """Content-agnostic: the examples must parse and lint, whatever they say."""

    def test_both_examples_parse(self) -> None:
        for path in (DEMO, ATOMIC):
            with self.subTest(path=path.name):
                _, data = run("--today", "2026-09-16", str(path))
                total = len(data["due"] + data["upcoming"] + data["undated"])
                self.assertGreaterEqual(total, 1, "no commitments parsed")

    def test_examples_directory_scan_finds_both_books(self) -> None:
        _, data = run("--today", "2026-12-31", str(EXAMPLES))
        books = {r["book"] for r in
                 data["due"] + data["upcoming"] + data["undated"]}
        self.assertEqual(len(books), 2, f"expected both example books: {books}")


class TestLint(unittest.TestCase):
    def test_shipped_examples_are_consistent(self) -> None:
        """Whatever the examples say, they must pass their own linter."""
        code, out = run_lint(str(EXAMPLES))
        self.assertEqual(code, 0, out)
        self.assertIn("consistent", out)

    def test_states_fixture_is_consistent(self) -> None:
        code, out = run_lint(str(STATES))
        self.assertEqual(code, 0, out)

    def test_resolved_without_takeaway_is_flagged(self) -> None:
        """A done commitment with no takeaway loses the point of the tool."""
        code, out = run_lint(str(MESSY))
        self.assertEqual(code, 1)
        self.assertIn("no Takeaway", out)

    def test_commitment_without_review_date_is_flagged(self) -> None:
        _, out = run_lint(str(MESSY))
        self.assertIn("not a commitment", out)

    def test_missing_updated_is_flagged(self) -> None:
        """A plan with open commitments and no `updated:` cannot be told
        apart from one being worked on."""
        _, out = run_lint(str(MESSY))
        self.assertIn("no `updated:`", out)

    def test_missing_log_is_flagged(self) -> None:
        _, out = run_lint(str(MESSY))
        self.assertIn("no ### Log", out)

    def test_chapter_count_counts_blocks_not_completions(self) -> None:
        """`chapters: N / M` is progress through the book: it must not drop
        when a commitment is skipped rather than done. The states fixture
        says 6 / 6 with four chapters resolved and two still open."""
        _, out = run_lint(str(STATES))
        self.assertNotIn("worked through but", out)


class TestExitCodes(unittest.TestCase):
    def test_nonzero_when_action_needed(self) -> None:
        code, _ = run("--today", "2026-09-16", str(STATES))
        self.assertEqual(code, 1)

    def test_zero_when_nothing_due_or_undated(self) -> None:
        code, _ = run("--today", "2026-01-01", str(STATES))
        self.assertEqual(code, 0)

    def test_directory_scan_finds_plans(self) -> None:
        _, data = run("--today", "2026-09-16", str(ROOT / "tests" / "fixtures"))
        found = {r["book"] for r in data["due"] + data["upcoming"]
                 + data["undated"]}
        self.assertIn("Test Book, A. Author", found)


if __name__ == "__main__":
    unittest.main(verbosity=2)

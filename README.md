<div align="center">

# 📕 book-to-plan

**Turn an actionable book into commitments you actually keep.**

A Claude Code skill that walks you through a book one chapter at a time,
converts each chapter into a dated action built from the author's own exercise
and your own life, then holds you to it.

[![tests](https://github.com/ferdelamad/book-to-plan/actions/workflows/test.yml/badge.svg)](https://github.com/ferdelamad/book-to-plan/actions/workflows/test.yml)
[![Agent Skills](https://img.shields.io/badge/standard-Agent%20Skills-6b46c1)](https://code.claude.com/docs/en/skills)
[![local first](https://img.shields.io/badge/data-100%25%20local-2ea44f)](#-reminders)
[![platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey)](#-requirements)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

[Why](#-why) · [What you get](#-what-you-get) · [Install](#-install) ·
[Usage](#-usage) · [How it works](#-how-it-works) · [Reminders](#-reminders) ·
[Which books](#-which-books-work)

**One chapter per session. One commitment per chapter. Nothing leaves your machine.**

</div>

---

**1. Point it at a book.** A PDF you own, or just the title.

**2. Answer three questions per chapter.** A name, a time, a place — the
specifics a real action can't be written without.

**3. Get one commitment, with a date and a first physical move.** Then it
stops and waits for you to actually do it.

---

## 🤔 Why

You finished the book. You highlighted the good parts. You did none of it.

The tooling that exists makes books *searchable* — ask a question, get a cited
answer. That's genuinely useful, and it isn't the problem. The problem is that
business, entrepreneurship and self-help books are full of instructions nobody
executes, and a summary of an instruction is still not a completed instruction.

`book-to-plan` does one thing: it refuses to let a chapter end without a
specific action, a date, and a first physical move.

> Every competing tool answers *what does the book say*. This one answers
> *what did you do about it*.

---

## 📋 What you get

One Markdown file per book that you own, can hand-edit, and can read in ten
years without this tool.

| Field | What it holds |
|---|---|
| **The claim** | The chapter in one sentence |
| **Why it matters here** | Tied to your 90-day outcome, not the book's |
| **Author's challenge** | The author's own exercise, split in-session / in-field |
| **What they said** | Your answers, verbatim — including *why* |
| **Commitment** | One action, a date, a time and place, a first physical move |
| **Review on** | When you get asked how it went |
| **Takeaway** | Written *after* the action, never from the text |
| **Log** | Append-only history of what actually happened |

Two worked examples, three chapters each, two different readers:

- 📗 **[Million Dollar Weekend](examples/million-dollar-weekend-plan.md)** — a
  dev who built two projects and showed neither to a stranger. Shows a
  challenge-heavy book, and a `partial` outcome where the ask happened but the
  rule got broken.
- 📘 **[Atomic Habits](examples/atomic-habits-plan.md)** — a teacher trying to
  be asleep by 10:30. Shows a theory-heavy book where chapters prescribe
  nothing, and a `dropped` commitment the reader declined on purpose.

<details>
<summary><strong>See a chapter run</strong></summary>

```
You  /book-to-plan ~/Downloads/million-dollar-weekend.pdf

...  Ch 2 — The Unlimited Upside of Asking

     The Ask muscle is trainable and rejection is the training load. Setting
     a Rejection Goal turns each no into progress toward a quota instead of
     evidence against you — and a follow-up ask is roughly twice as likely to
     land as the first.

     Kagan's challenge here is the Coffee Challenge: make a purchase in
     person and ask for 10 percent off, saying nothing else.

     Both your dead projects died at the ask, not the build. So:
       1. Which coffee shop do you already go to, and on what days?
       2. What makes asking a barista worse than cold email, in your words?
       3. How many noes are you aiming for, and by when?

You  Blue Bottle on 2nd, Tuesdays and Thursdays. It's worse because the
     person is right there and I have to watch their face. 25 noes, I guess?

...  Rejection Goal set: 25 noes by Oct 31, in your header.

     Commitment — At Blue Bottle on 2nd, Tue Sep 15 at 8:20am, order the
     usual and ask for 10 percent off. Say nothing after asking. First move
     is walking in without your phone in your hand.
     Review on: Sep 16.
```

</details>

---

## 📥 Install

```bash
git clone https://github.com/ferdelamad/book-to-plan ~/.claude/skills/book-to-plan
```

Restart Claude Code, and the skill is available.

> The install path matters on macOS. `~/.claude/` is readable by background
> agents; `~/Documents` is not. See [Reminders](#-reminders).

---

## 🚀 Usage

```
/book-to-plan <book title or PDF path>
```

| Command | What it does |
|---|---|
| `/book-to-plan ~/book.pdf` | Ground the book, set your situation, start chapter 1 |
| `/book-to-plan` | Resume — reviews anything due before opening a new chapter |
| `due.py ~/book-plans` | What's due right now — and what's gone quiet |
| `due.py --lint ~/book-plans` | Check a hand-edited plan still holds together |

---

## 🧠 How it works

### One chapter per session, then it stops

No dumping twelve chapters of advice you'll never action. Finish one, get your
commitment, leave.

### It uses the author's exercise, not an invented one

Actionable books prescribe their own — `CHALLENGE` blocks, end-of-chapter
questions, worksheets. Those get harvested during setup and sorted into two
kinds. **The test is whether it can be finished right now**, not whether it
involves another person:

| Kind | Test | Where it goes |
|---|---|---|
| **In-session** | Answerable from what you already know, under 5 min | Done *during the conversation*, stored in your plan header |
| **In-field** | Needs time, a place, another person, or research | Becomes your commitment |

That split is the single most important thing in here. "Decide your values by
Friday" is how a plan dies.

When a chapter prescribes nothing — Atomic Habits 1–3 are pure argument — the
action gets derived from the chapter's claim, and the plan records that it was
derived, so in six months you can still tell the author's instruction from
Claude's.

### One commitment per chapter

Chapter 3 of *Million Dollar Weekend* has five challenges. You get one; the
rest are parked. Twelve ideas and zero actions is the failure mode of every
book summary ever written.

Where several are possible, it picks the one closest to **where you said your
past attempts broke**. A reader who builds but never asks needs the asking
exercise, not the third idea-generation worksheet.

### Every commitment passes four bars

| | |
|---|---|
| **Specific to you** | Your words, your calendar, named people and places. One that would fit any reader has failed. |
| **Doable this week** | Inside the hours you actually have. |
| **Physically startable** | First move takes under two minutes. |
| **Observably done** | Or not done, on the review date. |

"Start journaling" fails all four and gets rewritten with you.

### "I decided not to" is a valid ending

Commitments resolve as `done`, `partial`, `skipped` or `dropped`. A reader who
tries an idea against their own life and rejects it has used the book
correctly. Nothing here treats that as failure — a tool that does becomes a
tool you stop opening.

### The takeaway is written after the action

Not from the text. It's what you learned by doing it, which is usually not what
the chapter said:

> The idea was never the bottleneck. One text to someone who already knew the
> answer beat eighteen months of solo building — and the reason it took
> eighteen months was that asking felt like a bigger commitment than building.
> It isn't; it's two minutes.

No summary of the book could have produced that. It's the part that's yours.

---

## ⏰ Reminders

A commitment that only surfaces when you open a terminal is not
accountability.

```bash
~/.claude/skills/book-to-plan/bin/install-reminders.sh ~/book-plans 9 0
```

A launchd agent checks your plans each morning at 09:00 and turns a due
commitment into a macOS notification. No server, no account, nothing leaving
the laptop.

Check by hand any time:

```
$ python3 bin/due.py ~/book-plans

1 commitment(s) due as of 2026-09-19:

  [due today] Atomic Habits, James Clear — Ch 3: How to Build Better Habits
     Wed through Fri, the moment you reach for the phone after grading, write
     down what happened in the ten seconds before. Three nights, one line
     each. First move is putting the pen on top of the calendar now.
     ~/book-plans/atomic-habits-plan.md
```

Exits non-zero when something needs action, so it composes in a shell prompt
or a git hook. `--json` for scripting.

### When you stop coming back

The real failure mode isn't skipping a commitment, it's quietly not opening
the plan again. Counting the days late doesn't help by then — you know — so
once the oldest waiting commitment is two weeks past its review date with
nothing written since, the report stops listing it and says the other thing:

```
$ python3 bin/due.py ~/book-plans

1 plan(s) gone quiet:

  [stale] Atomic Habits, James Clear — waiting 22 days, last touched 2026-08-20
     2 commitment(s) still open, oldest review was due 2026-08-25.
     Counting the days late stopped being useful here. The honest options are
     to restart the plan, drop it, or revisit the week shape it was built for.
     ~/book-plans/atomic-habits-plan.md
```

The morning notification changes with it, and the skill opens that session by
asking which of the three you want rather than reviewing a month-old
commitment as though it were yesterday's. Overdue but still being edited
isn't stale — that's a plan you're in, and three skips in a row is what
answers it. `--stale-after N` moves the line, `0` turns it off.

Because you're meant to hand-edit these files, there's a linter for when an
edit breaks something:

```
$ python3 bin/due.py --lint ~/book-plans

2 problem(s):

  atomic-habits-plan.md: Ch 4 — done but no Takeaway — the takeaway is
    written after the action, and it is the point
  atomic-habits-plan.md: Ch 6 — commitment with no Review on — an intention,
    not a commitment
```

### ⚠️ macOS caveat, found the hard way

Privacy protection (TCC) blocks background agents from reading `~/Documents`,
`~/Desktop` and `~/Downloads`. An agent pointed at one of those installs fine
and then fails every morning with `Operation not permitted`.

This applies to **both** your plan directory and the location you run the
installer from — a clone sitting in `~/Documents` can't be read by launchd
either, which is why the install path is `~/.claude/skills/`. The installer
checks both and refuses with instructions rather than failing silently at nine
every morning.

### Unscheduled commitments don't get to hide

A commitment with no review date is an intention. The checker surfaces those
separately, every run, until they get a date or get dropped:

```
1 commitment(s) with no review date (an intention, not yet a commitment):
  [unscheduled] Million Dollar Weekend — Ch Intro: Why This Book
     no review date set on purpose, still thinking
```

"I'll get to it" is the exact thing these books are written against.

---

## 📚 Which books work

| | Examples |
|---|---|
| ✅ **Good fit** | Business and entrepreneurship (*Million Dollar Weekend*, *$100M Offers*, *The Mom Test*), self-help and habits (*Atomic Habits*, *Deep Work*), craft and career books with exercises |
| ❌ **Bad fit** | Narrative non-fiction, history, biography, anything that asks nothing of the reader |

A book with named exercises harvests cleanly. A book that prescribes inline
prose works too — *Atomic Habits* returns zero hits on an exercise scan and is
still a good fit. Only a book that asks nothing anywhere is the wrong input,
and the skill says so rather than inventing busywork to look useful.

---

## 🔧 Requirements

<details>
<summary><strong>Expand</strong></summary>

| | |
|---|---|
| **Claude Code** | Any recent version with skills support |
| **Python 3** | System `python3` is fine — no packages needed |
| **PDF text** *(optional)* | `pdftotext` (`brew install poppler`) or `pypdf`. Without either, PDFs are read directly. |
| **Reminders** *(optional, macOS)* | `launchd` and `osascript`, both built in |

The parser and linter run anywhere Python does. Only the reminder installer is
macOS-specific.

</details>

## 📁 Repository structure

<details>
<summary><strong>Expand</strong></summary>

```
SKILL.md                    the skill — steps, quality bars, review loop
reference/plan-format.md    the plan file schema
bin/due.py                  what's due; non-zero exit when action is needed
bin/install-reminders.sh    register or remove the daily launchd check
examples/                   two worked plans, three chapters each
tests/test_due.py           32 tests
tests/fixtures/             a messy hand-edited plan, and one gone quiet
```

Plan files are hand-edited by real people, so the parser is tested against a
fixture with hyphens instead of em dashes, capitalised statuses, reordered
fields, wrapped values, a non-numeric chapter and a missing review date:

```bash
python3 tests/test_due.py
```

</details>

---

## 🧾 Copyright & fair use

This tool does not contain, redistribute or reproduce any book. It reads a copy
**you already own**, on your machine, and writes down *your* commitments in
response to it. The plan files quote a chapter's claim and the author's own
exercise in brief, the way notes in a margin do.

Buy the book. The exercises are the author's work and they're worth paying for.

## Status

Early. The loop and the tooling work and are tested; the plan format has been
through six revisions driven by actually using it. Expect the schema to move
before it settles.

Issues and PRs welcome — especially reports of which books' exercises harvest
cleanly and which don't.

## License

MIT — see [LICENSE](LICENSE).

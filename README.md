# book-to-plan

**Turn a book you've read into commitments you actually keep.** A Claude Code
skill that walks you through an actionable book one chapter at a time, converts
each chapter into a dated action built from the author's own exercise and your
own life, and then holds you to it.

Everything stays on your machine. One Markdown file per book that you own, can
edit, and can read in ten years without this tool.

---

## The problem

You finished the book. You highlighted the good parts. You did none of it.

The tooling that exists makes books *searchable* — ask a question, get a cited
answer. That's genuinely useful, and it is not the problem. The problem is that
business, entrepreneurship and self-help books are full of instructions nobody
executes, and a summary of an instruction is still not a completed instruction.

`book-to-plan` does one thing: it refuses to let a chapter end without a
specific action, a date, and a first physical move.

## What a chapter looks like

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

Full worked example, two chapters with real state:
**[examples/million-dollar-weekend-plan.md](examples/million-dollar-weekend-plan.md)**

## Install

```bash
git clone https://github.com/ferdelamad/book-to-plan \
  ~/.claude/skills/book-to-plan
```

Then in any Claude Code session:

```
/book-to-plan <book title or PDF path>
```

Requires Python 3 (system `python3` is fine). `pdftotext` or `pypdf` help with
PDFs but are not required.

## How it works

**One chapter per session, then it stops.** No dumping twelve chapters of
advice you'll never action. Finish one, get your commitment, leave.

**It uses the author's exercise, not an invented one.** Actionable books
prescribe their own — `CHALLENGE` blocks, end-of-chapter questions,
worksheets. Those get harvested during setup and sorted into two kinds:

- **In-session** — a decision needing nobody else (pick your Freedom Number,
  name your target customer). These get done *during the conversation* and
  stored in your plan header. They never become homework, because "decide
  your values by Friday" is how a plan dies.
- **In-field** — needs another person, a place, a time. These become your
  commitments.

That split is the single most important thing in here.

**One commitment per chapter.** Chapter 3 of *Million Dollar Weekend* has four
challenges. You get one; the rest are parked. Twelve ideas and zero actions is
the failure mode of every book summary ever written.

**Every commitment passes four bars** or gets rewritten with you:

| | |
|---|---|
| Specific to you | Your words, your calendar, named people and places. One that would fit any reader has failed. |
| Doable this week | Inside the hours you actually have. |
| Physically startable | First move takes under two minutes. |
| Observably done | Or not done, on the review date. |

"Start journaling" fails all four.

**"I decided not to" is a valid ending.** Commitments resolve as `done`,
`partial`, `skipped` or `dropped`. A reader who tries an idea against their own
life and rejects it has used the book correctly. Nothing here treats that as
failure, because a tool that does becomes a tool you stop opening.

**The takeaway is written after the action, not from the text.** It's what you
learned by doing it, which is usually not what the chapter said:

> The idea was never the bottleneck. One text to someone who already knew the
> answer beat eighteen months of solo building — and the reason it took
> eighteen months was that asking felt like a bigger commitment than building.
> It isn't; it's two minutes.

No summary of the book could have produced that. It's the part that's yours.

## Reminders

A commitment that only surfaces when you open a terminal is not
accountability.

```bash
~/.claude/skills/book-to-plan/bin/install-reminders.sh ~/book-plans 9 0
```

A launchd agent checks your plans each morning at 09:00 and turns a due
commitment into a macOS notification. No server, no account, nothing leaving
the laptop.

You can also check by hand at any time:

```
$ python3 bin/due.py ~/book-plans

1 commitment(s) due as of 2026-09-16:

  [due today] Million Dollar Weekend, Noah Kagan — Ch 2: The Unlimited Upside of Asking
     At Blue Bottle on 2nd, Tue 2026-09-15 at 8:20am, order the usual and ask
     for 10 percent off — say nothing after asking. First move is walking in
     without the phone in hand.
     /Users/you/book-plans/million-dollar-weekend-plan.md
```

Exits non-zero when something needs action, so it composes in a shell prompt
or a git hook. `--json` for scripting.

Because you're meant to hand-edit these files, there's a linter for when an
edit breaks something:

```
$ python3 bin/due.py --lint ~/book-plans

2 problem(s):

  ~/book-plans/atomic-habits-plan.md: Ch 4 — done but no Takeaway — the
    takeaway is written after the action, and it is the point
  ~/book-plans/atomic-habits-plan.md: Ch 6 — commitment with no Review on —
    an intention, not a commitment
```

**macOS caveat, found the hard way:** privacy protection (TCC) blocks
background agents from reading `~/Documents`, `~/Desktop` and `~/Downloads`. A
plan kept in a project folder under one of those installs fine and then fails
every morning with `Operation not permitted`. The installer refuses those paths
and tells you what to do instead; `~/book-plans` is the default for this
reason.

## Unscheduled commitments don't get to hide

A commitment with no review date is an intention. The checker surfaces those
separately, every run, until they get a date or get dropped:

```
1 commitment(s) with no review date (an intention, not yet a commitment):
  [unscheduled] Million Dollar Weekend — Ch Intro: Why This Book
     no review date set on purpose, still thinking
```

"I'll get to it" is the exact thing these books are written against.

## Which books work

**Good fit** — business and entrepreneurship (*Million Dollar Weekend*,
*$100M Offers*, *The Mom Test*), self-help and habit books (*Atomic Habits*,
*Deep Work*), craft and career books with exercises.

**Bad fit** — narrative non-fiction, history, biography, and anything without
prescribed action. The skill will tell you so rather than inventing busywork to
look useful.

## Prior art, and how this differs

This space already has good tools and they solve a different problem. Credit
where it's due:

- **[book-to-skill](https://github.com/virgiliojr94/book-to-skill)** — turns a
  book into a queryable reference you consult while you work. Excellent at
  that. It extracts structure, not obligations.
- **[the-knowledge-guy](https://github.com/vitalysim/the-knowledge-guy)** —
  your bookshelf as a tutor: ask, walk, quiz, cheatsheet. Its resumable
  `walk` mode is the closest prior art to what's here, and the resume-first
  pattern and append-only progress grammar in this repo are lifted from it.
- **NotebookLM / RAG** — search across a library.

All three answer *what does the book say*. This one answers *what did you do
about it*. If you want to look something up, use those. If you want the book to
change your week, use this.

## Layout

```
SKILL.md                  the skill — steps, quality bars, review loop
reference/plan-format.md  the plan file schema
bin/due.py                what's due; exits non-zero when action is needed
bin/install-reminders.sh  register or remove the daily launchd check
examples/                 a real two-chapter plan
tests/                    parser tests against a deliberately messy plan
```

Plan files are hand-edited by real people, so the parser is tested against a
fixture with hyphens instead of em dashes, capitalised statuses, reordered
fields, wrapped values, a non-numeric chapter and a missing review date:

```bash
python3 tests/test_due.py
```

## Status

Early. The loop and the tooling work and are tested; the format has been
through three revisions driven by actually using it. Expect the plan schema to
move before it settles.

Issues and PRs welcome — especially reports of which books' exercises harvest
cleanly and which don't.

## License

MIT — see [LICENSE](LICENSE).

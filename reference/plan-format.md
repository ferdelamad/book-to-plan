# Plan file format

The plan file is the only source of truth. Claude is its only writer; the
reader may hand-edit it freely. Anything else — a rendered page, a summary,
a reminder — is a projection, regenerated rather than edited.

It is Markdown because the reader owns it: readable without tooling,
diffable in git, editable when a commitment is worded wrong, and portable
when they stop using this skill.

Name it `<book-slug>-plan.md`, in `~/book-plans/` unless the reader asks for
it somewhere else. A second run through the same book years later is
`<book-slug>-plan-2.md`, not an overwrite.

## Header

```markdown
---
book: <title>, <author>
edition: <what the chapter map was grounded against>
started: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
chapters: <N worked through> / <M total>
status: in_progress | completed | abandoned
---

# <Book title> — action plan

**90-day outcome:** <observable, with how it gets measured>
**Week shape and constraints:** <the hours a step must fit inside>
**Already tried:** <and where it broke>
**Accountability:** <daily | weekly | none>
```

Below those, **setup values** — the reader constants an author asks you to
fix once and then reuse. Million Dollar Weekend's Freedom Number, a budget,
a target customer, a rejection quota. They belong in the header rather than
in a chapter, because later chapters refer back to them:

```markdown
**Freedom Number:** $2,000/month — rent share $1,200, childcare $500.
Set in session on 2026-09-12 (ch 1).
```

## Chapter block

```markdown
## Ch <N> — <title>

**Status:** committed | done | partial | skipped | dropped
**The claim:** <one sentence>
**Why it matters here:** <one sentence, tied to the 90-day outcome>
**Author's challenge (in-field):** <the author's own exercise, if there is one>
**Author's challenge (in-session, done <date>):** <exercise + the answer>
**What they said:** <their answers, verbatim where it matters>
**Commitment:** <action> — <date>, <time and place>, first move is <physical action>
**Review on:** <YYYY-MM-DD>
**Takeaway:** <written only after the outcome is known>
**Parked for later:** <the chapter's other ideas, one line each>

### Log
- <YYYY-MM-DD> committed — review set for <date>
- <YYYY-MM-DD> <state> — <what actually happened, in their words>
```

### Field rules

- **Status** is one of five. `due` is never stored — it is derived by
  comparing `Review on` to today, so it cannot go stale.
- **Review on** is required for a commitment to exist. Without it the item
  is an intention, and `bin/due.py` surfaces it as unscheduled every run.
- **Takeaway** is what the reader learned by *doing* it, and it is empty
  until the outcome is in. A takeaway written from the text is a book
  summary; this file is not that.
- **chapters** counts chapter blocks written, not commitments completed.
  Progress through the book must not go down when a commitment is skipped.
- **Log** is append-only. Earlier lines are never rewritten, because the
  history of what happened is worth more than the current state.
- Nothing references another file by name. Chapter number and title live
  inline; foreign keys drift and then need a migration script.

### States

| State | Meaning |
|---|---|
| `committed` | Agreed, review date in the future. |
| `done` | It happened. |
| `partial` | Some of it happened — record which part, in their words. |
| `skipped` | It did not happen and the reader still wants it. |
| `dropped` | The reader decided against it on purpose. |

`dropped` is a legitimate ending. A reader who tries an idea against their
own life and rejects it has used the book correctly.

## Index line

Add one line to `MEMORY.md` in the project's memory directory, so open
plans are visible at session start rather than needing to be remembered:

```
- [Plan: <book>](<path>) — chapter N/M, <K> due, last touched <date>
```

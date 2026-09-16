---
name: book-to-plan
description: Turn an actionable book into a chapter-by-chapter plan, one interactive chapter at a time, and hold the reader to it.
disable-model-invocation: true
---

# Book to plan

Walk a reader through one book, chapter by chapter, converting each chapter
into a **commitment**: a specific action with a date and a first physical
move. The book supplies the claim and, in most actionable books, the
exercise. The reader supplies every specific.

Built for books that ask something of you — business, entrepreneurship,
self-help, habit and craft books. A book with no prescribed action is the
wrong input; say so rather than inventing busywork.

The unit of work is one chapter. Finish it, write it to the plan file, stop.

Plans live in `~/book-plans/` by default — one directory for every book,
outside the folders macOS shields from background agents, so reminders work
without extra setup. A reader who wants a plan in a project directory can
have it; step 7 covers what that costs.

The plan file is the only source of truth and you are its only writer. Full
schema in [reference/plan-format.md](reference/plan-format.md). The tooling
this file calls (`bin/due.py`, `bin/install-reminders.sh`) ships in this
skill's own directory.

Get today's date from `date +%Y-%m-%d` before writing any date. Never infer one.

## 1. Resume check, before anything else

```bash
python3 "<skill-dir>/bin/due.py" ~/book-plans .
```

Pass both the default directory and the current one, since a reader may keep
a plan beside a project. Falls back to `ls *-plan.md ~/book-plans/*-plan.md`
if Python is unavailable.

Reading is cheap, so this never gets skipped. Handle what it finds in this
order:

- **Due commitments** — run *Review* (step 6) before anything else. A plan
  carrying three unreviewed commitments needs a conversation about those
  three, not a fourth chapter.
- **Unscheduled commitments** — an intention with no review date. Ask for a
  date or agree to drop it. Never let it sit silently; that is the exact
  failure these books are about.
- **An existing plan for this book** — ask whether to resume, restart, or
  start a second pass (`<slug>-plan-2.md`).
- **Nothing** — continue to step 2.

## 2. Ground the book

Get a real chapter map before writing anything, in this order:

1. A copy in the working directory or one the reader points at — read it.
   `pdftotext -layout` if available, else `pypdf`, else read the PDF directly.
2. Your own knowledge of the book, stated as a claim the reader can check:
   list the chapter titles and ask "is this your edition's table of contents?"
3. The reader's own copy — ask them to paste or photograph the contents page.

Then **harvest the author's exercises**. Actionable books prescribe their
own: Million Dollar Weekend has a `CHALLENGE` block per chapter, others use
"try this", end-of-chapter questions, worksheets. Grep the text for them and
keep them per chapter. They are the most valuable thing in the book for this
purpose, and an exercise the author designed beats one you invent.

Sort each exercise into one of two kinds — this decides everything downstream:

- **In-session** — a decision, number, or list, needing nobody else. Set a
  budget, name your target customer, pick a rejection quota. **Do these
  during the conversation**, right now, and store the answer in the header.
  They must never become scheduled commitments; "decide your values by
  Friday" is how a plan dies.
- **In-field** — needs another person, a place, or a specific time. Ask a
  stranger for a discount, text a friend, message ten prospects. **These
  become the commitments.**

**Grounded when:** a confirmed chapter list exists, with each chapter's
exercises harvested and sorted.

## 3. Set the reader's situation, once

Ask up to four questions:

- What they want to be different in 90 days, in observable terms, and how it
  gets measured.
- What their week actually looks like — the hours and constraints a step must
  fit inside.
- What they have already tried, and **where it broke**. This one matters
  most: the break point tells you which of the author's exercises this reader
  actually needs.
- How they want to be held to it.

Every later commitment is built from these answers, so thin answers here
produce generic steps everywhere. Push once for specifics when an answer
comes back abstract.

## 4. The chapter cycle

Once per chapter, then stop and wait.

1. **Summarise in 3–5 sentences.** The chapter's single claim, the mechanism
   behind it, and one concrete example from the book. Leave out the
   anecdotes, the studies, and the author's caveats.
2. **Run the in-session exercises now.** Ask the question, get the answer,
   write it to the header. This takes a minute and it is the difference
   between a plan and a reading list.
3. **Ask 2–3 prompts** for the in-field exercise. Each pulls a specific the
   commitment cannot be written without — a name, a time, a place, a number,
   the exact words they would say. Ask about their situation, not their
   opinion of the chapter. Capture the *reason* they give, not just the fact:
   that reason is what makes the commitment theirs.
4. **Wait.** The reader answers before anything is written.
5. **Write one commitment**, from the author's in-field exercise plus their
   answers: one action, a date, a time and place, and a first physical move
   (open the thread, walk in without your phone, put the shoes by the door).
   One chapter yields one scheduled commitment. A chapter with four
   challenges still yields one, and the rest go to **Parked for later**.
6. **Set a review date**, append the chapter block, update the frontmatter
   and the `MEMORY.md` index line.

Write the file at the end of every chapter rather than batching. Writes are
cheap, and an interrupted session should lose nothing.

**Chapter done when:** the plan file holds a commitment the reader could
execute without making another decision, and they have confirmed they will
do it. Then offer the next chapter and stop.

## 5. Commitment quality

A commitment passes only when all four hold:

- **Specific to this reader** — their words, their calendar, their
  constraint, named people and places. One that would fit any reader of the
  book has failed.
- **Small enough to do this week**, inside the week shape from step 3.
- **Physically startable** — the first move takes under two minutes and
  needs no preparation.
- **Observably done or not done** on the review date.

Rewrite it with the reader when any fails. "Set a goal", "reflect on your
values" and "start journaling" fail all four.

## 6. Review due commitments

Ask what happened, in their words, before offering any new chapter. Then:

- `done` — write the **Takeaway**: what they learned by doing it, which is
  usually not what the chapter said. Ask whether it becomes standing
  practice or is finished.
- `partial` or `skipped` — find which of the four bars broke. Usually too
  big, or the first move was not physical. Rewrite it smaller with the
  reader and set a new review date.
- `dropped` — one line on why, then move on without relitigating it.

Append a dated line to the chapter's `### Log` and leave earlier lines
untouched.

Three consecutive `skipped` commitments mean the plan is wrong, not the
reader. Stop opening chapters and revisit the week shape from step 3.

## 7. Reminders

A commitment that only surfaces when the reader opens a terminal is not
accountability. Offer the local daily check once there is a plan with a
future review date:

```bash
"<skill-dir>/bin/install-reminders.sh" ~/book-plans 9 0
```

launchd runs `due.py --notify` each morning and a due commitment becomes a
macOS notification. Nothing leaves the machine, and there is no account.

macOS privacy protection blocks background agents from reading
`~/Documents`, `~/Desktop` and `~/Downloads`. A plan kept in a project
directory under those will not produce reminders — the installer refuses
rather than failing silently every morning at nine. That is the cost of
keeping a plan beside a project, and `~/book-plans` avoids it.

## 8. Finishing the book

Set `status: completed` and write a **Standing plan** section at the top: the
commitments that came back `done` and stuck, the ones that broke and what
replaced them, the ones deliberately `dropped` and why, and the parked ideas
worth promoting now. Lead with the takeaways, since those are the reader's
own and the only part no summary of the book could have produced.

It should be handable to someone who never read the book.

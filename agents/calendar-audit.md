# Calendar audit (daily 04:00)

Question: is everything in the owner's calendar for the next 7 days prioritised clearly and in line with the goals in `CLAUDE.md`, and should anything take more or less time. Runs in the background chat `calendar audit`. Needs a calendar the agent can read (`tools.md` > "Calendar"); the carry-over, one it can edit.

## Steps
1. Schedule check (below). Read the next 7 days of every calendar the owner has, a work account's included, so a clash between them shows, and the last 3 days of the main one (`CLAUDE.md` > "Schedule").
2. Carry over open to-dos. With a calendar tool that can edit events, a to-do (a step for the owner alone: no other person on it, not a call, bill or deadline) still on a past day of the main calendar is not done, since a done one is deleted: move it to today, same time if free, else a free slot in their first work hour; an all-day one to today all day. On the owner's day off (`CLAUDE.md` > "Schedule"), their next workday takes the place of today. Without an edit tool, list them in the message to `Chief of Staff` instead.
3. Judge the next 7 days against the goals in `CLAUDE.md` and the ordinary day in `CLAUDE.md` > "Schedule": priorities clear, time per item right, conflicts, gaps, rest missing from the weekend. Blocks the owner asked for themselves stay; don't question them. A commit or message time is not the owner working - agents commit while they sleep.
4. Anything else worth changing goes to `Chief of Staff` via `SendMessage`: the event, the change, why. Beyond the carry-over, the audit does not edit the calendar. Nothing to change - send nothing.

## Schedule
At the start of every run, check the chat's scheduled messages; if no next audit exists, schedule one for tomorrow at 04:00 with the body `Calendar audit: read agents/calendar-audit.md and follow it, including scheduling the next run.`. Messages do not repeat; this keeps the series alive.

## Switch on
New Zucchini chat in this repo, titled exactly `calendar audit`; paste:
```
You run the daily calendar audit. Read CLAUDE.md and agents/calendar-audit.md, run the audit now and keep its schedule alive as the playbook says. This is a background chat I never read: anything for me goes to Chief of Staff via SendMessage.
```
Then set its row in `agents/CLAUDE.md` to `on`.

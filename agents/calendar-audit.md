# Calendar audit (daily 04:00)

Question: is everything in the owner's calendar for the next 7 days prioritised clearly and in line with the goals in `CLAUDE.md`, and should anything take more or less time. Runs in the background chat `calendar audit`. Needs a calendar the agent can read (`tools.md` > "Calendar").

## Steps
1. Schedule check (below). Sync the repo, then read the next 7 days of the calendar.
2. Judge them against the goals in `CLAUDE.md` and the ordinary day in `CLAUDE.md` > "Schedule": priorities clear, time per item right, conflicts, gaps, rest missing from the weekend. Blocks the owner asked for themselves stay; don't question them. A commit or message time is not the owner working - agents commit while they sleep.
3. Anything worth changing goes to `Chief of Staff` via `SendMessage`: the event, the change, why. The audit does not edit the calendar itself. Nothing to change - send nothing.

## Schedule
At the start of every run, `"$ZUCCHINI_SPAWNER_BIN" scheduled-messages list`; if no next audit exists, `"$ZUCCHINI_SPAWNER_BIN" scheduled-messages create --body "Calendar audit: read agents/calendar-audit.md and follow it, including scheduling the next run." --at <tomorrow at 04:00>` (naive local datetime). Messages do not repeat; this keeps the series alive.

## Switch on
New Zucchini chat in this repo, titled exactly `calendar audit`; paste:
```
You run the daily calendar audit. Read CLAUDE.md and agents/calendar-audit.md, run the audit now and keep its schedule alive as the playbook says. This is a background chat I never read: anything for me goes to Chief of Staff via SendMessage.
```
Then set its row in `agents/CLAUDE.md` to `on`.

Without Zucchini: cron `0 4 * * *` runs `claude -p "Calendar audit: read agents/calendar-audit.md and follow it; skip scheduling."`.

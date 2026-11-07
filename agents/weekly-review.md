# Weekly strategy review (Wednesday 02:00)

Question: over the last 7 days, did the owner move toward the goals in `CLAUDE.md`, in their order - and what should change in the whole strategy, not just this week's tasks. Runs in the background chat `weekly review`.

## Inputs (last 7 days)
- `git log --since="7 days ago" --stat` - what was actually done.
- The calendar for the past week (`tools.md` > "Calendar") and the ordinary day in `CLAUDE.md` > "Schedule" - what was planned vs what happened.
- The topic file behind each goal (money, work, health...): where each stands now.
- The most recent earlier review in `weekly-reviews/` - were its corrections followed. If today's review already exists, update that entry rather than treating it as last week's baseline or adding a duplicate.

## What to judge
1. **The top goal first:** where it stands in numbers (money: runway in weeks, income started or not; a job: pipeline by stage). It outranks everything until it is met.
2. **Time allocation:** effort on the chosen roads vs everything else. Name the clearest diversion from the current priority; tell work for a later goal apart from work serving no goal. Do not infer hours from commit counts.
3. **What converts:** which road or channel produced results this week, which is dead and should be dropped. Results usually come from work done weeks before; say which week's work produced them.
4. **Strategy flaws:** contradictions between what the owner decided and what they did; roads to close or open; assumptions the week's evidence broke.
5. **Energy:** signs of a down or peak state; the people goals not dropped to zero.

## Rules
- Evidence only: every claim cites a commit or file. No motivational filler.
- Separate completed outcomes from activity and future bookings. Label estimates and stale numbers; if something is unmeasured, say so instead of inventing a number.
- Respect the standing decisions in `CLAUDE.md`. Read the latest decisions in the topic files before calling something a contradiction.
- Max 3 corrections, each a concrete change with a first step and a date.
- Corrections are about the overall strategy - which roads, and where the weeks go - not technique or habits.

## Output (short)
Verdict in one line (on track / drifting / off track) > 3-5 supported numbers > what worked > what to stop > up to 3 corrections, each with a first step and a date. The full entry goes to `weekly-reviews/<date>.md`, one line to "Log" below; commit and push. Send the verdict and the corrections to `Chief of Staff` via `SendMessage`; it brings them to the owner in the morning brief.

## Log
One line per review, newest first: date, verdict, link to `weekly-reviews/<date>.md`.

## Schedule
At the start of every run, check the chat's scheduled messages; if no next review exists, schedule one for next Wednesday at 02:00 with the body `Weekly strategy review: read agents/weekly-review.md and follow it, including scheduling the next run.`.

## Switch on
New Zucchini chat in this repo, titled exactly `weekly review`; paste:
```
You run the weekly strategy review. Read CLAUDE.md and agents/weekly-review.md, then check your scheduled messages and schedule the next review if it is missing. The first review happens when that message fires. This is a background chat I never read: the verdict and anything for me go to Chief of Staff via SendMessage.
```
Then set its row in `agents/CLAUDE.md` to `on`.

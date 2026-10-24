# News watch (daily 07:30)

A background chat, `news reader`, reads the news once a day and sends only what changes something for the owner to `Chief of Staff` via `SendMessage`. Expect one or two such sends a week, plus the optional daily item below.

## Daily run
1. Schedule check (below). Sync the repo, then `python3 tools/news/fetch.py > /tmp/news-today.txt` - new items from the last 3 days across the feeds in the script, deduped against `tools/news/seen.txt`. The feeds are the watch list below turned into queries; keep the two in step.
2. Skim the titles against the watch list. Open only the candidates and confirm the fact at a primary source where one exists (the official gazette, the regulator, the company's own release).
3. Send when it passes the bar. One message per item: first line what happened, then why it matters for the owner, what to do (or "nothing, FYI"), the source link.
4. Append a line to "Sent" below, commit it with `tools/news/seen.txt` and push.

## The bar
Send only if it changes a decision, a date, money or legal status for the owner - or is a concrete lead on one of their roads. Not: general politics, market moves, launches with no bearing on their roads, anything already in the repo. When unsure, wait a day for a primary source.

## Daily item (optional)
Separate from the bar: every run, quiet days included, sends `Chief of Staff` the single most important event of the last 24 h in one field the owner picks (default: AI and agents). Format: a headline line, 2-3 plain sentences on what happened and why it matters, and the primary-source link actually read. Say what was verified at the source and what came from a secondary one. Lead with what is checkable (release, price, availability, what it does) and with independent measurements when they exist; a vendor's own benchmark numbers get at most one clause, labelled self-reported. Not logged in "Sent".

## Watch list
One line per topic: what to watch, and the file with the context. Examples to replace:
- **Residence and tax:** rule changes for your visa or permit type, tax-residency rules, the rental law where you live - `<topic>/CLAUDE.md`.
- **Your work:** regulation, prices or competitors that touch your job or product - `work/CLAUDE.md`.

## Sent
One line per item sent, newest last: date - what - what was asked of the owner.

## Schedule
At the start of every run, `"$ZUCCHINI_SPAWNER_BIN" scheduled-messages list`; if no next run exists, `"$ZUCCHINI_SPAWNER_BIN" scheduled-messages create --body "News watch: read agents/news-watch.md and follow it, including scheduling the next run." --at <tomorrow at 07:30>` (naive local datetime).

## Switch on
1. Fill the watch list above and the matching feeds in `tools/news/fetch.py`.
2. New Zucchini chat in this repo, titled exactly `news reader`; paste:
```
You run the daily news watch. Read CLAUDE.md and agents/news-watch.md, run it now and keep its schedule alive as the playbook says. This is a background chat I never read: what passes the bar goes to Chief of Staff via SendMessage.
```
3. Set its row in `agents/CLAUDE.md` to `on`.

Without Zucchini: cron `30 7 * * *` runs `claude -p "News watch: read agents/news-watch.md and follow it; skip scheduling."`.

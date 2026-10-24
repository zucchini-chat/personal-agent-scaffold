# Setup interview

Run this when `CLAUDE.md` still starts with the "Not set up yet" line. Goal: every `<placeholder>` in `CLAUDE.md` replaced with the owner's own facts, in their words, and the repo moved to a private remote of theirs.

## Before the questions
1. Say what is coming in two lines: about 15 minutes of questions, one at a time; any can be skipped and filled in later.
2. Private remote. This clone still points at the public scaffold, and everything the owner says will land in commits. Ask for an empty **private** repo of theirs (GitHub, GitLab, any git host), then, before switching, write `git remote get-url origin` and `git rev-parse HEAD` into `agents/repo-cleaner.md` > "Scaffold updates" (Source and Last ported), and run `git remote set-url origin <url> && git push -u origin master`. Until they have one, commit locally and skip the push.

## The questions
One at a time, in this order. A short follow-up when an answer is vague; never ask what a later question or a search will answer anyway.
1. Name, how to address them ("you", a name), and the language of replies.
2. Goals, in priority order: what they want in the next year or two, most important first. Push for 3-5 concrete ones and for which wins when two conflict.
3. Roads: the paths they have already chosen toward those goals. Everything else is off-limits for nudges.
4. Who they are: age, work, where they live and since when, where before, who lives with them.
5. Home: address or neighbourhood. Look up the coordinates yourself and confirm them; that point is the "near me" centre.
6. Ordinary weekday: wake, work hours, meals, family time, the hard stop. The stop time drives the "past <STOP_TIME> - stop" rule and the stop call.
7. Standing decisions: things already settled that agents must not re-propose.
8. Contacts: which email is for what (sign-ups and shops vs people), phone, messenger.
9. Calendar and mail: which ones they use. Nothing has to be plugged in now (`tools.md`).
10. Topic areas: the 3-6 parts of life they want help with (work, health, money, home, kids, travel, food...).
11. The machine: which one stays on, and whether Zucchini is installed on it.

## Writing it
- Fill `CLAUDE.md` in place: keep its structure and rules, replace placeholders, set pronouns as they prefer. A skipped answer keeps its placeholder; list those at the end.
- One folder per topic: `<topic>/CLAUDE.md` with a title, one line on what it covers and a file table (`| File | Covers |`), plus a row in the topic table of `CLAUDE.md`. What they told you about that topic goes in there, not in the root file.
- `people.md`: everyone they named.
- Times: set the morning brief and stop call times in `agents/chief-of-staff.md` and `agents/CLAUDE.md` from their ordinary day.
- Calendar: if a calendar command already works, write `tools/calendar-today` (executable, prints today's and tomorrow's events one per line) and run `python3 tools/overview.py` to check it.
- Delete the "Not set up yet" line, commit by explicit path, push.

## The end
Tell them in a few lines: what was written, which placeholders remain, and the next step - switch on the Chief of Staff rhythm (`agents/chief-of-staff.md` > "Switch on"), then one background agent at a time from `agents/CLAUDE.md`.

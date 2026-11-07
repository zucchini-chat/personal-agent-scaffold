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
- Duplicate check: run `git config core.hooksPath tools/git-hooks`; after each commit it prints lines elsewhere in the repo like the ones just committed. On by default: it is cheap and only prints. Tell the owner it is on; turning it off and the optional embeddings: `tools.md` > "Duplicate check".
- Delete the "Not set up yet" line, commit by explicit path, push.

## Shared browser (optional)
One always-on Chrome with its own profile that every agent drives: [shared-chrome-mcp](https://github.com/zucchini-chat/shared-chrome-mcp). It is what lets agents do computer work on sites (forms, uploads, accounts). Rules: `tools.md` > "Browser". Needs Google Chrome and Node.js; if either is missing, ask before installing it. Offer the step; skip it if they decline.
1. Claude Code, from this repo: `claude plugin marketplace add zucchini-chat/shared-chrome-mcp --scope project && claude plugin install shared-chrome-mcp@shared-chrome-mcp --scope project`. Then set `"autoUpdate": true` on the `shared-chrome-mcp` entry under `extraKnownMarketplaces` in `.claude/settings.json`, so new versions arrive by themselves, and commit that file. Codex (it fetches the latest at every start): `codex mcp add browser -- npx -y github:zucchini-chat/shared-chrome-mcp`.
2. Keep Chrome running: on macOS `npx -y github:zucchini-chat/shared-chrome-mcp install` (a launchd agent); elsewhere run `npx -y github:zucchini-chat/shared-chrome-mcp start` from the init system. Check with `npx -y github:zucchini-chat/shared-chrome-mcp status`. The new tools show up at the next session start.
3. Ask the owner to log in, in that Chrome's window, to the sites they want agents to use (mail, calendar, shops, work tools). Say plainly that this only saves time: agents can log in by themselves later in this profile, and every login made there stays for all agents.

## zsh globs (optional)
Only if the owner's shell is zsh (`echo $SHELL`). Agents write unquoted globs the bash way (`grep --include=*.md`, a `?` in a URL, `[*]`), and zsh's default `nomatch` aborts the whole command with "no matches found" ("bad pattern" or "= not found" for a stray `[` or `==`). Offer to append `setopt no_nomatch no_bad_pattern no_equals` to `${ZDOTDIR:-$HOME}/.zshenv` (unless already there), so such words stay as typed, as in bash. `.zshenv` because it is the one file every zsh reads, including the non-interactive ones agents run. Check: `zsh -c setopt` and `zsh -lc setopt` both list `nobadpattern`, `noequals` and `nonomatch`. It edits a file outside this repo and changes their own terminal too, so ask first; skip it if they decline.

## The end
Tell them in a few lines: what was written and set up, which placeholders remain, and the next step - switch on the Chief of Staff rhythm (`agents/chief-of-staff.md` > "Switch on"), then one background agent at a time from `agents/CLAUDE.md`.

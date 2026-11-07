# Agents

Background agents, one playbook each. All are off until the owner switches one on: follow the playbook's "Switch on", then set its row here to `on` and commit. Start with the Chief of Staff rhythm and add one agent at a time, a week apart, so each one's noise is easy to judge.

Index only: each playbook owns its schedule and steps; if a time here drifts from the playbook, the playbook wins. Times are local.

| Agent | When | Session | Playbook | Status |
|---|---|---|---|---|
| Morning brief | daily 07:00 | `Chief of Staff` | `chief-of-staff.md` | off |
| Stop call | daily 20:00 | `Chief of Staff` | `chief-of-staff.md` | off |
| Calendar audit | daily 04:00 | `calendar audit` | `calendar-audit.md` | off |
| News watch | daily 07:30 | `news reader` | `news-watch.md` | off |
| Weekly strategy review | Wed 02:00 | `weekly review` | `weekly-review.md` | off |
| Repo cleaner | Sat 02:00 | `repo cleaner` | `repo-cleaner.md` | off |
| Agent-fail bench | on demand; replay when a new model ships | any chat | `../bench/CLAUDE.md` | off |
| Mail desk (reads the whole inbox; mail guard recommended) | continuous | `email watcher` | `mail-desk.md` | off |

## How they run on Zucchini
Zucchini (zucchini.chat) keeps Claude Code and Codex chats running on your own always-on machine; you read and steer them from your phone or desktop. Three of its pieces carry these agents:
- **Named chats.** Each agent is one chat in this repo, and the chat's title is its Claude Code session name. Sessions on one machine find and message each other by name (`ListAgents`, `SendMessage`; Claude Code only, so background agents are Claude Code chats). Background agents send what needs the owner to `Chief of Staff`, the one chat the owner reads.
- **Scheduled messages.** A scheduled message drops a text into the chat at a set local time and wakes it. They do not repeat, so every run schedules the next; a chain that drops is silent, which is why each playbook checks its pending messages first.
- **Watches.** A watch runs a command and turns every line it prints into a turn in the chat; it is restarted after a Zucchini restart, so it must be safe to run twice, and keeps its cursor in `$ZUCCHINI_WATCH_STATE_DIR`. Lines are read as trusted input: a watch prints ids and event types only, never third-party text.

A chat that runs weekly is absent from `ListAgents` between runs; its scheduled message wakes it. Missing from `ListAgents` is not proof it is dead - check the playbook's log or `git log` for the last run first. A chat that did die: start a new chat in this repo with the exact session name and paste the playbook's start prompt.

> **DRAFT** - this README gets rewritten before anyone sees it.

# personal-agent-scaffold

A starting point for a personal AI agent: a chief of staff and coach that runs in Claude Code or Codex, keeps your schedule against your goals, does the computer work itself, and hands you only what truly needs you. Plus background agents you switch on one at a time.

It is a plain git repo of markdown files. The agent reads them, keeps them current and commits every change, so the files are its memory (current state) and the git log is its activity log (history).

## Start
1. `git clone <this repo's URL> my-agent && cd my-agent`
2. Start `claude` (or `codex`) in that folder and say hi.
3. The agent sees that `CLAUDE.md` is still a template and runs a setup interview (`setup.md`, about 15 minutes): your goals in priority order, who you are, where home is, how you want to be addressed, the parts of life you want help with. It writes your answers into `CLAUDE.md`, makes a folder per topic, and moves the repo to a private remote of yours.

There is no installer. The only code is three small Python and shell scripts that need nothing beyond Python 3 and git.

## What is inside
| Path | What |
|---|---|
| `CLAUDE.md` | The agent's instructions: its role, your goals, who you are, the working rules. A template until setup fills it. `AGENTS.md` links to it for Codex. |
| `setup.md` | The setup interview. |
| `people.md` | Who each recurring name is. |
| `tools.md` | What is plugged in (calendar, mail, search, browser) and how to call it. Nothing that needs your accounts ships here. |
| `agents/` | Background agents, one playbook each, all off until you switch one on. |
| `bench/` | Your own benchmark: moments an agent got it wrong, replayed on new models. |
| `tools/overview.py` | Runs at every Claude Code session start: your calendar for today and tomorrow (once plugged in) and the last 20 commits. |

## Background agents
- **Morning brief and stop call:** the daily rhythm of the `Chief of Staff` chat - the day's plan in the morning, an honest look back and tomorrow in three lines in the evening.
- **Calendar audit:** every night, checks the next 7 days against your goals and suggests changes.
- **News watch:** reads the news daily and tells you only what changes a decision, a date, money or your legal status.
- **Weekly strategy review:** did the week move you toward your goals, and what should change in the whole strategy.
- **Repo cleaner:** once a week, keeps the repo tidy - one fact in one place, no dead links.
- **Agent-fail bench:** logs the moments an agent got it wrong, to replay them on each new model.
- **Mail desk:** watches your inbox and tells you what needs you. Opt-in: it reads every mail you get. For whoever dares.

They run on [Zucchini](https://zucchini.chat), which keeps agent chats alive on your own always-on machine: chats wake themselves with scheduled messages, react to watches and message each other, and you read and steer them from your phone. Without it, each one runs from cron or launchd with `claude -p`. Details: `agents/CLAUDE.md`.

## Keep it private
Everything you tell the agent lands in this repo. Push it only to a private remote; setup points `origin` there. Updates from this scaffold arrive through the repo cleaner, which brings each new change over by meaning (`agents/repo-cleaner.md` > "Scaffold updates"). Secrets go in `credentials.txt`, which git ignores.

## For the agent reading this
If `CLAUDE.md` still starts with the "Not set up yet" line, run `setup.md` first. After setup, follow `CLAUDE.md`; this file is for humans.

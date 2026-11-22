# personal-agent-scaffold

A starting point for a personal AI agent: a chief of staff and coach that runs in Claude Code or Codex, keeps your schedule against your goals, does the computer work itself, and hands you only what truly needs you. Plus background agents you switch on one at a time.

It is a plain git repo of markdown files. The agent reads them, keeps them current and commits every change, so the files are its memory (current state) and the git log is its activity log (history).

## Start
1. `git clone <this repo's URL> my-agent && cd my-agent`
2. Start `claude` (or `codex`) in that folder and say hi.
3. The agent sees that `CLAUDE.md` is still a template and runs a setup interview (`setup.md`, about 15 minutes): your goals in priority order, who you are, where home is, how you want to be addressed, the parts of life you want help with. It saves each answer into `CLAUDE.md` as you go (a cut-off interview resumes where it stopped), makes a folder per topic, and moves the repo to a private remote of yours.

There is no installer. The code is a few small scripts that need nothing beyond Python 3 and git (the `.tyaml` type check also needs PyYAML), plus an optional shared browser ([shared-chrome-mcp](https://github.com/zucchini-chat/shared-chrome-mcp): one always-on, logged-in Chrome for all your agents; Chrome and Node.js) that setup can switch on.

## What is inside
| Path | What |
|---|---|
| `CLAUDE.md` | The agent's instructions: its role, your goals, who you are, the working rules. A template until setup fills it. `AGENTS.md` links to it for Codex. |
| `setup.md` | The setup interview. |
| `people.md` | Who each recurring name is. |
| `world-now.md` | Verified events past the model's training, so agents do not doubt real news. |
| `tools.md` | What is plugged in (calendar, mail, search, browser) and how to call it. Nothing that needs your accounts ships here. |
| `agents/` | Background agents, one playbook each, all off until you switch one on. |
| `bench/` | Your own benchmark: moments an agent got it wrong, replayed on new models. |
| `job-template/` | A notes repo for a job or contract, which setup copies out next to this repo: what agents may do in your name, where the employer's material may go, an agenda and a people file. |
| `tools/overview.py` | Runs when a Claude Code session starts, clears or compacts (not on resume): your calendar for today and tomorrow (once plugged in) and the last 20 commits. |
| `tools/git-hooks/post-commit`, `tools/dup-check/` | After each commit, prints lines elsewhere in the repo like the ones just committed, so a fact stays in one place. Python standard library (`tools.md` > "Duplicate check"). |
| `tools/git-hooks/pre-commit`, `tools/tyaml.py` | Before each commit, checks the `.tyaml` files in it against their own types and stops the commit on an error. Needs PyYAML (`tools.md` > "Typed YAML"). |
| `tools/data-guard/` | A Claude Code hook that stops an agent once when a web search, fetch, browser form or network command carries one of your private values (ID numbers, bank details, address), quoting when that value may go out. Off until you write its list (`tools.md` > "Data guard"). |
| `tools/mail-guard/` | For the mail desk: a model with no tools judges each new mail first, so the desk gets only a summary of a known sender's harmless mail, and a Claude Code hook stops agents reading a flagged one. Opt-in with the desk (`agents/mail-desk.md` > "Mail guard"). |

## Background agents
- **Morning brief and stop call:** the daily rhythm of the `Chief of Staff` chat - the day's plan in the morning, an honest look back and tomorrow in three lines in the evening.
- **Calendar audit:** every night, checks the next 7 days against your goals and suggests changes; moves undone to-dos to today when the calendar tool can edit.
- **News watch:** reads the news daily and tells you only what changes a decision, a date, money or your legal status.
- **Weekly strategy review:** did the week move you toward your goals, and what should change in the whole strategy.
- **Repo cleaner:** once a week, keeps the repo tidy - one fact in one place, no dead links.
- **Agent-fail bench:** logs the moments an agent got it wrong, to replay them on each new model.
- **Mail desk:** watches your inbox and tells you what needs you. Opt-in: it reads every mail you get; a recommended mail guard screens each one first. For whoever dares.

They run on [Zucchini](https://zucchini.chat), which keeps agent chats alive on your own always-on machine: chats wake themselves with scheduled messages, react to watches and message each other, and you read and steer them from your phone. Details: `agents/CLAUDE.md`.

## Keep it private
Everything you tell the agent lands in this repo. Push it only to a private remote; setup points `origin` there. Work for an employer or client gets its own notes repo, which this one never holds (`setup.md` > "A job"). Updates from this scaffold arrive through the repo cleaner, or through any chat you ask to update from the scaffold; either brings each new change over by meaning (`agents/repo-cleaner.md` > "Scaffold updates"). Secrets go in `credentials.txt`, which git ignores.

## For the agent reading this
If `CLAUDE.md` still starts with the "Not set up yet" line, run `setup.md` first. After setup, follow `CLAUDE.md`; this file is for humans.

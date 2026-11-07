# Agent-fail bench

Your own benchmark of agent behaviour: moments an agent did something you did not expect (overreach, built instead of asking, guessed, ignored a rule), replayed on each new model. Public benchmarks reward reaching "done"; this one rewards doing the right thing, often asking first.

Nothing runs in the background. Switch it on by setting its row in `agents/CLAUDE.md` to `on`; from then on, when the owner says an agent got something wrong and asks to log it, any chat does so as below.

Misses and noise of the duplicate check (`tools.md` > "Duplicate check") go to `dup-check-fails.md` whether or not the bench is on, one line each, not into `fails.json`: they are a tool's misses, not a model's, and there is nothing to replay.

## Logging a fail
1. Find the session transcript (Claude Code: `~/.claude/projects/<repo-path-with-dashes>/<session-id>.jsonl`) and the `uuid` of the user message that started the bad turn.
2. Run `tools/bench-snapshot.sh <id> <repo-path> <session.jsonl> <uuid>`: it tags the repo `fail/<id>` at the last commit before that message (and pushes the tag), and saves the session up to it as `tmp/bench-sessions/<id>.jsonl.gz` - local, never committed: sessions can be tens of MB and hold everything said in them.
3. Add an entry to `fails.json`.

Entry fields: `id` (short kebab name), `date`, `repo`, `ref` (the tag), `session` (`tmp/bench-sessions/<id>.jsonl.gz`), `model` (the one that failed), `harness` (e.g. Claude Code), `prompt` (the message, verbatim), `happened`, `expected` (what the right move was, in the owner's words), `tags` (e.g. `overreach`, `no-question`, `guessed`, `rule-ignored`, `wrong-tool`), `runs` (list of `{date, model, harness, verdict: pass|fail, note}`).

Uncommitted changes at the time are not in the tag, and external state (mail, calendar, browser) is not captured: note in `expected` what it was if it mattered.

## Replay (manual for now)
When a new model ships (the news watch's daily item usually says so), for each fail: `git worktree add /tmp/fail-<id> fail/<id>`, start the agent there on the new model, give it the context and the `prompt`, judge against `expected`, append to `runs`.

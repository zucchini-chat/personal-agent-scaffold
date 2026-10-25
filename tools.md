# Tools

What is plugged in and how to call it. One section per tool: the command, its limits, what it must never do. Add a section when you plug something in; keys go to `credentials.txt` (git-ignored), never here. Nothing below ships with this repo except `tools/overview.py`, `tools/news/fetch.py` and `tools/bench-snapshot.sh`.

## Calendar
Not plugged in. Options: `gog` (github.com/openclaw/gogcli, MIT: Gmail and Google Calendar from the command line, several accounts, your own OAuth client, JSON output; not tested with this scaffold), a calendar MCP server, or a calendar connector. Once a command lists events, put it in `tools/calendar-today` (executable, prints today's and tomorrow's events one per line) and `tools/overview.py` shows them at every session start.

## Email
Not plugged in. For Gmail, `gog` (see Calendar) covers search, read, labels, drafts and send. Needed for the mail desk and for reading or drafting mail: `agents/mail-desk.md` > "What you plug in". Sending stays behind the go-ahead rule in `CLAUDE.md`.

## Web search
Built-in web search and fetch work out of the box. A search API with its own MCP server or key is worth adding for non-US, recent or primary-source questions.

## Browser (shared, logged in)
[shared-chrome-mcp](https://github.com/zucchini-chat/shared-chrome-mcp): one always-on Chrome with its own logged-in profile, shared by every agent at once. Claude Code gets it as a plugin (MCP server, a skill with the rules, a hook that blocks Claude in Chrome); Codex and other clients as an MCP server. The server gives each session its own window and waits for the page after every action; the plugin's `shared-browser` skill carries the rest (logins, payments, downloads, popups, Chrome down). Set up in `setup.md` > "Shared browser".
- Parallel browser jobs need separate sessions, since subagents share their parent's: `claude -p "<job>" > tmp/<job>.log & echo $! >> tmp/<batch>.pids`, with the permissions the job needs. Wait on those PIDs, never on a `pgrep` pattern: `while ps -p $(paste -sd, tmp/<batch>.pids) >/dev/null; do sleep 30; done`.
- Chrome down: `npx -y github:zucchini-chat/shared-chrome-mcp status` shows it; with this setup's keep-alive on macOS, `launchctl kickstart -k gui/$(id -u)/shared-chrome-mcp` restarts it. Never start a second Chrome on another profile: it has none of the logins.
- Saved cards: Chrome's autofill popup does not react to automation, so paying with a saved card needs a helper of its own (none ships here).

## Money (optional)
A read-only script over your bank's API printing balances, for the morning brief to flag a low balance before upcoming bills.

## Messenger (optional)
A read-only script over your messenger's API, so agents can search your chats. It never sends and never marks read.

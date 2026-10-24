# Tools

What is plugged in and how to call it. One section per tool: the command, its limits, what it must never do. Add a section when you plug something in; keys go to `credentials.txt` (git-ignored), never here. Nothing below ships with this repo except the shared-browser kit (`tools/shared-chrome/`), `tools/overview.py`, `tools/news/fetch.py` and `tools/bench-snapshot.sh`.

## Calendar
Not plugged in. Options: `gog` (github.com/openclaw/gogcli, MIT: Gmail and Google Calendar from the command line, several accounts, your own OAuth client, JSON output; not tested with this scaffold), a calendar MCP server, or a calendar connector. Once a command lists events, put it in `tools/calendar-today` (executable, prints today's and tomorrow's events one per line) and `tools/overview.py` shows them at every session start.

## Email
Not plugged in. For Gmail, `gog` (see Calendar) covers search, read, labels, drafts and send. Needed for the mail desk and for reading or drafting mail: `agents/mail-desk.md` > "What you plug in". Sending stays behind the go-ahead rule in `CLAUDE.md`.

## Web search
Built-in web search and fetch work out of the box. A search API with its own MCP server or key is worth adding for non-US, recent or primary-source questions.

## Browser (shared, logged in)
Stock Playwright MCP attached over CDP (`127.0.0.1:9222`) to one always-on Chrome with its own profile (`.playwright-profile/`, git-ignored), plus a small kit in `tools/shared-chrome/`: `start.sh` (launch and keepalive), a launchd plist, `new-window.js`, `wait-ready.js`, and two hooks in `.claude/settings.json`. Any number of agents share its logins at once. macOS as shipped; Node.js (for `npx`) and Google Chrome required. Set up in `setup.md` > "Shared browser".
- Claude's server is in `.mcp.json`. Codex attaches to the same Chrome with the same server in `~/.codex/config.toml`: `[mcp_servers.playwright]`, `command = "npx"`, `args = ["-y", "@playwright/mcp@latest", "--cdp-endpoint", "http://127.0.0.1:9222"]`.
- Work in your own window, not a tab: a background tab reports `document.hidden`, which bot checks flag; a window's page stays visible even when covered. On attach you land in whatever tab is first - possibly another agent's.
- Open your window before any other browser call: `browser_run_code_unsafe` with `filename` `tools/shared-chrome/new-window.js` (resolved against the repo root; give the absolute path if your client sets no workspace root) returns `{index, url}`; `browser_tabs` `select` that index; check the current tab's URL in the result equals `url` (else list and select again); then `browser_navigate`.
- A link that opens a popup adds a tab to your window; close it when done with it. When the job is done, `browser_tabs` `close` with no index closes your window; make no browser calls after that. `browser_close` only disconnects your MCP (Chrome and your window stay open), so it is not a way to clean up.
- **After every navigate or click, wait for the page before reading it:** `browser_run_code_unsafe` with `filename` `tools/shared-chrome/wait-ready.js`, then `browser_snapshot`. The snapshot `browser_navigate` returns predates the page's data. `ready: false` means conclude nothing. A PostToolUse hook reminds you.
- One browser subagent at a time per session: each session runs its own MCP process with its own current-tab pointer, and subagents share their parent's (even with their own `mcpServers` entry). For parallel browser jobs, run separate sessions: `claude -p "<job>" > tmp/<job>.log & echo $! >> tmp/<batch>.pids`, with the permissions the job needs. Wait on those PIDs, never on a `pgrep` pattern: `while ps -p $(paste -sd, tmp/<batch>.pids) >/dev/null; do sleep 30; done`.
- Logins: the owner logs in once to the sites they want agents to use, and agents can log in by themselves in this profile too. Cookies are shared: never log out, and a login made in any window counts for all.
- Payment: only when the owner has clearly said to pay for that specific thing; without that, stop at checkout and ask. Chrome's saved-card autofill popup does not react to automation, so filling a saved card needs a helper of its own (none ships here).
- Downloads land in `~/Downloads`, not in Playwright's `download` event; move the file from there.
- The profile is encrypted with Chrome's mock keychain: launch it only with `--use-mock-keychain --password-store=basic` (`start.sh` does), or every site shows logged out.
- macOS sends Dock clicks and links from other apps to the oldest running Chrome, so `start.sh` starts the owner's own Chrome first when it is not running, and restarts the agents' Chrome within 30 s whenever the owner's restarts (a Chrome update, a quit) - open agent windows are lost then.
- Chrome down (`curl -s 127.0.0.1:9222/json/version` fails): `launchctl kickstart -k gui/$(id -u)/com.personal-agent.shared-chrome`; its log is `/tmp/shared-chrome.log`.
- Port 9222 hands the logged-in profile to any process on this machine; it listens on 127.0.0.1 only, never expose it.
- Not an option: Claude Code's own Chrome integration (`claude --chrome`). It refuses to log in - it stops at login and CAPTCHA pages and hands them to the human. A PreToolUse hook blocks its tools so agents stay on this browser.
- Alternatives: **agent-browser** (vercel-labs, Apache-2.0) can replace Playwright MCP as the driver over the same Chrome (`--cdp 9222 --pin-tab`, one `AGENT_BROWSER_SESSION` per agent): it pins each session to its own tab, has an auth vault and real wait commands; keep `start.sh` and the window-per-agent rule. **BrowserOS neo** (AGPL-3.0) is the no-setup option of the same shape - a separate browser for agents with imported logins and a tab group per agent, for Claude Code and Codex - but it is pre-1.0 and its bundled skill hands sign-ins to the human; worth re-checking once it reaches 1.0.

## Money (optional)
A read-only script over your bank's API printing balances, for the morning brief to flag a low balance before upcoming bills.

## Messenger (optional)
A read-only script over your messenger's API, so agents can search your chats. It never sends and never marks read.

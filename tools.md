# Tools

What is plugged in and how to call it. One section per tool: the command, its limits, what it must never do. Add a section when you plug something in; keys go to `credentials.txt` (git-ignored), never here. Nothing below ships with this repo except `tools/overview.py`, `tools/news/fetch.py` and `tools/bench-snapshot.sh`.

## Calendar
Not plugged in. Options: Google Calendar through the Google API with an OAuth client of your own (a short standard-library script can list, add, update and delete events), a calendar MCP server, or a calendar connector. Once a command lists events, put it in `tools/calendar-today` (executable, prints today's and tomorrow's events one per line) and `tools/overview.py` shows them at every session start.

## Email
Not plugged in. Needed for the mail desk and for reading or drafting mail: `agents/mail-desk.md` > "What you plug in". Sending stays behind the go-ahead rule in `CLAUDE.md`.

## Web search
Built-in web search and fetch work out of the box. A search API with its own MCP server or key is worth adding for non-US, recent or primary-source questions.

## Browser
For forms and clicking through sites: the Playwright MCP server, ideally attached to one logged-in Chrome profile that every agent shares, so each login is made once. Payment details stay out of agents' reach unless the owner has said to pay for that specific thing.

## Money (optional)
A read-only script over your bank's API printing balances, for the morning brief to flag a low balance before upcoming bills.

## Messenger (optional)
A read-only script over your messenger's API, so agents can search your chats. It never sends and never marks read.

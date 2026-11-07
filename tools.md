# Tools

What is plugged in and how to call it. One section per tool: the command, its limits, what it must never do. Add a section when you plug something in; keys go to `credentials.txt` (git-ignored), never here. Nothing below ships with this repo except `tools/overview.py`, `tools/news/fetch.py`, `tools/bench-snapshot.sh`, `tools/git-hooks/post-commit` and `tools/dup-check/`.

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

## Duplicate check
Agents write a fact a second time in another file and the copies drift. After every commit, the git `post-commit` hook (`tools/git-hooks/post-commit`) searches the rest of the repo's markdown for sentences like the ones the commit added or changed and prints up to 5 hits (`file:line` + the sentence) under "Possible duplicates of the facts you just committed". It only prints, never blocks or fails a commit, and works for any harness that commits (Claude Code, Codex).
- Deletion-only edits print nothing. `bench/`, `repo-reviews/` and `weekly-reviews/` are left out of the search: they are records that quote old lines verbatim.
- Search: BM25 (word matching), Python standard library only, works right after clone, about 0.1 s per commit on a small repo, 1.6-1.8 s at about 43k sentences. By hand: `python3 tools/dup-check/search.py "<text>"` prints the 20 lines most like a sentence; `python3 tools/dup-check/search.py <file.md>:<line>` does the same for a repo line, leaving that line out.
- On per clone (setup does it): `git config core.hooksPath tools/git-hooks`. Local git config, not tracked; git then runs the hooks in `tools/git-hooks/` instead of `.git/hooks/`, where a fresh clone has only samples. Off: `git config --unset core.hooksPath`.
- Embeddings (optional, off by default; the owner's and their agent's call). BM25 matches exact words, numbers and names, which most copied facts share; an embedding model also catches the same fact in other words. Measured on a personal repo of this kind against its own past deduplications from git history: BM25 alone put the other copy in the top 3 for about 3 pairs in 4; `BAAI/bge-small-en-v1.5` alone for about half over whole lines and about as many as BM25 over sentences; bigger models did no better; BM25 + bge-small over sentences, fused by reciprocal rank (RRF), did best: about 4 in 5 in the top 3 and 19 in 20 in the top 10. A cross-encoder reranker on top made real pairs worse (it favours on-topic passages over the line that repeats the number), so none is used.
- Switch embeddings on: (1) install `sentence-transformers` (pulls torch and numpy) into a Python outside the repo: `python3 -m venv ~/.venvs/dupcheck && ~/.venvs/dupcheck/bin/pip install sentence-transformers`; (2) download the model once: `~/.venvs/dupcheck/bin/python -c "from sentence_transformers import SentenceTransformer as S; S('BAAI/bge-small-en-v1.5')"`, cached in `~/.cache/huggingface/` (outside the repo; `HF_HOME` moves it); (3) `git config dupcheck.python ~/.venvs/dupcheck/bin/python` (local to this clone; `git config --unset dupcheck.python` switches it off). Then the first commit or search that finds no server starts `tools/dup-check/server.py` in the background with that Python and answers with BM25 alone; later ones get BM25 + embeddings. The server sets `HF_HUB_OFFLINE=1` (no hub calls once downloaded), holds model and index in memory, re-reads changed files and exits after 1 h idle; its lock and log are in `tmp/dup-check/`, its socket in the system temp dir. If the packages are missing it exits and everything stays on BM25. A repo not written in English: set `MODEL` in `server.py` to a multilingual model.
- Cost: about 0.7 GB of packages (mostly torch; more on Linux with CUDA wheels), about 130 MB for the model, about 1 GB of RAM while the server is warm, 5-10 s to start (the torch import); the warm-up embeds every sentence of the repo (seconds on a young repo; about 150 s and about 2 GB of RAM at ~43k sentences) and, with no disk cache, repeats whenever the server restarts after an idle hour. Worth it once `bench/dup-check-fails.md` shows misses that were the same fact in other words.

## Money (optional)
A read-only script over your bank's API printing balances, for the morning brief to flag a low balance before upcoming bills.

## Messenger (optional)
A read-only script over your messenger's API, so agents can search your chats. It never sends and never marks read.

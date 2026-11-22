# <JOB> - <NAME>'s work notes

> **Template.** Inside <NAME>'s personal repo this folder is only a template: its rules do not apply to a chat working there, and they restate that repo's rules on purpose, so it stands alone once copied out by `setup.md` > "A job". Once copied, fill the `<placeholders>` with the owner's facts and delete this line.

<NAME>'s own notes repo for their work at <EMPLOYER> (<ROLE>, <employment or contract>, <START> - <END or "ongoing">), loaded by every Claude Code session under this folder, the employer's clones included (Codex: only when started here). Its git has no remote, or only the employer's own remote <URL>, never a personal one: the employer's material stays on this machine or the employer's systems. The chat `<JOB>` keeps these notes. <NAME>'s personal agent lives in `<PERSONAL_REPO>`, a separate repo, with its `Chief of Staff` chat. Address <NAME> as <"you" / a name>, in <LANGUAGE>.

## Where things are
- `<REPO>/`: the employer's repo, cloned here; its own `AGENTS.md` or `CLAUDE.md` holds the code rules. Each clone is listed in `.gitignore`, so the two repos never mix; clone others on demand the same way.
- `AGENDA.md`, `people.tyaml`, `research/`: "Where knowledge goes" below.
- <CHAT>, <TRACKER>, <MAIL>: the employer's chat, tracker and mail; agents read them <HOW, or "not at all">.

## What stays inside
- The employer's documents, customer data and secrets never go into a pushed repo (one with a remote outside the employer) or into an AI tool the employer has not approved; they may live in this folder. Test data is synthetic or employer-approved.
- Approved AI tools and accounts: <TOOLS, WHICH ACCOUNT, WHO APPROVED, WHEN>; nothing else until the employer approves it in writing. An employer-paid AI account serves this job only: no personal session runs on it, since an org admin can export its history.
- Never edit `<PERSONAL_REPO>`: ask `Chief of Staff` by `SendMessage` for any change there, and for a missing secret, account or personal detail before asking <NAME>. Only what the personal side needs goes there: <NAME>'s dates and to-dos, the terms of their own contract.
- Nothing of the employer's goes to other people or anywhere public without <NAME>'s yes.
- The employer's sign-in (single sign-on) never goes into the personal shared Chrome, which every personal session reaches. Web work in the employer's accounts uses this job's own Chrome, the `<JOB_BROWSER>` MCP server (port `<PORT>`, profile `<PROFILE>`, label `<LABEL>`; how to drive it: `<PERSONAL_REPO>/tools.md` > "Browser", whose status and restart commands take these instead of the defaults: `npx -y github:zucchini-chat/shared-chrome-mcp status --port <PORT> --profile <PROFILE> --label <LABEL>`, `launchctl kickstart -k gui/$(id -u)/<LABEL>`); it holds only the employer's logins, never a personal account, never a payment. Browser work is never handed to a personal session.
- Paid model API keys: tests never call the live model, evals run only by hand, every call's output is capped (a max-tokens limit).

## In <NAME>'s name
One rule per action; <NAME> widens the list only explicitly, and the widening is written here. Anything not listed: ask.
- Never push to `main`; never approve or merge a pull request.
- Pushing a work branch and opening a pull request: allowed, except where a bot gives the required approval and a merge queue merges - there opening one is shipping, so show <NAME> the diff first.
- Issue and review comments and chat messages go out under <NAME>'s name: show the text, post only on their yes.
- A ticket or request form: fill it, never submit it; <NAME> submits.
- Reading leaves no trace: no mark-read, reactions, labels, assignments or status changes.
- Until `main` is protected on the server: link `tools/pre-push-no-main.sh` as the clone's `.git/hooks/pre-push` (`ln -s "$PWD/tools/pre-push-no-main.sh" <clone>/.git/hooks/pre-push`, run from this folder, in the main clone; its worktrees share it); a new clone lacks it, a clone with its own `core.hooksPath` ignores it, and `--no-verify` skips it.

## Work identity
- Repos here commit as `<WORK_EMAIL>` (an `includeIf` for this folder in `~/.gitconfig`); a clone or worktree outside this folder loses it: check `git config user.email` there before its first commit.
- Code-host calls run as `<WORK_LOGIN>` with a per-command token, `GH_TOKEN="$(gh auth token -u <WORK_LOGIN>)" gh ...` (on a `git push` over HTTPS too, when gh is git's credential helper: `gh auth setup-git`); never `gh auth switch`, which changes the account under every personal session too. `gh auth status` lists the accounts.

## Where knowledge goes
- Rules every contributor needs: the employer repo's `AGENTS.md` (or its equivalent), by pull request. Open work: <TRACKER>. Here: <NAME>'s own notes, plans and people map, and employer files <NAME> needs at hand ("What stays inside").
- Dated steps <NAME> takes go on their one calendar, <CALENDAR> (how: `<PERSONAL_REPO>/tools.md` > "Calendar"); undated open intentions and open questions in `AGENDA.md` (format in its header).
- People: `people.tyaml`, one record per person; add anyone new.
- A fact is known only with its source (who, where, when); otherwise mark it assumed or open.
- `research/`: onboarding research snapshots, one file per topic, the date read in the title, a header with the sources and that reading changed nothing (read-only). Never kept current, so exempt from replacing facts in place; newer research is a new file.

## This repo's git
- Files hold the current state, commit messages the history (old -> new, the source, who decided); commit right after a change, without asking.
- Commit by explicit path, `git commit -m "..." -- <paths>` (a new file: `git add <path>` first); never `git add -A`, `git add .`, a bare `git commit` or `--amend`: other agents work in this tree in parallel. Never stash, reset, restore, check out or clean a file you did not change.
- One fact in one place; never hard-wrap prose (one paragraph or list item = one line).
- `core.hooksPath tools/git-hooks` runs the duplicate check after each commit and the `.tyaml` check before it (`<PERSONAL_REPO>/tools.md` > "Duplicate check", "Typed YAML").

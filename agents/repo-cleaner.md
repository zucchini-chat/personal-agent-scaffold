# Repo cleaner (weekly, Saturday 02:00)

Question: is anything in this repo worth changing, simplifying, de-duplicating or rearranging, so agents and the owner find each fact faster and in one place. Autonomous. Runs in the background chat `repo cleaner`.

## Steps
1. Schedule check (below). Sync the repo. Judge last week's changes first: `git log --since="7 days ago" --grep="^Repo cleaner"` and the commits after them. A change that other sessions reverted, re-created in the old place, or kept tripping over is a failed change - fix or undo it before anything new.
2. Re-check each item in "Deferred" below against the week's commits: act if the week confirmed it, drop it if nothing touched it.
3. One read-only audit subagent: a full repo sweep against the criteria below, ranked proposals to `repo-reviews/<date>.md` (committed with the review), each with files, the change, why, risk and confidence.
4. Take at most 5 high-confidence proposals. Run one executor subagent per proposal, **one after another**, each with: the proposal, the rules below, done condition "every link to moved or renamed paths repointed (grep proves zero stale hits), commit by explicit path with message `Repo cleaner: <what> (<why>)`, push". Check each result (`git show --stat`, grep for stale paths) before the next.
5. Low-confidence or risky items go to "Deferred" with a one-line reason; revisit next week. Stale names, inconsistencies and superseded sections are this agent's to fix without asking, in any file including the root `CLAUDE.md`; the old value and the reason go in the commit message. Uncommitted tracked edits get committed as they are, so `git status` stays clean.
6. The commits and `repo-reviews/<date>.md` are the report. `SendMessage` to `Chief of Staff` only for a fact or decision only the owner has; never block on it.

## Criteria
- One fact in one place; a second copy becomes a pointer. `CLAUDE.md` files stay lean, detail in topic files.
- Flat folders with dozens of dated one-off files: group by kind when it cuts lookup time.
- Tracked tools living in `tmp/` (agent scratch) belong in `tools/`.
- Stale names, dead cross-links, files no one references and nothing in the last 30 days touched.
- Playbooks that overlap or contradict each other or a `CLAUDE.md` rule.

## Rules
- Do not change the meaning of any rule or fact; only where it lives and how it reads.
- Do not rewrite text in files the owner edits by hand; moving them is fine only with every link repointed.
- Paths hard-coded in scripts, hooks (`.claude/settings.json`), scheduled-message bodies, watch commands and `agents/CLAUDE.md` count as links.
- Other sessions work here in parallel: stage by explicit path, sync before each commit, small commits.
- When unsure, defer a week rather than change.

## Deferred
One line per item: date added, proposal, what would confirm it.

## Schedule
At the start of every run, `"$ZUCCHINI_SPAWNER_BIN" scheduled-messages list`; if no next run exists, `"$ZUCCHINI_SPAWNER_BIN" scheduled-messages create --body "Repo cleaner: read agents/repo-cleaner.md and follow it, including scheduling the next run." --at <next Saturday at 02:00>` (naive local datetime).

## Switch on
New Zucchini chat in this repo, titled exactly `repo cleaner`; paste:
```
You are the weekly repo cleaner. Read CLAUDE.md and agents/repo-cleaner.md, then run "$ZUCCHINI_SPAWNER_BIN" scheduled-messages list and schedule the next run if it is missing. The first run happens when that message fires. This is a background chat I never read: anything only I can answer goes to Chief of Staff via SendMessage.
```
Then set its row in `agents/CLAUDE.md` to `on`.

Without Zucchini: cron `0 2 * * 6` runs `claude -p "Repo cleaner: read agents/repo-cleaner.md and follow it; skip scheduling."`.

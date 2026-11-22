#!/usr/bin/env python3
"""The duplicate check of a commit, run by tools/git-hooks/pre-commit: for each sentence the commit adds to a .md or
.tyaml file - every sentence of a new line, only the sentences holding new words of an edited line - the most similar
line in any other file and the most similar in the rest of its own file (BM25; what a line compares and which lines
of its own file it skips: dupcheck.units). Those scoring FLOOR or more, best first, at most 5, stop the commit of an
agent (one of AGENT is set; exit code 3) until it fixes them or commits again with DUP_OK="<why>" in front; DUP_OK
passes only "->" lines a stop showed the same chat in the last hour. Any other committer only sees them. Logs every
run to tmp/dup-check/runs.jsonl. On its own error, or when it hits its 6 s limit, it logs an error line and the commit
goes through. `hook.py <commit>` replays an older commit (nothing is stopped or logged).
More: tools.md > "Duplicate check"."""
import ast, collections, difflib, json, os, re, signal, subprocess, sys, time

LOG = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../tmp/dup-check/runs.jsonl"))
REPLAY = sys.argv[1] if len(sys.argv) > 1 else None
CHAT = os.environ.get("ZUCCHINI_CHAT_ID") or os.environ.get("CLAUDE_CODE_SESSION_ID")  # who was shown a hit
MAX_QUERIES, MAX_HITS = 40, 5
AGENT = ("CLAUDECODE", "ZUCCHINI_CHAT_ID")  # set by Claude Code; by Zucchini for every agent it runs (Codex too)
END_PUNCT = ".,;:!?()[]{}\"'“”‘’«»`*_"  # stripped from a word's ends when an edit is compared (words)
FLOOR = 30  # raw BM25 score; how it was set and when to move it: tools.md > "Duplicate check"
STOPPED = "Commit stopped by the duplicate check: a line you are committing may repeat a fact that already lives elsewhere, in another file or in the same one (the \"->\" lines)."
UNSEEN = "Commit stopped by the duplicate check: DUP_OK passes only \"->\" lines a stop has already shown you, and these are new."
SEEN = "Possible duplicates of the facts you are committing (the \"->\" lines):"
HOW = ("Open each \"->\" line. Same fact: keep it in one place, put a link in the other or cut it, commit again.\n"
       "Not the same fact, or repeated on purpose: commit again with DUP_OK=\"<why, per number>\" in front of `git commit`. Never --no-verify.\n"
       "python3 tools/dup-check/search.py \"<text>\" shows the top 20 for a sentence.")


def hunks(commit):
    """(file, removed lines, added lines as (number, line)) per hunk of the .md and .tyaml diff: of the commit being
    made (the index git hands the hook), or of an older `commit` (not the root commit). Raises when git fails."""
    args = ["diff", "--unified=0", "--no-color", "--no-ext-diff", "--no-textconv", "--src-prefix=a/", "--dst-prefix=b/"]
    diff = (git(*args, f"{commit}~1", commit, "--", "*.md", "*.tyaml") if commit else
            subprocess.run(["git", "-c", "core.quotePath=false", *args, "--cached", "--", "*.md", "*.tyaml"],
                           capture_output=True, encoding="utf-8", errors="replace"))
    if diff.returncode:
        raise RuntimeError(diff.stderr.strip())
    f, old, new, header, n = None, [], [], True, 0
    for l in diff.stdout.split("\n") + ["diff --git end"]:
        if l.startswith(("diff --git", "@@")):
            if f and new:
                yield f, old, new
            old, new, header = [], [], l.startswith("diff --git")
            if header:
                f = None
            else:
                n = int(re.search(r"\+(\d+)", l)[1])
        elif header and l.startswith("+++ "):
            f = l[4:].rstrip("\t")  # git adds a tab after a name with a space
            if f.startswith('"'):  # a name with ", \ or a control char is C-quoted even with core.quotePath=false
                f = ast.literal_eval(f)
            f = f[2:] if f.startswith("b/") else None
        elif not header and l.startswith("-"):
            old.append(l[1:])
        elif not header and l.startswith("+"):
            new.append((n, l[1:]))
            n += 1


def words(text):
    """Lowercased whitespace tokens without punctuation or markdown emphasis at their ends: `Signal,` and `**signal**`
    are `signal`, while `$100` and `$-100` stay different."""
    return [w for w in (t.strip(END_PUNCT) for t in text.lower().split()) if w]


def changed(old, line):
    """The sentences of `line` to search: all of them for a new line; for an edit of one of `old` (most similar,
    ratio of words >= 0.5), only those holding inserted or replaced words - none when the edit only deleted words
    or changed case, end punctuation or emphasis."""
    sm = difflib.SequenceMatcher(None, autojunk=False)
    sm.set_seq2(words(line))
    ratio = lambda o: (sm.set_seq1(words(o)), sm.quick_ratio())[1]
    sm.set_seq1(words(max(old, key=ratio)) if old else [])
    if sm.ratio() < 0.5:
        return sentences(line)
    new = {j for op, _, _, j1, j2 in sm.get_opcodes() if op in ("insert", "replace") for j in range(j1, j2)}
    out, i = [], 0
    for s in sentences(line):  # sentences() splits only at whitespace, so word indices map onto sentences
        n = len(words(s))
        if new & set(range(i, i + n)):
            out.append(s)
        i += n
    return out


def stops():
    """The stopped runs among the last 200 of the log."""
    with open(LOG, encoding="utf-8") as fh:
        lines = collections.deque(fh, maxlen=200)
    for l in lines:
        try:
            r = json.loads(l)
        except ValueError:
            continue
        if r.get("stopped"):
            yield r


def log(record):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"time": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **record, "chat": CHAT}, ensure_ascii=False) + "\n")


def give_up(error):
    """Log why the commit goes through unchecked (a replay logs nothing); never raises."""
    if not REPLAY:
        try:
            log({"error": error[:300]})
        except Exception:
            pass


def main():
    qs, parsed = {}, {}  # (file, sentence): its line number, None when the working tree has it elsewhere
    for f, old, new in hunks(REPLAY):
        if excluded(f):
            continue
        if f not in parsed:
            try:
                with open(os.path.join(ROOT, f), encoding="utf-8", errors="replace") as fh:
                    body = fh.read()
            except OSError:  # deleted since
                body = ""
            parsed[f] = body.split("\n"), units(f, body)
        raw, u = parsed[f]
        for n, l in new:
            n = n if n <= len(raw) and raw[n - 1] == l else None
            t = u[n - 1][0] if n else l
            if is_line(t) and len(qs) < MAX_QUERIES:
                for s in changed(old, t):
                    if is_line(s):
                        qs.setdefault((f, s), n)
    qs = list(qs.items())[:MAX_QUERIES]
    if not qs:
        return
    found = search([s for (_, s), _ in qs], 20, at=[(f, n) for (f, _), n in qs])
    results = [(next((h for h in r if h[0] != f), None), next((h for h in r if h[0] == f), None))  # other file, own file
               for ((f, _), _), r in zip(qs, found)]
    hits = []  # (committed file, its sentence, hit), best first, one per hit line
    for (f, s), h in sorted(((q, h) for (q, _), r in zip(qs, results) for h in r if h and h[2] >= FLOOR),
                            key=lambda x: -x[1][2]):
        if h[:2] not in [x[:2] for _, _, x in hits]:
            hits.append((f, s, h))
    why = os.environ.get("DUP_OK", "").strip()
    agent = None if REPLAY else next((v for v in AGENT if v in os.environ), None)
    new = hits
    if why and agent and hits and os.path.exists(LOG):  # drop the "->" lines a stop showed in the last hour
        since = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(time.time() - 3600))
        seen = {(h[0], h[3]) for r in stops() if r["time"] >= since and r.get("chat") == CHAT
                for q in r["queries"] for h in (q["hit"], q.get("own")) if h and h[:2] in r["shown"]}
        new = [x for x in hits if (x[2][0], x[2][3]) not in seen]
    shown = new[:MAX_HITS]
    stop = bool(shown and agent)
    if shown:
        print(UNSEEN if stop and why else STOPPED if stop else SEEN)
        for i, (f, s, (hit_file, n, _, sentence)) in enumerate(shown, 1):
            print(f"{i}. {f}: {s.strip()[:120]}\n   -> {hit_file}:{n} {sentence.strip()[:200]}")
        if stop:
            print(HOW)
    if not REPLAY:
        log({"parent": git("rev-parse", "--short", "HEAD").stdout.strip(),
             "queries": [{"file": f, "text": s, "hit": hit, "own": own} for ((f, s), _), (hit, own) in zip(qs, results)],
             "shown": [h[:2] for _, _, h in shown], "stopped": stop, "ok": why or None, "agent": agent})
    if stop:
        sys.exit(3)


def timeout(*_):
    give_up("timeout")
    os._exit(0)


signal.signal(signal.SIGALRM, timeout)
signal.alarm(6)
try:
    from dupcheck import ROOT, excluded, git, is_line, search, sentences, units
    main()
except Exception as e:
    give_up(repr(e))

"""Duplicate-fact search over the repo's markdown and .tyaml, own file included, standard library only: BM25 over
sentences, rebuilt on each call; a line scores by its best sentence against the query's best sentence. Which files it
reads: corpus_files(); what each line compares: units()."""
import math, os, re, subprocess
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# records that quote old lines verbatim; job-template/ restates this repo's rules so it stands alone once copied out
EXCLUDE = ("bench/", "repo-reviews/", "weekly-reviews/", "job-template/")
SKIP_FIELDS = ("proof", "account", "see")  # .tyaml fields that say where a fact comes from, whose it is or where it lives
ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}  # a hook's GIT_INDEX_FILE may be temporary
K1, B = 1.2, 0.75


def excluded(path):
    return path.startswith(EXCLUDE) or path.endswith("-transcript.md")  # transcripts repeat what was said


def git(*args):
    return subprocess.run(["git", "-C", ROOT, "-c", "core.quotePath=false", *args], capture_output=True,
                          encoding="utf-8", errors="replace", env=ENV)


def is_line(text):
    """Not a heading, and 3+ word tokens, or 2+ when it holds a digit (table rows, amounts, phone numbers)."""
    t = text.strip()
    if t.startswith("#"):
        return False
    n = len(re.findall(r"\w+", t))
    return n >= 3 or n >= 2 and re.search(r"\d", t) is not None


def sentences(text):
    """Split at sentence ends; a piece under 6 words joins the previous one."""
    out, last = [], 0
    for s in re.split(r"(?<=[.!?])\s+", text.strip()):
        n = len(re.findall(r"\w+", s))
        if out and (n < 6 or last < 6):
            out[-1] += " " + s
            last += n
        else:
            out.append(s)
            last = n
    return out


def words(text):
    return re.findall(r"\w+", text.lower())


def units(path, text):
    """Per line of a file: (the text it compares, its block). A line is not compared with the lines of its own block:
    a markdown paragraph (the lines between blank lines and headings), a .tyaml record (each item of a data list, a
    one-line `- {key: value, ...}` included; the types document with the comments above it is one). A .tyaml data line
    compares its values without the keys; a SKIP_FIELDS field, list items under it included, compares nothing."""
    out, block, key, data, indent = [], 0, None, False, None
    for n, t in enumerate(text.split("\n"), 1):
        if not path.endswith(".tyaml"):
            if not t.strip() or t.startswith("#"):
                block = n
            out.append((t, block))
            continue
        flow = re.match(r"( *)- \{(.*)\}", t)  # a one-line record
        if data and flow:
            block, indent, key = n, len(flow[1]), None
            pairs = [re.match(r"(\w+):\s*(.*)", p) for p in re.split(r",\s*(?=\w+:\s)", flow[2])]
            out.append((", ".join(p[2] for p in pairs if p and p[1] not in SKIP_FIELDS), block))
            continue
        m = re.match(r"( *)(- )?(\w+):\s*(.*)", t)
        if t.strip() == "---":
            data, block = True, n
        elif data and m and not m[1] and not m[2]:  # a top-level key starts a list
            block, indent = n, None
        elif data and m and m[2] and (indent is None or len(m[1]) <= indent):  # the first field of a record
            block, indent = n, len(m[1])
        if data and m:
            key = m[3]
        out.append((t if not data else "" if key in SKIP_FIELDS else m[4] if m else re.sub(r"^\s*- ", "", t), block))
    return out


def corpus_files():
    """Tracked and untracked-but-not-ignored .md and .tyaml files, minus excluded() and symlinks (AGENTS.md ->
    CLAUDE.md). Raises when git fails, which must not look like an empty corpus."""
    r = git("ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "*.md", "*.tyaml")
    if r.returncode:
        raise RuntimeError(r.stderr.strip())
    return sorted({f for f in r.stdout.split("\0")
                   if f and not excluded(f) and not os.path.islink(os.path.join(ROOT, f))})


def index():
    """The corpus's sentences [(file, line, sentence)], BM25 postings {word: (idf, [(sentence id, term weight)])} and
    each file's blocks {file: [block of each line]}; a sentence's length is its number of distinct words."""
    sents, tfs, blocks = [], [], {}
    for f in corpus_files():
        try:
            with open(os.path.join(ROOT, f), encoding="utf-8", errors="replace") as fh:
                u = units(f, fh.read())
        except OSError:  # deleted but still in the git index
            continue
        blocks[f] = [b for _, b in u]
        for n, (t, _) in enumerate(u, 1):
            for s in sentences(t) if is_line(t) else []:
                sents.append((f, n, s))
                tfs.append(Counter(words(s)))
    avgdl = sum(map(len, tfs)) / max(len(tfs), 1) or 1
    postings = defaultdict(list)
    for d, tf in enumerate(tfs):
        for w, x in tf.items():
            postings[w].append((d, x * (K1 + 1) / (x + K1 * (1 - B + B * len(tf) / avgdl))))
    n = len(tfs)
    return sents, {w: (math.log(1 + (n - len(p) + 0.5) / (len(p) + 0.5)), p) for w, p in postings.items()}, blocks


def search(queries, k, at=None):
    """Per query, its k best lines as [file, line, score, sentence], best first, leaving out the block (units) of the
    query's own line at[i] = (file, line), or that whole file when line is None. score: raw BM25, growing with the
    words shared and how rare they are; sentence: the hit line's best-matching one."""
    sents, postings, blocks = index()
    out = []
    for i, q in enumerate(queries):
        own, line = at[i] if at and at[i] else (None, None)
        line = line if own in blocks and line and line <= len(blocks[own]) else None  # shortened since: the whole file
        near = blocks[own][line - 1] if line else None
        best = defaultdict(float)
        for qs in sentences(q):
            s = defaultdict(float)
            for w in set(words(qs)):
                idf, p = postings.get(w, (0, ()))
                for d, x in p:
                    s[d] += idf * x
            for d, x in s.items():
                best[d] = max(best[d], x)
        hits = {}
        for d in sorted(best, key=lambda d: (-best[d], d)):
            f, n, s = sents[d]
            if f == own and (not line or blocks[f][n - 1] == near):
                continue
            hits.setdefault((f, n), [f, n, round(best[d], 1), s])
            if len(hits) == k:
                break
        out.append(list(hits.values()))
    return out

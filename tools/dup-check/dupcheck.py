"""Duplicate-fact search over the repo's markdown, standard library only: BM25 over sentences, rebuilt on each call; a
line scores by its best sentence against the query's best sentence."""
import math, os, re, subprocess
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXCLUDE = ("bench/", "repo-reviews/", "weekly-reviews/")  # records that quote old lines verbatim
ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}  # a hook's GIT_INDEX_FILE may be temporary
K1, B = 1.2, 0.75


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


def corpus_files():
    """Tracked and untracked-but-not-ignored .md files, minus EXCLUDE and symlinks (AGENTS.md -> CLAUDE.md)."""
    out = git("ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "*.md").stdout.split("\0")
    return sorted({f for f in out if f and not f.startswith(EXCLUDE) and not os.path.islink(os.path.join(ROOT, f))})


def index():
    """The corpus's sentences [(file, line, sentence)] and BM25 postings {word: (idf, [(sentence id, term weight)])};
    a sentence's length is its number of distinct words."""
    sents, tfs = [], []
    for f in corpus_files():
        try:
            with open(os.path.join(ROOT, f), encoding="utf-8", errors="replace") as fh:
                for n, t in enumerate(fh, 1):
                    for s in sentences(t) if is_line(t) else []:
                        sents.append((f, n, s))
                        tfs.append(Counter(words(s)))
        except OSError:  # deleted but still in the git index
            pass
    avgdl = sum(map(len, tfs)) / max(len(tfs), 1) or 1
    postings = defaultdict(list)
    for d, tf in enumerate(tfs):
        for w, x in tf.items():
            postings[w].append((d, x * (K1 + 1) / (x + K1 * (1 - B + B * len(tf) / avgdl))))
    n = len(tfs)
    return sents, {w: (math.log(1 + (n - len(p) + 0.5) / (len(p) + 0.5)), p) for w, p in postings.items()}


def search(queries, k, files=None, skip=None):
    """Per query, its k best lines as [file, line, score, sentence], best first, leaving out its own file (files[i])
    and the line skip (file, line). score: raw BM25, growing with the words shared and how rare they are; sentence:
    the hit line's best-matching one."""
    sents, postings = index()
    out = []
    for i, q in enumerate(queries):
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
            if (files and f == files[i]) or (f, n) == skip:
                continue
            hits.setdefault((f, n), [f, n, round(best[d], 1), s])
            if len(hits) == k:
                break
        out.append(list(hits.values()))
    return out

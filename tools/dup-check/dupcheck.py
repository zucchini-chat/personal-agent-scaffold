"""Duplicate-fact search over the repo's markdown, stdlib only: BM25 over sentences, a line scored by its best
sentence pair with the query. With `git config dupcheck.python <a Python that has sentence-transformers>` set, it
asks the warm server.py (BM25 + embeddings) and, while that is cold, starts it and answers with BM25 alone."""
import contextlib, hashlib, json, math, os, re, socket, subprocess, tempfile
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TMP = os.path.join(ROOT, "tmp", "dup-check")
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


class Index:
    """The corpus's content lines, one BM25 document per sentence. A file is re-read only when its mtime changes."""

    def __init__(self):
        self.files = {}  # file: (mtime, [(line, sentence, words)])
        self.sents = None  # [(file, line, sentence)], the sentences of a line next to each other

    def refresh(self):
        """Re-reads changed files; True when the corpus changed and BM25 was rebuilt."""
        files = {}
        for f in corpus_files():
            path = os.path.join(ROOT, f)
            try:
                m = os.stat(path).st_mtime_ns
                if f in self.files and self.files[f][0] == m:
                    files[f] = self.files[f]
                    continue
                with open(path, encoding="utf-8", errors="replace") as fh:
                    files[f] = (m, [(n, s, words(s)) for n, t in enumerate(fh, 1) if is_line(t) for s in sentences(t)])
            except OSError:  # deleted but still in the git index
                pass
        if self.sents is not None and files == self.files:
            return False
        self.files = files
        self.sents = [(f, n, s) for f, (_, rows) in files.items() for n, s, _ in rows]
        toks = [w for _, rows in files.values() for _, _, w in rows]
        avgdl = sum(map(len, toks)) / max(len(toks), 1) or 1
        postings = defaultdict(list)  # word: [(sentence id, term weight)]
        for d, t in enumerate(toks):
            for w, tf in Counter(t).items():
                postings[w].append((d, tf * (K1 + 1) / (tf + K1 * (1 - B + B * len(t) / avgdl))))
        self.n = n = len(toks)
        self.postings = {w: (math.log(1 + (n - len(p) + 0.5) / (len(p) + 0.5)), p) for w, p in postings.items()}
        return True

    def bm25(self, text):
        """{sentence id: its best BM25 score against one of text's sentences, divided by the largest idf sum of text's
        sentences so scores of different texts compare}, scores > 0 only."""
        best, top = {}, 0
        for q in sentences(text):
            s, idfs = defaultdict(float), 0
            for w in set(words(q)):
                idf, p = self.postings.get(w, (math.log(1 + (self.n + 0.5) / 0.5), ()))
                idfs += idf
                for d, x in p:
                    s[d] += idf * x
            top = max(top, idfs)
            for d, x in s.items():
                best[d] = max(best.get(d, 0), x)
        return {d: x / top for d, x in best.items()}

    def search(self, queries, k, files=None, skip=None):
        """Per query, its k best lines by BM25, leaving out its own file (files[i]) and the line skip (file, line)."""
        out = []
        for i, q in enumerate(queries):
            scores, best = self.bm25(q), {}
            for d in sorted(scores, key=lambda d: (-scores[d], d)):
                f, n, s = self.sents[d]
                if (files and f == files[i]) or (f, n) == skip:
                    continue
                best.setdefault((f, n), (f, n, scores[d], s))
            out.append({"hits": [[f, n, round(sc, 4), s] for f, n, sc, s in list(best.values())[:k]]})
        return out


def sock():
    """server.py's socket: in the temp dir, as a socket path over ~104 bytes cannot bind. Raises OSError when there is
    no writable temp dir, so only the embeddings path calls it."""
    name = "dupcheck-" + hashlib.sha1(os.path.realpath(ROOT).encode()).hexdigest()[:12] + ".sock"
    return os.path.join(tempfile.gettempdir(), name)


def start_server(python):
    """Best effort: if it fails, BM25 still answers."""
    with contextlib.suppress(OSError):
        os.makedirs(TMP, exist_ok=True)
        with open(os.path.join(TMP, "server.log"), "a") as log:
            try:
                subprocess.Popen([python, os.path.join(ROOT, "tools", "dup-check", "server.py")],
                                 start_new_session=True, stdin=subprocess.DEVNULL, stdout=log, stderr=log, cwd=ROOT,
                                 env=ENV)
            except OSError as e:
                log.write(f"cannot start {python}: {e!r}\n")


def query(queries, k, files=None, skip=None, timeout=3.0):
    """Per query {"hits": [[file, line, score, sentence], ...]}, best first, sentence = the hit line's best-matching
    one; and the mode: "hybrid" (warm server), "bm25-cold" (in-process, the server not up yet) or "bm25" (in-process,
    embeddings off)."""
    python = git("config", "--type=path", "--get", "dupcheck.python").stdout.strip()
    if python:
        try:
            path = sock()
            if os.stat(path).st_uid != os.getuid():  # on a shared /tmp another user could bind it first
                raise PermissionError(path)
            with socket.socket(socket.AF_UNIX) as s:
                s.settimeout(timeout)
                s.connect(path)
                s.sendall((json.dumps({"queries": queries, "k": k, "files": files, "skip": skip}) + "\n").encode())
                return json.loads(s.makefile("rb").readline())["results"], "hybrid"
        except (OSError, ValueError, KeyError):
            start_server(python)
    index = Index()
    index.refresh()
    return index.search(queries, k, files, skip), "bm25-cold" if python else "bm25"

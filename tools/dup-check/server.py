"""Optional warm search server on dupcheck.sock(): BM25 + bge-small embeddings (CPU), fused per line by
reciprocal rank. Started detached by dupcheck.query() when `git config dupcheck.python` is set; a second copy exits
at once; per request re-reads changed files and embeds only sentences it has not seen; exits after 1 h idle
(DUPCHECK_IDLE_S overrides) or when that refresh fails. The model is downloaded once by hand; no hub calls here."""
import fcntl, json, os, socket, sys, time
from dupcheck import TMP, Index, sentences, sock

SOCK = sock()  # before the slow model load: no temp dir, no server
MODEL = "BAAI/bge-small-en-v1.5"
IDLE_S = int(os.environ.get("DUPCHECK_IDLE_S", 3600))


def log(msg):
    print(time.strftime("%F %T"), msg, flush=True)


os.makedirs(TMP, exist_ok=True)
lock = open(os.path.join(TMP, "server.lock"), "w")
try:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
except OSError:
    sys.exit(0)

os.environ["HF_HUB_OFFLINE"] = "1"
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL, device="cpu")
except Exception as e:
    log(f"embeddings unavailable, clients stay on BM25: {e!r}")
    sys.exit(0)

vecs = {}  # sentence: unit vector


def embed(texts):
    new = [t for t in dict.fromkeys(texts) if t not in vecs]
    if new:
        vecs.update(zip(new, model.encode(new, normalize_embeddings=True, batch_size=64)))
    return np.array([vecs[t] for t in texts])


def ranks(x):
    """The number of strictly higher scores: 0 for the best, ties share a rank."""
    return np.searchsorted(np.sort(-x), -x)


def rrf(a, b):
    return 1 / (60 + ranks(a)) + 1 / (60 + ranks(b))


index = Index()


def refresh():
    global emb, bounds, sent_file, sent_line
    try:
        if not index.refresh():
            return
        emb = embed([s for _, _, s in index.sents])
    except Exception as e:  # the index may now be ahead of the vectors: exit, the next client starts a clean server
        log(f"refresh failed, exiting: {e!r}")
        if os.path.exists(SOCK):
            os.unlink(SOCK)
        os._exit(1)
    ss = index.sents  # a line's sentences [bounds[j], bounds[j + 1])
    bounds = [i for i in range(len(ss)) if i == 0 or ss[i][:2] != ss[i - 1][:2]] + [len(ss)]
    sent_file = np.array([f for f, _, _ in index.sents])
    sent_line = np.array([n for _, n, _ in index.sents])


def search(queries, k, files=None, skip=None):
    """As Index.search, with each line ranked by BM25 and by cosine (both its best sentence) and fused as RRF."""
    if not index.sents:
        return [{"hits": []} for _ in queries]
    qs = [sentences(q) for q in queries]
    qvecs = np.split(embed([s for q in qs for s in q]), np.cumsum([len(q) for q in qs])[:-1])
    out = []
    for i, qv in enumerate(qvecs):
        bm = np.zeros(len(index.sents))
        for d, x in index.bm25(queries[i]).items():
            bm[d] = x
        de = (emb @ qv.T).max(1)
        drop = sent_file == files[i] if files and files[i] else np.zeros(len(bm), bool)
        if skip:
            drop |= (sent_file == skip[0]) & (sent_line == skip[1])
        bm[drop], de[drop] = -np.inf, -np.inf
        line_bm, line_de = np.maximum.reduceat(bm, bounds[:-1]), np.maximum.reduceat(de, bounds[:-1])
        line, sent = rrf(line_bm, line_de), rrf(bm, de)
        hits = []
        for j in np.argsort(-line, kind="stable")[:k]:
            if np.isfinite(line_de[j]):
                a, b = bounds[j], bounds[j + 1]
                f, n, s = index.sents[a + int(np.argmax(sent[a:b]))]
                hits.append([f, n, round(float(line[j]), 4), s])
        out.append({"hits": hits})
    return out


t0 = time.time()
refresh()
log(f"warm in {time.time() - t0:.1f}s: {len(index.sents)} sentences")
if os.path.exists(SOCK):
    os.unlink(SOCK)
srv = socket.socket(socket.AF_UNIX)
srv.bind(SOCK)
srv.listen()
srv.settimeout(IDLE_S)
while True:
    try:
        conn, _ = srv.accept()
    except socket.timeout:
        break
    with conn:
        try:
            conn.settimeout(10)
            data = conn.makefile("rb").readline()
            if not data:
                continue
            req = json.loads(data)
            refresh()
            results = search(req["queries"], req.get("k", 3), req.get("files"), req.get("skip"))
            conn.sendall((json.dumps({"results": results}) + "\n").encode())
        except Exception as e:
            log(f"request failed: {e!r}")
os.unlink(SOCK)
log("idle, exiting")

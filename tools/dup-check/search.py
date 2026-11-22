#!/usr/bin/env python3
"""Lines of the repo's markdown and .tyaml most like a text or like one repo line, best first: file:line  BM25 score
the line's best-matching sentence. The pre-commit hook (hook.py) stops an agent's commit on a hit from its FLOOR up.
Usage: search.py "text" [-k 20]      search.py path/to/file.md:LINE [-k 20]   (or .tyaml; that line's own paragraph
or record is left out, dupcheck.units)"""
import argparse, os, re, sys
from dupcheck import ROOT, search, units

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("target")
ap.add_argument("-k", type=int, default=20)
a = ap.parse_args()
m = re.fullmatch(r"(.+\.(?:md|tyaml)):(\d+)", a.target)
if m:
    path = next((p for p in (os.path.abspath(m[1]), os.path.join(ROOT, m[1])) if os.path.isfile(p)), None)
    if not path:
        sys.exit(f"no such file: {m[1]}")
    f, n = os.path.relpath(os.path.realpath(path), os.path.realpath(ROOT)), int(m[2])
    with open(path, encoding="utf-8", errors="replace") as fh:
        u = units(f, fh.read())
    if not 1 <= n <= len(u):
        sys.exit(f"{m[1]} has no line {n}")
    text, at = u[n - 1][0], (f, n)
else:
    text, at = a.target, None
if not re.search(r"\w", text):
    sys.exit(f"nothing to search for: {text!r}")
for f, n, score, sentence in search([text], a.k, at=[at])[0]:
    print(f"{f}:{n}  {score:5.1f}  {sentence.strip()[:200]}")

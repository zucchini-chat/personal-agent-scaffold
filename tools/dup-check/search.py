#!/usr/bin/env python3
"""Lines of the repo's markdown most like a text or like one repo line, best first: file:line  BM25 score  the line's
best-matching sentence. The post-commit hook shows a hit only from its FLOOR score up.
Usage: search.py "text" [-k 20]      search.py path/to/file.md:LINE [-k 20]   (that line itself is left out)"""
import argparse, os, re, sys
from dupcheck import ROOT, search

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("target")
ap.add_argument("-k", type=int, default=20)
a = ap.parse_args()
m = re.fullmatch(r"(.+\.md):(\d+)", a.target)
if m:
    path = next((p for p in (os.path.abspath(m[1]), os.path.join(ROOT, m[1])) if os.path.isfile(p)), None)
    if not path:
        sys.exit(f"no such file: {m[1]}")
    line = int(m[2])
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().split("\n")
    if not 1 <= line <= len(lines):
        sys.exit(f"{m[1]} has no line {line}")
    text, skip = lines[line - 1], (os.path.relpath(os.path.realpath(path), os.path.realpath(ROOT)), line)
else:
    text, skip = a.target, None
if not re.search(r"\w", text):
    sys.exit(f"nothing to search for: {text!r}")
for f, n, score, sentence in search([text], a.k, skip=skip)[0]:
    print(f"{f}:{n}  {score:5.1f}  {sentence.strip()[:200]}")

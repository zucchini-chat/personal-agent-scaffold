#!/usr/bin/env python3
"""Checks .tyaml files (typed YAML: CLAUDE.md > "Working rules", tools.md > "Typed YAML"); run by
tools/git-hooks/pre-commit. Usage: tyaml.py FILE...  Exit 3 when a file breaks its types or PyYAML is missing."""
import datetime
import re
import sys

try:
    import yaml
except ImportError:
    print('tyaml.py: PyYAML is missing, so the .tyaml files cannot be checked; install it: tools.md > "Typed YAML"',
          file=sys.stderr)
    sys.exit(3)

BASE = {"str": str, "int": int, "num": (int, float), "bool": bool, "date": datetime.date}


def ok(value, t):
    if t.endswith("[]"):
        return isinstance(value, list) and value and all(ok(v, t[:-2]) for v in value)
    if t in BASE:
        return isinstance(value, BASE[t]) and (t == "bool" or not isinstance(value, bool))
    return value in t.split("|")


def errors(path):
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        docs = list(yaml.safe_load_all(text))
    except (OSError, ValueError, yaml.YAMLError) as e:  # ValueError: a bad date such as 2027-02-30
        return [f"{path}: {e}"]
    if len(docs) != 2 or not isinstance(docs[0], dict) or "types" not in docs[0]:
        return [f"{path}: needs two documents, types: first and the data second"]
    types, data = docs[0]["types"], {} if docs[1] is None else docs[1]
    if not isinstance(types, dict):
        return [f"{path}: types: is not a mapping of keys to their fields"]
    if not isinstance(data, dict):
        return [f"{path}: the data is not a mapping of keys to lists of records"]
    errs = [f"{path}: types: {key}: needs field: type lines, each type a string"
            for key, fields in types.items()
            if not isinstance(fields, dict) or not all(isinstance(t, str) for t in fields.values())]
    errs += [f"{path}: types: {key}: {f}: unknown type {t} (use {', '.join(BASE)} or a|b)"
             for key, fields in types.items() if isinstance(fields, dict)
             for f, t in fields.items() if isinstance(t, str)
             and "|" not in t and t.rstrip("?").removesuffix("[]") not in BASE]
    if errs:
        return errs
    errs = [f"{path}: {key}: no types for it" for key in data.keys() - types.keys()]
    errs += [f"{path}:{n}: '' is an apostrophe in a single-quoted string, which grep misses: write the value as a |- block"
             for n, line in enumerate(text.splitlines(), 1) if re.search(r"'.*''", line)]
    for key, fields in types.items():
        recs = [] if data.get(key) is None else data[key]
        if not isinstance(recs, list):
            errs.append(f"{path}: {key}: is not a list of records")
            continue
        for i, rec in enumerate(recs):
            if not isinstance(rec, dict):
                errs.append(f"{path}: {key}[{i}]: is not a record of field: value lines: {rec!r}")
                continue
            where = f"{path}: {key}[{i}] {rec.get('name', '')}"
            errs += [f"{where}: unknown field {f}" for f in rec.keys() - fields.keys()]
            for f, t in fields.items():
                if f not in rec:
                    if not t.endswith("?"):
                        errs.append(f"{where}: missing {f}")
                elif not ok(rec[f], t.rstrip("?")):
                    errs.append(f"{where}: {f} is not {t}: {rec[f]!r}")
    return errs


if __name__ == "__main__":
    errs = [e for path in sys.argv[1:] for e in errors(path)]
    if errs:
        print("\n".join(errs), file=sys.stderr)
        sys.exit(3)

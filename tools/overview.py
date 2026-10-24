#!/usr/bin/env python3
"""Session-start status: calendar today + tomorrow (when tools/calendar-today exists) and the last N commits.

usage: overview.py [N]   (default 20)
"""
import datetime
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CALENDAR = os.path.join(HERE, "calendar-today")


def calendar():
    r = subprocess.run([CALENDAR], capture_output=True, text=True)
    if r.returncode:
        return f"(tools/calendar-today failed: {r.stderr.strip()[-300:]})"
    return r.stdout.strip() or "(nothing)"


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    print(f"# Overview {datetime.datetime.now():%a %Y-%m-%d %H:%M}\n")
    if os.access(CALENDAR, os.X_OK):
        print(f"# Calendar today + tomorrow\n{calendar()}\n")
    log = subprocess.run(["git", "-C", HERE, "log", f"-{n}", "--date=format:%m-%d %H:%M", "--format=%ad %s"],
                         capture_output=True, text=True).stdout
    print(f"# Git log (last {n})\n{log}", end="")


if __name__ == "__main__":
    main()

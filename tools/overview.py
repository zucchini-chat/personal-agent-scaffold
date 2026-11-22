#!/usr/bin/env python3
"""Session-start status: the mail desk's health (when it is on), calendar today + tomorrow (when tools/calendar-today exists) and the last N commits.

usage: overview.py [N]   (default 20)
Commit lines are cut to 110 characters: Claude Code shows only a short preview of hook output over 10,000 characters.
"""
import datetime
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CALENDAR = os.path.join(HERE, "calendar-today")
AGENTS = os.path.join(os.path.dirname(HERE), "agents", "CLAUDE.md")
CURSOR = os.path.join(HERE, "mail-watch-cursor")  # the mail tool touches it after every poll


def calendar():
    r = subprocess.run([CALENDAR], capture_output=True, text=True)
    if r.returncode:
        return f"(tools/calendar-today failed: {r.stderr.strip()[-300:]})"
    return r.stdout.strip() or "(nothing)"


def mail_desk():
    """None unless the Mail desk row in agents/CLAUDE.md is on; else OK or DOWN by the age of the mail tool's cursor."""
    try:
        with open(AGENTS, encoding="utf-8") as f:
            row = next((line for line in f if line.startswith("| Mail desk")), "")
    except (OSError, ValueError):
        return None
    if row.strip().strip("|").split("|")[-1].strip() != "on":
        return None
    try:
        age = int((time.time() - os.path.getmtime(CURSOR)) / 60)
    except OSError:
        return "DOWN (no poll yet)"
    return "OK" if age < 5 else f"DOWN (last poll {age} min ago)"


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    print(f"# Overview {datetime.datetime.now():%a %Y-%m-%d %H:%M}")
    desk = mail_desk()
    if desk:
        print(f"Mail desk: {desk}")
    print()
    if os.access(CALENDAR, os.X_OK):
        print(f"# Calendar today + tomorrow\n{calendar()}\n")
    log = subprocess.run(["git", "-C", HERE, "log", f"-{n}", "--date=format:%m-%d %H:%M", "--format=%ad %s"],
                         capture_output=True, text=True).stdout
    log = "".join((line if len(line) <= 110 else line[:109] + "…") + "\n" for line in log.splitlines())
    print(f"# Git log (last {n})\n{log}", end="")


if __name__ == "__main__":
    main()

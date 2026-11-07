#!/usr/bin/env python3
"""PreToolUse hook: denies reading a mail the mail guard flagged or has not judged yet (its last route in
verdicts.jsonl next to this file is FLAG or PENDING): Bash naming its id with a read word or a URL, WebFetch or an MCP
tool naming its id anywhere. No verdicts file, no checks; unknown ids pass. Fails open: on any error the call goes
through. Docs: agents/mail-desk.md > "Mail guard"."""
import json
import os
import re
import sys

VERDICTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verdicts.jsonl")
READS = re.compile(r"(?<![\w-])(?:read|raw|get|show|thread|attachments?|download|open|fetch|view)(?![\w-])")
URL = re.compile(r"https?://")
REASONS = {
    "FLAG": "Mail guard: mail {id} is flagged; only the owner reads it. Never open it another way (browser, API, "
            "another tool). If its only miss was an unknown sender and the owner vouches for them, add them to "
            "\"Known senders\" in agents/mail-desk.md and run `python3 tools/mail-guard/guard.py recheck {id}`; "
            "otherwise tell Chief of Staff.",
    "PENDING": "Mail guard: mail {id} is not judged yet; retry in a minute. If it comes back FLAG, do not open it "
               "another way. If it stays unjudged, the guard is down: agents/mail-desk.md > \"Mail guard\"."}


def routes():
    """The last route per id; malformed lines skipped."""
    last = {}
    with open(VERDICTS, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if isinstance(r, dict) and isinstance(r.get("id"), str):
                last[r["id"]] = r.get("route")
    return last


def main():
    call = json.load(sys.stdin.buffer)
    if not os.path.exists(VERDICTS):
        return
    name, inp = call.get("tool_name", ""), call.get("tool_input") or {}
    if name == "Bash":
        text = inp.get("command", "")
        if not (READS.search(text) or URL.search(text)):
            return
    elif name == "WebFetch" or name.startswith("mcp__"):
        text = json.dumps(inp, ensure_ascii=False)
    else:
        return
    last = routes()
    for route in ("FLAG", "PENDING"):
        for i, r in last.items():
            if r == route and len(i) >= 6 and i in text and re.search(rf"(?<![\w-]){re.escape(i)}(?![\w-])", text):
                print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                         "permissionDecisionReason": REASONS[route].format(id=i)}}))
                return


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass

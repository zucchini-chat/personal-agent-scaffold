#!/usr/bin/env python3
"""PreToolUse hook for the mail guard; first deny wins:
- every session: Write/Edit of verdicts.jsonl or desk-chat-id next to this file (only guard.py writes them);
- the mail desk's chat (ZUCCHINI_CHAT_ID equal to desk-chat-id, which `guard.py watch` records): sending mail (a send
  word outside quotes, SMTP, an MCP send tool) and changing the mail guard or the hooks' settings;
- reading a mail the guard flagged, has not judged yet or routed to a job's chat (its last route in verdicts.jsonl is
  FLAG, PENDING or CODE): Bash naming its id with a read word or a URL, WebFetch or an MCP tool naming its id anywhere.
No verdicts file, no checks; unknown ids and tools pass. Fails open: on any error the call goes through.
Docs: agents/mail-desk.md > "Mail guard"."""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
VERDICTS = os.path.join(HERE, "verdicts.jsonl")
DESK = os.path.join(HERE, "desk-chat-id")
FILE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
READS = re.compile(r"(?<![\w-])(?:read|raw|get|show|thread|attachments?|download|open|fetch|view)(?![\w-])")
URL = re.compile(r"https?://")
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1([^\n]*)\n.*?^\s*\2\s*$", re.S | re.M)
QUOTED = re.compile(r"'[^']*'|\"(?:[^\"\\]|\\.)*\"")
SEND_WORDS = re.compile(r"(?<![a-z])(?:send|reply|forward|drafts?|sendmail|smtp)(?![a-z])", re.I)
SEND_RAW = re.compile(r"smtplib|smtps?://|/send\b|/drafts", re.I)
SEND_TOOL = re.compile(r"send|reply|forward|draft", re.I)
GUARD_PATHS = re.compile(r"verdicts\.jsonl|desk-chat-id|\.claude(?![\w-])|mail-guard(?![\w-])", re.I)
GUARD_RUN = re.compile(r"(^|[;&|(])\s*python3?\s+(?:-u\s+)?[\w./~-]*mail-guard/guard\.py(?=\s|$)", re.M)  # as a command
REASONS = {
    "FLAG": "Mail guard: mail {id} is flagged; only the owner reads it. Never open it another way (browser, API, "
            "another tool). If its only miss was an unknown sender and the owner vouches for them, add them to "
            "\"Known senders\" in agents/mail-desk.md and run `python3 tools/mail-guard/guard.py recheck {id}`; "
            "otherwise tell Chief of Staff.",
    "PENDING": "Mail guard: mail {id} is not judged yet; retry in a minute. If it comes back FLAG, do not open it "
               "another way. If it stays unjudged, the guard is down: agents/mail-desk.md > \"Mail guard\".",
    "CODE": "Mail guard: mail {id} is a code-host notification for a job; its text is the employer's and stays out of "
            "this repo's chats. Send the job chat the `GITHUB` line built from `python3 tools/mail-guard/guard.py "
            "verdict {id}` as agents/mail-desk.md > \"Handling a mail\" says; the job chat reads the thread on the "
            "code host.",
    "VERDICTS": "Mail guard: the verdicts are guard.py's alone; only it writes verdicts.jsonl and desk-chat-id. Read a "
                "verdict with `python3 tools/mail-guard/guard.py verdict <id>`; never change one another way.",
    "SEND": "Mail guard: the mail desk never sends mail (no send, reply, forward or draft). Anything for a person goes "
            "to Chief of Staff via SendMessage; never send it another way.",
    "GUARD": "Mail guard: the mail desk never edits the mail guard or the hooks' settings. A change goes through Chief "
             "of Staff; never work around this."}


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


def resolved(path):
    """A path resolved against the repo, lowercased (macOS paths ignore case by default)."""
    return os.path.realpath(os.path.join(REPO, os.path.expanduser(path))).lower()


def inside(path, *dirs):
    return any((path + os.sep).startswith(resolved(d) + os.sep) for d in dirs)


def desk():
    """Whether this is the mail desk's chat."""
    chat = os.environ.get("ZUCCHINI_CHAT_ID", "")
    try:
        with open(DESK, encoding="utf-8") as f:
            return chat != "" and f.read().strip() == chat
    except OSError:
        return False


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))


def main():
    call = json.load(sys.stdin.buffer)
    if not os.path.exists(VERDICTS):
        return
    name, inp = call.get("tool_name", ""), call.get("tool_input") or {}
    path = inp.get("file_path") or inp.get("notebook_path") if name in FILE_TOOLS else None
    path = resolved(path) if isinstance(path, str) and path else ""
    if path in (resolved(VERDICTS), resolved(DESK)):
        return deny(REASONS["VERDICTS"])
    if desk():
        if name == "Bash":
            cmd = inp.get("command", "")
            if SEND_WORDS.search(QUOTED.sub("''", HEREDOC.sub(r"<<\3", cmd))) or SEND_RAW.search(cmd):
                return deny(REASONS["SEND"])
            if GUARD_PATHS.search(GUARD_RUN.sub(r"\1", cmd)):
                return deny(REASONS["GUARD"])
        elif name.startswith("mcp__") and SEND_TOOL.search(name.split("__", 2)[-1]):
            return deny(REASONS["SEND"])
        elif path and inside(path, HERE, os.path.join(REPO, ".claude"), "~/.claude"):
            return deny(REASONS["GUARD"])
    if name == "Bash":
        text = inp.get("command", "")
        if not (READS.search(text) or URL.search(text)):
            return
    elif name == "WebFetch" or name.startswith("mcp__"):
        text = json.dumps(inp, ensure_ascii=False)
    else:
        return
    last = routes()
    for route in ("FLAG", "PENDING", "CODE"):
        for i, r in last.items():
            if r == route and len(i) >= 6 and i in text and re.search(rf"(?<![\w-]){re.escape(i)}(?![\w-])", text):
                return deny(REASONS[route].format(id=i))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass

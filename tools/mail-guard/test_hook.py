#!/usr/bin/env python3
"""Runs hook.py on sample PreToolUse calls, each test in a throwaway repo layout with a fake verdicts file.
Run: python3 -m unittest discover -s tools/mail-guard   (or this file directly)"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hook.py")
VERDICTS = """{"id": "flag-000001", "account": "acct", "route": "FLAG"}
{"id": "pend-000001", "account": "acct", "route": "PENDING"}
{"id": "new-0000001", "account": "acct", "route": "NEW"}
{"id": "code-000001", "account": "acct", "route": "CODE"}
{"id": "flip-000001", "account": "acct", "route": "FLAG"}
{"id": "flip-000001", "account": "acct", "route": "NEW"}
{"id": "abc12", "account": "acct", "route": "FLAG"}
not json
[]
{"id": 1234567, "route": "FLAG"}
{"route": "FLAG"}
"""
MAIL = "python3 tools/mail.py"
B = "mcp__plugin_shared-chrome-mcp_browser__browser_"


class HookTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo, self.home = tmp.name, os.path.join(tmp.name, "home")
        self.dir = os.path.join(tmp.name, "tools", "mail-guard")
        os.makedirs(self.dir)
        shutil.copy(HOOK, self.dir)
        with open(os.path.join(self.dir, "verdicts.jsonl"), "w") as f:
            f.write(VERDICTS)
        with open(os.path.join(self.dir, "desk-chat-id"), "w") as f:
            f.write("c-desk\n")
        self.chat = None  # this session's ZUCCHINI_CHAT_ID

    def run_hook(self, stdin):
        env = {k: v for k, v in os.environ.items() if k != "ZUCCHINI_CHAT_ID"}
        env.update(HOME=self.home, **({"ZUCCHINI_CHAT_ID": self.chat} if self.chat is not None else {}))
        r = subprocess.run([sys.executable, os.path.join(self.dir, "hook.py")], input=stdin, capture_output=True,
                           encoding="utf-8", env=env)
        return r.returncode, r.stdout, r.stderr

    def reason(self, tool, inp):
        """The deny reason, or None when the call goes through."""
        call = {"session_id": "s1", "hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": inp}
        code, out, err = self.run_hook(json.dumps(call))
        self.assertEqual((code, err), (0, ""))
        if not out:
            return None
        out = json.loads(out)["hookSpecificOutput"]
        self.assertEqual((out["hookEventName"], out["permissionDecision"]), ("PreToolUse", "deny"))
        return out["permissionDecisionReason"]

    def bash(self, cmd):
        return self.reason("Bash", {"command": cmd})

    def test_reading_a_flagged_mail_is_denied(self):
        r = self.bash(f"{MAIL} read acct flag-000001")
        self.assertIn("mail flag-000001 is flagged; only the owner reads it", r)
        self.assertIn("python3 tools/mail-guard/guard.py recheck flag-000001", r)
        self.assertIsNotNone(self.bash(f"{MAIL} raw acct 'flag-000001' > tmp/m.eml"))
        self.assertIsNotNone(self.bash(f"{MAIL} attachments acct flag-000001"))
        self.assertIsNotNone(self.bash(f'{MAIL} "read" acct flag-000001'))
        self.assertIsNotNone(self.bash(f'bash -lc "{MAIL} read acct flag-000001"'))

    def test_reading_a_pending_mail_is_denied(self):
        r = self.bash(f"{MAIL} raw acct pend-000001")
        self.assertIn("mail pend-000001 is not judged yet; retry in a minute", r)

    def test_reading_a_code_host_mail_is_denied(self):
        r = self.bash(f"{MAIL} read acct code-000001")
        self.assertIn("mail code-000001 is a code-host notification for a job", r)
        self.assertIn("python3 tools/mail-guard/guard.py verdict code-000001", r)
        self.assertIsNotNone(self.reason(B + "navigate", {"url": "https://mail.example.test/#inbox/code-000001"}))
        for cmd in ("python3 tools/mail-guard/guard.py verdict code-000001", f'{MAIL} mark code-000001 "sent to job"'):
            self.assertIsNone(self.bash(cmd), cmd)

    def test_url_browser_and_fetch_naming_the_id_are_denied(self):
        self.assertIsNotNone(self.bash('curl -s "https://mail.example.test/api/messages/flag-000001?format=raw"'))
        self.assertIsNotNone(self.reason(B + "navigate", {"url": "https://mail.example.test/#inbox/flag-000001"}))
        self.assertIsNotNone(self.reason("WebFetch", {"url": "https://mail.example.test/m/pend-000001",
                                                      "prompt": "summarize"}))
        self.assertIsNotNone(self.reason("mcp__mail__get_message", {"id": "flag-000001"}))

    def test_other_calls_on_a_flagged_id_pass(self):
        for cmd in (f"{MAIL} mark-read acct flag-000001", f'{MAIL} mark flag-000001 "reported to Chief of Staff"',
                    "python3 tools/mail-guard/guard.py verdict flag-000001",
                    "python3 tools/mail-guard/guard.py recheck flag-000001"):
            self.assertIsNone(self.bash(cmd), cmd)
        self.assertIsNone(self.reason("Read", {"file_path": "/tmp/flag-000001.eml"}))

    def test_judged_unknown_and_short_ids_pass(self):
        for cmd in (f"{MAIL} read acct new-0000001", f"{MAIL} read acct unknown-0001", f"{MAIL} read acct abc12",
                    f"{MAIL} read acct flag-0000012", f"{MAIL} read acct xflag-000001", f"{MAIL} read acct 1234567"):
            self.assertIsNone(self.bash(cmd), cmd)

    def test_last_record_wins(self):
        self.assertIsNone(self.bash(f"{MAIL} read acct flip-000001"))

    def test_desk_never_sends_mail(self):
        self.chat = "c-desk"
        for cmd in (f"{MAIL} send acct x", f"{MAIL} Reply acct m-000001", f"{MAIL} forward acct m-000001 a@b.test",
                    f"{MAIL} draft acct x", f"{MAIL} drafts acct", "sendmail -t < tmp/m.eml",
                    "gog gmail send --to a@b.test --subject hi --body x", "curl --url smtps://smtp.example.test -T m",
                    "python3 -c \"import smtplib; smtplib.SMTP('smtp.example.test')\"",
                    "curl -X POST https://mail.example.test/v1/users/me/messages/send -d @m.json",
                    "curl https://mail.example.test/v1/users/me/drafts", f'{MAIL} mark m1 "x" && {MAIL} send acct x',
                    f"{MAIL} send-message acct x", f"{MAIL} SEND_MESSAGE acct x", "tool reply-all m1",
                    "gmail create_draft x", "openssl s_client -starttls smtp -connect host:587",
                    "ls tools/send_mail.py send-later"):
            self.assertIn("the mail desk never sends mail", self.bash(cmd) or "", cmd)
        for tool in ("mcp__mail__send_message", "mcp__gmail__create_draft", "mcp__mail__Reply_all", "mcp__m__forward"):
            self.assertIn("the mail desk never sends mail", self.reason(tool, {"id": "m-000001"}) or "", tool)

    def test_desk_never_edits_the_guard_or_settings(self):
        self.chat = "c-desk"
        hook = os.path.join(self.dir, "hook.py")
        for tool, inp in (("Write", {"file_path": hook, "content": "x"}),
                          ("Write", {"file_path": "tools/mail-guard/hook.py", "content": "x"}),
                          ("Edit", {"file_path": os.path.join(self.repo, ".claude", "settings.json")}),
                          ("Edit", {"file_path": os.path.join(self.home, ".claude", "settings.json")}),
                          ("MultiEdit", {"file_path": "~/.claude/settings.json", "edits": []}),
                          ("NotebookEdit", {"notebook_path": os.path.join(self.dir, "x.ipynb")}),
                          ("Bash", {"command": "rm tools/mail-guard/verdicts.jsonl"}),
                          ("Bash", {"command": "sed -i '' 's/deny/allow/' tools/mail-guard/hook.py"}),
                          ("Bash", {"command": "echo c-x > tools/mail-guard/desk-chat-id"}),
                          ("Bash", {"command": "cd tools/mail-guard && rm hook.py"}),
                          ("Bash", {"command": "cp x tools/mail-guard/guard.py.bak"}),
                          ("Bash", {"command": "rm tools/mail-guard/guard.py"}),
                          ("Bash", {"command": "echo x > tools/mail-guard/guard.py"}),
                          ("Bash", {"command": "python3 tools/mail-guard/guard.py verdict m1 "
                                               "> tools/mail-guard/guard.py"}),
                          ("Bash", {"command": "sed -i s/a/b/ tools/mail-guard/hook.py"}),
                          ("Bash", {"command": "tee python3 tools/mail-guard/guard.py < x"}),
                          ("Bash", {"command": "python3 x;rm${IFS}tools/mail-guard/guard.py"}),
                          ("Bash", {"command": "cat ~/.claude/settings.json"})):
            self.assertIn("the mail desk never edits the mail guard", self.reason(tool, inp) or "", inp)

    def test_desk_allowances(self):
        self.chat = "c-desk"
        for cmd in ("python3 tools/mail-guard/guard.py verdict m-000001", f"{MAIL} read acct new-0000001",
                    f'{MAIL} mark m-000001 "reply needed, sent to Chief of Staff"', f"{MAIL} mark-read acct m-000001",
                    'git commit -m "forward rule" -- f', "git commit -F - -- f <<'EOF'\nSender rule: reply to X\nEOF",
                    'python3 -u tools/mail-guard/guard.py watch --once --tool "python3 tools/mail.py"',
                    "python3 tools/mail-guard/guard.py verdict m1",
                    "cd /repo && python3 -u /repo/tools/mail-guard/guard.py recheck m1",
                    "ls tools/sender-list resend senders replying forwarded Drafted smtplike"):
            self.assertIsNone(self.bash(cmd), cmd)
        self.assertIsNone(self.reason(B + "click", {"element": "Archive", "ref": "e12"}))
        self.assertIsNone(self.reason("Write", {"file_path": os.path.join(self.repo, "notes.md"), "content": "x"}))
        self.assertIn("flagged", self.bash(f"{MAIL} read acct flag-000001"))

    def test_no_desk_lock_outside_the_desk_chat(self):
        hook = os.path.join(self.dir, "hook.py")
        for chat in ("c-other", None, ""):
            self.chat = chat
            self.assertIsNone(self.bash(f"{MAIL} send acct x"), chat)
            self.assertIsNone(self.reason("Edit", {"file_path": hook}), chat)
        self.chat = "c-desk"
        os.remove(os.path.join(self.dir, "desk-chat-id"))
        self.assertIsNone(self.bash(f"{MAIL} send acct x"))
        self.assertIsNone(self.reason("Edit", {"file_path": hook}))

    def test_only_guard_writes_the_verdicts(self):
        link = os.path.join(self.repo, "link.jsonl")
        os.symlink(os.path.join(self.dir, "verdicts.jsonl"), link)
        for chat in (None, "c-desk"):
            self.chat = chat
            for tool, path in (("Write", os.path.join(self.dir, "verdicts.jsonl")),
                               ("Edit", "tools/mail-guard/desk-chat-id"),
                               ("MultiEdit", "tools/x/../mail-guard/verdicts.jsonl"), ("Write", link)):
                self.assertIn("the verdicts are guard.py's alone", self.reason(tool, {"file_path": path}) or "", path)
        self.chat = None
        self.assertIsNone(self.reason("Write", {"file_path": os.path.join(self.repo, "notes.md"), "content": "x"}))

    def test_no_verdicts_file_allows_everything(self):
        os.remove(os.path.join(self.dir, "verdicts.jsonl"))
        self.assertIsNone(self.bash(f"{MAIL} read acct flag-000001"))
        self.chat = "c-desk"
        self.assertIsNone(self.bash(f"{MAIL} send acct x"))

    def test_malformed_stdin_fails_open_silently(self):
        for stdin in ("", "not json", "[]", "null", '{"tool_name": "Bash", "tool_input": "x"}',
                      '{"tool_name": "Bash", "tool_input": {"command": 5}}'):
            self.assertEqual(self.run_hook(stdin), (0, "", ""), stdin)


class SettingsTest(unittest.TestCase):
    def test_settings_route_the_guarded_tools_to_the_hook(self):
        with open(os.path.join(os.path.dirname(HOOK), "..", "..", ".claude", "settings.json")) as f:
            entries = json.load(f)["hooks"]["PreToolUse"]
        [matcher] = [e["matcher"] for e in entries
                     if any("tools/mail-guard/hook.py" in h["command"] for h in e["hooks"])]
        for tool in ("Bash", "WebFetch", "Write", "Edit", "MultiEdit", "NotebookEdit", "mcp__mail__get_message"):
            self.assertTrue(re.fullmatch(matcher, tool), tool)
        self.assertFalse(re.fullmatch(matcher, "Read"))


if __name__ == "__main__":
    unittest.main()

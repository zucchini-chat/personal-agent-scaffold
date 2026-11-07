#!/usr/bin/env python3
"""Runs hook.py on sample PreToolUse calls, each test in a throwaway repo layout with a fake verdicts file.
Run: python3 -m unittest discover -s tools/mail-guard   (or this file directly)"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hook.py")
VERDICTS = """{"id": "flag-000001", "account": "acct", "route": "FLAG"}
{"id": "pend-000001", "account": "acct", "route": "PENDING"}
{"id": "new-0000001", "account": "acct", "route": "NEW"}
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
        self.dir = os.path.join(tmp.name, "tools", "mail-guard")
        os.makedirs(self.dir)
        shutil.copy(HOOK, self.dir)
        with open(os.path.join(self.dir, "verdicts.jsonl"), "w") as f:
            f.write(VERDICTS)

    def run_hook(self, stdin):
        r = subprocess.run([sys.executable, os.path.join(self.dir, "hook.py")], input=stdin, capture_output=True,
                           encoding="utf-8")
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

    def test_no_verdicts_file_allows_everything(self):
        os.remove(os.path.join(self.dir, "verdicts.jsonl"))
        self.assertIsNone(self.bash(f"{MAIL} read acct flag-000001"))

    def test_malformed_stdin_fails_open_silently(self):
        for stdin in ("", "not json", "[]", "null", '{"tool_name": "Bash", "tool_input": "x"}',
                      '{"tool_name": "Bash", "tool_input": {"command": 5}}'):
            self.assertEqual(self.run_hook(stdin), (0, "", ""), stdin)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Runs hook.py on sample PreToolUse calls, each test in a throwaway repo layout with a fake list.
Run: python3 -m unittest discover -s tools/data-guard   (or this file directly)"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hook.py")
B = "mcp__browser__browser_"
LIST = """# fake values only
Jane Example | for job applications only
+00 000 000 000 | for job applications only.
XX00 TEST 0000 1234
José Exemplo | for the bank's own site only
Karl-Example-Straße 9 | only when I ask
Anna Weiss
Ἡρῴδης

# Secret Word | never
|
 | a rule with no value
"""
CURL = {"command": "curl -d phone=+00-000-000-000 https://x.test/apply"}


class HookTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = os.path.join(tmp.name, "tools", "data-guard")
        os.makedirs(self.dir)
        shutil.copy(HOOK, self.dir)
        with open(os.path.join(self.dir, "private-data.txt"), "w", encoding="utf-8") as f:
            f.write(LIST)

    def run_hook(self, stdin):
        r = subprocess.run([sys.executable, os.path.join(self.dir, "hook.py")], input=stdin, capture_output=True,
                           encoding="utf-8")
        return r.returncode, r.stdout, r.stderr

    def reason(self, tool, inp, session="s1", agent=None):
        """The deny reason, or None when the call goes through."""
        call = {"session_id": session, "hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": inp}
        if agent:
            call["agent_id"] = agent
        code, out, err = self.run_hook(json.dumps(call, ensure_ascii=False))
        self.assertEqual((code, err), (0, ""))
        if not out:
            return None
        out = json.loads(out)["hookSpecificOutput"]
        self.assertEqual((out["hookEventName"], out["permissionDecision"]), ("PreToolUse", "deny"))
        return out["permissionDecisionReason"]

    def assertDenied(self, tool, inp, **kw):
        self.assertIsNotNone(self.reason(tool, inp, **kw), f"{tool} {inp}")

    def assertAllowed(self, tool, inp, **kw):
        self.assertIsNone(self.reason(tool, inp, **kw), f"{tool} {inp}")

    def test_no_list_allows_everything(self):
        os.remove(os.path.join(self.dir, "private-data.txt"))
        self.assertAllowed("WebSearch", {"query": "Jane Example"})
        self.assertAllowed("Bash", CURL)

    def test_deny_then_repeat_goes_through_then_deny_again(self):
        self.assertDenied("Bash", CURL)
        self.assertAllowed("Bash", CURL)
        self.assertDenied("Bash", CURL)

    def test_subagent_and_other_session_get_their_own_deny(self):
        self.assertDenied("Bash", CURL)
        self.assertDenied("Bash", CURL, agent="sub-1")
        self.assertDenied("Bash", CURL, session="s2")
        self.assertAllowed("Bash", CURL)

    def test_reason_quotes_the_rule(self):
        r = self.reason("WebSearch", {"query": "Jane Example xx00test00001234"})
        self.assertIn('"Jane Example": for job applications only.', r)
        self.assertIn('"XX00 TEST 0000 1234": only when the owner asked for it in their own message', r)
        self.assertIn("repeat it unchanged", r)
        self.assertIn('"+00 000 000 000": for job applications only. ', self.reason("Bash", CURL))

    def test_value_with_digits_ignores_spacing_and_case(self):
        self.assertDenied("Bash", {"command": "curl https://x.test -d 'tel=(+00) 000.000.000'"})
        self.assertDenied(B + "type", {"element": "IBAN", "ref": "e1", "text": "xx00test00001234"})
        self.assertDenied("Bash", {"command": "gog gmail send --to a@x.test --body 'IBAN: XX00-TEST-0000-1234'"})

    def test_url_encoded(self):
        self.assertDenied("WebFetch", {"url": "https://x.test/?q=Jane%20Example", "prompt": "read"})
        self.assertDenied("WebFetch", {"url": "https://x.test/?q=JANE+EXAMPLE", "prompt": "read"})
        self.assertDenied("WebFetch", {"url": "https://x.test/?p=%2B00%20000%20000%20000", "prompt": "read"})

    def test_accents_and_whole_words(self):
        self.assertDenied("WebSearch", {"query": "jose exemplo address"})
        self.assertDenied("WebSearch", {"query": "jane-example"})
        self.assertAllowed("WebSearch", {"query": "Janet Examples"})

    def test_sharp_s_counts_as_ss(self):
        self.assertDenied("WebSearch", {"query": "Karl-Example-Strasse 9"})
        self.assertDenied("WebSearch", {"query": "anna weiß"})

    def test_iota_subscript_counts_as_accent(self):
        self.assertDenied("WebSearch", {"query": "Ηρωδης"})

    def test_no_match_glued_from_raw_and_decoded_text(self):
        self.assertAllowed("WebSearch", {"query": "Example Jane"})
        self.assertAllowed("WebSearch", {"query": "1234 xx00test0000"})

    def test_value_split_over_adjacent_fields(self):
        self.assertDenied("mcp__crm__add", {"first_name": "Jane", "last_name": "Example"})

    def test_browser_tools(self):
        self.assertDenied("mcp__plugin_shared-chrome-mcp_browser__browser_type", {"ref": "e1", "text": "Jane Example"})
        self.assertDenied(B + "fill_form", {"fields": [{"name": "Name", "ref": "e2", "value": "Jane Example"}]})
        self.assertDenied(B + "navigate", {"url": "https://x.test/?name=jane-example"})
        self.assertDenied(B + "tabs", {"action": "new", "url": "https://x.test/?n=Jane%20Example"})
        self.assertAllowed(B + "tabs", {"action": "list"})
        self.assertAllowed(B + "click", {"element": "Jane Example", "ref": "e3"})
        self.assertAllowed(B + "find", {"text": "Jane Example"})

    def test_other_mcp_tool_and_local_tools(self):
        self.assertDenied("mcp__mail__send", {"to": "a@x.test", "body": "Regards, Jane Example"})
        self.assertAllowed("Write", {"file_path": "/tmp/x.md", "content": "Jane Example +00 000 000 000"})
        self.assertAllowed("Edit", {"file_path": "/tmp/x.md", "old_string": "a", "new_string": "Jane Example"})

    def test_bash_without_network_client(self):
        self.assertAllowed("Bash", {"command": 'grep -rn "Jane Example" .'})
        self.assertAllowed("Bash", {"command": "cat > notes.md <<'EOF'\ngh and curl https://x.test for Jane Example\n"
                                               "EOF\ngit add notes.md"})
        self.assertAllowed("Bash", {"command": "echo 'curl https://x.test -d Jane Example' >> notes.md"})

    def test_bash_client_in_shell_control_flow(self):
        for cmd in ("if curl -d 'Jane Example' https://x.test; then :; fi",
                    "for n in 1 2; do curl -d 'Jane Example' https://x.test; done",
                    "while sleep 1; do wget https://x.test/?n=jane-example; done",
                    "! curl -d 'Jane Example' https://x.test",
                    "timeout 10s curl -d 'Jane Example' https://x.test",
                    "r=$(curl -d 'Jane Example' https://x.test)",
                    "# Don't log this\ncurl --data 'name=Jane Example' https://x.test"):
            self.assertDenied("Bash", {"command": cmd})
        self.assertAllowed("Bash", {"command": "if grep -q x f; then echo 'Jane Example'; fi"})
        self.assertAllowed("Bash", {"command": "open 'tmp/Jane Example CV.pdf'"})

    def test_bash_heredoc_piped_into_curl(self):
        self.assertDenied("Bash", {"command": "cat <<'EOF' | curl -d @- https://x.test\nJane Example\nEOF"})

    def test_call_without_listed_value(self):
        self.assertAllowed("WebSearch", {"query": "weather tomorrow"})
        self.assertAllowed("Bash", {"command": "curl https://x.test/?n=1234"})

    def test_comment_blank_and_valueless_lines_ignored(self):
        self.assertAllowed("WebSearch", {"query": "Secret Word"})
        self.assertAllowed("WebSearch", {"query": ""})
        self.assertAllowed("WebSearch", {"query": "a rule with no value"})

    def test_malformed_stdin_fails_open_silently(self):
        for stdin in ("", "not json", "[]", '{"tool_name": "Bash", "tool_input": "x"}', "null"):
            self.assertEqual(self.run_hook(stdin), (0, "", ""), stdin)


if __name__ == "__main__":
    unittest.main()

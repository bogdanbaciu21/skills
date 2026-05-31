import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "chat_analysis.py"
spec = importlib.util.spec_from_file_location("chat_analysis", SCRIPT)
chat_analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chat_analysis)


class RedactionTests(unittest.TestCase):
    def test_redacts_common_secret_and_pii_patterns(self):
        text = (
            "token sk-ant-abcdefghijklmnopqrstuvwxyz "
            "openai sk-abcdefghijklmnopqrstuvwxyz "
            "email person@example.com "
            "path /Users/danb/Desktop/client"
        )

        redacted = chat_analysis.redact(text)

        self.assertIn("[REDACTED_ANTHROPIC_KEY]", redacted)
        self.assertIn("[REDACTED_API_KEY]", redacted)
        self.assertIn("[REDACTED_EMAIL]", redacted)
        self.assertIn("/Users/[REDACTED]", redacted)
        self.assertNotIn("person@example.com", redacted)


class SchemaTests(unittest.TestCase):
    def test_label_schema_contains_aggregation_fields(self):
        schema = chat_analysis.LABEL_SCHEMA

        for field in (
            "taskSummary",
            "outcome",
            "reworkCycles",
            "rootCauseArchetype",
            "verificationLevel",
            "codebbaseAwareness",
        ):
            self.assertIn(field, schema)


class ParserTests(unittest.TestCase):
    def test_parses_codex_response_item_messages(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "codex.jsonl"
            rows = [
                {
                    "timestamp": "2026-05-31T00:00:00Z",
                    "type": "session_meta",
                    "payload": {"id": "abc", "cwd": "/tmp/project"},
                },
                {
                    "timestamp": "2026-05-31T00:00:01Z",
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": "wrong, rerun the test"}],
                    },
                },
                {
                    "timestamp": "2026-05-31T00:00:02Z",
                    "type": "response_item",
                    "payload": {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": "Running it now."}],
                    },
                },
            ]
            path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

            session = chat_analysis.parse_session(path, "codex")

            self.assertEqual("codex", session["source"])
            self.assertEqual("abc", session["session_id"])
            self.assertEqual("/tmp/project", session["cwd"])
            self.assertEqual(1, len(session["user_turns"]))
            self.assertTrue(chat_analysis.has_friction(session))


if __name__ == "__main__":
    unittest.main()

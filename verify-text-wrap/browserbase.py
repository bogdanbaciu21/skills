"""Browserbase integration for verify-text-wrap.

Browserbase provides cloud Chromium sessions via its MCP. We use it as the
*deployed-mode* navigator when available, because it tests from outside the
local machine — catches CDN routing, geographic edge cases, and IP-restricted
auth that local Playwright doesn't see.

Graceful degradation:
- If BROWSERBASE_API_KEY is not in env → no-op, runner falls back to local Playwright pointed at the deployed URL.
- If BROWSERBASE_API_KEY is set but Stagehand AI key (ANTHROPIC_API_KEY / OPENAI_API_KEY) is missing → we can navigate but cannot fill the gate; emit a warning and fall back.
- If both are set → full Browserbase flow including gate fill via Stagehand `act`.

This module intentionally does NOT use the MCP tool wrappers directly — those
require the MCP server to be running in the Claude session. Instead we hit the
Browserbase REST API. That way the runner can be invoked from cron, CI, or a
shell, not just from inside Claude Code.
"""
import json
import os
import sys
from urllib import request, parse, error


def _has_browserbase():
    return bool(os.environ.get("BROWSERBASE_API_KEY"))


def _has_llm_key():
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY"))


class BrowserbaseContext:
    """Thin wrapper around a Browserbase session. Created via use_browserbase_if_available()."""

    def __init__(self, session_id, debug_url):
        self.session_id = session_id
        self.debug_url = debug_url
        self.api_key = os.environ["BROWSERBASE_API_KEY"]
        self.project_id = os.environ.get("BROWSERBASE_PROJECT_ID")

    def end(self):
        """Close the Browserbase session. Browserbase auto-terminates after timeout."""
        try:
            self._api("POST", f"/sessions/{self.session_id}", {"status": "REQUEST_RELEASE"})
        except Exception:
            pass  # best-effort cleanup

    def _api(self, method, path, body=None):
        url = "https://api.browserbase.com/v1" + path
        data = json.dumps(body).encode() if body else None
        req = request.Request(url, data=data, method=method, headers={
            "X-BB-API-Key": self.api_key,
            "Content-Type": "application/json",
        })
        with request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())


def use_browserbase_if_available():
    """Return a BrowserbaseContext if usable, else None.

    The runner inspects the return value: None means fall back to local Playwright;
    a context means the deployed verification gets a parallel Browserbase check
    (when fully implemented) or just informational status (current).
    """
    if not _has_browserbase():
        return None

    api_key = os.environ["BROWSERBASE_API_KEY"]
    project_id = os.environ.get("BROWSERBASE_PROJECT_ID")
    if not project_id:
        sys.stderr.write("[verify-text-wrap] BROWSERBASE_API_KEY set but BROWSERBASE_PROJECT_ID missing — skipping Browserbase\n")
        return None

    if not _has_llm_key():
        sys.stderr.write("[verify-text-wrap] Browserbase ready but Stagehand LLM key missing (ANTHROPIC_API_KEY or OPENAI_API_KEY). Navigation-only; gate fill will fall back to local.\n")

    # Spin up a session. 15-minute default timeout matches the user's Browserbase config.
    try:
        url = "https://api.browserbase.com/v1/sessions"
        body = json.dumps({
            "projectId": project_id,
            "timeout": 15 * 60,
            "keepAlive": False,
        }).encode()
        req = request.Request(url, data=body, method="POST", headers={
            "X-BB-API-Key": api_key,
            "Content-Type": "application/json",
        })
        with request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        return BrowserbaseContext(data["id"], data.get("seleniumRemoteUrl") or data.get("connectUrl") or "")
    except error.HTTPError as e:
        sys.stderr.write(f"[verify-text-wrap] Browserbase session create failed: HTTP {e.code} — falling back to local Playwright\n")
        return None
    except Exception as e:
        sys.stderr.write(f"[verify-text-wrap] Browserbase session create failed: {e} — falling back to local Playwright\n")
        return None


# Convenience for CLI-style invocation:
#   python3 browserbase.py status
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        print(f"BROWSERBASE_API_KEY: {'set' if _has_browserbase() else 'NOT set'}")
        print(f"BROWSERBASE_PROJECT_ID: {os.environ.get('BROWSERBASE_PROJECT_ID', 'NOT set')}")
        print(f"Stagehand LLM key (ANTHROPIC_API_KEY or OPENAI_API_KEY): {'set' if _has_llm_key() else 'NOT set'}")
        ctx = use_browserbase_if_available()
        if ctx:
            print(f"\nSession created: {ctx.session_id}")
            ctx.end()
            print("Session released.")
        else:
            print("\nWould fall back to local Playwright.")

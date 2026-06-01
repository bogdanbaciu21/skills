#!/usr/bin/env python3
"""Report which deep-research provider API keys are available locally."""

import json
import os


PROVIDERS = {
    "claude_managed_agent": "ANTHROPIC_API_KEY",
    "gemini_deep_research": "GEMINI_API_KEY",
    "parallel_ai": "PARALLEL_API_KEY",
}


def availability(environ=os.environ):
    return {
        provider: {
            "env_var": env_var,
            "available": bool(environ.get(env_var)),
        }
        for provider, env_var in PROVIDERS.items()
    }


def main():
    print(json.dumps(availability(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

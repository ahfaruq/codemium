#!/usr/bin/env python3
"""Verify Codemium's OpenAI Codex plugin lifecycle contract."""
from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "codemium"
MANIFEST = PLUGIN / ".codex-plugin" / "plugin.json"
HOOKS = PLUGIN / "hooks" / "hooks.json"
HOOK_SCRIPT = PLUGIN / "hooks" / "project_brain_gate.py"
HOOK_TEST = PLUGIN / "tests" / "test_codex_persistence_hook.py"


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("name") != "codemium" or manifest.get("version") != version:
        fail("Codex plugin manifest/version mismatch")
    if manifest.get("hooks") != "./hooks/hooks.json":
        fail("Codex manifest must explicitly bundle ./hooks/hooks.json")

    hooks = json.loads(HOOKS.read_text(encoding="utf-8"))
    configured = hooks.get("hooks", {})
    for event in ("UserPromptSubmit", "Stop"):
        entries = configured.get(event)
        if not isinstance(entries, list) or not entries:
            fail(f"missing Codex lifecycle hook: {event}")
        handlers = entries[0].get("hooks", [])
        if not handlers or handlers[0].get("type") != "command":
            fail(f"{event} must use a command hook")
        if "commandWindows" not in handlers[0]:
            fail(f"{event} must define commandWindows")

    for path in (HOOK_SCRIPT, HOOK_TEST):
        if not path.exists():
            fail(f"missing {path.relative_to(ROOT)}")
        py_compile.compile(str(path), doraise=True)

    script = HOOK_SCRIPT.read_text(encoding="utf-8")
    for phrase in (
        "UserPromptSubmit",
        "Stop",
        "persistence-gates",
        "enforcement_failed",
        "finalize",
        "source",
    ):
        if phrase not in script:
            fail(f"hook contract missing: {phrase}")

    result = subprocess.run(
        [sys.executable, str(HOOK_TEST)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        fail("Codex persistence hook fixture failed")

    print(json.dumps({
        "status": "pass",
        "version": version,
        "scope": "codex-plugin-lifecycle",
        "checked": [
            "plugin-bundled hooks",
            "UserPromptSubmit activation",
            "Stop persistence enforcement",
            "captured/reused/none states",
            "workspace-write constraint",
            "retry loop guard",
        ],
    }, indent=2))
    print("PASS: Codex plugin lifecycle")


if __name__ == "__main__":
    main()

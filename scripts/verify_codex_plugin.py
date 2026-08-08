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
DISPATCH_SCRIPT = PLUGIN / "hooks" / "project_brain_dispatch.py"
HOOK_TEST = PLUGIN / "tests" / "test_codex_persistence_hook.py"
FAST_PATH_TEST = PLUGIN / "tests" / "test_codex_project_brain_fast_path.py"


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
        command_text = str(handlers[0].get("command", "")) + str(handlers[0].get("commandWindows", ""))
        if "project_brain_dispatch.py" not in command_text:
            fail(f"{event} must route through project_brain_dispatch.py")

    for path in (HOOK_SCRIPT, DISPATCH_SCRIPT, HOOK_TEST, FAST_PATH_TEST):
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

    dispatch = DISPATCH_SCRIPT.read_text(encoding="utf-8")
    for phrase in (
        "PROJECT BRAIN FAST PATH",
        "rank_entries",
        "Do not run task_compiler",
        "fast_path",
        "project_brain_gate",
    ):
        if phrase not in dispatch:
            fail(f"fast-path contract missing: {phrase}")

    for fixture, label in (
        (HOOK_TEST, "Codex persistence hook fixture"),
        (FAST_PATH_TEST, "Codex Project Brain fast-path fixture"),
    ):
        result = subprocess.run(
            [sys.executable, str(fixture)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            sys.stdout.write(result.stdout)
            sys.stderr.write(result.stderr)
            fail(f"{label} failed")

    print(json.dumps({
        "status": "pass",
        "version": version,
        "scope": "codex-plugin-lifecycle",
        "checked": [
            "plugin-bundled hooks",
            "UserPromptSubmit activation",
            "Stop persistence enforcement",
            "captured/reused/none states",
            "Project Brain retrieval fast path",
            "fast-path pre-satisfied persistence",
            "workspace-write constraint",
            "retry loop guard",
        ],
    }, indent=2))
    print("PASS: Codex plugin lifecycle")


if __name__ == "__main__":
    main()

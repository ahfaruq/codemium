#!/usr/bin/env python3
"""Fast, host-agnostic Codemium core verification.

This check intentionally does not validate host packaging/installers. It answers only:
"Is the shared Codemium engineering core structurally healthy?"
"""
from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "plugins/codemium/engine"
TESTS = ROOT / "plugins/codemium/tests"

REQUIRED_ENGINE = [
    "common.py",
    "project_brain.py",
    "repo_graph.py",
    "working_set.py",
    "impact.py",
    "scope_guard.py",
    "test_map.py",
    "cache.py",
    "telemetry.py",
    "health.py",
    "reasoning_profile.py",
    "task_compiler.py",
]


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> None:
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not version:
        fail("VERSION is empty")

    for name in REQUIRED_ENGINE:
        path = ENGINE / name
        if not path.exists():
            fail(f"missing engine/{name}")
        py_compile.compile(str(path), doraise=True)

    fixture = TESTS / "test_core_fixture.py"
    if not fixture.exists():
        fail("missing host-agnostic core fixture")
    py_compile.compile(str(fixture), doraise=True)

    # Project Brain schema is a core contract, not a host-adapter contract.
    brain = (ENGINE / "project_brain.py").read_text(encoding="utf-8")
    for phrase in [
        "GENERIC_REASONING",
        "TRANSIENT_IGNORE",
        "tasks/active.json",
        "host_profiles",
    ]:
        if phrase not in brain:
            fail(f"Project Brain contract missing: {phrase}")

    compiler = (ENGINE / "task_compiler.py").read_text(encoding="utf-8")
    for depth in ["FAST", "NORMAL", "DEEP", "CRITICAL"]:
        if depth not in compiler:
            fail(f"task compiler depth missing: {depth}")

    result = subprocess.run(
        [sys.executable, str(fixture)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        fail("core fixture failed")

    print(json.dumps({
        "status": "pass",
        "version": version,
        "scope": "codemium-core",
        "checked": [
            "engine syntax",
            "Project Brain invariants",
            "generic task/depth contract",
            "host-agnostic core fixture",
        ],
    }, indent=2))
    print("PASS: Codemium core integrity")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fast, host-agnostic Codemium core verification."""
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
    "common.py", "project_brain.py", "parsers.py", "repo_graph.py", "graph_query.py", "working_set.py", "impact.py",
    "scope_guard.py", "slop_guard.py", "execution_guard.py", "test_map.py", "cache.py", "telemetry.py", "health.py", "reasoning_profile.py", "task_compiler.py",
]


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def run_fixture(path: Path, label: str) -> None:
    if not path.exists():
        fail(f"missing {label} fixture")
    py_compile.compile(str(path), doraise=True)
    result = subprocess.run([sys.executable, str(path)], cwd=ROOT, text=True, capture_output=True)
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        fail(f"{label} fixture failed")


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
    slop_fixture = TESTS / "test_slop_guard.py"
    execution_fixture = TESTS / "test_execution_guard.py"
    calibration = ROOT / "benchmarks/calibrate_v09_blocking.py"

    brain = (ENGINE / "project_brain.py").read_text(encoding="utf-8")
    for phrase in ["GENERIC_REASONING", "TRANSIENT_IGNORE", "tasks/active.json", "host_profiles", "def capture(", "find_active_duplicate", "init(root, emit=False)", "def entry_freshness(", "NEEDS_REVALIDATION", "def revalidate("]:
        if phrase not in brain:
            fail(f"Project Brain contract missing: {phrase}")
    parsers = (ENGINE / "parsers.py").read_text(encoding="utf-8")
    for phrase in ["class ParserAdapter", "class PythonAstParser", "class TreeSitterJSTSParser", "class RegexFallbackParser", "fallback-regex", "PARSER_VERSION = \"3\""]:
        if phrase not in parsers:
            fail(f"parser abstraction contract missing: {phrase}")
    graph = (ENGINE / "repo_graph.py").read_text(encoding="utf-8")
    for phrase in ["GRAPH_SCHEMA_VERSION = 3", "DIRECT", "RESOLVED", "HEURISTIC", "DEPENDS_ON", "TESTS", "IMPORTS_SYMBOL", "cross_language", "bindings_by_path"]:
        if phrase not in graph:
            fail(f"Polyglot graph contract missing: {phrase}")
    query = (ENGINE / "graph_query.py").read_text(encoding="utf-8")
    for phrase in ["def shortest_path(", "def bounded_expand(", "def dependents_for_nodes(", "def dependents_for_files(", "callers", "tests-for", "IMPORTS_SYMBOL"]:
        if phrase not in query:
            fail(f"graph query contract missing: {phrase}")
    impact = (ENGINE / "impact.py").read_text(encoding="utf-8")
    for phrase in ["changed_line_ranges", "changed_symbol_seeds", "symbol-structural", "cross_language_dependents", "test_plan"]:
        if phrase not in impact:
            fail(f"impact intelligence contract missing: {phrase}")
    tests = (ENGINE / "test_map.py").read_text(encoding="utf-8")
    for phrase in ["schema_version\": 3", "prioritized", "confidence", "cross_language_relationships"]:
        if phrase not in tests:
            fail(f"test intelligence contract missing: {phrase}")
    compiler = (ENGINE / "task_compiler.py").read_text(encoding="utf-8")
    for depth in ["FAST", "NORMAL", "DEEP", "CRITICAL"]:
        if depth not in compiler:
            fail(f"task compiler depth missing: {depth}")
    if "init_project_brain(root, emit=False)" not in compiler:
        fail("normal task compilation must auto-initialize Project Brain")
    if "apply_structural_escalation" not in compiler:
        fail("task compiler must consume structural risk")
    for phrase in ["execution_policy", "evidence_delta_gate", "ui_stabilization_required", "repeated investigation either produces material evidence or stops"]:
        if phrase not in compiler:
            fail(f"v0.10 task execution contract missing: {phrase}")

    slop = (ENGINE / "slop_guard.py").read_text(encoding="utf-8")
    for phrase in [
        "SCHEMA_VERSION = 1", "ADJUDICATION_SCHEMA_VERSION = 1", "PROVENANCE_VALUES", "UNJUSTIFIED_SCOPE",
        "DUPLICATE_IMPLEMENTATION", "UNJUSTIFIED_DEPENDENCY", "UNJUSTIFIED_PUBLIC_API", "cleanup_set",
        "protected_complexity", "underengineering_gate", "scoreable", "risk_score", "--adjudications", "--strict",
    ]:
        if phrase not in slop:
            fail(f"Anti-Slop contract missing: {phrase}")

    execution = (ENGINE / "execution_guard.py").read_text(encoding="utf-8")
    for phrase in [
        "Every action must buy information or produce the solution.",
        "unresolved_contradictions", "evidence_fingerprint", "REPEAT_SENSITIVE_ACTIONS",
        "NEW_EVIDENCE", "NECESSARY_MUTATION", "REQUIRED_VERIFICATION", "NO_GAIN",
        "unstabilized negative screenshot", "rejected_evidence_fingerprint", "--override-reason",
    ]:
        if phrase not in execution:
            fail(f"Execution Intelligence contract missing: {phrase}")

    codex_skill = (ROOT / "plugins/codemium/skills/codemium/SKILL.md").read_text(encoding="utf-8")
    for phrase in [
        "Project Brain persistence contract", "Do **not** require the user to run `$cm-init` first", "Persistence gate",
        "captured", "skipped by user constraint", "Slop Guard", "Underengineering Counter-Gate",
        "Execution Intelligence", "Evidence Delta Gate", "Every action must buy information or produce the solution.",
    ]:
        if phrase not in codex_skill:
            fail(f"Codex behavior missing: {phrase}")

    portable_skill = (ROOT / "skills/cm/SKILL.md").read_text(encoding="utf-8")
    for phrase in [
        "minimum justified engineering", "Slop Guard", "Underengineering Counter-Gate",
        "Execution Intelligence", "Evidence Delta Gate", "Every action must buy information or produce the solution.",
    ]:
        if phrase not in portable_skill:
            fail(f"portable Codemium behavior missing: {phrase}")

    execution_policy = (ROOT / "plugins/codemium/skills/codemium/references/execution-policy.md").read_text(encoding="utf-8")
    for phrase in ["Evidence before mutation", "Contradiction Gate", "UI runtime truth order", "Hypothesis Ledger", "Evidence Delta Gate", "No arbitrary token/action budget"]:
        if phrase not in execution_policy:
            fail(f"Execution policy missing: {phrase}")

    run_fixture(fixture, "host-agnostic core")
    run_fixture(slop_fixture, "v0.9 Slop Guard")
    run_fixture(execution_fixture, "v0.10 Execution Intelligence")
    run_fixture(calibration, "v0.9 blocking calibration")

    print(json.dumps({
        "status": "pass", "version": version, "scope": "codemium-core",
        "checked": [
            "engine syntax",
            "Project Brain persistence/evidence/freshness",
            "parser abstraction + deterministic fallback",
            "Structural Graph v3 + provenance",
            "incremental graph refresh",
            "symbol-aware impact/test mapping",
            "automatic Project Brain initialization/capture",
            "generic task/depth + execution-policy contract",
            "task-aware Slop Guard + coverage honesty",
            "finding provenance + evidence-backed adjudication",
            "CLEANUP surface classification",
            "Underengineering Counter-Gate",
            "Execution Intelligence observation/contradiction/evidence-delta gates",
            "UI stabilization + rejected-hypothesis protection",
            "execution waste telemetry",
            "blocking-rule calibration corpus",
            "host-agnostic core + Anti-Slop + Execution Intelligence fixtures",
        ],
    }, indent=2))
    print("PASS: Codemium core integrity")


if __name__ == "__main__":
    main()

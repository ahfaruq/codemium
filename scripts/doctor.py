#!/usr/bin/env python3
"""Validate Codemium repository/adapters and report locally available hosts."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

HOST_BINARIES = {"codex": ["codex"], "claude-code": ["claude"], "gemini-cli": ["gemini"], "cursor": ["agent", "cursor-agent"], "opencode": ["opencode"]}


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition: errors.append(message)


def load_json(path: Path, errors: list[str]) -> dict:
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc: errors.append(f"invalid JSON {path}: {exc}"); return {}


def detect_binary(candidates: list[str]) -> dict:
    for binary in candidates:
        resolved = shutil.which(binary)
        if resolved: return {"available": True, "command": binary, "path": resolved}
    return {"available": False, "command": None, "path": None, "candidates": candidates}


def parser_runtime(root: Path) -> dict:
    engine = root / "plugins/codemium/engine"
    sys.path.insert(0, str(engine))
    try:
        from parsers import parser_runtime as runtime
        return runtime()
    except Exception as exc:
        return {"parser_version": None, "tree_sitter_available": False, "deep_languages": ["python"], "error": str(exc)}
    finally:
        if sys.path and sys.path[0] == str(engine): sys.path.pop(0)


def runtime_structural_report(root: Path) -> dict:
    state = root / ".codemium"
    if not state.exists(): return {"state_present": False, "status": "not_initialized", "parser_runtime": parser_runtime(root)}
    health = root / "plugins/codemium/engine/health.py"
    try:
        p = subprocess.run([sys.executable, str(health), "--root", str(root)], capture_output=True, text=True, timeout=30)
        if p.returncode == 0:
            data = json.loads(p.stdout)
            return {"state_present": True, "status": "healthy" if data.get("repository_graph", {}).get("present") else "degraded", "repository_graph": data.get("repository_graph", {}), "project_brain_freshness": data.get("project_brain_freshness", {}), "parser_runtime": data.get("repository_graph", {}).get("parser_runtime", parser_runtime(root))}
        return {"state_present": True, "status": "health_failed", "error": p.stderr.strip(), "parser_runtime": parser_runtime(root)}
    except Exception as exc:
        return {"state_present": True, "status": "health_failed", "error": str(exc), "parser_runtime": parser_runtime(root)}


def validate(root: Path) -> tuple[list[str], dict]:
    errors: list[str] = []
    version_path = root / "VERSION"; check(version_path.exists(), "VERSION missing", errors); version = version_path.read_text(encoding="utf-8").strip() if version_path.exists() else "unknown"
    codex_market = load_json(root / ".agents/plugins/marketplace.json", errors); codex_manifest = load_json(root / "plugins/codemium/.codex-plugin/plugin.json", errors)
    check(codex_manifest.get("version") == version, "Codex manifest version mismatch", errors); check(codex_manifest.get("name") == "codemium", "Codex plugin name mismatch", errors); check(codex_manifest.get("interface", {}).get("displayName") == "Codemium", "Codex displayName must be Codemium", errors); check("@Codemium" in codex_manifest.get("interface", {}).get("longDescription", ""), "Codex manifest must document @Codemium primary invocation", errors); check(codex_manifest.get("hooks") == "./hooks/hooks.json", "Codex manifest must bundle lifecycle hooks", errors)
    codex_hooks_path = root / "plugins/codemium/hooks/hooks.json"; check(codex_hooks_path.exists(), "Codex hooks/hooks.json missing", errors)
    check((root / "plugins/codemium/hooks/project_brain_gate.py").exists(), "Codex Project Brain gate hook missing", errors); check((root / "scripts/verify_codex_plugin.py").exists(), "Codex lifecycle verifier missing", errors)
    codex_skill = root / "plugins/codemium/skills/codemium/SKILL.md"; check(codex_skill.exists(), "Codex cm skill missing", errors)
    if codex_skill.exists():
        text = codex_skill.read_text(encoding="utf-8"); check("# Codemium" in text, "Codex skill heading missing", errors); check("@Codemium" in text, "Codex skill must document @Codemium primary plugin invocation", errors); check("$cm" in text, "Codex skill must preserve direct $cm compatibility invocation", errors)
    if codex_market: check(any(p.get("name") == "codemium" for p in codex_market.get("plugins", [])), "Codex marketplace entry missing", errors)

    shared_skill = root / "skills/cm/SKILL.md"; check(shared_skill.exists(), "shared cm Agent Skill missing", errors)
    claude_market = load_json(root / ".claude-plugin/marketplace.json", errors); claude_manifest = load_json(root / ".claude-plugin/plugin.json", errors)
    check(claude_manifest.get("version") == version, "Claude plugin version mismatch", errors); claude_entries = [p for p in claude_market.get("plugins", []) if p.get("name") == "codemium"]; check(len(claude_entries) == 1, "Claude marketplace must contain one codemium entry", errors)
    if claude_entries: check(claude_entries[0].get("source") == "./", "Claude plugin source must be repository root", errors); check(claude_entries[0].get("version") == version, "Claude marketplace version mismatch", errors)
    gemini = load_json(root / "gemini-extension.json", errors); check(gemini.get("version") == version, "Gemini extension version mismatch", errors); check(gemini.get("contextFileName") == "GEMINI.md", "Gemini contextFileName must be GEMINI.md", errors)
    try:
        command = tomllib.loads((root / "commands/cm.toml").read_text(encoding="utf-8")); check("{{args}}" in command.get("prompt", ""), "Gemini /cm must forward {{args}}", errors)
    except Exception as exc: errors.append(f"invalid Gemini command TOML: {exc}")

    required_engine = ["project_brain.py", "parsers.py", "repo_graph.py", "graph_query.py", "working_set.py", "impact.py", "scope_guard.py", "test_map.py", "cache.py", "telemetry.py", "health.py", "reasoning_profile.py", "task_compiler.py"]
    for name in required_engine: check((root / "plugins/codemium/engine" / name).exists(), f"engine/{name} missing", errors)
    graph_path = root / "plugins/codemium/engine/repo_graph.py"; graph_text = graph_path.read_text(encoding="utf-8") if graph_path.exists() else ""
    check("GRAPH_SCHEMA_VERSION = 3" in graph_text, "Structural Graph v3 contract missing", errors); check("IMPORTS_SYMBOL" in graph_text and "cross_language" in graph_text, "cross-language graph contract missing", errors); check("HEURISTIC" in graph_text and "RESOLVED" in graph_text and "DIRECT" in graph_text, "relationship provenance contract missing", errors)
    parser_text = (root / "plugins/codemium/engine/parsers.py").read_text(encoding="utf-8") if (root / "plugins/codemium/engine/parsers.py").exists() else ""
    check("class TreeSitterJSTSParser" in parser_text, "Tree-sitter parser adapter missing", errors); check("class RegexFallbackParser" in parser_text, "parser fallback missing", errors)
    check((root / "requirements-polyglot.txt").exists(), "requirements-polyglot.txt missing", errors); check((root / "scripts/verify_polyglot.py").exists(), "polyglot verifier missing", errors)

    detected = {host: detect_binary(candidates) for host, candidates in HOST_BINARIES.items()}
    return errors, {"version": version, "host_binaries": detected, "polyglot_runtime": parser_runtime(root), "structural_intelligence": runtime_structural_report(root)}


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1]); ap.add_argument("--require-host", choices=sorted(HOST_BINARIES)); ns = ap.parse_args(); root = ns.repo.resolve(); errors, report = validate(root)
    if ns.require_host and not report["host_binaries"][ns.require_host]["available"]: errors.append(f"required host binary not found (tried: {', '.join(HOST_BINARIES[ns.require_host])})")
    report["status"] = "pass" if not errors else "fail"; report["errors"] = errors; print(json.dumps(report, indent=2))
    if errors: raise SystemExit(1)


if __name__ == "__main__": main()

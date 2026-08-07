#!/usr/bin/env python3
"""Install/uninstall Codemium's portable Agent Skill for supported skill hosts.

Stdlib only. This installer never edits a host's global configuration file; it only
manages the Codemium-owned skill directory selected below.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

HOST_DIRS = {
    "cursor": Path(".cursor/skills/cm"),
    "opencode": Path(".config/opencode/skills/cm"),
    "agents": Path(".agents/skills/cm"),
}
PROJECT_DIRS = {
    "cursor": Path(".cursor/skills/cm"),
    "opencode": Path(".opencode/skills/cm"),
    "agents": Path(".agents/skills/cm"),
}
MARKER = ".codemium-installed.json"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def version(root: Path) -> str:
    return (root / "VERSION").read_text(encoding="utf-8").strip()


def target_for(host: str, scope: str, project: Path | None) -> Path:
    if scope == "user":
        return Path.home() / HOST_DIRS[host]
    base = (project or Path.cwd()).resolve()
    return base / PROJECT_DIRS[host]


def is_owned(target: Path) -> bool:
    marker = target / MARKER
    if not marker.exists():
        return False
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except Exception:
        return False
    return data.get("product") == "codemium"


def copy_tree(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, dirs_exist_ok=True)


def install(host: str, scope: str, project: Path | None, force: bool, dry_run: bool) -> dict:
    root = repo_root()
    target = target_for(host, scope, project)
    if target.exists() and any(target.iterdir()) and not is_owned(target) and not force:
        raise SystemExit(
            f"refusing to overwrite non-Codemium skill directory: {target}\n"
            "Use --force only after reviewing the existing directory."
        )
    plan = {
        "action": "install",
        "host": host,
        "scope": scope,
        "target": str(target),
        "version": version(root),
    }
    if dry_run:
        return {**plan, "status": "dry-run"}

    if target.exists() and force and not is_owned(target):
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    # skills/cm/SKILL.md is the single source of truth for Claude, Gemini,
    # Cursor, OpenCode, and other Agent Skills-compatible hosts.
    shutil.copy2(root / "skills/cm/SKILL.md", target / "SKILL.md")
    copy_tree(root / "plugins/codemium/engine", target / "engine")
    copy_tree(root / "plugins/codemium/skills/codemium/references", target / "references")
    shutil.copy2(root / "LICENSE", target / "LICENSE")
    (target / "VERSION").write_text(version(root) + "\n", encoding="utf-8")
    (target / MARKER).write_text(
        json.dumps(
            {
                "product": "codemium",
                "version": version(root),
                "host": host,
                "scope": scope,
                "source": "https://github.com/admahmad/codemium",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {**plan, "status": "installed"}


def uninstall(host: str, scope: str, project: Path | None, force: bool, dry_run: bool) -> dict:
    target = target_for(host, scope, project)
    plan = {"action": "uninstall", "host": host, "scope": scope, "target": str(target)}
    if not target.exists():
        return {**plan, "status": "not-installed"}
    if not is_owned(target) and not force:
        raise SystemExit(
            f"refusing to remove directory not marked as Codemium-owned: {target}\n"
            "Use --force only after reviewing the target."
        )
    if dry_run:
        return {**plan, "status": "dry-run"}
    shutil.rmtree(target)
    return {**plan, "status": "removed"}


def main() -> None:
    ap = argparse.ArgumentParser(description="Install Codemium portable Agent Skill")
    ap.add_argument("--host", required=True, choices=sorted(HOST_DIRS))
    ap.add_argument("--scope", choices=["user", "project"], default="user")
    ap.add_argument("--project", type=Path, help="Project root for --scope project (default: cwd)")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ns = ap.parse_args()
    if ns.project and ns.scope != "project":
        ap.error("--project requires --scope project")
    result = (
        uninstall(ns.host, ns.scope, ns.project, ns.force, ns.dry_run)
        if ns.uninstall
        else install(ns.host, ns.scope, ns.project, ns.force, ns.dry_run)
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

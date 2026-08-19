#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "plugins/codemium/engine"
sys.path.insert(0, str(ENGINE))

from slop_guard import Finding, verdict  # noqa: E402


def main() -> None:
    corpus_path = ROOT / "benchmarks/v09-blocking-calibration.json"
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    cases = corpus.get("cases", [])
    failures = []
    results = []
    for case in cases:
        findings = []
        for raw in case.get("findings", []):
            adjudication = None
            if raw.get("justified"):
                adjudication = {
                    "status": "accepted",
                    "decision": "JUSTIFIED",
                    "reason": "Calibration fixture provides evidence-backed justification.",
                    "evidence": [{"kind": "task", "detail": "calibration fixture"}],
                }
            findings.append(Finding(
                rule=raw["rule"],
                path=raw["path"],
                severity=raw["severity"],
                confidence=float(raw["confidence"]),
                evidence_class="DETERMINISTIC",
                autofix="REVIEW_REQUIRED",
                reason="calibration fixture",
                provenance=raw["provenance"],
                adjudication=adjudication,
            ))
        removed = [{"path": "src/safety.py", "line": 1, "text": "transaction"}] if case.get("protected_removal") else []
        protected = {
            "added": [],
            "removed": removed,
            "underengineering_gate": {
                "status": "review_required" if removed else "pass",
                "reason": "calibration protected removal" if removed else "no protected removal",
            },
        }
        actual = verdict(findings, protected)
        expected = case["expected_status"]
        results.append({"id": case["id"], "expected": expected, "actual": actual, "pass": actual == expected})
        if actual != expected:
            failures.append(case["id"])

    output = {
        "schema_version": 1,
        "status": "pass" if not failures else "fail",
        "cases": len(cases),
        "failed": failures,
        "results": results,
        "note": "Blocking calibration only; not a competitive performance or efficiency claim."
    }
    print(json.dumps(output, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

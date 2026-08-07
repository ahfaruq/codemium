---
name: cm-init
description: "Short Codemium initialization skill: create Project Brain and deterministic repository/test intelligence without narratively loading the whole codebase."
---

# $cm-init

From repository root, initialize `.codemium`, then build repository and test maps. Do not ask a frontier model to narratively read every file.

Use:

```sh
python <plugin-dir>/engine/project_brain.py init --root .
python <plugin-dir>/engine/repo_graph.py build --root .
python <plugin-dir>/engine/test_map.py build --root .
```

Inspect deterministic results, then populate only durable high-value project facts: stack/entry points, architecture boundaries, existing decisions/constraints/interfaces/patterns. Do not guess facts and do not store secrets. Normal `$cm` may perform this initialization automatically when needed.

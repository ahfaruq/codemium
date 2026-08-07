---
name: audit
description: "Codemium repository audit: deterministic hotspot discovery first, targeted AI inspection second, avoiding full-repo prompt loading."
---

# Codemium Audit

Do not load the entire repository into model context. Build/refresh repository graph, identify structural hotspots and risk candidates deterministically, rank them, inspect top candidates, then expand only where evidence warrants. Report findings; do not auto-refactor the whole repository.

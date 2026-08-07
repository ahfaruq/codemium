---
name: cm-audit
description: "Short Codemium repository-audit skill: deterministic hotspot discovery first, bounded AI inspection second, with depth based on audit risk."
---

# $cm-audit

Audit is repository-wide in discovery, not in model context. Build/refresh repository graph, identify structural hotspots and risk candidates deterministically, rank them, inspect top candidates, then expand only where evidence warrants.

Plain `$cm-audit` uses normal adaptive audit depth. `deep` and `critical` may request stronger investigation; a `fast` request must not reduce audit below the minimum useful deterministic scan. Report findings and evidence. Do not auto-refactor the whole repository.

---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261011-VISUAL-ASSETS-REAL-ART-KEYS
artifact_type: investigation
tags: [architecture, testing, documentation]
---

# Investigation: Register three optional keys, refresh snapshots

Question: what does adding `ui.panel_frame`, `fx.selection_ring`, `fx.campfire` cost the registry and the tests? Measured: registry 28,241 B / 62 keys -> 29,525 B / 65 keys, load median 0.045 s -> 0.064 s (noise), 6.4 % of `MAX_REGISTRY_BYTES`. Families `ui`/`fx` are free strings (`Family` is a pattern). Finding: `runtime_export.py:87` compares the registry file hash with the candidate's (`release.py:120`), so any registry edit makes older candidates unexportable until a new one is assembled (12 tests that export rc-0008 go red). Four registry-content pin tests need exact new values. asset-planner ruled option B: one commit per ticket, known red until rc-0009.

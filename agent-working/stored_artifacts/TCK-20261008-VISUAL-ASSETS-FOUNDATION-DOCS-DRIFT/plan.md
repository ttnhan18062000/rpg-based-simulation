---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-FOUNDATION-DOCS-DRIFT
artifact_type: plan
date: 2026-10-09
tags: [architecture, documentation]
---

# Plan

1. Fix the named drift (`drawing_tools.md:18` "designed, not built"; the foundation plan's `handoff.py`, CLI and `test_catalog_integrity` lines; the `visual_assets/README.md` skeleton rows) and the register's stale "Yes" summary rows for W02.7, W03.1 and W06.3.
2. Repair the evidence gap found in child 6: every git-ignored file under `agent-working/stored_artifacts/TCK-*VISUAL-ASSETS*/` gets a tracked `<name>.txt` twin (originals untouched), the exact list in `evidence_twins_manifest.txt`; a guard test beside `test_no_ignored_files`; the shared `.gitignore` rule is NOT changed (codebase-wide, planner decision).
3. Refresh both handoff snapshots; close the epic and its folder; `make knowledge-index-update`.

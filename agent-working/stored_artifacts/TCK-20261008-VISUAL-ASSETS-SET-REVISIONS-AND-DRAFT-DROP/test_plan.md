---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-SET-REVISIONS-AND-DRAFT-DROP
artifact_type: test_plan
date: 2026-10-09
tags: [architecture, testing]
---

# Test plan

`tests/visual_assets/store/unit/test_set_revisions.py` (26 tests): keep --revises (accept, four refusals, revoked parent, old behaviour kept), byte-identical sets without the new fields, mixed new+revision adoption (one confirmation, NEW/REVISION listing, counts, records), lineage identical to `adopt --parent`, stale parent, changed slot, one bad entry writes nothing, publish-time collision rolls back, the existing gate properties for a mixed set (not confirmed, licence, evidence, renderer, no terminal, wrong typed id), the tightened `adopt --parent` (key and detail, default spelled either way), drop (record, hash change, default detail, unknown slot, adopted set, adopted entry, reason and count, re-keep clears the record, failed write), CLI, no agent surface. `test_record_bounds` (widest set), `test_budgets_parity`. Mutants M1-M14. Scoped suites.

---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260913-PERF-M0-SOURCE-AUDIT
date: 2026-10-02
tags: [performance, architecture]
---

# Investigation: TCK-20260913-PERF-M0-SOURCE-AUDIT

The full evidence is in `source_inventory.md` (same folder). Summary of what changed the ticket's
premises:

- All 21 cited paths exist and are tracked; C-17 is resolved. The package has 11 files, not 12.
- The source proposal is tracked but sits in the registry-skipped `docs/brainstorm/` subtree
  (`tools/generate_registry.py` `_SKIP_DOC_SUBDIRS`), so it is never registered.
- Real broken citations: two stale paths in `system_design_terms_and_concepts.md`, and a roadmap
  reference to `python_code_craft_roadmap.md`, which exists only on branch `python-code-craft`.
- Three cited `docs/` outputs are planned deliverables, not broken links.
- Both P1 tracking tickets (`TCK-20260825-EPIC-PERFORMANCE-EVOLUTION`,
  `TCK-20260825-EPIC-SUBPHASE-DOMAIN-CONTRACTS`) do not exist.
- Semantic search mostly returns `working_log.csv` rows for closed work; open tickets were found by
  the names the ticket supplied, so an unnamed open ticket could be missed.

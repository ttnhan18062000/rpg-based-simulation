---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-TEST-DOMAIN-LEVEL-MARKERS-ADVISORY-CHECK
artifact_type: plan
tags: [testing]
---

# Plan

Scope and approach: see the ticket's Scope and Implementation Notes.

`domain(name)`/`level(name)` registered in pyproject. `marker_check` reads the vocabulary from the doc, flags unknown-domain, unknown-level, domain-mismatch, level-placement-mismatch and unmarked-core-rpg (from git diff or --files); always exits 0, no CI wiring. `core_rpg_report` now has per-domain import roots (`DOMAIN_IMPORT_PREFIXES`; the gameplay tuple is derived from it) and lists declared markers per file in the classification layer. No existing test was marked.

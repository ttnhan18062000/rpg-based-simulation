---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-KEY-USAGE-REPORT
phase: done
date: 2026-10-08
tags: [architecture, testing]
---

# TCK-20261008-VISUAL-ASSETS-KEY-USAGE-REPORT

## Title
A key-usage report: which visual keys the code references against the registry and manifest (report only)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Child 6 of `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING`. External research (Unreal Reference Viewer, Addressables Analyze, Knip): a reference graph finds unknown keys, unused adopted keys and keys that only resolve through a fallback. Report-only now; a CI gate belongs to activation.

## Scope
- A command that scans frontend (and any backend) sources for visual-key references and compares them with the registry and the latest runtime manifest: unknown keys, registered-but-unreferenced, adopted-but-unreleased, fallback-only. Deterministic output; tests with planted cases; documented in store_contract.md.

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art. Failing CI on findings.

## Acceptance Criteria
- [x] Report command tested; first run recorded in the ticket.

## Related Tickets


## Related Docs


## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-KEY-USAGE-REPORT/ (plan, investigation with the first run, first_run_2026-10-09.json.txt, test_plan, mutant_proof)

## Related Code Areas


## Assumptions / Open Questions
- A literal scan cannot see keys built with template literals (iconScene.ts builds icon keys that way) nor tell a comment from code; both stated in the docs and the report lists the dynamic references.

## Implementation Notes
- `visual_assets/review/key_usage.py` and `python -m visual_assets.review key-usage` (report only, exit 0, deterministic JSON). `catalog` added to the review layer's allowed store layers (the read-only registry loader). Documented in store_contract.md.
- **First run (2026-10-09):** 62 registry keys; rc-0007 holds 26 keys; unknown 0; fallback_only 0; adopted_unreleased 36 (all adopted icons); unreferenced 22 (icon keys only mentioned through the dynamic `icon.${...}` builders in iconScene.ts, so a literal scan reports them; not unused); 4 dynamic references; every referenced key (40) is referenced only from the isolated harness, none from application code.

## Test Summary
- 8 tests; mutants M1-M8 (M1 survived the first test version and the planted case was strengthened; M4 was equivalent dead code and was removed). Scoped suites: see the commit report.

## Files Changed
- visual_assets/review/{key_usage,__main__}.py, tests/visual_assets/{test_key_usage,test_boundaries}.py, docs/assets/store_contract.md, ticket and artifacts.

## Completion Summary
A report-only command compares the key references in the code with the registry, the adopted sources and the latest release candidate; the first run shows no unknown keys, no application code referencing a key, and 36 adopted icons that no candidate covers yet.

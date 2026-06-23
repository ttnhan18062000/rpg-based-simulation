---
status: open
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260623-FIX-DOCS-INTEGRITY
phase: open
date: 2026-06-23
tags: [test-repair, docs, integrity, architecture, parity, P2]
---

# TCK-20260623-FIX-DOCS-INTEGRITY

## Title
Fix docs/integrity/architecture test failures (~15 failures)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Several test suites verify structural properties of the repository (doc existence, link integrity, parity oracle artifacts, import boundaries). These are currently failing:

**docs/ failures (5):**
- `test_contributor_guardrails.py::test_extension_templates_present` — extension template files missing
- `test_doc_integrity.py::test_manifest_file_existence` — manifest file missing
- `test_doc_integrity.py::test_document_structural_compliance` — some doc fails structural check
- `test_doc_integrity.py::test_release_target_binding` — `FileNotFoundError` (missing file)
- `test_doc_integrity.py::test_link_integrity` — `FileNotFoundError` (broken link in a doc)

**integrity/ failures (4 + 1 error):**
- `test_doc_guards.py::test_mandatory_doc_existence` — a mandatory doc file is missing
- `test_logic_guards.py::test_autonomous_loop_determinism_drift_guard` — determinism drift guard
- `test_logic_guards.py::test_resolution_phase_ordering_integrity` — phase ordering integrity
- `test_logic_guards.py::test_subsystem_order_documentation` — subsystem order doc missing/stale
- `test_parity_guards.py::test_oracle_artifact_existence` — parity oracle artifact missing
- ERROR `test_parity_guards.py::test_critical_parity_scenarios_presence`

**architecture/ failures (2):**
- `test_no_new_hardcoded_gameplay_truth.py::test_known_baseline_stale_guard` — baseline stale
- `test_phase18_import_boundaries.py::test_entity_models_do_not_import_domain_services` — import boundary violation

## Scope
- Read each failing test with `--tb=long` to get the exact file paths that are missing or failing
- Create/fix missing files (templates, manifests, oracle artifacts)
- Fix broken doc links
- Fix import boundary violation in entity models
- Update stale baseline snapshot if the architecture change was intentional

## Out of Scope
- Logic changes to the docs/integrity checkers themselves
- New doc authoring beyond what the tests require
- Architecture changes to remove the import boundary violation (prefer injection)

## Acceptance Criteria
- `tests/docs/` — all 5 failures resolved (may require creating missing files or fixing broken links)
- `tests/integrity/` — all 4 failures + 1 error resolved
- `tests/architecture/test_no_new_hardcoded_gameplay_truth.py` passes
- `tests/architecture/test_phase18_import_boundaries.py::test_entity_models_do_not_import_domain_services` passes

## Related Tickets
- D10 audit (structural test gaps)
- D17 (documentation currency — stale docs causing doc structure tests to fail)
- TCK-20260623-FIX-KERNEL-PHASES (phase ordering integrity may be linked)

## Related Docs
- `docs/testing/v2_test_taxonomy.md`
- `docs/compliance/checklist.md`
- `docs/parity_ledger/` (oracle artifact)

## Related Code Areas
- `tests/docs/`
- `tests/integrity/`
- `tests/architecture/`
- `src/entities/` (import boundary violation)

## Assumptions / Open Questions
- Which entity model imports a domain service? (`test_phase18_import_boundaries` will say which file)
- What is the "parity oracle artifact" that is missing?
- What is the "manifest file" that `test_manifest_file_existence` requires?

## Implementation Notes
Run each failing test with `--tb=long` first to get exact filenames before creating anything. Do not create placeholder files — create the actual required content.

Order: start with the most specific failures (file existence) before the behavioral ones (import boundaries, phase ordering).

## Test Summary
Run: `pytest tests/docs/ tests/integrity/ tests/architecture/ --tb=short`
Expected: all pass.

## Files Changed
_To be filled during implementation._

## Completion Summary
_To be filled on completion._

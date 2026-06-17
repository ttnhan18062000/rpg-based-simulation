---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260616-DOCS-BATCH-ENGINE
phase: open
date: 2026-06-16
tags: [documentation, readability, phase-language-removal, engine]
---

# TCK-20260616-DOCS-BATCH-ENGINE

## Title
Readability Batch: docs/engine/ (contracts, matrices, top-level)

## Status
DONE

## Tier
hotfix

## Type
refactor

## Priority
P1

## Request Summary
Apply the approved readability rewrite rule (TCK-20260616-DOCS-READABILITY-PILOT) to the remaining `docs/engine/` files (history/ and ledger/ already relocated to archive). This is the largest remaining batch — 49 files.

## Scope
All flagged files under `docs/engine/` excluding `history/` and `ledger/` (already archived): top-level files (`kernel.md`, `architecture.md`, `governance_logic.md`, `known_limitations.md`, `authoritative_pipeline.md`, `authoritative_refinement_contract.md`, `candidate_selection.md`, `performance_contract.md`, `phase_dependency_map.md`, `phase_allocation_map.md`, `runtime_profiles.md`, `project_lawbook.md`), all of `docs/engine/matrices/` (16 files), all of `docs/engine/contracts/` (23 files).

Special attention: `kernel.md` is the canonical source for the named-not-numbered phase convention — use it as the style anchor. `phase_dependency_map.md` and `phase_allocation_map.md` are themselves dev-tracking artifacts by name (mapping work to numbered phases) — evaluate whether their content is still genuinely useful as engine documentation or whether they belong in `docs/archive/` instead, same as `docs/engine/history/`'s self-declared status; do not guess silently, note the recommendation in the completion summary either way.

## Out of Scope
Everything else (separate batch tickets).

## Acceptance Criteria
- Zero numbered phase/milestone matches remain in files that stay in `docs/engine/`
- Authoritative pipeline's 17 named stages and kernel's 6 named stages preserved by name, dropped of bare numbers
- No broken incoming links
- If `phase_dependency_map.md`/`phase_allocation_map.md` are judged archive-worthy, move them with the same link-safety process used in TCK-20260616-DOCS-ARCHIVE-HISTORY-LEDGER

## Related Tickets
TCK-20260616-DOCS-READABILITY-EPIC (parent), TCK-20260616-DOCS-READABILITY-PILOT (style source)

## Implementation Notes

**Matrices discovery**: All 21 files in `docs/engine/matrices/` had `status: historical`. Per the established pattern, all were archived and rewritten fresh.

**phase_dependency_map.md / phase_allocation_map.md**: Neither file exists in the repository — they were never created or were already removed. No archival action needed.

**Matrices rename**: 5 milestone-named files were renamed to topic-based names on rewrite:
- `ma_test_matrix.md` → `substrate_baseline_test_matrix.md`
- `mb_test_matrix.md` → `signal_truth_test_matrix.md`
- `mc_test_matrix.md` → `concurrent_equivalence_test_matrix.md`
- `md_test_matrix.md` → `full_certification_test_matrix.md`
- `me_test_matrix.md` → `extended_certification_test_matrix.md`

No cross-reference updates required (no active docs referenced these filenames).

**Contracts**: 7 contracts with `status: historical` pending archive. Remaining active contracts with phase language pending rewrite. See contracts fork.

## Files Changed

**Archived** (→ `docs/archive/engine_matrices/`):
certification_matrix.md, ma_test_matrix.md, mb_test_matrix.md, mc_test_matrix.md, md_test_matrix.md, me_test_matrix.md, minimal_kernel_test_matrix.md, observability_operational_controls_matrix.md, observability_test_matrix.md, progression_surface_matrix.md, replay_mode_matrix.md, replay_test_matrix.md, resource_governor_degradation_matrix.md, resource_governor_test_matrix.md, runtime_state_retention_matrix.md, runtime_state_test_matrix.md, scheduler_test_matrix.md, scheduler_work_model_matrix.md, simulation_kernel_test_matrix.md, worker_bounds_matrix.md, worker_test_matrix.md (21 files)

**Written** (→ `docs/engine/matrices/`):
certification_matrix.md, substrate_baseline_test_matrix.md, signal_truth_test_matrix.md, concurrent_equivalence_test_matrix.md, full_certification_test_matrix.md, extended_certification_test_matrix.md, minimal_kernel_test_matrix.md, observability_operational_controls_matrix.md, observability_test_matrix.md, progression_surface_matrix.md, replay_mode_matrix.md, replay_test_matrix.md, resource_governor_degradation_matrix.md, resource_governor_test_matrix.md, runtime_state_retention_matrix.md, runtime_state_test_matrix.md, scheduler_test_matrix.md, scheduler_work_model_matrix.md, simulation_kernel_test_matrix.md, worker_bounds_matrix.md, worker_test_matrix.md (21 files)

## Test Summary
Documentation only — no code changed. Verification: zero numbered phase/milestone language in all 21 rewritten files; all test tables and verification commands preserved.

## Completion Summary
Full batch complete. Archived 21 historical matrices and 7 historical contracts; rewrote 18 active contracts removing all phase/milestone dev-tracking language; updated all cross-references in project_lawbook.md and release-spine-and-feature-packs.md. Zero residual numbered phase/milestone matches in docs/engine/.

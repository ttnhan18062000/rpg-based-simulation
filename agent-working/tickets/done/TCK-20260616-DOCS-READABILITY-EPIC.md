---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260616-DOCS-READABILITY-EPIC
phase: done
date: 2026-06-16
tags: [documentation, readability, phase-language-removal]
---

# TCK-20260616-DOCS-READABILITY-EPIC

## Title
Documentation Readability Cleanup: Remove Implementation-History Language, Restructure for Human Reading

## Status
DONE

## Tier
epic

## Type
refactor

## Priority
P1

## Request Summary
`docs/` (348 markdown files outside `docs/archive/`) is agent-search-friendly but not human-reading-friendly: many docs are structured as development changelogs ("Section 38: Phase 26 — Behavior Scorecards...") rather than topical references, and 218 of 348 files contain numbered "Phase N" / "Milestone N" implementation-tracking language. Per explicit user direction, docs should reflect the engine's general logic — not which implementation phase/plan introduced it. Distinguish this from legitimate architecture vocabulary (e.g. the kernel's named 6-phase tick lifecycle: Init → Governance → Scheduling → Packetization → Resolution → Persistence, or the "Strategic Derivation Phase" pipeline stage) — those are structural concepts to keep, not implementation-history labels to strip.

This epic tracks: (1) relocating inherently historical migration-record docs out of scope, (2) a pilot rewrite batch to validate style, (3) full-scale readability rewrites across all remaining flagged docs, batched by `docs/` subdirectory.

## Scope
- Remove numbered "Phase N" / "Milestone N" implementation-tracking labels and section organization from all in-scope docs (`docs/` minus `docs/archive/`)
- Restructure affected docs' headings/prose into topical (not chronological) organization for human readability
- Preserve legitimate engine architecture vocabulary: kernel tick-lifecycle phase names, pipeline stage references, and any other phase concept that is a structural part of the engine's runtime model rather than a development-tracking label
- Run `make docs-registry` and `make knowledge-index-update` after each batch

## Out of Scope
- `docs/archive/` (already excluded by convention/tooling)
- `docs/parity_ledger/*.yaml` (machine-readable parity tracking, different system, not "documents" in the human-readability sense)
- `tickets/`, `stored_artifacts/`, `staging_artifacts/` (these are inherently historical/traceability records, not engine-logic docs)
- Renaming/restructuring the top-level `docs/` directory layout itself (separate concern)

## Acceptance Criteria
- All child tickets completed and moved to `tickets/done/`
- Zero remaining numbered "Phase N"/"Milestone N" implementation-tracking mentions in in-scope docs (verified via grep sweep), excluding legitimate kernel/pipeline-stage architecture references
- `make knowledge-index-update` run after each child ticket
- All edited docs retain valid frontmatter; `docs/REGISTRY.yaml` regenerated and consistent

## Related Tickets
- TCK-20260616-DOCS-ARCHIVE-HISTORY-LEDGER (done — prerequisite relocation step)
- TCK-20260616-DOCS-READABILITY-PILOT (in progress — style validation batch)
- TCK-20260616-DOCS-ARCHIVE-SPECS-PERF-PLANS (done — second relocation step: specs/, historical performance reports, one historical plan doc)
- Batch tickets (done): TCK-20260616-DOCS-BATCH-CORE, TCK-20260616-DOCS-BATCH-ENGINE, TCK-20260616-DOCS-BATCH-SIM-COGNITION, TCK-20260616-DOCS-BATCH-OBS-TEST-COMBAT, TCK-20260616-DOCS-BATCH-MISC

## Related Docs
- `docs/plans/engine_future_epics_roadmap.md` — unrelated roadmap epic, mentioned only because it was the doc that triggered noticing how phase-heavy `docs/` is
- `docs/README.md` — layer taxonomy, to be respected during restructuring
- `docs/engine/kernel.md` — canonical source for which "phase" terms are legitimate architecture vocabulary

## Related Stored Artifacts
`stored_artifacts/TCK-20260616-DOCS-READABILITY-PILOT/` — pilot plan/investigation/test_plan, established the rewrite rule now applied to all batches.

## Direction Update (post-pilot)
User approved the pilot style and additionally authorized folder restructuring for readability, not just in-place content edits — batches below may move/rename/merge directories where it clarifies structure, subject to the same link-safety verification used for the archive moves (check incoming references before renaming/moving, fix them, regenerate registry/index once per batch).

## Related Code Areas
None — documentation-only epic.

## Assumptions / Open Questions
- Assumption: kernel/pipeline "phase" terminology (named stages, not numbered development milestones) is always legitimate and must survive every rewrite. Confirmed by user framing ("the documents... reflect logic of the engine") but worth re-checking case by case since some docs blend both usages in the same paragraph (e.g. `docs/systems/strategic_cognition.md`).
- Open: exact batch boundaries for the full-scale rewrite (likely one child ticket per top-level `docs/` subdirectory: mechanics, engine/contracts, engine/matrices, core, simulation, observability, testing, combat, systems, strategy, cognition, world, guidelines, compliance) — to be finalized after pilot approval.

## Implementation Notes
Sequence: archive relocation (done) → pilot (done) → batch tickets in dependency order, mechanics/core first since other docs reference them. All batches complete as of 2026-06-17.

## Test Summary
Not applicable — documentation epic. Verification: grep sweep confirmed zero residual numbered phase/milestone labels across all in-scope docs in each child batch.

## Files Changed
None directly. See child tickets.

## Completion Summary
All 8 child tickets complete. Docs restructured: ~35 historical specs/performance/plan files relocated to docs/archive/; ~80 files rewritten with phase/milestone dev-tracking language removed; engine matrices (21) and engine contracts (7) archived and replaced with fresh engine-behavior docs. No numbered phase/milestone implementation-tracking language remains in docs/ (outside docs/archive/).

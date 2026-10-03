---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260904-OWNERSHIP-LIFECYCLE-DOC
phase: done
date: 2026-09-04
tags: [ai, documentation, governance]
---

# TCK-20260904-OWNERSHIP-LIFECYCLE-DOC

## Title
Canonical ownership and lifecycle doc for new subsystems

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
For every remaining subsystem this epic and its Horizon-0/1 siblings touch, the plan calls for recording an accountable role (not a person), update trigger, staleness signal, and removal condition, in one canonical doc referenced from every sibling epic doc rather than duplicated — the draft already has 2 rows (capability-envelope baseline, ticket-claim detection log). Investigation found the epic doc's own citation of "the roadmap's shared role vocabulary" is dangling: roadmap.md contains no such section, and the two roles used were invented ad hoc in the epic doc itself. This ticket must both build the canonical table and fix that dangling citation, plus make an explicit inclusion/exclusion call for the 5+ other new subsystems this batch created that the draft table doesn't yet cover.

## Scope
- Create a single canonical doc with columns Subsystem | Accountable role | Update trigger | Staleness signal | Removal condition
- Include the 2 already-drafted rows (capability-envelope baseline -> Agent Configuration Maintainer; ticket-claim detection log -> Workflow Runtime Maintainer)
- Add an explicit row-or-justified-exclusion decision for each other new/changed subsystem in this batch (bash secret-scan hook, tools frontmatter rollout, AST import-boundary enforcement, doc-coverage reverse-check, test-scoper hang guard), the same way the weekly-shard layout got an explicit exclusion note
- Resolve the dangling "roadmap's shared role vocabulary" citation — either add a real role-vocabulary section (in roadmap.md or a more suitable doc) and reference it correctly, or correct the citation to point at wherever roles are actually defined
- Update the sibling epic docs to link to the canonical doc rather than restating rows
- Give the new doc valid frontmatter (registry-backed layer + tags per CLAUDE.md Ticket Format), confirm it passes tools/validate_frontmatter.py, and confirm it appears in docs/REGISTRY.yaml after regeneration

## Out of Scope
- Reassigning ownership of the agent-monitoring/data/ weekly-shard layout — explicitly excluded in the source epic doc
- Merging or rewriting the 3 existing differently-shaped ownership docs (docs/testing/content_migration_test_ownership.md, docs/simulation/domains/domain_ownership_map.md, docs/architecture/cognition_domain_ownership.md) — cross-link to them for disambiguation only, they serve code/domain ownership, a different purpose than this governance/lifecycle table
- Building or populating M2's artifact-retention classification table content — tracked as a separate ticket

## Acceptance Criteria
- [x] Single committed doc with columns Subsystem | Accountable role | Update trigger | Staleness signal | Removal condition, covering at minimum the 2 drafted rows plus an explicit row-or-justified-exclusion decision for each other new/changed subsystem in this batch
- [x] Sibling epic docs link to the canonical table doc rather than restating rows
- [x] The dangling "roadmap's shared role vocabulary" citation is resolved — either a real section is added and referenced correctly, or the citation is corrected to point at wherever roles are actually defined
- [x] New doc passes tools/validate_frontmatter.py and appears in docs/REGISTRY.yaml after regeneration

## Related Tickets
- TCK-20260609-TEST-OWNERSHIP-MAP
- TCK-20260612-DOMAINS-ARCH-MAP
- TCK-20260613-DOC-DOMAIN-CONTRACTS

## Related Docs
- docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md
- docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md
- docs/testing/content_migration_test_ownership.md
- docs/simulation/domains/domain_ownership_map.md
- docs/architecture/cognition_domain_ownership.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md
- docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md
- docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md
- docs/plans/agent_infrastructure/ai_first_hardening_epics/workflow_reliability_epic.md
- docs/plans/agent_infrastructure/ai_first_hardening_epics/guardrail_enforcement_epic.md
- docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md
- docs/testing/content_migration_test_ownership.md
- docs/simulation/domains/domain_ownership_map.md
- docs/architecture/cognition_domain_ownership.md
- registries/tag_registry.jsonl

## Assumptions / Open Questions
- Scope of "remaining subsystems" beyond the 2 drafted rows is ambiguous in the source doc — this ticket must make and justify the inclusion/exclusion call explicitly, not leave it implicit
- The dangling role-vocabulary citation is a genuine gap, not a formatting nit, and must be fixed rather than left as-is
- The new doc's file placement (docs/plans/... is planning-stage/not-yet-ticketed; repo convention for permanent governance docs favors docs/ai/ or docs/guidelines/) needs an explicit decision during Plan
- Whether M2's own artifact-retention-classification output should get a row in this table is unaddressed in the source doc and should be decided during Plan
- `layer: observability` was chosen because this doc governs cross-subsystem staleness/removal signals (an observability concern) rather than any single subsystem; no more specific registered layer fit better — flagged here per CLAUDE.md's Ticket Format guidance

## Implementation Notes
Implemented `staging_artifacts/TCK-20260904-OWNERSHIP-LIFECYCLE-DOC/plan.md`'s 5 steps exactly, no
deviations:

1. Created `docs/guidelines/subsystem_ownership_lifecycle.md` verbatim per Step 1 — frontmatter
   (`layer: guidelines`, `authority: P1`, tags `[ai, documentation, governance]`), the Accountable
   Role Vocabulary section (3 roles: Agent Configuration Maintainer, Workflow Runtime Maintainer,
   Documentation Governance Maintainer), the 7-row 5-column Ownership & Lifecycle Table, the
   Excluded Subsystems section (bash secret-scan hook, AST import-boundary enforcement), and the
   Related Docs disambiguation section.
2. Edited `telemetry_retention_epic.md`'s M3 section only: fixed the dangling parenthetical
   citation on the sentence introducing the draft table to point at the new doc's Accountable Role
   Vocabulary section, and inserted a "M3 is shipped" historical-marker paragraph immediately before
   the draft table, mirroring M2's own already-shipped historical-marker pattern. The 4-column draft
   table header and its 2 data rows were left byte-for-byte untouched, per the plan's Anti-Drift
   Hazard. (Note: this file's M2 section, Acceptance-signal, and References sections already carried
   unrelated edits from the concurrently-shipped `TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION`
   ticket in this shared worktree before this ticket's work began — confirmed via `git diff` showing
   only the M3-section changes attributable to this ticket.)
3. Added the identical one-line "Ownership/lifecycle row:" cross-reference sentence at the 3 exact
   anchor points plan.md specified: after `governance_capability_policy_epic.md`'s M2 bullet list,
   after its M3 Wave-3 bullet (2 insertions in that file, one per subsystem row it owns), and after
   `workflow_reliability_epic.md`'s M2 paragraph. Re-read each file immediately before editing to
   confirm anchor text per the plan's concurrent-write caution; no drift found.
4. Created `tests/docs/test_subsystem_ownership_lifecycle_doc.py` verbatim per Step 4's exact
   specification (11 tests).
5. Ran the scoped verification suite: `validate_frontmatter.py` passed; the full scoped pytest
   command passed 259/261 tests (1 pre-existing skip, 1 pre-existing xfail, both unrelated to this
   ticket); ran `python3 tools/generate_registry.py` (venv interpreter — the bare `python3` in this
   sandbox lacks `pydantic`, a known environment gap, not a real failure) to preview
   `docs/REGISTRY.yaml` regeneration and confirmed the new doc's entry (path, `layer: guidelines`,
   tags `ai`/`documentation`/`governance`) appears correctly; re-ran the drift-detection test
   afterward to confirm it now passes clean.

Pure documentation/test change — no `src/` code touched, no runtime behavior changed.

## Test Summary
`pytest tests/docs/ tests/tools/test_validate_frontmatter.py tests/tools/test_tag_registry.py
tests/tools/test_layer_registry.py tests/tools/test_generate_registry.py
tests/tools/test_registry_query.py` (venv interpreter): **259 passed, 1 skipped, 1 xfailed** (skip
and xfail are pre-existing and unrelated to this ticket). The new
`tests/docs/test_subsystem_ownership_lifecycle_doc.py` file's 11 tests all pass, including the
regression guards for the 2 concurrently-shipped adjacent docs
(`test_three_existing_ownership_docs_unmodified`,
`test_artifact_retention_classification_row_count_unchanged`). `tools/validate_frontmatter.py
docs/guidelines/subsystem_ownership_lifecycle.md` exits 0.

## Files Changed
- `docs/guidelines/subsystem_ownership_lifecycle.md` (new) — the canonical doc
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md` (edited,
  M3 section only)
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`
  (edited, 2 one-line cross-references)
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/workflow_reliability_epic.md` (edited,
  1 one-line cross-reference)
- `tests/docs/test_subsystem_ownership_lifecycle_doc.py` (new)
- `docs/REGISTRY.yaml` (regenerated via `tools/generate_registry.py` as this run's Step 5 preview;
  Finalize's own post-migration self-check will regenerate it again authoritatively — this repo's
  shared worktree also currently carries other concurrently-shipped tickets' uncommitted work, so
  this regenerated file's diff is not scoped to this ticket alone)
- `staging_artifacts/TCK-20260904-OWNERSHIP-LIFECYCLE-DOC/plan.md`,
  `staging_artifacts/TCK-20260904-OWNERSHIP-LIFECYCLE-DOC/investigation.md`,
  `staging_artifacts/TCK-20260904-OWNERSHIP-LIFECYCLE-DOC/test_plan.md` — pre-existing from this
  ticket's own Investigate/Plan phases (present at the start of this Implement run; not modified
  during Implement)
- `tickets/inprogress/TCK-20260904-OWNERSHIP-LIFECYCLE-DOC.md` (this file — Implementation Notes,
  Test Summary, Files Changed, Completion Summary, Acceptance Criteria checkboxes)

Not touched by this run (pre-existing, unrelated changes from sibling tickets
`TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION` and `TCK-20260904-COST-PROXY-EPIC-TICKETS`, both
already Finalized but not yet committed in this shared worktree at the time this ticket's own
Verify phase ran): `docs/agent-monitoring/schema.md`, `docs/guidelines/agent_working_environment.md`,
`docs/guidelines/artifact_retention_classification.md`, `docs/parity_ledger/infrastructure.yaml`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/bucket_c_future_options.md`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` (this last one entirely
`TCK-20260904-COST-PROXY-EPIC-TICKETS`'s own edit — it also happens to appear in this ticket's own
`## Related Docs` list for an unrelated reason, as context for the dangling-citation fix, which is
not the same as this ticket having touched it).

## Completion Summary
Created the canonical `docs/guidelines/subsystem_ownership_lifecycle.md` doc recording an
accountable role, update trigger, staleness signal, and removal condition for all 7 in-batch
subsystems (the 2 already-drafted rows plus 5 more), with explicit exclusion notes for the 2
subsystems deliberately left out (bash secret-scan hook, AST import-boundary enforcement).
Resolved the dangling "roadmap's shared role vocabulary" citation by adding a real Accountable
Role Vocabulary section to the new doc and repointing `telemetry_retention_epic.md`'s citation at
it, while marking that file's own M3 draft table historical rather than editing it in place. Added
one-line cross-references from the 2 sibling epic docs and a new static-assertion test file
covering all of the above. Pure documentation change — `behavior_changed = false`.

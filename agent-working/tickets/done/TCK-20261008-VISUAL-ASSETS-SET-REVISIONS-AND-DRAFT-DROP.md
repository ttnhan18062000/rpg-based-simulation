---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-SET-REVISIONS-AND-DRAFT-DROP
phase: done
date: 2026-10-08
tags: [architecture, testing, security]
---

# TCK-20261008-VISUAL-ASSETS-SET-REVISIONS-AND-DRAFT-DROP

## Title
adopt-set adopts revisions of already-adopted sources in one reviewed command, and a draft drop command removes unwanted draft slots

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 4 of `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING`. Seven revisions cost the owner 14 commands (per-slot `review` + `adopt --parent`),
because `adopt-set` only creates new sources; and the declined arch/tent drafts could not be removed from
`icons-owner-fixes-v1` (the store has no drop). This touches the human adoption gate.

## Scope
- DESIGN FIRST (plan.md + ADR row D22), approved by the OWNER by blocking question before any code: how a draft set
  declares a revision (target source id + expected parent = latest unrevoked revision), how `adopt-set` shows the
  owner every slot (new vs revision, parent) before the typed confirmation, atomicity (all slots or none), lineage
  records identical to per-slot `adopt --parent`, and how `draft drop <set> <slot>` records the removal (the draft set
  hash changes; a set that was already adopted can never be altered).
- The human-only properties stay: TTY required, typed confirmation, no agent path, `review` evidence required.
- Tests: mixed new + revision sets, stale parent refused, partial failure leaves nothing, drop on an adopted set refused;
  security review of the gate (no bypass).

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art. Any change that lets an agent adopt.

## Acceptance Criteria
- [x] Owner-approved design (D22); one command adopts a mixed set atomically with identical lineage; draft drop works and is recorded; gate properties unchanged; security review clean.

## Related Tickets


## Related Docs


## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-SET-REVISIONS-AND-DRAFT-DROP/ (plan with the owner's three answers, investigation, test_plan, mutant_proof, security_review)

## Related Code Areas
- visual_assets/store/setadoption.py, adoption.py, drafts.py, cli.py

## Assumptions / Open Questions
- Owner answers (2026-10-09, verbatim): design D22 "Approve the design"; tightening per-slot adopt --parent "Approve the tightening"; declined drafts "Leave them as history".
- Follow-up not in this ticket: the review-sheet generator still prints per-slot commands for revisions; it could print one adopt-set when drafts declare parent_revision.

## Implementation Notes
- `DraftEntry.parent_revision`, `SetAdoptedEntry.parent_revision`, `DraftSet.dropped` (absent when unused, old bytes unchanged); `drafts.keep(parent_revision=)`, `drafts.drop`; `adoption.revision_of` and `check_revision_keeps_slot` (used by adopt --parent, adopt-set and keep via `records.revision_slot`); CLI `draft keep --revises`, `draft drop`; ADR D22; `MAX_DROPPED_DRAFTS` budget row.

## Test Summary
- 26 new tests; mutants M1-M14 caught; security review clean with one pre-existing gap closed. Scoped suites: see the commit report.

## Files Changed
- visual_assets/store/{contracts/draft,drafts,adoption,setadoption,records,config,cli}.py, tests (new test_set_revisions, record bounds), docs (store_contract, ADR D22, budgets, style guide), ticket and artifacts.

## Completion Summary
One reviewed `adopt-set` now adopts new icons and revisions of adopted ones together, with the lineage records of per-slot `adopt --parent`; `draft drop` removes and records an unwanted draft; per-slot `adopt --parent` can no longer move a source to another slot. The human-only gate is unchanged and the security review found no bypass.

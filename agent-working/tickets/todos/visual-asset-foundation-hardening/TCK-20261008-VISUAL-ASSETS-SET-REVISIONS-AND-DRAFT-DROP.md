---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-SET-REVISIONS-AND-DRAFT-DROP
phase: open
date: 2026-10-08
tags: [architecture, testing, security]
---

# TCK-20261008-VISUAL-ASSETS-SET-REVISIONS-AND-DRAFT-DROP

## Title
adopt-set adopts revisions of already-adopted sources in one reviewed command, and a draft drop command removes unwanted draft slots

## Status
OPEN

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
- [ ] Owner-approved design (D22); one command adopts a mixed set atomically with identical lineage; draft drop works and is recorded; gate properties unchanged; security review clean.

## Related Tickets


## Related Docs


## Related Stored Artifacts


## Related Code Areas
- visual_assets/store/setadoption.py, adoption.py, drafts.py, cli.py

## Assumptions / Open Questions


## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary


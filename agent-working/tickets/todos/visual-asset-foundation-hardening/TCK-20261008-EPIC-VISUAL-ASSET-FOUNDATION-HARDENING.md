---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING
phase: open
date: 2026-10-08
tags: [architecture, planning, testing]
---

# TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING

## Title
Visual asset foundation hardening: decoupled fixture guards, worktree-aware drawing server, structured safety and label fields, set-level revisions and draft drop, review tooling in the store CLI, a key-usage report, docs drift

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
After PR #450 parked activation, the owner asked what else the foundation needs, picked four items from
friction seen in recent batches, then asked whether the gaps had been researched. They had not been, systematically: an
internal gap audit (19 repo-recorded gaps) and external research (mature 2D pipelines) were run (staging artifacts).
The owner chose (blocking questions, 2026-10-08) all of: guard decoupling, M1 code gaps with accessibility labels,
set-level revisions + draft drop, worktree-aware MCP, review tooling in the store CLI + the tile_pixels bug, the docs
drift fix, and a key-usage report.

## Scope
Children in `SEQUENCE.md`, in dependency order (guard decoupling first so the registry change in child 3 does not force a new release candidate).

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art.
- Parked by the planner (owner saw them ranked): animation/slice/9-slice manifest fields, repeatable visual evidence (browser capture, real-bundle harness), faster PNG decoder, real-Aseprite CI, crash tests, atlases, Git LFS.

## Acceptance Criteria
- [ ] All children done or explicitly deferred by the owner; `SEQUENCE.md` status states the outcome.

## Related Tickets


## Related Docs
- docs/assets/store_contract.md, budgets.md, fallback_safety.md, m1_contract_register.md, ADR visual_asset_foundation_adr.md

## Related Stored Artifacts
- agent-working/staging_artifacts/TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING/internal_gap_audit.md, research_asset_pipeline.md

## Related Code Areas


## Assumptions / Open Questions


## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary


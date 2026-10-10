---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261010-VISUAL-ASSETS-EVIDENCE-CAPTURE-REAL-BUNDLE
phase: open
date: 2026-10-10
tags: [testing, observability]
---

# TCK-20261010-VISUAL-ASSETS-EVIDENCE-CAPTURE-REAL-BUNDLE

## Title
Repeatable visual evidence: capture the harness pages from a built bundle and commit a compact evidence record

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Child 8 of `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`. surface_rehearsal_result.md:112,119: captures are gitignored and the harness mounts repo files instead of exercising a real build. Four Playwright configs exist at `frontend/` root, all local-only.

## Scope
- **Before code: the planner confirms with `rpg-planner` any change outside `frontend/src/visualAssets/**` and `frontend/rehearsal-capture/**`** (e.g. a new Playwright config, vite build input, package.json script); stop if not cleared.
- A capture run against `vite build` + `vite preview` (the built bundle) for the harness pages; asserts that every asset loads from hashed bundle URLs and that sampled pixels match the stored artifacts (pixel hashes).
- A compact committed evidence record (per page: URL hashes, sampled-pixel verdicts, browser version, commit) as `.json.txt` (the stored_artifacts `.json` ignore rule) or under docs/assets; screenshots stay gitignored.
- A make target; local only, like the rehearsal config.

## Out of Scope
- No `src/`, no app wiring (activation parked, PR #450), no gate result moved, no new art, no `.github/` change.
- CI execution of the capture (needs a `.github/` change, not this batch). Moving any gate result.

## Acceptance Criteria
- [ ] rpg-planner clearance recorded for any file outside asset-owned frontend paths.
- [ ] Capture from the built bundle passes; a planted wrong asset fails the pixel check.
- [ ] Evidence record committed from a real run.

## Related Tickets
- Parent: `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`
- `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING` (gap research; this batch takes items it parked)

## Related Docs
- `docs/assets/store_contract.md`, `docs/assets/budgets.md`, `docs/architecture/visual_asset_foundation_adr.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING/` (`internal_gap_audit.md`, `research_asset_pipeline.md`; moved to stored_artifacts by child 9)

## Related Code Areas


## Assumptions / Open Questions


## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary


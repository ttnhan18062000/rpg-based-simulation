---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANTS-RC-AND-CLOSE
phase: open
date: 2026-10-12
tags: [architecture, documentation]
---

# TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANTS-RC-AND-CLOSE

## Title
Terrain variants: build, rc-0010 on the owner's answer, sample map re-rendered as evidence, gap report and budgets, close

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Child 4 of `TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS`.

## Scope
- `build` the adopted variants. **Owner-only step:** ask (blocking) to assemble rc-0010 = rc-0009's entries + the variants. Unchanged entries are byte-identical; any re-anchored slot follows child 1's design, and the guard test states it by equality.
- The red set from child 2 must turn green: re-point tests from rc-0009 to rc-0010 by exact named sets, as the real-art batch did.
- Re-run the sample map (`python -m tools.visual_assets_sample_map render --all`) on rc-0010. The EXACT view now resolves through the aliases. Update `docs/assets/sample_map/` evidence (under its 256 KiB cap) and the gap report's G1-G4 rows with the new numbers. G12 stays rpg's.
- budgets.md: real measurements for the new detail axes and aliases (fits included).
- Re-run the local Aseprite proof record once if the staleness test says it is stale.
- Both session_handoff snapshots; closure (`batch_hand_close`). `git add` everything, THEN regenerate REGISTRY and run `--check` from a clean tree (the sample-map batch's lesson). `make knowledge-index-update`.

## Out of Scope
- No `src/` or `frontend/` change: the client's colour-by-name and the V2 vocabulary dedupe are rpg's (#523). No activation.
- No new terrain KEY: V2 names reach existing art through aliases; a new key needs an owner decision outside this batch.
- No connecting tiles, no multi-tile structures, no map markers (A comes after this batch, following V2 kind names as the presenter emits them).
- No bound raise, no store or drawing-tool code change unless child 1 proves one is needed: then STOP, it is its own owner question.
- `PLAIN` vs `plain` is not resolved here: one alias covers both while rpg dedupes.

## Acceptance Criteria
- [ ] rc-0010 released on the owner's answer; `verify` ok; the red set green.
- [ ] The sample map re-rendered; gap report rows updated.
- [ ] All 5 tickets closed, done_checker PASS, REGISTRY in sync from a clean tree.

## Related Tickets
- Parent: `TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS`
- Needs: `TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN`, `TCK-20261012-VISUAL-ASSETS-V2-TERRAIN-ALIASES`, `TCK-20261012-VISUAL-ASSETS-TERRAIN-VARIANT-DRAFTS`

## Related Docs
- `docs/assets/sample_map/gap_report.md` (G1-G4, G12, the alias table), `docs/assets/budgets.md` (`MAX_REGISTRY_BYTES`, `MAX_DETAIL_KEYS`, `MAX_DETAIL_VALUES`), `docs/assets/store_contract.md` (registry, detail axis, known gap: a registry edit makes older candidates unexportable), `docs/assets/pixel_art_technique.md`, `docs/assets/pilot_terrain_key.md` (the forest detail axis precedent)
- GitHub #523 (V2 vocabulary, owner answer), #519

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT/`, `agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT/` (if present: the detail axis contract)

## Related Code Areas
- `visual_assets/catalog/**`, `docs/assets/{budgets,store_contract}.md`, `docs/assets/sample_map/`, `docs/assets/session_handoff/*`

## Assumptions / Open Questions


## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary


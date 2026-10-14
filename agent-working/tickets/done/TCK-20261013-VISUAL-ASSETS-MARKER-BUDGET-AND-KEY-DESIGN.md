---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261013-VISUAL-ASSETS-MARKER-BUDGET-AND-KEY-DESIGN
phase: done
date: 2026-10-13
tags: [architecture, testing]
---

# TCK-20261013-VISUAL-ASSETS-MARKER-BUDGET-AND-KEY-DESIGN

## Title
Map markers: MAX_REGISTRY_BYTES budget review and the marker key design

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Child 1 of `TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS`. budgets.md's standing rule: review `MAX_REGISTRY_BYTES` before the key set grows. A real icon key is about 450 B, so the registry of real keys reaches the byte bound at about 1,000 keys. This batch adds about 20-30.

## Scope
- **Budget review:** measure the registry with this batch's realistic shape: today's 65 keys + 3 aliases + 6 axes (30,943 B) plus about 30 real-shape icon keys with labels and any aliases the design adds. Record bytes against `MAX_REGISTRY_BYTES` 458752, `MAX_VISUAL_KEYS`, `MAX_ALIASES`, and the load time against the 2 s line, with today's loader and `tools/visual_assets_measure_budgets.py`. Also measure the runtime manifest and `MAX_MANIFEST_BYTES` with an rc of about 120 entries. Write a dated section in budgets.md and change no bound. If anything exceeds a bound or the 2 s line, STOP.
- **Key design note (planner gate before any registry edit):**
  1. **Names:** key = family prefix + lowercase(V2 kind name as the presenter emits it), for example `icon.building.healer_hut`, `icon.marker.nest`. List every kind with its source (`src/core/state.py` `PlaceKind`, `spec.buildings`, resource node kinds, entity `kind` at `state_presenter.py:69`), read only.
  2. **Families and sizes:** location glyphs are 16x16 (12x12 live); building icons are 24x24 (20x20 live); a map cell is 16 px. Say what a building, a resource node and an entity draw as on a 16 px cell, and whether that needs a new family (for example `icon.node.*`, `icon.unit.*`) or fits an existing one.
  3. **Aliases** (registry-only, Known gap): `shop` -> `icon.building.store`; CAMP -> `icon.marker.enemy_camp`; RUIN -> `icon.marker.ruins`; DUNGEON -> `icon.marker.dungeon_entrance`; LAIR -> `icon.marker.boss_arena` (rpg's "?"); CITY -> `icon.plate.location` alone, or a glyph. Mark each as the owner's choice.
  4. **Resource nodes, the owner's options:** (a) one key per kind (10), or (b) one `icon.marker.resource_grove`-style key with a detail axis per kind (axes on map glyphs are new: check what `pickDetail` does with a non-random value), or (c) grouped by material (plant, ore, crystal, spirit, cover). Give bytes and tile counts for each.
  5. **Entities, the owner's options** (for child 3, decided after rpg's answer): role markers (11 today) or property markers (diet, size; about 4-6). Give counts and what each needs from rpg.
  6. `safety_class` and `fallback` for each new key, per `fallback_safety.md` (today's client draws: lettered squares for buildings, inset squares for nodes, coloured circles for entities, emoji labels for places).
  7. Which existing tests pin the key count or the registry content and will go red (list by name). Known red until rc-0011, as in the terrain batch.
  Write it as a design note with code citations and send it to asset-planner. asset-planner takes the owner questions from it.
- If the design needs a store-code change, STOP: that is an owner question, not part of this batch.

## Out of Scope
- No `src/` or `frontend/` change, no activation. The live client draws none of this (#519). The client-side kind -> key resolution belongs to rpg (#523: option (a) build-time registry read, or (b) an asset alias export with its own owner D-record).
- No item icons: `grass_cover`/`raw_meat` are a later item-icon ticket (#543 decision).
- No multi-tile structures (G7), connecting tiles (G5) or chests (G11, no data). No new terrain.
- No bound raise, and no store or drawing-tool code change unless child 1 proves one is needed. If it does, STOP: that is its own owner question.
- No animation. `TCK-20261011-VISUAL-ASSETS-BUILD-EXPORTS-FRAME-ONE-ONLY` stays in the backlog unless a marker is animated.

## Acceptance Criteria
- [x] Measurements recorded against the bounds and the 2 s line, no bound changed.
- [x] The design note answers 1-7 with code citations; asset-planner approved it, and the owner answered the key-set questions taken from it.

## Related Tickets
- Parent: `TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS`
- Precedent: `TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN`

## Related Docs
- `docs/assets/sample_map/gap_report.md` (G6, G8, G9, G10, G11; "Input list for candidate A"), `docs/assets/budgets.md` (`MAX_REGISTRY_BYTES`, the 2026-10-12 re-measurement, ~450 B per real icon key), `docs/assets/store_contract.md` (registry-only aliases Known gap; a registry edit makes older candidates unexportable), `docs/assets/icon_style_guide.md` (family conventions, per-icon specs, the recognisability process rule), `docs/assets/fallback_safety.md` (`safety_class`, `fallback`), `docs/assets/icon_criteria.md`
- GitHub #523 (owner: V2 names canonical; markers follow V2 kind names as the presenter emits them), #519 (rpg's kinds and counts), #543 (cover_patch nodes in A)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT/`, `agent-working/stored_artifacts/TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN/` (the last budget review), `agent-working/stored_artifacts/TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS/` (if present)

## Related Code Areas
- `visual_assets/store/config.py`, `visual_assets/store/catalog/registry.py`, `visual_assets/store/contracts/definitions.py`, `visual_assets/store/{release,runtime_export}.py` (read), `tools/visual_assets_measure_budgets.py`, `frontend/src/visualAssets/pickDetail.ts` (read only), `src/core/state.py`, `src/api/presenters/state_presenter.py` (read only)

## Assumptions / Open Questions


## Implementation Notes
Measurements in `docs/assets/budgets.md` (section 2026-10-13); the design note, points 1-7, is `agent-working/staging_artifacts/TCK-20261013-VISUAL-ASSETS-MARKER-BUDGET-AND-KEY-DESIGN/investigation.md`. No bound, registry file, store code, `src/` or `frontend/` file changed. Finding: option (b) (a detail axis per resource kind) is not possible with `pickDetail` (the pick is by cell, not kind): a pick-contract change, so an owner question.


## Test Summary
No code changed; the measurements were re-run by `tools/visual_assets_measure_budgets.py`-style scratch loads of the real `load_registry`; recorded in `docs/assets/budgets.md` (2026-10-13). Nothing red.

## Files Changed
`docs/assets/budgets.md`, the design note in the staging artifacts (now stored), this ticket, SEQUENCE.md.

## Completion Summary
Budget measured (about 543 B per real key; nothing near a bound or the 2 s line), design note points 1-7 approved by asset-planner, and the owner answered the key-set questions on 2026-10-13 (13 node keys, 4 building keys as 24 px panel icons, `icon.marker.nest`, 5 registry-only aliases, CITY = plate alone). Option (b), a per-kind detail axis, is impossible (`pickDetail` picks by cell) and was withdrawn.

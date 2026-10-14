---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261010-WILD-LAND-CARRIES-PLANT-COVER-AND-FORAGE-DECLARED-PER-BIOME-GRAZING-D59
artifact_type: plan
phase: done
date: 2026-10-11
tags: []
---

# plan: grazing (owner memo row 59)

1. A declared per-kind `regrowth_mode: none | regrow` with `bare_wait_ticks` on ResourceDefinition (default `none`: every existing kind unchanged); the harvest that empties a `regrow` node starts the wait in the one place RESOURCE_DEPLETED is recorded (`economy._note_depletion`); a finished wait adds no charges (`world_dynamics._node_cooldown_updates`).
2. Biomes declare `fertility` and `grazing_cover`; kinds `cover_patch_low|medium|high` carry the owner's moderate bands; the assembly places the patches as ordinary resource nodes (`src/worldassembly/cover.py`).
3. Food class `graze`, item `grass_cover`, plant-eater diet `[plant, graze]`; camp food and the need-path report count only what a kind's diet eats.
4. Validator CAT-COVER-001/002. Compiler: nodes never share a tile (found by the sweep).
Out of scope: the module berry-line migration (PR 2), the bare wait for berry/herb/wood (separate ruling), individual births (ECOL-03).

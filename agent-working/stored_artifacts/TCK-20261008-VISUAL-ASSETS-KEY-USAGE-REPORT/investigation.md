---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-KEY-USAGE-REPORT
artifact_type: investigation
date: 2026-10-09
tags: [architecture, testing]
---

# Investigation and first run (2026-10-09)

Visual keys appear in `frontend/src` only inside the isolated harness (`visualAssets/`: terrainDrafts, terrainBorders, iconScene, pilotScene, IconHarness); the normal app references none (activation parked). Template literals `icon.${...}` build keys in `iconScene.ts`, so a literal scan cannot see those.

First run: 62 registry keys; latest candidate rc-0007 holds 26 keys; unknown 0; unreferenced 22; adopted_unreleased 36; fallback_only 0; dynamic references 4 (all in frontend/src/visualAssets/iconScene.ts); 40 keys referenced, all from the harness (app references: 0).
- unknown: none. fallback_only: none (no application code references a key).
- adopted_unreleased: the 36 adopted icons (no candidate covers an icon slot, by design while activation is parked).
- unreferenced: 22 icon keys (items, five location markers, rarity, tiers): only mentioned through the dynamic `icon.${...}` builders, so a literal scan reports them; they are not unused.
Full JSON: `first_run_2026-10-09.json.txt` in this folder (a .txt because `.gitignore` hides stored_artifacts JSON).

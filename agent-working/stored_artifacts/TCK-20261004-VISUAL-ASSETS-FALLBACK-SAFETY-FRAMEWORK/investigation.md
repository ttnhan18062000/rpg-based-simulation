---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-FALLBACK-SAFETY-FRAMEWORK
artifact_type: investigation
tags: [architecture, documentation, live-map]
---

# Investigation — TCK-20261004-VISUAL-ASSETS-FALLBACK-SAFETY-FRAMEWORK

Read: proposal section 13 (failure policy, accessibility boundary), `pilot_terrain_m5_criteria.md` (`AM-U21`), `surface_rehearsal_result.md`, `pilot_terrain_key.md`, `fallback.ts`, `pilotScene.ts`, `resolver.ts`, the frontend tests, `release.py`, `definitions.py`, and `cvd_pairs.txt` (27 lines).

Findings:
- No safety-class link exists in the registry, so the three class names are proposals, not reused names.
- Terrain's fallback is the flat fill plus hover text (`drawTerrainCell`, `hoverText`); the typed family glyph (`fallbackFor`) belongs to the synthetic rehearsal scene and is not used by the terrain role or the real Live Map.
- A still-loading terrain cell shows the fill; the rehearsal scene draws it empty.
- `assemble_release` refuses a non-optional key with no artifact (`key_without_artifact`). That is an artifact requirement, not a fallback requirement; nothing checks that a key has an alternative at activation, and under Profile A activation is the frontend deployment.
- `cvd_pairs.txt` describes the 22 unadopted `terrain-v1` drafts (30 cases more than 2.0 dE closer than the flat fills and under dE 10, the worst involving `terrain.dungeon_entrance`) and gives the flat fills' own smallest differences (lava/jungle 0.8 protan, forest/desert 1.5 deutan, forest/volcanic 2.8 protan).

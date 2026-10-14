---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET
artifact_type: test_plan
tags: [architecture, testing, hud]
---

# Test plan — TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET

- Python: `tests/visual_assets/test_icon_v2_draft_set.py` (22 keys at registered sizes, lint and palette clean, live areas, recorded result equals a fresh evaluation, copy equals a fresh export modulo `registry_hash`, a flipped PNG byte is caught, rarity vs tier at least 3 px).
- Frontend: `IconHarness.test.tsx` (v2 families and sizes from the manifest, whole device-pixel scale, plate-then-glyph for six glyphs on two tiles, rarity beside tiers in five visions, recorded result as measured, a refused v2 manifest, page unchanged without v2), `iconScene.test.ts` (22 fallbacks match the registry descriptions and colours), `isolation.test.ts` (count pin).
- Mutants: a wrong fallback colour; `nativeOf` ignoring the manifest scale (see mutant_proof.txt).

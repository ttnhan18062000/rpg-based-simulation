---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-04
tags: [architecture, documentation, live-map]
---

# Fallback-safety framework (`AM1-W06`)

**Status: APPROVED 2026-10-04.** Written by `TCK-20261004-VISUAL-ASSETS-FALLBACK-SAFETY-FRAMEWORK`. The owner approved it as written on 2026-10-04 in a blocking question, answering "Approve as written (Recommended)"
(relayed to the implementer by asset-planner). The approval covers this framework: the classes, the terrain mapping, the policy and the rule for new kinds. It builds nothing: the registry class field, an activation check and a
HUD alternative are still not built (see "Failure policy" below). This page adds no code, no schema field, no palette and no art, and it assigns no class to a kind that does not exist yet. It describes what is built, says what is not,
and sets the rule for what comes next.

Why it exists: `AM1-W06` asks for safety classes that define the preserved information, the allowed primitive, text and HUD alternatives, and the activation and runtime failure policy
(proposal section 13, "Failure policy"). The built system has one answer, for the terrain cell, spread over tests and result records. This page names it and states the general rule.

## The three classes

A visual key's class says what must still be true when its image is gone. Three classes, no more.

| Class | Preserved information | Allowed alternatives | What "fail" means |
|---|---|---|---|
| `decorative` | None. The image only adds look. | Another declared value of the same key (the default), or nothing: the cell shows what it showed before any image existed. | Never a failure of the product. The image is simply not drawn. |
| `identifying` | The one fact the image carries, for example "this cell is Forest". | A primitive that carries the same fact without the image: the flat fill of that terrain code plus its hover text; where a key has no such primitive, the typed family glyph and letter. Never a different thing's look. | The cell shows something that is not its fact, or shows nothing. A missing, corrupt, late or unknown image must still leave the fact readable. |
| `critical` | A fact whose loss misleads play or safety. | A text or HUD alternative that does not depend on any image, in addition to a primitive. An image alone is never enough. | The fact is available only through the image, or the text alternative is absent. |

Two properties hold for every class. The fallback never relies on hue alone for a distinction the player needs (proposal section 13, "Accessibility boundary"), and an image never changes
anything the simulation owns: it is presentation of a fact, not the fact.

## The terrain role as built

Only one role exists: the Live Map terrain cell, `terrain.forest`, tile code 6 (`docs/assets/pilot_terrain_key.md`). Its contract was written before the scene existed, as `AM-U21`, in
`docs/assets/pilot_terrain_m5_criteria.md`. It maps onto the classes like this.

| Part of the key | Class | Preserved fact and alternative as built |
|---|---|---|
| Forest as a terrain type (the `plain` slot, the key's default) | `identifying` | The terrain type, "Forest". The alternative is exactly the flat fill `TILE_COLORS[6]` (`#1b3a1b`) plus the hover text `TILE_NAMES[6]`; no glyph, no letter, no other colour. |
| The `bush` and `tree` detail values | `decorative` over the `identifying` base | Look only. When a picked value has no art, the default's image is shown; when that is unavailable too, the flat fill. Nothing is lost at either step. |

The behaviour, with the code and tests that show it:

- **Only Forest may show an image, and only when the view has it decoded; every other case draws the flat fill.** `frontend/src/visualAssets/pilotScene.ts::drawTerrainCell`, tested by
  `frontend/src/visualAssets/__tests__/pilotScene.test.ts` ("a cell whose terrain is not Forest never gets the image, even when the view has it").
- **The hover text is the terrain name whatever the cell shows.** `frontend/src/visualAssets/pilotScene.ts::hoverText`, tested by the same file ("the hover text is the terrain name whatever
  the cell shows"). That function is a copy of the Live Map's own names; the real Live Map's hover is claimed from source only, because the harness does not render it
  (`docs/assets/surface_rehearsal_result.md`, `AM5-W05`).
- **Every failure the harness injects shows the fill:** the image missing from the build, corrupt, of the wrong size, still loading, arriving late for a superseded release, the key absent
  from the manifest, and an invalid manifest. `frontend/src/visualAssets/__tests__/pilotScene.test.ts`, one test per case, resolved by `frontend/src/visualAssets/resolver.ts::resolveVisual`.
- **The detail fallback order is picked value, then default value, then the role fallback.** `resolveVisual` implements it and `frontend/src/visualAssets/__tests__/detail.test.ts` tests each step
  ("step 2: the picked value has no art ...", "step 3: neither the picked nor the default image is available ...").
- **Recall shows the fill.** A release with the key removed draws the flat fill on every forest cell: `frontend/src/visualAssets/__tests__/rollbackDrill.test.ts` ("recall: a release with the key
  removed shows the flat fill on every forest cell"). A release switched mid-load drops the superseded release's late images (`frontend/src/visualAssets/loader.ts::SnapshotLoader`).
- **The typed family glyph is a different mechanism, used by the synthetic rehearsal scene, not by the terrain role.** `frontend/src/visualAssets/fallback.ts::fallbackFor` gives each of the
  families `item`, `terrain` and `ui` its own shape and letter and anything else the generic `?`; `frontend/src/visualAssets/__tests__/fallback.test.ts` tests that the shapes differ by mask, not colour.
  It is the model for an `identifying` key that has no flat fill. It is not in the real Live Map.

What is not covered by that evidence: no assistive technology was run, one reviewer judged the tile, and the real Live Map's hover text and a real deployment were not exercised
(`docs/assets/surface_rehearsal_result.md`, `AM5-W05`, `AM-C07` are `INCONCLUSIVE`).

## Terrain borders (D19)

Border masks (`border.*`) and the fringes they draw are `decorative`: the fringe adds look between two terrains and carries no fact. A missing, corrupt or unavailable mask leaves no fringe for that piece
(a missing inner-corner mask falls back to its two edges), which is exactly the hard edge the map showed before borders existed. The role's preserved fact, "this cell is X", is protected twice: a fringe covers
at most the outer 4 px of a 16 px cell, enforced by the compositor whatever a mask holds, so the cell centre always shows its own terrain; and built terrains (`crisp`) get no fringe at all.

## Colour vision: an open risk against `identifying`

The fallback for terrain is the flat fill, and terrain types are told apart by flat hue. So a pair of fallbacks that are hard to tell apart is a safety question for the `identifying` class, not
a style note. The known findings, all open and none resolved here:

- Even the flat fills are close under some vision types. The smallest differences between flat fills, simulated for protanopia, deuteranopia and tritanopia, include `terrain.lava` / `terrain.jungle`
  (dE 0.8, protan), `terrain.forest` / `terrain.desert` (1.5, deutan) and `terrain.forest` / `terrain.volcanic` (2.8, protan)
  (`agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET/cvd_pairs.txt`).
- The 22 unadopted terrain drafts of set `terrain-v1` have 30 pair-and-vision cases that are more than 2.0 dE closer than the flat fills and under dE 10, the worst involving
  `terrain.dungeon_entrance` (the same file). These are drafts, not shipped art; the finding is that adopting them as they are would make some pairs harder to tell apart than the fallback is.
- `AM5-W05` for the one adopted tile is `INCONCLUSIVE` for the same reason: terrain types are told apart by hue on the normal map, and Forest and Desert are nearly identical under deuteranopia
  with the fill as well (`docs/assets/surface_rehearsal_result.md`).

Palettes are not fixed here. A class definition cannot make a hue-only distinction safe; it can only require that the non-hue alternative (the hover text, a pattern, a label) exists.

## Failure policy

**At runtime, as built.** Each failure resolves to a typed result and the caller draws the alternative; none throws or draws another thing's look
(`frontend/src/visualAssets/resolver.ts::resolveVisual`, reasons `unknown_key`, `missing_image`, `decode_failed`, `manifest_invalid`, `late_result_dropped`).

| Failure | Built behaviour |
|---|---|
| Key not in the manifest | typed `unknown_key` fallback, no fetch, no registration |
| Image missing from the build, corrupt or wrong size | typed fallback, never a partial image |
| Image still loading | the terrain cell shows the flat fill (the synthetic rehearsal scene draws the cell empty); never a stale image |
| Late completion for a superseded release | dropped and recorded; the newer view shows only its own images |
| Invalid manifest | every key resolves `manifest_invalid` |
| Recall (key removed from a release) | the key is absent, so the cell shows the alternative |

**At activation: not built.** Under Profile A (`docs/architecture/visual_asset_foundation_adr.md`, D8) activation is the reviewed frontend deployment, and nothing asks, at that point, whether a key has its
alternative. What is built is narrower: `assemble_release` refuses a registry key that is not `optional` and has no artifact (`visual_assets/store/release.py::assemble_release`, code
`key_without_artifact`). That is an artifact requirement, not a fallback requirement. `GAP` for later, not a requirement this page meets.

**Gaps against this framework, none fixed here:**

- The registry has no class field, so a key does not declare its class (`visual_assets/store/contracts/definitions.py::VisualKeyDefinition`; `AM1-W02` safety-class link).
- No check refuses a release, a build or an adoption whose `identifying` or `critical` key has no named alternative.
- No `critical` key exists, and the HUD has no fallback or text contract at all; the HUD package owns that.
- The family glyph fallback is not wired into the real Live Map.
- No fail-closed rule exists for an image that decodes but is the wrong thing; integrity is the build and `verify` (D9), and the client checks decoded size only.

## Rule for new kinds

Approved policy for entities, buildings, items and UI when they are unparked. No schema field is added by this page.

1. Every new visual key declares one class (`decorative`, `identifying` or `critical`) before its first adoption, in the ticket that introduces the key, until the registry can carry it.
2. An `identifying` key names its non-image alternative before adoption: the primitive that carries the fact and the text that names it.
3. A `critical` key names a text or HUD alternative that works with no image at all, and that alternative is reviewed by the owner of the surface it appears on.
4. A `decorative` key must sit on a declared default or on an `identifying` base, so its failure leaves a readable cell. A detail or variant value is the usual case (rule 5).
5. A detail or variant value is `decorative` over its key. Its failure falls back to the key's default value, and that default carries the key's own class, so a value can never weaken what the key preserves.
6. A class is a statement about information, not about art quality: a beautiful image of a `critical` fact is still `critical`.

## Not decided here

Adding a class field to the registry, requiring alternatives at activation, a HUD alternative, and the colour-vision risk are owner decisions or later tickets. They are
listed in the register's follow-ups (`docs/assets/m1_contract_register.md`).

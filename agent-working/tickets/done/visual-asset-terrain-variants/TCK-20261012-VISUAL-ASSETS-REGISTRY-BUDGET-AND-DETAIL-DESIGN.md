---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN
phase: done
date: 2026-10-12
tags: [architecture, testing]
---

# TCK-20261012-VISUAL-ASSETS-REGISTRY-BUDGET-AND-DETAIL-DESIGN

## Title
Terrain variants: MAX_REGISTRY_BYTES budget review and the design for a detail axis on keys that already have adopted art

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Child 1 of `TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS`. budgets.md's standing rule: the registry's realistic maximum is about 90 % of `MAX_REGISTRY_BYTES`, and the next growth of the key schema needs a budget review first (lead: first step).

## Scope
- **Budget review:** re-measure the registry at the realistic maximum with this batch's shape (detail axes on 7 keys, 3 aliases), using the method in budgets.md's `MAX_REGISTRY_BYTES` row: bytes and load time. Also measure the worst legal case (`MAX_DETAIL_KEYS` 64 x `MAX_DETAIL_VALUES` 16 plus `MAX_ALIASES`) again on today's code. Write a dated note on the budgets.md rows; change no bound. If a measurement exceeds a bound or the 2 s line, STOP.
- **Design (planner gate, before any registry edit):** what adding a `detail` axis to a key that already has an adopted source does to:
  1. its existing adoption (no `detail_value`, so it resolves to the axis `default`): name the default `base` so the current art stays the default;
  2. its slot identity in rc-0009 and in a new candidate (key, None) vs (key, base): is rc-0009's entry for that key byte-identical in rc-0010, or does it re-anchor?
  3. `pickDetail` in the client rehearsal and the sample-map renderer (the FNV pick over the values).
  4. the runtime manifest's `details` block size.
  Write the answer as a design note with code citations; send it to asset-planner before child 2.
- If the design needs a store-code change (e.g. a detail axis cannot be added to an adopted key), STOP: that is an owner question, not part of this batch.

## Out of Scope
- No `src/` or `frontend/` change: the client's colour-by-name and the V2 vocabulary dedupe are rpg's (#523). No activation.
- No new terrain KEY: V2 names reach existing art through aliases; a new key needs an owner decision outside this batch.
- No connecting tiles, no multi-tile structures, no map markers (A comes after this batch, following V2 kind names as the presenter emits them).
- No bound raise, no store or drawing-tool code change unless child 1 proves one is needed: then STOP, it is its own owner question.
- `PLAIN` vs `plain` is not resolved here: one alias covers both while rpg dedupes.

## Acceptance Criteria
- [ ] Measurements recorded against the bounds and the 2 s line, no bound changed.
- [ ] The design note answers 1-4 with code citations; asset-planner approved it.

## Related Tickets
- Parent: `TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS`

## Related Docs
- `docs/assets/sample_map/gap_report.md` (G1-G4, G12, the alias table), `docs/assets/budgets.md` (`MAX_REGISTRY_BYTES`, `MAX_DETAIL_KEYS`, `MAX_DETAIL_VALUES`), `docs/assets/store_contract.md` (registry, detail axis, known gap: a registry edit makes older candidates unexportable), `docs/assets/pixel_art_technique.md`, `docs/assets/pilot_terrain_key.md` (the forest detail axis precedent)
- GitHub #523 (V2 vocabulary, owner answer), #519

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT/`, `agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT/` (if present: the detail axis contract)

## Related Code Areas
- `visual_assets/store/catalog/registry.py`, `visual_assets/store/contracts/definitions.py`, `visual_assets/store/{release,runtime_export,adoption,setadoption}.py`, `frontend/src/visualAssets/` (read only), `tools/visual_assets_sample_map_render.py`

## Assumptions / Open Questions


## Implementation Notes
- DESIGN NOTE (approved by asset-planner 2026-10-12; the owner answered the two open questions it raised, asked directly with neutral options):
  1. Existing adoption: untouched, no re-adoption. `AdoptionRecord.detail_value` stays None and `VisualKeyDefinition.effective_detail(None)` returns the axis default (`visual_assets/store/contracts/definitions.py:96-100`), so `adoption.check_slot` and `records.slot_holders` (`records.py:216-229`) see the old source holding `(key, "base")`; the new slots `(key, v1..)` are free. Same mechanism that kept the pilot forest adoption valid (`TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT`).
  2. Slot identity: `release.py assemble_release` builds `slots = [None] if definition.detail is None else sorted(values)`, so a key with an axis gets entries with `detail="base"`; `ReleaseEntry.detail` is dropped from the JSON when None, so rc-0009's entry (no `detail`) and rc-0010's (`"detail":"base"`) differ in bytes, with the same `artifact_id` and `pixel_hash`: 6 of rc-0009's 73 entries (grassland, mountain, cave, ruins, swamp, shallow_water; road has no axis) are re-anchored; the other 67 stay byte-identical. Precedent: `terrain.forest`, rc-0001 (no detail) -> rc-0002 (`"detail":"plain"`), same artifact and hash. OWNER ANSWER (2026-10-12): "Accept detail: base". Child 4's guard pins exactly: the 67 others byte-identical, the 6 equal to their rc-0009 entry plus `detail: base`, no more.
  3. `pickDetail` and the sample-map renderer: no code change. The pick is `fnv1a32("key|x|y|seed") % len(declared values)` over the manifest's declared order (`frontend/src/visualAssets/pickDetail.ts`, ported in `tools/visual_assets_sample_map_render.py`); `[base, v1..vN]` asks for `base` on about 1/(N+1) of the cells, and a declared value with no art falls back to the default value's image (`resolver.ts`, ported as `Release.tile`), so declaring the axis before the art exists changes no pixel. Adding a value later reshuffles only that key.
  4. Runtime manifest `details` block: 310 B for 4 keys today (`runtime_export.py` copies the declared values from the registry); about 481 B more for the 6 new axes; the estimated rc-0010 runtime manifest is about 22.7 KB (4.3 % of `MAX_MANIFEST_BYTES`).
- SECOND FINDING (for child 2; owner answer: "Registry-only aliases"): registry aliases have no runtime consumer. `Registry.resolve` follows one alias, but the only caller of `aliases` outside the loader is `visual_assets/review/key_usage.py:85-86` (a report); `release.py`, `runtime_export.py`, the runtime manifest contract and the client (`frontend/src/visualAssets/manifest.ts`, `resolver.ts`) carry none. The aliases are added as the documented mapping shown by `key-usage`; the client or rpg maps V2 names onto keys itself at activation (#523). Child 2 states this as a Known gap in `store_contract.md`; the sample-map re-render (child 4) may resolve names through `Registry.resolve` because it is an offline tool, and its page and gap report say the live client does NOT.
- Budget review (measured on today's code, real loader, no bound changed; full table in `docs/assets/budgets.md` "Registry re-measurement for the terrain-variants batch (2026-10-12)"): registry committed 29,374 B (6.4 %), this batch's shape 29,852 B (+478 B, 6.5 %), load about 0.06 s; worst legal case 1,024 keys + 1,024 aliases + 64 detail axes of 16 values 367,838 B (80.2 %) at 1.012 s; 1,601 keys of today's shape reach the byte bound (454,442 B) at 1.036 s; a 1,024-entry manifest with 32-character details 337,129 B, parse 0.005 s. All under every bound and the 2 s line.
- CORRECTION to the real-art batch's docs: the registry was recorded as 29,525 B; the committed file is 29,374 B (the measurement preceded asset-planner's shortening of the three descriptions). Corrected in the `budgets.md` row and the sample-map gap report; the closed real-art tickets keep their wording as history.
- Measurement tool refresh (`tools/visual_assets_measure_budgets.py`, an asset tool; no store code): `registry_scaling`, `registry_at_byte_bound` and `manifest_scaling` no longer ran on today's loader. Their synthetic keys used `variant_axes` (refused since D17, only the detail axis exists), had no `safety_class` or `fallback` (required, AM1-W02.7), and `manifest_scaling` went to 4,096 entries (over `MAX_VISUAL_KEYS` 1,024). They now build keys through `_legal_keys` (class and glyph-and-text fallback on every key, an optional `detail` axis) and the manifest sizes are 256 to 1,024 entries with a 32-character `detail`; the `registry_scaling` rows are 0 or 64 detail keys of 16 values.
- No registry edit, no store or drawing code change, no bound change. A first design question (the re-anchor, lead's condition 2) and a second (aliases) were sent to asset-planner and answered by the owner before this commit.

## Test Summary
Measurement runs (`python -m tools.visual_assets_measure_budgets --only registry_scaling|registry_at_byte_bound|manifest_scaling`, 2 GB cap) and a scratch load of the real registry with the 6 axes and 3 aliases added textually to a temp copy (not committed). `tests/visual_assets/test_budgets_parity.py` 6 passed (the new section does not touch the `Bounds` table).

## Files Changed
- `docs/assets/budgets.md` (dated re-measurement note, the 29,374 B correction), `docs/assets/sample_map/gap_report.md` (the corrected figure), `tools/visual_assets_measure_budgets.py` (generators to today's legal shape)

## Completion Summary
DONE `e2f3565e4`. Budget review (registry 29,374 B corrected, worst legal case 80.2 % at 1.0 s) and the detail-axis design note, approved by the planner; the owner answered both open questions. No registry edit, no bound change.


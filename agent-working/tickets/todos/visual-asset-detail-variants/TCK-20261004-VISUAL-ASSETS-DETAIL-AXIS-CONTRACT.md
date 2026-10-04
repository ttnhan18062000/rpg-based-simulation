---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT
phase: open
date: 2026-10-04
tags: [architecture, determinism, mcp]
---

# TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT

## Title
A declared decorative detail axis on a visual key: one adopted artifact per value, carried through adoption, release candidate and runtime manifest

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
First child of `TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS`. Replace the stated limit "one visual key maps to
one artifact" (`visual_assets/store/release.py` docstring, `docs/assets/store_contract.md`) with a declared, bounded
**detail axis**, without breaking the pilot's adopted `terrain.forest` (adoption `ad-caf09a15bd89d2af`, release
`pilot/rc-0001`). Contract only: no picking, no new art.

## Scope
Planner's design (deviate only after telling the planner why):
- **Registry.** A separate optional field on `VisualKeyDefinition`, not a `variant_axes` entry:
  `detail: DetailAxis | None = None`, `DetailAxis = {values: tuple[AxisValue, ...] (1..MAX_AXIS_VALUES, unique),
  default: AxisValue (must be one of values)}`. Reason for the ADR row: `variant_axes` are context-selected axes with
  strict precedence (proposal 9.2: scale/state/contrast/motion); detail is the only axis picked by a coordinate hash and
  the only one with a mandatory default, so overloading `variant_axes` with a reserved name would hide that difference.
  `variant_axes` stays as it is (still unused).
- **Adoption.** `AdoptionRecord.detail_value: AxisValue | None = None`. `None` means "the key's declared default value"
  (or the key itself when it has no detail axis). This is what keeps the pilot adoption valid with no re-adoption. The
  `adopt` CLI gains `--detail <value>`; refused (stable codes) when the key has no detail axis or the value is not
  declared. Explicit `--detail <default>` and `None` are the same slot.
- **Holding.** A slot is `(visual_key, effective detail value)`. `key_holders`, the `visual_key_taken` adoption refusal
  and the release's `ambiguous_key` check work per slot, not per key.
- **Release candidate.** `ReleaseEntry.detail: AxisValue | None` (None only for a key without a detail axis). Entries
  unique per slot, sorted by `(visual_key, detail)`. A non-optional key with a detail axis needs its default value's
  artifact (else `key_without_artifact`); other values are optional (the client falls back to the default).
- **Runtime manifest.** `RuntimeEntry.detail` as above, plus `RuntimeManifest.details`: one
  `{visual_key, values, default}` per key that declares an axis, copied from the registry, so the client picks over the
  **declared** values (adding art for an already-declared value never reshuffles the map; only changing the declaration
  does). The client parser `frontend/src/visualAssets/manifest.ts` mirrors every new rule in this ticket so the tree
  stays green (strict, unknown fields rejected).
- **Bounds (owner decision 2026-10-04, blocking question, after the implementer's measurement).** `MAX_AXIS_VALUES` does
  not bound the detail axis. New bounds in `visual_assets/store/config.py` + `docs/assets/budgets.md`, rows
  `APPROVED 2026-10-04` (owner): `MAX_DETAIL_VALUES = 16` (values per key's detail axis) and `MAX_DETAIL_KEYS = 64`
  (keys declaring a detail axis per registry); `MAX_MANIFEST_BYTES` raised from `6 * 64 KiB` (393216) to `8 * 64 KiB`
  (524288). Measured basis: widest runtime manifest today 359764 B; per-entry `detail` adds about 45056 B at 1024
  entries; the `details` block at the new bounds is about 48 KB; total about 453 KB. Total manifest entries (all slots)
  stay at most `MAX_VISUAL_KEYS`. The client parser mirrors all three. Re-measure the widest legal candidate and runtime
  manifest in `test_record_bounds.py` and their parse cost (the R rules in `budgets.md`); record the measured values in
  the budget rows. If the measurement still exceeds 524288 B or the cost rules, stop and tell the planner again.
- **Schema version.** No version bump: every new field has a default, old records parse unchanged, and strict clients
  reject the new fields (fail closed). Record this in the ADR row. `verify` learns the new rules (unknown detail value,
  duplicate slot, a manifest entry whose value the registry does not declare).
- **Docs.** `docs/assets/store_contract.md` (limit replaced, not silently broken), an ADR row in
  `docs/architecture/visual_asset_foundation_adr.md`, `docs/assets/budgets.md` budget note, deviations list in
  `docs/plans/visual-asset-foundation/README.md` if it states the old limit.
- Declare the axis on `terrain.forest` in `visual_assets/catalog/definitions/visual_keys.yaml`
  (`values: [plain, bush, tree]`, `default: plain`) **only if** the existing release and runtime fixture stay valid; the
  pilot fixture is regenerated only by ticket 3 (a new release), never edited by hand.

## Out of Scope
- `pickDetail`, resolver fallback, pilot scene (ticket 2). New art, adoption, `pilot/rc-0002` (ticket 3).
- Any change to `src/`, the API, world generation or the normal Live Map.

## Acceptance Criteria
- [ ] The one-key-one-artifact statement is replaced in code docstrings, `store_contract.md` and the ADR (row with the separate-field and no-version-bump decisions).
- [ ] The committed pilot adoption, `pilot/rc-0001` and its runtime export still parse and `verify` is clean; the pilot adoption fills the `plain` slot (test).
- [ ] Tests: adopt with a declared / undeclared / no-axis detail value; a second holder of the same slot refused, of a different slot accepted; release needs the default slot, not the others; entries unique and sorted per slot; total entries bounded by `MAX_VISUAL_KEYS`.
- [ ] Python and TS manifest parsers accept and reject the same cases (shared cases or mirrored tests).
- [ ] `test_record_bounds.py` covers the widest legal manifests with detail fields under the new bounds; `budgets.md` rows for `MAX_DETAIL_VALUES`, `MAX_DETAIL_KEYS` and the raised `MAX_MANIFEST_BYTES` carry measured values and `APPROVED 2026-10-04`; the budget parity test passes.

## Related Tickets
- TCK-20261004-VISUAL-ASSETS-TERRAIN-DETAIL-VARIANTS (epic), TCK-20261004-VISUAL-ASSETS-PILOT-TERRAIN-TILE

## Related Docs
- docs/assets/store_contract.md, docs/assets/budgets.md, docs/architecture/visual_asset_foundation_adr.md
- docs/brainstorm/render-and-art/asset_management_and_runtime_integration_proposal.md §9.2, §9.3

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261003-VISUAL-ASSETS-RUNTIME-MANIFEST/

## Related Code Areas
- visual_assets/store/contracts/{definitions,adoption,release,runtime}.py, visual_assets/store/{adoption,release,runtime_export,records,verify,cli}.py
- visual_assets/catalog/definitions/visual_keys.yaml, frontend/src/visualAssets/manifest.ts, tests/visual_assets/

## Assumptions / Open Questions
- Changing a key's declared `default` after adoptions exist re-binds every `None` adoption to the new default; the release lists the explicit value per entry, so the effect is visible. Accepted; no lock is added.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

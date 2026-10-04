---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT
phase: done
date: 2026-10-04
tags: [architecture, determinism, mcp]
---

# TCK-20261004-VISUAL-ASSETS-DETAIL-AXIS-CONTRACT

## Title
A declared decorative detail axis on a visual key: one adopted artifact per value, carried through adoption, release candidate and runtime manifest

## Status
DONE

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
- [x] The one-key-one-artifact statement is replaced in code docstrings, `store_contract.md` and the ADR (row with the separate-field and no-version-bump decisions).
- [x] The committed pilot adoption, `pilot/rc-0001` and its runtime export still parse and `verify` is clean; the pilot adoption fills the `plain` slot (test).
- [x] Tests: adopt with a declared / undeclared / no-axis detail value; a second holder of the same slot refused, of a different slot accepted; release needs the default slot, not the others; entries unique and sorted per slot; total entries bounded by `MAX_VISUAL_KEYS`.
- [x] Python and TS manifest parsers accept and reject the same cases (shared cases or mirrored tests).
- [x] `test_record_bounds.py` covers the widest legal manifests with detail fields under the new bounds; `budgets.md` rows for `MAX_DETAIL_VALUES`, `MAX_DETAIL_KEYS` and the raised `MAX_MANIFEST_BYTES` carry measured values and `APPROVED 2026-10-04`; the budget parity test passes.

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
- Hard stop first: before building, the widest legal runtime manifest measured 404820 B with a `detail` on every entry (11604 B over the 393216 B bound) and the `details` block at `MAX_AXIS_VALUES` (64) could reach about 2.3 MB. The planner took it to the owner, who raised `MAX_MANIFEST_BYTES` to 524288 and set `MAX_DETAIL_VALUES` 16 and `MAX_DETAIL_KEYS` 64 (2026-10-04). Measured at the new bounds: runtime 451552 B (parse 0.008 s), candidate 337137 B (0.003 s), registry with 64 detail keys 431326 B (loads in 1.52 s, under the R3 2 s line and `MAX_REGISTRY_BYTES`).
- Design as the ticket says: `DetailAxis` on the key, `AdoptionRecord.detail_value` (`None` = the key's default), slots per `(key, effective value)` in `records.slot_holders` (replaces `key_holders`), release and runtime entries, `RuntimeManifest.details`, TS mirror, ADR D11, `store_contract.md`, `budgets.md`.
- Byte stability without a version bump: `detail_value`, `detail` and an empty `details` are omitted from the serialised bytes when absent (`drop_absent`, a wrap serializer per record), so every committed record, the rehearsal and pilot fixtures and the committed registry round-trip byte-identically. The TS parser treats an explicit `null` detail as absent, as the Python model does.
- New refusal codes: `detail_not_declared`, `unknown_detail_value` (adopt); `undeclared_detail` (release); `ADOPTION_UNKNOWN_DETAIL`, `MANIFEST_UNKNOWN_DETAIL` (verify). A manifest entry WITHOUT a detail value is tolerated for a key that now declares an axis (the candidate predates the declaration, and ticket 3 declares the axis on `terrain.forest` after `rc-0001`); an optional key may omit its default slot (the ticket required the default only for non-optional keys).
- The registry is NOT declared on `terrain.forest` here: that changes `registry_hash`, so `rc-0001` could no longer be exported and the pilot fixture would break; ticket 3 does it with the new release.
- Two existing tests were adjusted on purpose: `RuntimeManifest`'s field allow-list gained `details` (and `detail` on the entry), and a readmodel test's synthetic entries are now zero-padded so they are sorted (the new candidate sortedness rule).
- Parity of the two parsers: `frontend/src/visualAssets/__fixtures__/detail_cases.json` (26 cases) is decided by both `parse_record(RuntimeManifest)` and `parseManifest`.

## Test Summary
`tests/visual_assets`: 1258 passed (real Aseprite is local; run under a 2 GB cap). New: `test_detail_axis.py` (24 + 26 shared cases), bounds for the widest manifests and registry with detail fields. Frontend: `vitest src/visualAssets` 115 passed, `tsc -b` and `eslint src/visualAssets` clean. `verify` on the committed catalog: store ok; runtime fixtures `--check`: current.

## Files Changed
- visual_assets/store/{config,records,release,runtime_export,verify,adoption,cli,readmodel}.py, catalog/registry.py, contracts/{base,definitions,adoption,release,runtime}.py
- frontend/src/visualAssets/manifest.ts, __tests__/manifest.test.ts, __fixtures__/detail_cases.json (new)
- tests/visual_assets/store/unit/{test_detail_axis (new),test_record_bounds,test_runtime_contract,test_readmodel}.py, store/adoption_support.py
- docs/assets/{store_contract,budgets}.md, docs/architecture/visual_asset_foundation_adr.md (D11), docs/plans/visual-asset-foundation/README.md

## Completion Summary
A key may now declare a bounded decorative detail axis; one adopted artifact per declared value flows through adoption, holding, release candidate, runtime manifest (`details`) and the client parser, with no schema bump and no change to any committed record or fixture. The pilot adoption fills the `plain` slot of such a key unchanged. No picking, no art (tickets 2 and 3).

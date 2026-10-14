---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-FIXTURE-GUARD-DECOUPLING
artifact_type: plan
date: 2026-10-08
tags: [architecture, testing]
---

# Plan: fixture guards stop riding the current release candidate

## Probe (measured, not assumed)
A throwaway icon key was appended to `visual_keys.yaml` (then reverted) and `pytest tests/visual_assets tests/static tests/docs` run: 10 failures.
- **Rc-coupled (this ticket):** `test_pilot_fixture::test_the_committed_pilot_export_equals_the_forest_slots_of_a_fresh_export_of_the_release`, `test_terrainset_fixture::test_the_committed_terrainset_export_equals_a_fresh_export_of_the_current_release`. Both call `export_runtime("pilot", "rc-0007", ...)`, which the store refuses (`registry_mismatch`) once the registry hash moves.
- **Inventory pins (not touched, by design):** `test_registry` (exact key list), `test_icon_draft_set`, `test_icon_recognition`, `test_icon_set_adoption`, `test_icon_specs` (x2), `test_icon_v2_keys` (x2). They assert WHICH keys exist; adding a key is a deliberate registry decision that must update them. No rc is involved, so they never forced a candidate.

## Before / after of what each guard checks
| Guard | Before | After |
|---|---|---|
| pilot check 1 | fresh `export_runtime(pilot, rc-0007)`; fixture's 3 forest entries+details equal the fresh ones; only `release_id`, `registry_hash`, `candidate_manifest_hash` differ; dir holds exactly 3 PNGs + manifest; PNG bytes equal fresh | a manifest DERIVED from the stored candidate rc-0007 and the artifact files (no export, no registry-hash check): the 3 forest entries and PNG bytes equal what the candidate+artifacts give; details equal the CURRENT registry's declared values for terrain.forest; dir holds exactly 3 PNGs + manifest; the `changed fields` clause is dropped (nothing is compared to a fresh export any more) |
| pilot check 2 (vs rc-0004 stored) | unchanged | unchanged |
| terrainset | fresh `export_runtime(pilot, rc-0007)` equals the committed dir file for file | derived manifest of the stored rc-0007 + artifact PNGs equals the committed `runtime_manifest.json` (all fields: ids, hashes, entries, details, fallback version, canonical JSON bytes) and every PNG equals the artifact file byte for byte; the dir holds nothing else |
| store `registry_mismatch` refusal | `test_runtime_export.py:150` | unchanged, and still the only place a candidate's registry hash is compared to the live registry |
| NEW drift guard | none | in the hermetic fixture catalog (`runtime_fixture`), the derivation helper's manifest + files equal `export_runtime`'s output byte for byte, so the helper cannot drift from the store |
| NEW decoupling proof | none | a test catalog with a throwaway key registered: `export_runtime` of the old candidate is refused (`registry_mismatch`, store unchanged) while the derived-manifest guards still pass |

## Design choice (alternatives weighed)
1. **Derive from the stored candidate (chosen):** keeps every substantive assertion (slots, details, bytes, hashes) and never calls the refusing function; one ~20-line helper in `tests/visual_assets`, proven equal to `export_runtime` by the drift guard. No store change.
2. Export ignoring only registry-hash fields (as icondraft does): needs a parameter or a patch on `export_runtime`, weakening or forking the store's refusal path; rejected.
3. Stop checking the fixture: rejected (weakens what is asserted).

## Mutants
a flipped PNG byte in the fixture; a dropped slot; a changed entry (detail); a changed `registry_hash` field in the fixture; helper-drift (helper omits a field) -> the drift guard fails; and the probe: registering a key no longer fails either guard.

## Out of scope
No `src/`, no wiring, no new candidate, no change to the inventory pins, the store, or any recorded result.

## Planner approval (2026-10-08, cross-session message)
Approved: derive from the stored candidate, no export call; the store's `registry_mismatch` refusal untouched and the only live-registry comparison; the drift guard is the key piece; inventory pins stay untouched by design (deliberate decisions, not rc coupling); options 2 and 3 rightly rejected. Added: assert each artifact PNG decodes to the candidate's recorded pixel hash (done directly in `derived_runtime.derive`; `store verify` guarantees it transitively via `verify._check_entry` and the artifact-record hash check, cited in the module docstring) plus a mutant for it (M6).

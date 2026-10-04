---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-04
tags: [architecture, documentation, testing]
---

# `AM-M2` evidence charter (`AM1-W11`)

**Status: APPROVED 2026-10-04.** Written by `TCK-20261004-VISUAL-ASSETS-M2-EVIDENCE-CHARTER`. The owner approved it on 2026-10-04 in a blocking question, answering "Approve, with the rerun rule (Recommended)"
(relayed to the implementer by asset-planner), which includes the prior-evidence rule below as proposed; the alternative (counting old results as they stand) was declined. Approving the charter **authorizes nothing else**: it does not
authorize running `AM-M2`, adding a fixture or test, or any code change, and `AM-M2` stays `BLOCKED` (`AM-M1` is not `PASS`, no implementation authorization exists). The register records the `AM1-W11` rows
(`docs/assets/m1_contract_register.md`).

Why it exists: `AM-M2` (`docs/plans/visual-asset-management-runtime-integration/02_synthetic_contract_harness_plan.md`) lists `AM1-W11`, an approved evidence charter, as a prerequisite, and `AM1-W11` asks that
synthetic fixtures, supported conditions, exact gate setup, retained evidence and allowed conclusions are predeclared. Much of the `AM-M2` harness was in effect built by the foundation and hardening batches on
synthetic fixtures, without a charter declared first. This page declares it now, says what exists, what is missing, and what a run may and may not conclude. No `AM-M2` result record exists.

## Where `AM-M2` stands today

| Prerequisite in the plan | State |
|---|---|
| `AM-M1` `PASS` (`AM-C01`, profile, contracts, owners, budgets, approved evidence charter) | Not `PASS`: the register shows `PARTIAL`/`OPEN` items (this charter is approved) |
| Separate implementation authorization through the normal ticket workflow | None |
| Synthetic roots isolated from production assets and manifests | Partly: synthetic fixtures use the reserved `fixture.*` namespace and live apart from the catalog's real key (below) |
| No `CAP-A`, `CAP-B`, Aseprite, manual-art result or real candidate needed | Holds for the tests named below; the Aseprite-needing tests are excluded from `AM-M2` |

So a run today would be `BLOCKED` as a whole (plan, "Result classification"): the prerequisites are absent, not failed.

## Supported conditions

What an `AM-M2` run may claim to cover, and nothing wider.

- **Python:** the `tests/visual_assets` suite as CI runs it (`pytest tests/visual_assets -m "not slow and not extra_slow"`, the `api-tools` job in `.github/workflows/test.yml`). Tests marked `needs_aseprite` are local-only evidence (ADR D10) and do not count toward `AM-M2`.
- **Frontend:** `vitest run` over `frontend/src/visualAssets/__tests__/` (jsdom). No browser is required for `AM-M2`; a browser capture is `AM-M5` evidence and is not claimed here.
- **Deployment profile:** Profile A (ADR D8). Profile B behaviour (bootstrap, pointer, cache fencing) does not exist and is not tested.
- **Clients:** none declared. `AM-M2` makes no supported-client claim; that declaration is the charter signature's job in `AM-M6` (`docs/assets/pilot_charter_am6.md`).
- **Fixtures:** synthetic only (next section). The pilot fixture (`frontend/src/visualAssets/__fixtures__/pilot/`, `terrain.forest`) and the draft fixtures are real-key material and are excluded.

## Synthetic fixtures

Fixtures an `AM-M2` run may use. All are committed, use the `fixture.*` key namespace (rejected by the loader without an explicit flag), and contain no real art.

| Fixture | Path | What it is |
|---|---|---|
| Record fixtures, one per record type | `visual_assets/catalog/fixtures/contracts/` (`*.json`, `visual_keys.fixture.yaml`) | Valid synthetic instances; parser and registry tests mutate them |
| Rehearsal runtime export | `frontend/src/visualAssets/__fixtures__/rehearsal/` | Three `fixture.rehearsal.*` keys (a diamond, a disc, a hollow frame), their PNGs and `runtime_manifest.json`; equals a fresh regeneration (`tests/visual_assets/store/runtime_fixture.py`, `tests/visual_assets/store/unit/test_runtime_fixture.py`) |
| Detail cases shared by both languages | `frontend/src/visualAssets/__fixtures__/detail_cases.json` | Golden cases for the detail pick and parsing |
| Builders | `tests/visual_assets/store/builders.py` | Synthetic catalog trees for `gc`, `verify` and release tests |

## Per deliverable: what exists, what is missing, the allowed conclusion

"Allowed conclusion today" is what a run on the coverage below may claim. It uses the plan's classes: `PASS` (valid evidence satisfies every stated condition), `FAIL`, `BLOCKED`, `INCONCLUSIVE` (it ran, but
coverage or evidence is insufficient). A missing result is never a pass.

| ID | Exists today (paths resolve on this branch) | Missing | Allowed conclusion today |
|---|---|---|---|
| `AM2-W01` Finite semantic fixture set | Valid and unknown keys: `tests/visual_assets/store/unit/test_registry.py` (`test_fixture_registry_loads_with_the_flag_and_only_with_it`, `test_resolve_unknown_raises_and_registers_nothing`); malformed keys: `tests/visual_assets/store/unit/test_identities.py` (`test_identities_never_normalise`, `test_visual_key_length_bound`); aliases and cycles: `test_registry.py::test_alias_problems_are_rejected` (an alias of an alias and a missing target are rejected, so a cycle cannot load); variants: `tests/visual_assets/store/unit/test_records.py::test_registry_record_rejects_bad_axes`; cardinality: `test_registry.py::test_count_bounds` | Nothing resolves `variant_axes`, so variant precedence has no fixture; no test shows that diagnostics stay bounded for hostile input (the store's unknown-key message echoes the caller's key) | `INCONCLUSIVE`: determinism and bounds hold for what exists, but variants and bounded diagnostics are not established |
| `AM2-W02` Strict contract parser | `tests/visual_assets/store/unit/test_records.py` (duplicate keys, unknown fields, wrong version, oversize, non-finite numbers, type confusion); `tests/visual_assets/store/unit/test_runtime_contract.py`; client: `frontend/src/visualAssets/__tests__/manifest.test.ts` (rejection table, duplicate key `JSON.parse` would collapse, entry bound); hash encoding: `tests/visual_assets/store/unit/test_identities.py::test_file_hash_and_pixel_hash_are_not_interchangeable` | The client reader has no input byte bound (it bounds entries, details and dimensions, not text length), so "reject before allocation" is shown for Python only | `INCONCLUSIVE` for the client side; `PASS` only if the client gains a bound and a test, or the owner narrows the clause to the Python parser |
| `AM2-W03` Deterministic resolver harness | `frontend/src/visualAssets/__tests__/resolver.test.ts` (unknown key resolves with no fetch, prototype-chain and path-like keys), `frontend/src/visualAssets/__tests__/detail.test.ts` (picked, then default, then fallback), `frontend/src/visualAssets/__tests__/pickDetail.test.ts` (golden vectors) | Precedence is exact only for the detail axis; no context-axis precedence exists to test (register `W03.1`) | `INCONCLUSIVE` unless the owner declares context axes out of scope for `AM-M2`, then `PASS` for the detail axis alone |
| `AM2-W04` Fallback-safety fixtures | `frontend/src/visualAssets/__tests__/fallback.test.ts`, `frontend/src/visualAssets/__tests__/scene.test.ts`, `frontend/src/visualAssets/__tests__/pilotScene.test.ts` (image missing, corrupt, wrong size, loading, late, unknown key, invalid manifest) | The classes are approved (`docs/assets/fallback_safety.md`) and the terrain fixtures follow the `identifying` class, but the registry class field, any `critical` key, a HUD alternative and the cache and animation failures do not exist | `INCONCLUSIVE`; today's evidence is contributing evidence toward `AM-C07` only |
| `AM2-W05` Snapshot/cache harness | `frontend/src/visualAssets/__tests__/loader.test.ts`, `frontend/src/visualAssets/__tests__/rollbackDrill.test.ts` (mid-load switch drops the superseded release's late images) | No cache exists, so cache keys have nothing to test; decoded-resource disposal is not asserted as a property | `INCONCLUSIVE`: single-generation pinning and late loads are shown; cache and disposal are not |
| `AM2-W06` Compatibility/rollback harness | `frontend/src/visualAssets/__tests__/rollbackDrill.test.ts` (new/old client x new/old release, recall); incompatible versions: `manifest.test.ts` (`unsupported_version`) | No test that a prior working snapshot stays available after an incompatible manifest is rejected; client range and renderer range do not exist | `INCONCLUSIVE`; a drill, not a real rollback |
| `AM2-W07` Trust/locator negatives | `tests/visual_assets/store/unit/test_runtime_contract.py` (a file that is not a pixel-hash `.png` is rejected), `tests/visual_assets/store/unit/test_pixels.py` (bad CRC, decoded-size and dimension bounds, truncation, every single-byte corruption), `tests/visual_assets/store/unit/test_runtime_export.py::test_an_artifact_that_does_not_match_its_pixel_hash_is_refused`, `frontend/src/visualAssets/__tests__/loader.test.ts` (a file the build does not contain is never fetched; wrong-size image) | Origins, redirects and MIME have no tests because under Profile A the client fetches only its own build's files; the client does not recompute the pixel hash | `INCONCLUSIVE`, or `PASS` for the contract as narrowed by Profile A if the owner accepts that origins, redirects and MIME are out of scope |
| `AM2-W08` Retention/GC dry run | `tests/visual_assets/store/unit/test_gc.py` (dry run changes nothing; tracked state, young intakes, adopted intakes and referenced review evidence survive; only unreachable eligible items listed; unreferenced artifacts reported, never deleted) | Supported-client roots are a deployment fact under Profile A and are not modelled; no `AM-M4` records exist to include | `INCONCLUSIVE`: it reaches the narrowed definition in the pilot charter ("`gc` removes no protected object") and nothing wider |
| `AM2-W09` Evidence bundle | The result-record shape in `docs/assets/surface_rehearsal_result.md` | No `AM-M2` bundle, no named commit, no retained raw output | `BLOCKED` until a run produces one |
| `AM2-W10` Isolation/cleanup proof | `frontend/src/visualAssets/__tests__/isolation.test.ts` (no normal-app import, no fixture or module in the production build), `tests/visual_assets/test_boundaries.py` | No proof that synthetic state can be removed without residue; the rehearsal fixtures are committed | `INCONCLUSIVE`: isolation is shown, removal is not |

## Gate setup

- **`AM-C02` Semantic resolution, in full.** Setup: the fixtures above, the supported conditions above, one named commit with a clean tree. Condition (proposal section 17): every lookup is deterministic, bounded and explainable and
  performs no dynamic fetch or creation from unknown input. `PASS` needs valid retained evidence for every `AM2-W01`..`W03` condition; `FAIL` on any ambiguity, unbounded key or cardinality, cycle, closest-match guess or
  unknown-triggered fetch; `BLOCKED` while the prerequisites or the authorization are absent; `INCONCLUSIVE` when it runs but coverage or diagnostics cannot establish determinism and bounds. On today's coverage `AM-C02` is
  `INCONCLUSIVE` (`W01`, `W03`).
- **Contributing checks only**, toward `AM-C05` (`AM2-W05`), `AM-C06` (`AM2-W06`), `AM-C07` (`AM2-W04`) and `AM-C09` (`AM2-W08`). Each becomes a full gate result only if that gate's complete supported-client, authority and environment
  setup exists; none does (`docs/assets/surface_rehearsal_result.md` classifies all four `INCONCLUSIVE`). A run reports them as "contributing evidence", never as a gate pass.
- `AM-M2` does not pass `AM-C03`, `C04`, `C08`, `C10` or any `CAP` gate, and an `AM-M2` pass is not production readiness.

## Retained evidence (`AM2-W09`)

A run keeps, in a folder named for its ticket under `agent-working/stored_artifacts/`, and summarised in a result record under `docs/assets/` shaped like `docs/assets/surface_rehearsal_result.md` (a per-deliverable table, a per-gate table, the checks run on
one named commit, known gaps stated):

- the commit SHA, with the tree clean before and after, and the environment (operating system, Python and Node versions, the test commands as run);
- the fixture list with their file hashes (the rehearsal manifest's `candidate_manifest_hash` and each PNG's pixel hash);
- raw results: pytest output with counts (including the skipped count), vitest output with counts, the negative-test output;
- per deliverable `PASS`, `FAIL`, `BLOCKED` or `INCONCLUSIVE`, the coverage gaps, and the allowed conclusion actually drawn;
- the reviewer and the date.

Diagnostics in the bundle use bounded categories (finding codes, fallback reasons), not unbounded input values. Mutation proofs follow the project's rule: show the mutant applied at the right site and failed for the right reason.

## Allowed conclusions for `AM-M2` as a whole

- **Today:** `BLOCKED`. The prerequisites `AM-M1` `PASS` and an implementation authorization are absent (this charter is approved).
- **If they existed and the run used today's coverage:** at best `INCONCLUSIVE`, for the reasons in the table. `PASS` additionally needs the missing coverage or an owner narrowing of a clause, decided before the run.
- **Never allowed from `AM-M2`:** a production-readiness claim, an art claim, a full pass of `AM-C05`, `C06`, `C07` or `C09`, or a client-support claim.

## Prior-evidence rule: APPROVED 2026-10-04

**Approved by the owner on 2026-10-04 ("Approve, with the rerun rule (Recommended)"; proposed by the planner).** Evidence produced before this charter was approved may count toward `AM-M2` only if it is rerun unchanged on a named commit after the charter is approved. Reason: a charter
predeclares conditions and conclusions, and it cannot be fitted to results already seen. The existing tests and fixtures are reusable as they are; their old results are not evidence for `AM-M2`. The alternative,
counting old results as they stand, was declined by the owner: it would let existing evidence define what the charter predeclares.

## Not decided here

Whether to close the gaps above by adding fixtures or tests (a separate authorization), and whether to narrow any clause to what Profile A needs are owner decisions. Running `AM-M2`
is a later, separate authorization. Nothing was run for this page.

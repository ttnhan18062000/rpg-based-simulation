---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-NOISE-FILL-DETERMINISM-TEST
artifact_type: investigation
tags: [world, determinism, testing]
---

# Investigation — TCK-20260821-NOISE-FILL-DETERMINISM-TEST

## Current Behavior

### `WorldCompiler.compile()` (`src/worldbuilding/compiler.py`)
- Signature confirmed: `compile(spec, seed, output_report_path=None, context=None) -> tuple[AuthoritativeState, dict]` (`compiler.py:176-182`).
- Region-painting loop (`compiler.py:201-236`): for each `r_spec`, if `r_spec.terrain_variants` is truthy, per-tile terrain is drawn via `rng.weighted_choice(Domain.INIT, tick=0, entity_id=(region_hash ^ tile_offset), seq=[...], weights=[...], sub_id=1)` using a 16-bits-per-axis `tile_offset` encoding; otherwise the tile is flat-filled with `r_terrain = r_spec.terrain`. Both paths write into `terrain: Dict[tuple[int,int], str]`, gated by the existing `0 <= x < width and 0 <= y < height` clamp.
- `terrain` is assembled onto `AuthoritativeState.terrain` (`compiler.py:601`, field defined at `src/core/state.py:1126`) — **not** `RegionState.terrain`. The ticket's AC #1 phrasing ("frozen RegionState.terrain") is imprecise; the actual attribute under test is `AuthoritativeState.terrain`, a world-wide `(x,y) -> str` dict. This does not change the substance of the ACs — the three existing tests already correctly key off `state.terrain[(x, y)]` — but the investigation flags the naming mismatch so it doesn't cause confusion during implementation.
- Report construction (`compiler.py:612-635`): `fingerprint = StateFingerprinter.get_fingerprint(state)`, `state_hash = fingerprint["state_hash"]`, then `report = {..., "state_hash": state_hash}`. Confirmed `report["state_hash"]` is a string (`hashlib.md5(...).hexdigest()`), matching `test_compiler_minimal_world`'s `isinstance(report["state_hash"], str)` assertion.

### `StateFingerprinter.get_fingerprint()` (`src/replay/fingerprint.py:32-125`)
- Confirmed (independently, not just trusting the prior ticket's investigation): the hashed `raw_data` string is built only from `entity_ident`, `resource_ident` (global_resources), `node_ident` (resource node charges/cooldown), `region_ident` (`rid`/`owner_faction_id`/`influence`/`hazard_level` only), `scar_ident`, `group_ident`, `macro_ident` (`maturity`/`last_calamity_tick`/`movement_count`), plus `tick`/`seed`. **`state.terrain` is never read.** This means `report["state_hash"]` equality is structurally blind to terrain content — it cannot detect a terrain-painting regression by itself, in either the same-seed or cross-seed case.

### `tests/unit/worldbuilding/test_world_compiler.py` (read in full, 967 lines)
Three tests added by the immediately-prior ticket (`TCK-20260821-COMPILER-NOISE-FILL`) directly satisfy ACs #1-#3, confirmed by direct reading (not by trusting the orchestrator's line citations, though they turned out accurate):
- `test_compiler_terrain_variants_deterministic_same_seed` (lines 716-731) — compiles the same variant-declaring spec twice at `seed=42`, asserts `region_tiles_1 == region_tiles_2` dict equality over the region's 15-40 x/y bounds (26x26 tiles). Satisfies AC #1's tile-level requirement exactly. **Does not** capture or compare `report["state_hash"]` — both calls discard the report (`state1, _ = ...`, `state2, _ = ...`).
- `test_compiler_terrain_variants_different_seed_differs` (lines 734-752) — seed 42 vs 99, asserts `diff_count / len(tiles) > 0.10`. Satisfies AC #2 exactly.
- `test_compiler_no_terrain_variants_declared_produces_byte_identical_terrain_dict` (lines 805-819) — asserts every non-declaring region's in-bounds tiles equal `r_spec.terrain` for every `(x, y)`. Satisfies AC #3 exactly. Its own docstring explicitly documents why: "not state_hash equality, since StateFingerprinter does not read state.terrain at all."
- No other test in the file (confirmed by reading all 967 lines, not just the cited ranges) asserts `report["state_hash"]` equality anywhere in combination with a terrain_variants-declaring spec. `test_compiler_minimal_world` only checks `isinstance(report["state_hash"], str)`, not equality across two compiles.

**Conclusion: the orchestrator's overlap analysis is correct.** ACs #1-#3 are already fully satisfied by existing, passing tests. AC #4 (`report["state_hash"]` equality as one signal, in addition to tile-level dict comparison, mirroring `test_compiler_seeding_determinism`) is the only genuinely uncovered requirement.

### `tests/certification/test_world_compile_determinism.py::test_compiler_seeding_determinism` (read in full)
- Pattern to mirror (lines 44-71): compiles the same spec twice at `seed=999`, then `assert report1["state_hash"] == report2["state_hash"]` as its first assertion, followed by entity-count and per-entity/per-resource coordinate equality checks. This confirms the exact assertion shape AC #4 wants reused: `report1["state_hash"] == report2["state_hash"]` from two same-seed `compile()` calls, captured as a named variable rather than discarded with `_`.

## Mechanics / Engine Constraints
- `docs/engine/contracts/regression_and_verification.md` (read in full): documents the `HeadlessRunner`/`ArenaRunner`/Bors-Check determinism mechanisms (§1, §4, §6), all operating at the full-engine/replay level via `TestStrategicRegression::test_headless_run_determinism` — explicitly Out of Scope for this ticket per its own ticket body. **No "golden hash fixture corpus" requirement appears anywhere in this doc.** It does not mention `WorldCompiler.compile()`, `report["state_hash"]`, or any persisted/literal hash fixture at all. This confirms the prior ticket's own investigation finding (see Prior Work below): there is no golden-hash fixture corpus anywhere in this repo tied to `compile()`.
- No Mechanics Bible chapter constrains the shape of a determinism *test* (as opposed to the noise-fill *behavior*, which `docs/mechanics/06_worldbuilding_foundation.md`'s "Noise-Fill Terrain Law" subsection already documents, added by the prior ticket).

## Docs Requiring Update
None.

This ticket adds test coverage only — it does not change `WorldCompiler.compile()`, `StateFingerprinter`, or any documented behavior. The noise-fill mechanism itself was already fully documented by the prerequisite ticket (`TCK-20260821-COMPILER-NOISE-FILL`): `docs/mechanics/06_worldbuilding_foundation.md` ("Noise-Fill Terrain Law"), `docs/parity_ledger/substrate.yaml` (`SUB-385`, `status: verified`), `docs/guidelines/intentional_divergences.md` (§2.46), and `docs/world/compiler_contract.md` — all confirmed present in that ticket's own Files Changed section. There is no new logic, feature, or setting here to describe, and no divergence to record — this is a deliberate judgment call, not a default: I checked each of those four docs' current state via the prior ticket's closed record rather than assuming.

## Parity Ledger Overlap
- `docs/parity_ledger/substrate.yaml` — `SUB-385` (status: `verified`, priority: `P2`). Text covers exactly this feature (`terrain_variants` schema plumbing + `WorldCompiler.compile()` per-tile noise-fill consumption). Its `test_path` currently points only to `test_compiler_no_terrain_variants_declared_produces_byte_identical_terrain_dict` (the AC #3 test). `SUB-385` is `P2`, not `P0`, so it does **not** require a passing `test_path` update as a hard gate — but since the schema only carries a single `test_path` string and this ticket's new/extended test adds a second, independent determinism signal for the *declaring* case (as opposed to the *non-declaring* case `SUB-385`'s current `test_path` covers), there is a reasonable opportunity to broaden `SUB-385`'s `test_path` to the extended `test_compiler_terrain_variants_deterministic_same_seed` instead, or leave it as-is. Not required for Done — flagging as an open, non-blocking judgment call for the implementer/parity-updater.
- No `P0` entries found touching this scope. Searched `docs/parity_ledger/` for `terrain_variant`/`noise.fill`/`noise_fill` — only `SUB-385` matched.

## Prior Work
- `stored_artifacts/TCK-20260821-COMPILER-NOISE-FILL/investigation.md` — directly on-point. Its own investigation (Section "Certification / golden-hash regression risk") already independently established, before this ticket existed: (1) there is no literal golden-hash fixture corpus in this repo tied to `compile()` — searched for `golden`, `CERTIFICATION_CORPUS`, and literal fixed hash-string assertions, found none; (2) `state_hash` structurally excludes `state.terrain`, so hash equality alone is an incomplete regression guard for terrain content; (3) this is exactly why that ticket's own test plan added the three direct `state.terrain` dict-content tests instead of relying on `state_hash`. This ticket (`NOISE-FILL-DETERMINISM-TEST`)'s AC #4 is consistent with that finding — it asks for `state_hash` equality as an *additional* signal, not a replacement for the dict-content comparison, and my own independent reading of `fingerprint.py` reconfirms the same conclusion.
- `stored_artifacts/TCK-20260821-COMPILER-NOISE-FILL/test_plan.md` exists alongside — not read in depth since this investigation's own test-plan output supersedes it for this ticket's narrower scope, but its existence corroborates that the prior ticket's own test additions were planned, not incidental.

## Risks and Open Questions
- **None blocking.** The scope is narrow and fully bounded by two already-passing, already-read existing tests plus one small addition.
- Minor, non-blocking: AC #1's own text says "frozen RegionState.terrain" where the actual field is `AuthoritativeState.terrain`. Implementer should just use `state.terrain` as the three existing tests already do — no ambiguity in practice, just a wording correction worth being aware of so no one goes looking for a `RegionState.terrain` field that doesn't exist.

## Anti-Drift Hazards
- **Do not re-implement ACs #1-#3.** `test_compiler_terrain_variants_deterministic_same_seed`, `test_compiler_terrain_variants_different_seed_differs`, and `test_compiler_no_terrain_variants_declared_produces_byte_identical_terrain_dict` already satisfy them exactly. Adding duplicate tests would be pure scope creep and would violate this repo's existing single-responsibility test convention in this file.
- **Do not treat `report["state_hash"]` equality as sufficient proof of terrain correctness on its own** — it cannot detect a terrain-content regression (fingerprint.py never reads `state.terrain`). AC #4 explicitly frames it as "one signal, in addition to" the tile-dict comparison — never let it substitute for the dict comparison in either this ticket or any future one touching this area.
- **Do not scope this into `HeadlessRunner`/`TestStrategicRegression::test_headless_run_determinism`** — explicitly Out of Scope per the ticket body, and confirmed unnecessary: `docs/engine/contracts/regression_and_verification.md` documents that mechanism as a separate, broader full-engine/replay-level concern with no golden-hash-fixture requirement that would pull this ticket's narrower compiler-level test into it.
- **Do not require the real `TCK-20260821-WOLF-DEN-NOISE-MIGRATION` module** — the ticket's own Out of Scope confirms a synthetic `WorldSpec` fixture (following `create_base_valid_spec()`) is sufficient, matching every existing test in this file.

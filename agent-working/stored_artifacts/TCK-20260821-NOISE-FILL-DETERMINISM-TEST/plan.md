---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260821-NOISE-FILL-DETERMINISM-TEST
artifact_type: plan
tags: [world, determinism, testing]
---

# Implementation Plan — TCK-20260821-NOISE-FILL-DETERMINISM-TEST

## Summary
This ticket needs exactly one behavioral test edit: extend the already-passing
`test_compiler_terrain_variants_deterministic_same_seed` (currently
`tests/unit/worldbuilding/test_world_compiler.py:716-731`, verified by direct read) to also
capture and assert `report["state_hash"]` equality across the two same-seed `compile()` calls,
mirroring `test_compiler_seeding_determinism`'s pattern. ACs #1-#3 are already fully satisfied by
three existing tests added by the prior ticket (`TCK-20260821-COMPILER-NOISE-FILL`) and must not
be re-implemented. A second, optional step broadens `SUB-385`'s `test_path` in
`docs/parity_ledger/substrate.yaml` to cite the newly-extended test, via `write_entry()` only.

## Steps

### Step 1 — Extend `test_compiler_terrain_variants_deterministic_same_seed` with a `state_hash` equality assertion
**Files:** `tests/unit/worldbuilding/test_world_compiler.py`

**Current code (verified by direct read, lines 716-731):**
```python
def test_compiler_terrain_variants_deterministic_same_seed():
    """Compiling the same terrain_variants-declaring spec twice with the same seed produces
    an identical per-tile terrain dict within the region's bounds."""
    data = create_base_valid_spec()
    data["regions"][1]["terrain_variants"] = [
        {"terrain": "FOREST", "weight": 1.0},
        {"terrain": "SWAMP", "weight": 1.0},
    ]
    spec = WorldSpec.model_validate(data)

    state1, _ = WorldCompiler.compile(spec, seed=42)
    state2, _ = WorldCompiler.compile(spec, seed=42)

    region_tiles_1 = {(x, y): state1.terrain[(x, y)] for x in range(15, 41) for y in range(15, 41)}
    region_tiles_2 = {(x, y): state2.terrain[(x, y)] for x in range(15, 41) for y in range(15, 41)}
    assert region_tiles_1 == region_tiles_2
```

**Change:** Replace lines 716-731 in place with:
```python
def test_compiler_terrain_variants_deterministic_same_seed():
    """Compiling the same terrain_variants-declaring spec twice with the same seed produces
    an identical per-tile terrain dict within the region's bounds, and an identical
    report["state_hash"] as one additional signal (mirroring test_compiler_seeding_determinism)."""
    data = create_base_valid_spec()
    data["regions"][1]["terrain_variants"] = [
        {"terrain": "FOREST", "weight": 1.0},
        {"terrain": "SWAMP", "weight": 1.0},
    ]
    spec = WorldSpec.model_validate(data)

    state1, report1 = WorldCompiler.compile(spec, seed=42)
    state2, report2 = WorldCompiler.compile(spec, seed=42)

    assert report1["state_hash"] == report2["state_hash"]

    region_tiles_1 = {(x, y): state1.terrain[(x, y)] for x in range(15, 41) for y in range(15, 41)}
    region_tiles_2 = {(x, y): state2.terrain[(x, y)] for x in range(15, 41) for y in range(15, 41)}
    assert region_tiles_1 == region_tiles_2
```

Three changes from current code, all confirmed necessary and sufficient:
1. Docstring updated to name both signals (state_hash equality + tile-dict equality).
2. `state1, _` / `state2, _` become `state1, report1` / `state2, report2` — `WorldCompiler.compile()`'s
   return signature is confirmed `tuple[AuthoritativeState, dict]` (investigation.md, citing
   `compiler.py:176-182`), so `report1`/`report2` are plain dicts, matching how
   `test_compiler_seeding_determinism` (`tests/certification/test_world_compile_determinism.py:44-71`,
   read in full per investigation.md) captures and compares them.
3. `assert report1["state_hash"] == report2["state_hash"]` is inserted before the tile-dict
   comparison — assertion order matches `test_compiler_seeding_determinism`'s own ordering and the
   test_plan's stated rationale (cheaper check surfaces first).

No other line in the file changes. The test name is unchanged (extended in place, not renamed) —
this preserves its identity as the citation target for `SUB-385` (see Step 2) and any other
existing reference to it.

**Do NOT touch:** Any other test in the file, including the three ACs #1-#3 tests
(`test_compiler_terrain_variants_deterministic_same_seed`'s sibling tests) — see Scope Guards.
Do not touch `src/worldbuilding/compiler.py`, `src/replay/fingerprint.py`, or any other source file
— this ticket changes test code only, zero production-code diff.

**Verify:** `PYTHONPATH=. pytest tests/unit/worldbuilding/test_world_compiler.py::test_compiler_terrain_variants_deterministic_same_seed -v` passes, then the full scoped command in Verification below.

### Step 2 — Broaden `SUB-385`'s `test_path` to the extended test (decision made below)
**Files:** `docs/parity_ledger/substrate.yaml` (via `tools/parity_ledger_writer.write_entry()` only — never raw `Edit`)

**Change:** Confirmed current `SUB-385` entry (`docs/parity_ledger/substrate.yaml:4806-4823`, read directly):
`status: verified`, `priority: P2`, `v2_evidence: src/worldbuilding/compiler.py:211-237`,
`test_path: tests/unit/worldbuilding/test_world_compiler.py::test_compiler_no_terrain_variants_declared_produces_byte_identical_terrain_dict`.

Per the Design Decisions section below, update only the `test_path` field to
`tests/unit/worldbuilding/test_world_compiler.py::test_compiler_terrain_variants_deterministic_same_seed`,
leaving every other field (`text`, `status`, `priority`, `v2_evidence`, `legacy_evidence`,
`proof_type`) byte-identical to its current value. Implementer must call
`tools/parity_ledger_writer.write_entry("substrate.yaml", entry, ...)` with the full entry dict
(all fields reproduced, only `test_path` changed) — confirmed signature
(`tools/parity_ledger_writer.py:88`): `write_entry(shard_filename: str, entry: dict, ledger_dir=None, db_path=None) -> dict`,
which validates via `validate_entry()`, upserts by `id` (so `id: SUB-385` must be preserved exactly),
and rebuilds the derived parity index in-process. Do not hand-edit the YAML file with `Edit` — the
upsert-by-id + index-rebuild behavior is the reason this schema is exposed via a writer tool rather
than treated as a plain YAML file (per project instructions: parity ledger changes go through the
tracked API).

**Other writers to this shared resource:** `docs/parity_ledger/substrate.yaml` is a single shared
file with 500+ other entries besides `SUB-385`. `write_entry()`'s upsert-by-`id` semantics (reading
the full shard, replacing only the matching `id` entry, rewriting the whole file) mean this call is
safe against collision with any other entry in the shard as long as `id: SUB-385` is passed
unchanged and no concurrent writer targets the same `id` in the same window — this ticket is the
only in-flight ticket touching `SUB-385` (confirmed via investigation.md's parity-ledger overlap
search, which found no other `P0`/matching entries). No other ticket, agent, or pipeline phase in
this workflow writes to `substrate.yaml` concurrently with Implement; `parity-updater` (a downstream
agent role) is not invoked by this ticket's tier routing beyond the standard pipeline's own
Parity phase, which operates on this same ticket's diff — not a competing writer.

**Do NOT touch:** Any other `id` entry in `substrate.yaml`. Do not touch any other parity ledger
shard file. Do not change `SUB-385`'s `status`, `priority`, `text`, or `v2_evidence` — only
`test_path` changes.

**Verify:** After the write, `python3 -c "import yaml; entries = yaml.safe_load(open('docs/parity_ledger/substrate.yaml')); e = [x for x in entries if x['id']=='SUB-385'][0]; assert e['test_path'] == 'tests/unit/worldbuilding/test_world_compiler.py::test_compiler_terrain_variants_deterministic_same_seed'; print('OK')"` confirms the field updated and no other field drifted (spot-check `status`/`priority` unchanged in the same read). This step has no independent pytest target — it is a metadata update, not a behavior change; Step 1's own test run is what actually exercises the cited test.

## Design Decisions

**Question (from investigation.md, "Parity Ledger Overlap"):** Should `SUB-385`'s `test_path`
broaden from `test_compiler_no_terrain_variants_declared_produces_byte_identical_terrain_dict` to
the now-extended `test_compiler_terrain_variants_deterministic_same_seed`, or stay as-is?

**Decision: broaden it (Step 2 above).**

**Reasoning:** `SUB-385`'s `text` field describes two things: (1) the `terrain_variants` schema
plumbing, and (2) `WorldCompiler.compile()`'s actual consumption mechanism — "per-tile terrain is
sampled via `DeterministicRNG.weighted_choice()` keyed under `Domain.INIT` ... using a 16-bits-per-axis
tile-offset encoding" — with the non-declaring flat-fill behavior mentioned only as a trailing
backward-compat clause. The *currently* cited test
(`test_compiler_no_terrain_variants_declared_produces_byte_identical_terrain_dict`) exercises only
the non-declaring path — it never triggers `weighted_choice()`, `Domain.INIT` sampling, or the
tile-offset encoding at all, so it does not actually exercise the mechanism the entry's `text` spends
most of its words describing. The newly-extended `test_compiler_terrain_variants_deterministic_same_seed`
does exercise that mechanism (a `terrain_variants`-declaring spec, sampled via the real code path)
and, post-Step-1, additionally proves both of `compile()`'s two independent determinism signals
(`state_hash` and per-tile dict) agree for it. This makes it the single most representative test for
what `SUB-385` actually describes. This is a `P2`, non-blocking judgment call per the investigation —
not a hard requirement — and the change is scoped to one field via the tracked writer, so it carries
no meaningful risk to the ledger's integrity.

## Scope Guards

Reiterated verbatim from investigation.md's Anti-Drift Hazards — none of these are steps in this plan:

- **Do not re-implement ACs #1-#3.** `test_compiler_terrain_variants_deterministic_same_seed`,
  `test_compiler_terrain_variants_different_seed_differs`, and
  `test_compiler_no_terrain_variants_declared_produces_byte_identical_terrain_dict` already satisfy
  them exactly. Adding duplicate tests would be pure scope creep and would violate this repo's
  existing single-responsibility test convention in this file.
- **Do not treat `report["state_hash"]` equality as sufficient proof of terrain correctness on its
  own** — it cannot detect a terrain-content regression (`fingerprint.py` never reads
  `state.terrain`). AC #4 explicitly frames it as "one signal, in addition to" the tile-dict
  comparison — never let it substitute for the dict comparison in either this ticket or any future
  one touching this area.
- **Do not scope this into `HeadlessRunner`/`TestStrategicRegression::test_headless_run_determinism`**
  — explicitly Out of Scope per the ticket body, and confirmed unnecessary:
  `docs/engine/contracts/regression_and_verification.md` documents that mechanism as a separate,
  broader full-engine/replay-level concern with no golden-hash-fixture requirement that would pull
  this ticket's narrower compiler-level test into it.
- **Do not require the real `TCK-20260821-WOLF-DEN-NOISE-MIGRATION` module** — the ticket's own Out
  of Scope confirms a synthetic `WorldSpec` fixture (following `create_base_valid_spec()`) is
  sufficient, matching every existing test in this file.
- No production code file (`src/worldbuilding/compiler.py`, `src/replay/fingerprint.py`,
  `src/core/state.py`, `src/platform/rng.py`) is touched by this plan — this is a pure test-extension
  (plus one optional parity-ledger metadata) ticket.
- No doc under `docs/mechanics/`, `docs/guidelines/intentional_divergences.md`, or
  `docs/world/compiler_contract.md` is touched — the noise-fill mechanism itself was already fully
  documented by the prerequisite ticket; there is no new behavior here to describe.

## Dependency Map

Step 2 is independent of Step 1's test passing (it is a metadata citation, not a functional
dependency) but should be applied after Step 1 lands, since it cites Step 1's post-edit test name.
Both steps can be verified independently; do Step 1 first for logical ordering.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — same-seed compile twice produces bit-identical per-tile terrain dicts | Already satisfied; no new work | `test_compiler_terrain_variants_deterministic_same_seed` (pre-existing tile-dict assertion, unchanged by Step 1) |
| AC #2 — two different seeds produce at least one differing tile within variant region bounds | Already satisfied; no new work | `test_compiler_terrain_variants_different_seed_differs` |
| AC #3 — non-declaring region still produces exact pre-epic flat single-terrain fill | Already satisfied; no new work | `test_compiler_no_terrain_variants_declared_produces_byte_identical_terrain_dict` |
| AC #4 — reuse `report["state_hash"]` equality as one signal in addition to tile-level dict comparison, mirroring `test_compiler_seeding_determinism` | Step 1 | `test_compiler_terrain_variants_deterministic_same_seed` (extended) |

## Verification

Scoped pytest command (from test_plan.md — never `pytest tests/`):
```bash
PYTHONPATH=. pytest tests/unit/worldbuilding/test_world_compiler.py tests/certification/test_world_compile_determinism.py -v
```

## Anti-Drift Notes

- `state_hash` equality alone never proves terrain correctness — `StateFingerprinter.get_fingerprint()`
  (`src/replay/fingerprint.py:32-125`, confirmed by investigation.md's independent read) never reads
  `state.terrain`. Step 1's new assertion must stay paired with the existing tile-dict comparison in
  the same test, in that order (state_hash first — cheaper check fails fast; dict comparison second).
- `test_compiler_terrain_variants_tile_offset_injective_across_wide_regions` must keep passing as a
  precondition — a colliding tile-offset encoding could produce a same-seed-identical hash by
  coincidence while masking a real per-tile collision bug. This plan does not touch that test, but
  Step 1's determinism claim depends on it staying green.
- AC #1's ticket text says "frozen RegionState.terrain" — the actual field is
  `AuthoritativeState.terrain` (`src/core/state.py:1126`, per investigation.md). This is a wording
  artifact in the ticket, not a discrepancy in the plan; Step 1 uses `state.terrain` exactly as all
  existing tests in the file already do.

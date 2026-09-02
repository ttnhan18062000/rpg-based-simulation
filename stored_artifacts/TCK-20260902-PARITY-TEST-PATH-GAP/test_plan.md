---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260902-PARITY-TEST-PATH-GAP
artifact_type: test_plan
tags: [testing]
---

# Test Plan — TCK-20260902-PARITY-TEST-PATH-GAP

## Regression Surface
No `src/` behavior changes in this ticket, so regression risk is limited to confirming the two
repointed tests and the new test all still pass, and that no ledger/tooling write breaks other
consumers of the ledger.

**Unit**
- `tests/unit/social/test_teach.py` (full file) — TOWN-027's cited test lives here; run the whole
  file to catch any fixture/import regressions from this ticket's read (no edits expected).
- `tests/unit/resource/test_loot_channeling.py` (full file) — TOWN-076's cited test lives here.
- `tests/unit/core/test_rpg_math.py` — style precedent for the new SUB-051 test; also the existing
  `test_stat_recalculation` test that already exercises `LevelingService.recalculate_combat_stats`
  and must keep passing unmodified.
- `tests/unit/core/test_rpg_depth.py` — contains `TestAttributeCaps` (`enforce_attribute_caps`) and
  `TestEffectiveStats` (`SkillScalingService.get_effective_stats`), the two closest existing analogs
  to the new SUB-051 test; must keep passing unmodified — this ticket does not touch this file's
  existing tests.

**Integration**
- `tests/integration/pipeline/test_combat_legality_matrix.py` — cited by SUB-052/SUB-054; must keep
  passing (no edits expected, referenced only as style precedent).

**Tooling**
- `tools/parity_ledger_writer.py`'s own validation path is exercised implicitly by the three writes
  this ticket makes — no direct test file for the writer itself is in scope to run beyond the
  writer's own successful/failed `validate_entry()` behavior at write time.

## New Tests Required

### 1. SUB-051 — new `CombatComponent`/stats invariant test
- **Test name**: implementer's choice, naturally named for what it asserts — e.g.
  `test_combat_stats_stay_within_bounds_after_normal_recalculation` or
  `test_effective_stats_invariants_hold_for_normal_attributes` (do not force-fit
  `test_stats_invariants` verbatim unless it turns out to be the most natural name).
- **Category**: unit.
- **What it verifies** (grounded in real code traced above, scoped to normal/in-range
  construction per Scope item 3's own wording and the Risks section's recommendation — do not use
  adversarial/out-of-range attribute inputs, which would correctly fail against a confirmed,
  out-of-scope, pre-existing gap in `AttributePatch.apply`/`enforce_attribute_caps` wiring):
  - Construct one or more `AttributeComponent`s spanning the documented valid range (e.g. the
    dataclass default of 5 across all nine attributes, plus at least the low end near 1 and a
    high-but-in-range value near 99, mirroring `test_rpg_math.py::test_stat_recalculation`'s
    explicit-value style) and call `LevelingService.recalculate_combat_stats(attrs)` directly (or
    `SkillScalingService.get_effective_stats(attrs)` for the fuller path including the evasion
    clamp) for each.
  - Assert `stats["max_hp"] > 0` and is an `int` (not NaN/float artifact) for every case.
  - Assert `stats["atk"] >= 1` and `stats["def_stat"] >= 1` for every case (matching the "min 1"
    law stated in `SkillScalingService.get_effective_stats`'s own docstring at
    `src/engine/rpg_depth.py:360`, which holds trivially for in-range attributes even though the
    code only clamps to it conditionally under wounds/scars — see Investigation Risks).
  - Assert `0.0 <= stats["evasion"] <= 0.95` for every case (the code's own unconditional clamp,
    `rpg_depth.py:390`).
  - Assert `stats["readiness_speed"] >= 1.0` for every case (formula floor,
    `leveling.py:104`: `max(1.0, 10.0 + (agility - 5) * 1.0)`), including an explicit low-agility
    case (e.g. `agility=1`) to prove the floor engages, not just that it's never hit.
  - Additionally construct a `CombatComponent` via normal `V2EntityBuilder(...).combat(...)`
    defaults (or explicit kwargs) and assert `hp <= max_hp`, `hp >= 0`, `max_hp > 0` — the
    `CombatComponent` dataclass itself enforces none of this, so this proves the *constructed*
    entity's invariant, not just the derived-stat formula's.
  - Do **not** assert anything about negative-attribute or >99-attribute inputs, or about
    `AttributePatch.apply`'s delta-application clamp — those exercise the confirmed live gap
    described in Investigation → Risks and are out of scope for this ticket to fix or to fail a
    gate over.
- **Where it should live**: `tests/unit/core/test_rpg_math.py` (co-locate with
  `test_stat_recalculation`, same style/imports, same subject —
  `LevelingService.recalculate_combat_stats`) is the most natural fit; `tests/unit/core/test_rpg_depth.py`
  (next to `TestEffectiveStats`) is an acceptable alternative if the implementer prefers grouping
  with `SkillScalingService.get_effective_stats` coverage. Either is consistent with the ticket's
  "mirroring the sibling tests' style" instruction — pick one file, do not split the test across
  both.

## Scoped Pytest Commands
```
pytest tests/unit/social/test_teach.py -k test_teach_resolves_target_capability_blocker_not_teacher -v
pytest tests/unit/resource/test_loot_channeling.py -k test_loot_corpse_completion_transfers_all_item_stacks -v
pytest tests/unit/core/test_rpg_math.py tests/unit/core/test_rpg_depth.py -v
```
Run the third command last, after the new SUB-051 test is added to whichever of these two files the
implementer chooses — it covers both the new test and its closest existing siblings
(`TestAttributeCaps`, `TestEffectiveStats`, `test_stat_recalculation`) in one pass.

Never run the bare `pytest tests/` per project convention — all three commands above are scoped to
the exact files this ticket's changes touch or cite.

## Anti-Drift Test Guards
- **`TestAttributeCaps::test_cap_enforcement` and `TestAttributeCaps::test_no_cap_within_range`
  (`tests/unit/core/test_rpg_depth.py:452-464`) must still pass unmodified.** These are the only
  existing tests that exercise `enforce_attribute_caps`'s lower-bound behavior; if a future change
  (in this ticket or any other) silently deletes or weakens them while "cleaning up" nearby code,
  the only proof that `enforce_attribute_caps` computes correct `[1, 99]` deltas disappears, even
  though the investigation found the function is already disconnected from the live pipeline.
- **`test_evasion_capped` (`tests/unit/core/test_rpg_depth.py:507-511`) must still pass
  unmodified** — it is the one existing proof that the unconditional evasion clamp
  (`rpg_depth.py:390`) actually engages under extreme input (`agility=999`); the new SUB-051 test
  must not duplicate or replace this test, only add coverage for `atk`/`def_stat`/`max_hp`/
  `readiness_speed`, which this test does not cover.
- **`test_stat_recalculation` (`tests/unit/core/test_rpg_math.py:25-...`) must still pass
  unmodified** — the new SUB-051 test must not alter or subsume this test's exact-value assertions;
  it adds a bounds/invariant check alongside it, not a replacement.
- **No test added by this ticket may assert on `AttributePatch.apply`'s clamp behavior
  (`src/engine/patches.py:579-594`) or on `enforce_attribute_caps` being wired into the apply
  path** — a test asserting either of those would either fail honestly (exposing real,
  out-of-scope work) or, worse, would create pressure to "fix" `src/` to pass it, which is exactly
  the scope-creep this ticket's Out of Scope section forbids. If the implementer or a reviewer
  wants that coverage, it belongs in a new, separately-scoped ticket, not folded into this one's
  SUB-051 test.
- **Ledger schema validity guard**: after all three `parity_ledger_writer.py` writes, the resulting
  `substrate.yaml`/`town_resource.yaml` must still validate against `docs/parity_ledger/schema.json`
  (the writer enforces this itself via `validate_entry()`, but re-running
  `python3 tools/parity_index.py build` after each write, per Scope item 5, is the guard that keeps
  the derived SQLite index from silently going stale and masking a partial/failed write).

---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260824-WOUND-THRESHOLD-DECISION
artifact_type: test_plan
tags: [combat]
---

# Test Plan — TCK-20260824-WOUND-THRESHOLD-DECISION

## Regression Surface

Unit:
- `tests/unit/core/test_rpg_depth.py` — full file, especially `TestWoundInfliction` (193-229,
  directly implicated by any delete/keep change) and `TestScarPermanence` (231-278, uses
  `WoundService.create_wound()`/`get_scar_stat_penalties()`, both live and unrelated to this
  ticket's change but sharing the same test module — must still collect and pass after any edit to
  the module-level import list at line 40).
- `tests/unit/core/test_rpg_math.py` — imports/exercises adjacent `rpg_depth.py` math; confirm no
  accidental import breakage from removing `WOUND_THRESHOLD_RATIO`.
- `tests/unit/core/test_entity_integrity.py`, `tests/unit/core/test_p1_semantic_hardening.py` —
  touch wound/scar state shape; regression guard against unrelated breakage.

Integration / arena-combat:
- `tests/unit/combat/test_direct_combat_outcomes.py` — the two live-path wound tests added by
  `TCK-20260824-WOUND-PENALTY-FORMULA-WIRING`
  (`test_wound_penalties_scale_with_severity_through_live_combat_path`,
  `test_severe_wound_max_hp_penalty_reduces_effective_max_hp_through_apply_path`) must keep passing
  unchanged — they exercise the live 25% gate this ticket must not alter.
- `tests/integration/combat/test_wound_healing_permanence.py` — added by
  `TCK-20260824-WOUND-HEALING-DECISION`; asserts zero production producers for wound healing/scar
  formation via a real `Kernel.tick_once()` run. Not directly touched by this ticket but shares the
  same `_get_wound_infliction()` call path and must keep passing.
- `tests/integration/optimization/test_apply_plan_parity.py` — exercises the apply path consumer of
  wound state; regression guard.

Tooling / gate:
- `tests/tools/test_validate_frontmatter.py` — this ticket's own staging artifacts must pass
  frontmatter validation (`artifact_type` in `{investigation, plan, test_plan, report}`).
- `tests/tools/test_parity_ledger_schema.py`, `tests/tools/test_parity_ledger_scan.py` — COMB-290's
  edit must remain schema-valid.
- If "keep" path chosen: `tests/agent_orchestration_claude_adapter/test_divergence_log.py` and/or
  `tests/agent_replay_codex/test_divergence_registration.py` — guard the
  `intentional_divergences.md` format for the new `DEV-00N` entry.

## New Tests Required

Exact set depends on the delete-vs-keep decision (reserved for the orchestrator/planner). Both
branches are enumerated so the implementer has a ready-made spec either way.

**If DELETE:**
- **Test name**: (none new — deletion removes `TestWoundInfliction::test_wound_infliction_massive_hit`)
  - **Category**: n/a (test removal, not addition)
  - **What it verifies**: n/a
  - **Where**: `tests/unit/core/test_rpg_depth.py` — remove the test method and the
    `WOUND_THRESHOLD_RATIO` import at line 40; keep `TestWoundInfliction`'s other three tests
    (`test_wound_stat_impact`, `test_wound_cumulative_penalties`, `test_healed_wound_not_penalized`)
    unchanged since they exercise live `create_wound()`/`get_wound_stat_penalties()`, not the
    deleted method.
- **Test name**: `test_wound_infliction_below_live_threshold_produces_no_wound` (new, optional but
  recommended — closes a real coverage gap: no existing test currently asserts the *negative* case
  of the live 25% gate through the real combat path)
  - **Category**: unit / integration (mirrors `test_wound_penalties_scale_with_severity_through_live_combat_path`'s
    pattern — drive `CombatResolutionSystem.resolve_attack()` with damage below `max_hp * 0.25`)
  - **What it verifies**: `update.wound_update is None` when `damage <= defender.combat.max_hp *
    0.25`, proving the live gate's *boundary* is exercised (not just its positive/massive-hit side)
    now that `should_inflict_wound()`'s own boundary test is gone.
  - **Where it should live**: `tests/unit/combat/test_direct_combat_outcomes.py` (same module as the
    sibling live-path wound tests from `TCK-20260824-WOUND-PENALTY-FORMULA-WIRING`).

**If KEEP:**
- **Test name**: no test-code change required for `should_inflict_wound()` itself — it keeps its
  existing dead-code test coverage (`test_wound_infliction_massive_hit` stays as-is, since it is now
  explicitly documented as testing legacy/dormant code, not deleted).
  - **Category**: n/a
  - **What it verifies**: n/a
  - **Where**: no file changes to `test_rpg_depth.py`.
- **Test name**: a doc-format guard test is not required per-ticket (the divergence-log format is
  already guarded by the existing `test_divergence_log.py`/`test_divergence_registration.py` suite
  listed in Regression Surface) — no new test needed for the "keep" path itself, only the code
  annotation and `intentional_divergences.md` entry (non-code artifacts).

**Regardless of decision (both paths):**
- **Test name**: implicit via existing suite — confirm `docs/parity_ledger/combat_movement.yaml`
  still validates after COMB-290's edit.
  - **Category**: architecture guard (schema/static check, not a new pytest test)
  - **What it verifies**: COMB-290's corrected `test_path` actually exists and is collectible
    (`pytest --collect-only <new_test_path>` should succeed before committing the ledger edit).
  - **Where**: enforced by `tests/tools/test_parity_ledger_schema.py` / `test_parity_index.py` at
    regression-run time, not a new test file.

## Scoped Pytest Commands

```
pytest tests/unit/core/test_rpg_depth.py tests/unit/core/test_rpg_math.py \
  tests/unit/core/test_entity_integrity.py tests/unit/core/test_p1_semantic_hardening.py \
  tests/unit/combat/test_direct_combat_outcomes.py \
  tests/integration/combat/ \
  -v -m "not slow"
```

```
pytest tests/tools/test_validate_frontmatter.py tests/tools/test_parity_ledger_schema.py \
  tests/tools/test_parity_ledger_scan.py -v
```

If "keep" path: additionally
```
pytest tests/agent_orchestration_claude_adapter/test_divergence_log.py \
  tests/agent_replay_codex/test_divergence_registration.py -v
```

Never: `pytest tests/`.

## Anti-Drift Test Guards

- `tests/unit/combat/test_direct_combat_outcomes.py::test_wound_penalties_scale_with_severity_through_live_combat_path`
  and `::test_severe_wound_max_hp_penalty_reduces_effective_max_hp_through_apply_path` must pass
  byte-identically before and after this ticket — any change to their outcome would mean the live
  25% gate or the `create_wound()` delegation was accidentally touched, which is out of scope.
- `TestWoundInfliction`'s other three tests (`test_wound_stat_impact`,
  `test_wound_cumulative_penalties`, `test_healed_wound_not_penalized`) must keep passing unchanged
  in either decision branch — they test live `create_wound()`/`get_wound_stat_penalties()`, not
  `should_inflict_wound()`, and are not implicated by this ticket regardless of the delete/keep
  call.
- `tests/integration/combat/test_wound_healing_permanence.py` must keep passing unchanged — it
  proves zero wound-healing producers exist; this ticket must not accidentally add a healing path
  while resolving the threshold question.
- COMB-102 (P0) and COMB-104 (P0) must not be left with a broken `test_path` as an unannounced side
  effect: if `TestWoundInfliction::test_wound_infliction_massive_hit` is deleted or rewritten,
  re-run `pytest --collect-only tests/unit/core/test_rpg_depth.py::TestWoundInfliction::test_wound_infliction_massive_hit`
  (or its replacement id) to confirm COMB-102's `test_path` still resolves before closing this
  ticket — this is a regression guard on ledger integrity, not new ticket scope, but it is a hard
  gate against silently breaking a P0 entry.

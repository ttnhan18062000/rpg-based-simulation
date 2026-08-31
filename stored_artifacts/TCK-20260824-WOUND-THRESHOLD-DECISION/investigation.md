---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260824-WOUND-THRESHOLD-DECISION
artifact_type: investigation
tags: [combat]
---

# Investigation — TCK-20260824-WOUND-THRESHOLD-DECISION

## Context Search (Step 0c)

`mcp__knowledge-search__search_docs` failed with `{"error":"index not found","action":"run make
knowledge-index"}` — same as noted earlier this session. Fallback `python3
tools/knowledge_search.py query "wound threshold WoundService should_inflict_wound" --top-k 5`
also failed with `knowledge index not found — run make knowledge-index`; skipped silently per
instructions (no index is available on this branch/worktree).

`graphify query "WoundService should_inflict_wound WOUND_THRESHOLD_RATIO wound infliction
threshold"` (163 nodes, BFS depth=2 from `WoundService`) confirmed the primary targets already
supplied in the task: `WoundService` at `src/engine/rpg_depth.py:113`, `._get_wound_infliction()`
at `src/engine/combat.py:605`, `test_rpg_depth.py`'s `TestWoundInfliction` class, and
`CombatResolutionSystem` at `src/engine/combat.py:17`. No additional relevant nodes outside the
already-supplied targets were surfaced. All subsequent grep/read steps below are follow-up
narrowing on these graph-returned nodes, not a cold start.

## Current Behavior

### `WoundService` (`src/engine/rpg_depth.py:113-183`)

- `WOUND_THRESHOLD_RATIO = 0.40` — module-level constant, line 111.
- `should_inflict_wound(damage, max_hp)` (lines 116-122): `return damage >= (max_hp *
  WOUND_THRESHOLD_RATIO)`. **Zero real (non-test) callers anywhere in `src/`** — confirmed by
  `grep -rn "should_inflict_wound" src/ tests/`: the only matches are the method's own definition
  and three assertions in `tests/unit/core/test_rpg_depth.py:199-201`
  (`TestWoundInfliction::test_wound_infliction_massive_hit`). No caller in `src/engine/combat.py`,
  `src/engine/apply.py`, or anywhere else.
- `WOUND_THRESHOLD_RATIO` itself: **zero real references outside `should_inflict_wound()`** —
  `grep -rn "WOUND_THRESHOLD_RATIO" src/ tests/` returns only the definition (line 111), its use
  inside `should_inflict_wound()` (line 122), and one test-file import
  (`tests/unit/core/test_rpg_depth.py:40`) that is never actually asserted against directly (no
  test reads the constant's value — the three assertions at lines 199-201 hardcode `40`/`60`/`30`
  literally).
- `create_wound(damage, max_hp, tick, wound_id)` (lines 124-146): **live** — called from
  `src/engine/combat.py:611` inside `_get_wound_infliction()` (wired in by the already-completed
  `TCK-20260824-WOUND-PENALTY-FORMULA-WIRING`).
- `get_wound_stat_penalties(wounds)` (lines 148-167): **live** — called from
  `src/engine/rpg_depth.py:385` inside `SkillScalingService.get_effective_stats()`.
- `get_scar_stat_penalties(scars)` (lines 169-183): **live** — called from
  `src/engine/rpg_depth.py:392`, same `get_effective_stats()`.
- No `heal_wound()` or `MedicalService` exists anywhere in the current tree — `grep -rn
  "heal_wound|get_diagnosis_quality|MedicalService" src/ tests/` returns zero matches. These were
  deleted by the already-completed sibling `TCK-20260824-WOUND-HEALING-DECISION` (DEV-005 in
  `intentional_divergences.md`, confirmed below) as zero-caller dead code — this ticket's own
  Assumptions section anticipated this ("whether `heal_wound()` should be handled here... needs
  confirming once C4's decision lands"); C4 has landed and already resolved it, so `heal_wound()`
  is out of scope here by virtue of no longer existing.

**Conclusion on Q4 (other zero-caller methods)**: `should_inflict_wound()` is the *only* zero-real-
caller method remaining on `WoundService`. `create_wound()`, `get_wound_stat_penalties()`, and
`get_scar_stat_penalties()` are all live. `heal_wound()`/`MedicalService` were already deleted by
the prior sibling ticket and no longer exist to be zero-caller.

### Live wound-infliction path — `CombatResolutionSystem._get_wound_infliction()` (`src/engine/combat.py:604-618`)

```python
@staticmethod
def _get_wound_infliction(attacker, defender, damage, tick, alive) -> Optional[WoundUpdate]:
    """Calculates and returns a WoundUpdate if damage is sufficient."""
    if damage > defender.combat.max_hp * 0.25 and alive:
        from src.core.updates import WoundUpdate
        from src.engine.rpg_depth import WoundService
        w_id = f"w_{attacker.id}_{defender.id}_{tick}"
        wound = WoundService.create_wound(
            damage=int(damage), max_hp=defender.combat.max_hp, tick=tick, wound_id=w_id,
        )
        return WoundUpdate(wounds_add=[wound])
    return None
```

This is the real, live 25% gate (`damage > defender.combat.max_hp * 0.25`, a raw literal — **not**
a named constant, and **not** `WOUND_THRESHOLD_RATIO`). It is called from five sites in
`combat.py`: `resolve_attack` (line 194), `resolve_skill_usage` (line 288),
`resolve_multi_attack`/`resolve_aoe_attack` (lines 504, 562). It calls `WoundService.create_wound()`
directly — it **never calls `WoundService.should_inflict_wound()`** at any point. The two threshold
implementations (25% inline literal in `combat.py`, 40% via `WOUND_THRESHOLD_RATIO` in
`rpg_depth.py`) are fully independent code paths; `should_inflict_wound()` is unreachable dead code,
confirming the ticket's premise exactly.

### `TestWoundInfliction` (`tests/unit/core/test_rpg_depth.py:193-229`)

- `test_wound_infliction_massive_hit` (196-201): calls `WoundService.should_inflict_wound(40, 100)`
  / `(60, 100)` / `(30, 100)` directly — exercises **only the dead 40% branch**, never the live
  25% path.
- `test_wound_stat_impact`, `test_wound_cumulative_penalties`, `test_healed_wound_not_penalized`
  (205-228): call `WoundService.create_wound()` and `get_wound_stat_penalties()` directly — these
  exercise **live** methods, just not through the live combat call path (`combat.py`'s
  `_get_wound_infliction()`). Not implicated by a should_inflict_wound()-only deletion.

## Mechanics / Engine Constraints

- `docs/mechanics/01_entity_anatomy.md` Section 6 "Trauma: Wounds & Scars" (lines 144-181),
  "Wound Infliction" subsection (147-152): states the threshold as **strictly greater than 25%**
  with pseudocode `WOUND_THRESHOLD_RATIO = 0.25` / `is_wound = damage > (max_hp *
  WOUND_THRESHOLD_RATIO)`. **This is already the correct value** (25%, strict `>`, matching
  `combat.py:607` exactly). It does not cite `should_inflict_wound()` or `rpg_depth.py` as the
  source for the threshold check itself.
- `docs/mechanics/02_combat_laws.md` Section 5 "Wound Infliction" (lines 70-92): states the same
  25%/strict-`>` rule, pseudocode `is_wound = damage > (defender.max_hp * 0.25) and
  defender.alive` — matches `combat.py:607` verbatim including the `alive` gate, and explicitly
  cites `CombatResolutionSystem._get_wound_infliction()` (`src/engine/combat.py:605-617`) as the
  evidence source. Also already correct.
- Neither doc contains any `40%`/`0.40`/`0.4` reference anywhere (`grep -n "40%\|0\.40" docs/mechanics/01_entity_anatomy.md
  docs/mechanics/02_combat_laws.md` returns zero matches). **The ticket's Request Summary premise
  ("two Mechanics Bible docs cross-reference the stale value") is not literally true of the value**
  — both docs already state 25%. The ticket's own Assumptions section already narrows this
  correctly: "the residual gap is an identifier-name collision in doc pseudocode, not a value
  error." Confirmed: the only collision is that `01_entity_anatomy.md`'s pseudocode reuses the
  identifier name `WOUND_THRESHOLD_RATIO` (with the correct value, 0.25) while the dead code in
  `rpg_depth.py` defines a real Python symbol of the exact same name with a different value (0.40)
  — so a grep for `WOUND_THRESHOLD_RATIO` surfaces both and looks contradictory without reading
  the values.

## Docs Requiring Update

- `docs/parity_ledger/combat_movement.yaml`: COMB-290's `v2_evidence` cites `_get_wound_infliction() line 583` (stale — the function is now at line 605-618 after intervening edits) and its `test_path` points to `tests/unit/combat/test_combat_matrix.py`, which contains zero wound-related tests (confirmed by `grep -in wound tests/unit/combat/test_combat_matrix.py` returning no matches). Both must be corrected regardless of which delete/keep decision is made, per this ticket's explicit AC #5.

Two further mechanics docs were named in "Related Docs" and are addressed here even though neither requires a change:

`docs/mechanics/01_entity_anatomy.md` (Section 6, lines 144-181) is not required to change for
either decision path: its stated value (25%, strict `>`) and evidence already match live code
exactly. If the **delete** path is chosen, the `WOUND_THRESHOLD_RATIO` Python symbol disappears
from `rpg_depth.py` entirely, which resolves the identifier-name collision by removing the
colliding side — no doc edit is needed to achieve consistency, since the doc's own pseudocode
identifier was never wrong. If the **keep** path is chosen instead, the doc still doesn't need to
change (it already correctly describes only the live 25% behavior and doesn't reference
`should_inflict_wound()` at all) — only `docs/guidelines/intentional_divergences.md` gains a new
entry documenting the dormant branch, per the ticket's own "If keep" AC.

`docs/mechanics/02_combat_laws.md` (Section 5, lines 70-92) is not required to change for the same
reason: its pseudocode already uses the raw literal `0.25` (not the colliding identifier name at
all), states the correct threshold, and already cites `combat.py:605-617` as the evidence source.
Neither decision path touches this doc's content.

**If the "keep" path is chosen** (decision reserved for the orchestrator/planner, not this
investigation): `docs/guidelines/intentional_divergences.md` becomes a required-update doc — a new
`DEV-00N` entry must be added following the exact format of `DEV-004` (`AllocateAttributeAction`,
lines 1464-1494) and `DEV-005` (`heal_wound()`/`MedicalService`, most recent entry, ending "Last
updated: 2026-08-29"). Whichever decision is finalized should re-run this section of the
investigation to add that bullet in Format 1 form if "keep" is selected.

## Parity Ledger Overlap

- **COMB-290** (`docs/parity_ledger/combat_movement.yaml:3023-3041`) — `status: verified`,
  `priority: P1`. Text: "Wound infliction threshold — damage > max_hp * 0.25 (strict greater-than,
  25%) triggers a wound on a surviving defender." `v2_evidence` cites `_get_wound_infliction() line
  583` (stale line number) and both mechanics docs (correctly, per above). `test_path:
  tests/unit/combat/test_combat_matrix.py` — **confirmed wrong**, this file has no wound-related
  test at all. This is the entry this ticket must correct per its explicit scope/AC.
- **COMB-102** (`docs/parity_ledger/combat_movement.yaml:1104-1113`) — `status: verified`,
  `priority: P0`. Text: `'test_wound_infliction_massive_hit: wound infliction'`. `v2_evidence`
  describes the live `create_wound()` delegation (correct, live behavior), but `test_path` points
  to `tests/unit/core/test_rpg_depth.py::TestWoundInfliction::test_wound_infliction_massive_hit` —
  **this test exercises `WoundService.should_inflict_wound()`, the dead 40% branch**, not the
  `create_wound()` delegation the evidence text describes. This is a P0 entry with an
  evidence/test_path mismatch that is *adjacent to but not named in* this ticket's explicit scope
  (only COMB-290 is named). If the delete decision removes or rewrites
  `test_wound_infliction_massive_hit`, COMB-102's `test_path` becomes dangling and must be
  repointed — flagged as a risk below, not resolved by this investigation.
- **COMB-104** (`docs/parity_ledger/combat_movement.yaml`, immediately following COMB-103) —
  `priority: P0`, `test_path: tests/unit/core/test_rpg_depth.py::TestWoundInfliction::test_scar_permanence`
  — **pre-existing, unrelated bug**: `test_scar_permanence` is actually defined inside the
  `TestScarPermanence` class (line 234), not `TestWoundInfliction` (which ends at line 229). This
  wrong-class pointer predates this ticket (introduced by `TCK-20260824-WOUND-PENALTY-FORMULA-
  WIRING`'s COMB-102/103/104 batch update) and is out of this ticket's scope, but is flagged since
  it sits in the same P0 cluster and the same file region this ticket touches.
- **COMB-103** (`docs/parity_ledger/combat_movement.yaml`, between COMB-102 and COMB-104) —
  `priority: P0`, `test_path: tests/unit/core/test_rpg_depth.py::TestWoundInfliction::test_wound_stat_impact`
  — correct and live (`test_wound_stat_impact` calls `WoundService.create_wound()` directly, a live
  method). Not implicated by a `should_inflict_wound()`-only deletion.

## Prior Work

- `TCK-20260824-WOUND-PENALTY-FORMULA-WIRING` (done, hotfix tier): wired `_get_wound_infliction()`
  to delegate to `WoundService.create_wound()` for the severity-scaled penalty formula, replacing a
  flat `atk_penalty=5.0/def_penalty=5.0` bug. Explicitly left the 25% inline threshold check
  untouched and explicitly out-of-scoped "the unreachable 40% `should_inflict_wound()` threshold
  branch and `WOUND_THRESHOLD_RATIO` cleanup" to this ticket. Added
  `tests/unit/combat/test_direct_combat_outcomes.py::test_wound_penalties_scale_with_severity_through_live_combat_path`
  and `::test_severe_wound_max_hp_penalty_reduces_effective_max_hp_through_apply_path` — both drive
  the real `resolve_attack()` entry point end-to-end through the live 25% gate.
- `TCK-20260824-WOUND-HEALING-DECISION` (done, standard tier): resolved the sibling "keep vs.
  delete" decision for `heal_wound()`/`MedicalService.get_diagnosis_quality()` — **deleted both as
  zero-caller dead code**, explicitly citing the `DEV-004` precedent (`AllocateAttributeAction`
  deletion). Recorded as `DEV-005` in `docs/guidelines/intentional_divergences.md`. This is the
  closest direct precedent for the delete-vs-keep call this ticket must make on
  `should_inflict_wound()`/`WOUND_THRESHOLD_RATIO`: same evidentiary bar (zero-caller, confirmed by
  full-repo grep), same subsystem, same day, same author intent.
- `DEV-004` (`docs/guidelines/intentional_divergences.md:1464-1494`,
  `TCK-20260824-ALLOCATE-AP-BRANCH-DECISION`): the original precedent for deleting zero-caller dead
  code (`AllocateAttributeAction`) rather than annotating it dormant, when a decision ticket exists
  to weigh both options. Establishes the format both `keep`- and `delete`-path write-ups should
  follow if `keep` is chosen instead (a `DEV-00N` "kept dormant" entry, following DEV-004's own
  "Keep... wired but dormant" shape for the alternative outcome, rather than DEV-005's deletion
  shape).
- `TCK-20260619-PARITY-P0-BUGS`: original ticket that corrected both mechanics docs from a
  previously-documented (and previously actually-divergent) 40% figure down to the correct 25%,
  per COMB-290's own `divergence_note`: "Previously divergent: Chapter 02 stated 40%, entity_anatomy
  stated 40%, code used 25%. Resolved... docs corrected to match source-authoritative 25% value."
  This confirms the docs were already fixed well before this ticket; the 40% branch in
  `rpg_depth.py` was left behind as dead code at that time and has remained unreachable since.

## Risks and Open Questions

- **Open (reserved for orchestrator/planner, not answered here)**: delete vs. keep for
  `should_inflict_wound()`/`WOUND_THRESHOLD_RATIO`. Strong precedent exists for delete (DEV-004,
  DEV-005 — same evidentiary bar, same ticket cluster, same day), but this investigation does not
  make that call.
- **COMB-102's test_path is adjacent risk, not named in this ticket's explicit scope.** COMB-102
  (P0) currently points to `TestWoundInfliction::test_wound_infliction_massive_hit`, the exact test
  that exercises `should_inflict_wound()`. If the delete path removes/rewrites that test method,
  COMB-102's `test_path` will point to nothing (or to a rewritten test that no longer proves what
  COMB-102's text claims). Since COMB-102 is P0 (requires a passing `test_path` per project rule),
  this is a real risk of leaving a P0 ledger entry broken as a side effect of an in-scope change to
  an out-of-scope-named entry. Recommend the planner explicitly decide whether COMB-102's
  `test_path` correction rides along with this ticket (mechanically necessary either way once
  `test_wound_infliction_massive_hit` changes) or is deferred to a fast follow-up — but leaving it
  silently broken is not an option under the project's P0 test_path rule.
- **COMB-104's wrong-class `test_path` is a pre-existing, unrelated bug**, not caused by this
  ticket and not required by this ticket's scope to fix — flagged for awareness only, since a
  planner scanning the same file region might otherwise conflate it with this ticket's work.
- If "delete" is chosen: `tests/unit/core/test_rpg_depth.py:40`'s import list includes
  `WOUND_THRESHOLD_RATIO` — this import must be removed alongside the constant, or the test file
  fails to collect (`ImportError`).

## Anti-Drift Hazards

- Do not touch `WoundService.create_wound()`, `get_wound_stat_penalties()`, or
  `get_scar_stat_penalties()` — all three are live and out of this ticket's scope (owned by the
  now-completed `TCK-20260824-WOUND-PENALTY-FORMULA-WIRING`).
- Do not touch the live 25% inline threshold in `combat.py:607` itself — the ticket's scope is
  resolving the *dead* 40% branch and the doc/ledger consistency around it, not changing live
  gating behavior.
- Do not silently fix COMB-102/COMB-104 as an unannounced side effect — if `test_path` correction
  becomes mechanically necessary for COMB-102 as a consequence of touching
  `TestWoundInfliction::test_wound_infliction_massive_hit`, document that explicitly in this
  ticket's Implementation Notes/Files Changed, the same way `TCK-20260824-WOUND-PENALTY-FORMULA-
  WIRING` explicitly documented touching COMB-072/073/102/103/104 as part of its own scope.
- Do not conflate this ticket with `TCK-20260824-TACTICAL-WOUND-SCAR-WIRING` (a separate, not-yet-
  built scar-formation mechanic) or the wound-healing event-extractor tuple/list bug
  (`TCK-20260829-HOTFIX-WOUND-SCAR-EVENT-EXTRACTOR-TUPLE-BLIND`, filed but not implemented) — both
  are unrelated follow-ups surfaced by sibling tickets, not this ticket's concern.
- If "keep" is chosen, use `tools/parity_ledger_writer.py` (the sanctioned schema-validating write
  path) to update COMB-290, not a raw Edit on the YAML — per this session's own established
  precedent on parity ledger file risk.

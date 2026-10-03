---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260824-TACTICAL-WOUND-SCAR-WIRING
artifact_type: plan
tags: [combat]
---

# Implementation Plan — TCK-20260824-TACTICAL-WOUND-SCAR-WIRING

## Summary

Wire the existing `WoundService.get_wound_stat_penalties`/`get_scar_stat_penalties` aggregators
(`src/engine/rpg_depth.py:139-173`, confirmed unmodified) into three narrow, additive spots inside
`TacticalDecisionSystem.evaluate_entity_intent` (`src/engine/tactical.py`): the cover-seeking/retreat
gate (line 443), the same gate's hp threshold (scar durability), and the PROTECTOR
guard-wounded-ally branch (lines 497-507). All three changes are pure new *readers* — never
mutating wounds/scars, never touching the aggregators themselves, and never widening the existing
hp_percent-only paths for zero-wound/zero-scar entities. Two module-level distress helpers
(`_wound_distress`, `_scar_distress`, `_combined_wound_scar_distress`) centralize the "sum the
aggregator's dict output into one scalar" logic so no branch hand-derives penalty math. Two new
threshold constants are grounded in `WoundService.create_wound()`'s existing severity boundaries
(`rpg_depth.py:118-125`), not picked arbitrarily. A new parity ledger entry (`COMB-315`) and a new
Mechanics Bible bullet document the new tactical-decision consequence, kept distinct from
COMB-268's untouched hp-ratio-only entry.

## Resolved Design Decisions (Planner's Call)

These were flagged as open in `investigation.md`'s Risks and Open Questions. Per the task
instruction, the planner resolves them here rather than punting back up:

1. **AC #1 "sufficient severity" threshold**: `WOUND_DISTRESS_COVER_THRESHOLD = 9.0`, defined as
   the summed output of `WoundService.get_wound_stat_penalties(wounds).values()`. This equals the
   sum produced by a single active wound at `severity == 0.6` — the exact severity boundary
   `WoundService.create_wound()` (`rpg_depth.py:120-123`, confirmed by this session's own read)
   already uses to select `"SLASH"` as the wound `kind`: `atk_penalty=int(0.6*3)=1`,
   `def_penalty=int(0.6*2)=1`, `speed_penalty=int(0.6*2)=1`, `max_hp_penalty=int(0.6*10)=6`, sum
   `= 9.0`. Not an arbitrary number — it reuses an existing formula boundary.
2. **AC #2 combination logic**: option (b) from investigation.md's three options — an independent
   OR-condition added alongside the existing `hp_ratio < 0.8`/`< 0.7` checks, using a *lower*
   threshold (`PROTECTOR_GUARD_DISTRESS_THRESHOLD = 5.0`, corresponding to `severity == 0.4`:
   `atk=1, def=0, speed=0, max_hp=4`, sum `= 5.0`) than the self-retreat trigger, since guarding a
   teammate is a softer response than fleeing. This applies to both the leader check (Priority 1)
   and the "any other ally" predicate (Priority 2). Investigation also asked whether Priority 2
   should switch from "first ally matching the predicate" to "highest-distress ally among
   qualifiers" — **this plan keeps the existing first-match selection mechanism and only widens the
   *predicate*** (adds the OR-condition), because `test_plan.md`'s AC #2 test (test 3) only requires
   that a wound/scar-distressed ally *qualifies* when hp_ratio alone would not have selected them —
   it does not require ranking multiple qualifying allies by severity. Reordering to
   highest-distress-first would be extra, untested surface area beyond what the ACs ask for
   (Planning Rule: "Never plan more work than the ticket scope").
3. **AC #3 scar durability mechanism**: a capped, per-scar-point bump to the cover-seeking branch's
   `hp_percent` threshold (`0.4 -> 0.4 + min(SCAR_DISTRESS_HP_THRESHOLD_BUMP_CAP, scar_distress *
   SCAR_DISTRESS_HP_THRESHOLD_BUMP_PER_POINT)`), since `ScarState` has no `severity` field
   (`src/core/state.py:104-112`, confirmed) and its own docstring at line 106 (confirmed) describes
   it as "lesser but persistent" — a small, capped, always-on threshold shift is the design that
   best matches that description and produces a *durable* difference (present even at zero active
   wounds) rather than a one-off trigger.

## Steps

### Step 1 — Import WoundService and add threshold constants
**Files:** `src/engine/tactical.py`

**Change:** `tactical.py` currently only lazily imports `LeashService` from
`src.engine.rpg_depth` inside `evaluate_entity_intent` at line 106 (confirmed by this session's own
read: `from src.engine.rpg_depth import LeashService`) — there is no module-level import of
`rpg_depth` anywhere in the file (confirmed by reading lines 1-120), which is the existing pattern
this file uses to avoid whatever circular-import concern motivated deferring `rpg_depth` imports
to call-time (several other `src.engine.*`/`src.domains.*` imports in this file are also deferred
inline, e.g. lines 56, 77-78, 83, 301-302). Follow that same pattern: change line 106 to
`from src.engine.rpg_depth import LeashService, WoundService`.

Add three module-level constants near the top of the file (after the existing imports, before the
`TacticalDecisionSystem` class definition at line 23), each with a comment citing the specific
`rpg_depth.py` boundary it reuses (see "Resolved Design Decisions" above for the exact numbers and
citations — copy that reasoning into the code comments verbatim, not as a bare magic number):

```python
# See TCK-20260824-TACTICAL-WOUND-SCAR-WIRING plan.md "Resolved Design Decisions" for full derivation.
WOUND_DISTRESS_COVER_THRESHOLD = 9.0
PROTECTOR_GUARD_DISTRESS_THRESHOLD = 5.0
SCAR_DISTRESS_HP_THRESHOLD_BUMP_PER_POINT = 0.01
SCAR_DISTRESS_HP_THRESHOLD_BUMP_CAP = 0.10
```

**Do NOT touch:** Any other import in the file; do not move the `LeashService` import to module
level (keep the existing lazy-import pattern/location, just add `WoundService` to the same line).

**Verify:** No behavioral test yet — verified transitively by Step 3's test (import must resolve
without `ImportError` for any existing test in `tests/unit/combat/` to keep passing, e.g.
`tests/unit/combat/test_engagement_behavior.py::test_attack_vs_pursuit_intent`).

---

### Step 2 — Add distress-aggregation helper functions
**Files:** `src/engine/tactical.py`

**Change:** Add three module-level private helper functions (placed after the constants from Step
1, before the `TacticalDecisionSystem` class), each a thin wrapper that sums an aggregator's
returned dict — never re-deriving `atk_penalty`/`def_penalty`/etc. inline (AC #4):

```python
def _wound_distress(wounds) -> float:
    """Single distress scalar from active wound penalties.
    Reuses WoundService.get_wound_stat_penalties (rpg_depth.py:139-157) -- sums its
    returned dict, never re-derives w.atk_penalty/etc. inline."""
    return sum(WoundService.get_wound_stat_penalties(wounds).values())


def _scar_distress(scars) -> float:
    """Single distress scalar from scar penalties.
    Reuses WoundService.get_scar_stat_penalties (rpg_depth.py:159-173) -- sums its
    returned dict. Note the dict has no 'max_hp_penalty' key (ScarState has no such
    field, src/core/state.py:104-112); summing .values() never indexes by key name,
    so that asymmetry cannot KeyError here."""
    return sum(WoundService.get_scar_stat_penalties(scars).values())


def _combined_wound_scar_distress(wounds, scars) -> float:
    """Combined wound + scar distress signal, used only by the PROTECTOR guard
    branch (AC #2's 'ally wound/scar severity as an additional signal')."""
    return _wound_distress(wounds) + _scar_distress(scars)
```

`WoundService` here resolves to the module-level name bound by Step 1's import inside
`evaluate_entity_intent` -- since these helpers are called *from within* `evaluate_entity_intent`
(never at import time or from outside it), and Python resolves free variables at call time against
the enclosing module namespace, the lazy import executed earlier in the same call stack (line 106)
will already have bound `WoundService` into the module globals by the time any of these three
helpers run. (If a future edit calls these helpers from a code path that never executes line 106
first, that call will raise `NameError` -- Step 3/4/5 below only ever call them after line 106 has
already run in the same `evaluate_entity_intent` invocation, so this is not a concern for this
ticket's own new call sites.)

**Do NOT touch:** `WoundService.get_wound_stat_penalties`/`get_scar_stat_penalties` themselves
(`rpg_depth.py:139-173`) -- these helpers only call them, never modify them.

**Verify:** No standalone test for the helpers in isolation; exercised indirectly by Steps 3-5's
tests. (Test 5 / Step 6 below additionally patches the underlying `WoundService` methods to prove
these helpers still route through them.)

---

### Step 3 — Wire wound-distress trigger into the cover-seeking/retreat gate (AC #1)
**Files:** `src/engine/tactical.py`, new test file `tests/unit/combat/test_tactical_wound_scar_wiring.py`

**Change:** At `tactical.py:442-443` (confirmed exact text via this session's own read):
```python
hp_percent = entity.combat.hp / max(1, entity.combat.max_hp)
if (role == "SKIRMISHER" or hp_percent < 0.4):
```
Change to:
```python
hp_percent = entity.combat.hp / max(1, entity.combat.max_hp)
wound_distress = _wound_distress(entity.combat.wounds)
if (role == "SKIRMISHER" or hp_percent < 0.4 or wound_distress >= WOUND_DISTRESS_COVER_THRESHOLD):
```
This is a pure OR-widening of the existing gate -- for any entity with `entity.combat.wounds == []`
(or all wounds healed, since `_wound_distress`/`get_wound_stat_penalties` already skip `w.healed`
wounds per `rpg_depth.py:147`), `wound_distress == 0.0 < 9.0`, so the condition reduces to exactly
`role == "SKIRMISHER" or hp_percent < 0.4` -- unchanged from today. This satisfies the Anti-Drift
Hazard that zero-wound entities must behave identically to before.

Do not yet touch the `hp_percent < 0.15` pure-retreat check at line 459, or the `0.4` literal
itself (that is Step 4's job, kept separate so this step's diff is reviewable as "add an OR
condition" in isolation).

Add the new test file `tests/unit/combat/test_tactical_wound_scar_wiring.py` (new sibling file to
`test_engagement_behavior.py`, chosen over appending to that already-large file per
`test_plan.md`'s "planner's call" note -- keeps this ticket's tests isolated and traceable as one
unit) with two tests per `test_plan.md` items 1-2, following the `V2EntityBuilder(...).combat(...)`
+ bare `AuthoritativeState(entities={...})` pattern already used in
`tests/unit/combat/test_engagement_behavior.py`:
- `test_severe_wound_triggers_cover_seeking_at_high_hp`: entity with `hp=90, max_hp=100`
  (`hp_percent=0.9`), `wounds=[WoundState(id=..., kind="SLASH", severity=0.6, tick_inflicted=0,
  atk_penalty=1, def_penalty=1, speed_penalty=1, max_hp_penalty=6)]` (matching
  `WoundService.create_wound(damage=60, max_hp=100, ...)`'s actual output so the wound is
  internally consistent, not just a distress-score-matching fabrication), a ranged hostile present
  (`combat.range > 2`) -> asserts `payload_set["reason"] == "SEEK_COVER"`.
- `test_unwounded_entity_at_same_hp_does_not_trigger_wound_branch`: identical setup but
  `wounds=[]` -> asserts the cover-seeking/retreat branch does NOT fire (falls through past line
  469 to whatever the next applicable branch produces, or returns a non-`SEEK_COVER`/
  `PANIC_RETREAT` reason) -- this is the negative control guarding against the threshold silently
  re-implementing `hp_percent` under a new name.

**Do NOT touch:** The `ranged_threats`/`cover_pos` logic (lines 445-456), the `hp_percent < 0.15`
retreat sub-branch (lines 458-469), `PositioningService.find_nearest_cover` -- none of these need
changes for AC #1, only the outer gate.

**Verify:** `pytest tests/unit/combat/test_tactical_wound_scar_wiring.py::test_severe_wound_triggers_cover_seeking_at_high_hp tests/unit/combat/test_tactical_wound_scar_wiring.py::test_unwounded_entity_at_same_hp_does_not_trigger_wound_branch -v`, plus regression: `tests/unit/combat/test_engagement_behavior.py::test_retreat_behavior` must still pass unchanged (proves the existing `hp_percent < 0.15` unwounded path is untouched).

---

### Step 4 — Wire scar-distress hp-threshold bump into the same gate (AC #3)
**Files:** `src/engine/tactical.py`, `tests/unit/combat/test_tactical_wound_scar_wiring.py`

**Depends on:** Step 3 (edits the same `if` line Step 3 just changed).

**Change:** Extend the line Step 3 produced:
```python
wound_distress = _wound_distress(entity.combat.wounds)
if (role == "SKIRMISHER" or hp_percent < 0.4 or wound_distress >= WOUND_DISTRESS_COVER_THRESHOLD):
```
to:
```python
wound_distress = _wound_distress(entity.combat.wounds)
scar_distress = _scar_distress(entity.combat.scars)
scar_hp_bump = min(
    SCAR_DISTRESS_HP_THRESHOLD_BUMP_CAP,
    scar_distress * SCAR_DISTRESS_HP_THRESHOLD_BUMP_PER_POINT,
)
if (
    role == "SKIRMISHER"
    or hp_percent < (0.4 + scar_hp_bump)
    or wound_distress >= WOUND_DISTRESS_COVER_THRESHOLD
):
```
For an entity with `entity.combat.scars == []`, `scar_distress == 0.0`, `scar_hp_bump == 0.0`, so
`0.4 + scar_hp_bump == 0.4` -- again a no-op for zero-scar entities, preserving the Anti-Drift
regression guarantee.

Add one test per `test_plan.md` item 4:
- `test_scarred_entity_differs_from_unwounded_entity_at_same_hp_ratio`: two entities, both
  `hp=45, max_hp=100` (`hp_percent=0.45`, deliberately chosen to sit just above the unscarred 0.4
  threshold but below a scarred threshold once the bump is applied), zero wounds on both. Entity A:
  `scars=[]`. Entity B: `scars=[ScarState(id=..., wound_kind="SLASH", tick_created=0,
  atk_penalty=1, def_penalty=1, speed_penalty=1)]` (`scar_distress = 3.0`, `scar_hp_bump = 0.03`,
  effective threshold `0.43` -- still not enough to flip `0.45`; use `scars` summing to at least
  `scar_distress >= 5.0` instead, e.g. two scars of that shape, so `scar_hp_bump = 0.05`, effective
  threshold `0.45`, and assert with `hp=44` so `hp_percent=0.44 < 0.45` for B but
  `0.44 >= 0.4` -- wait, `0.44 >= 0.4` is false for the unscarred check too since `0.44` is not
  `< 0.4`; pick `hp=44, max_hp=100` so `hp_percent = 0.44`, ensure `scar_distress` is large enough
  that `0.4 + scar_hp_bump > 0.44`, e.g. 5 scars each contributing `atk=1` (`scar_distress=5.0`,
  `scar_hp_bump=0.05`, threshold `0.45 > 0.44`). With a ranged hostile present, assert entity B
  (scarred) reaches `SEEK_COVER` while entity A (unscarred, same `hp_percent=0.44`) does not.
  Whoever implements this step must recompute the exact `hp`/`scars` numbers so the arithmetic
  genuinely straddles the two thresholds -- the values above are illustrative, not
  copy-paste-exact; use `V2EntityBuilder(...).combat(scars=[...])` (`src/core/builder.py:238-274`,
  confirmed to accept a `scars: Optional[List[ScarState]]` kwarg) to hand-construct scars, since
  scars have zero production producers (investigation.md, confirmed).

**Do NOT touch:** The `0.15` pure-retreat literal, or Step 3's `wound_distress`/
`WOUND_DISTRESS_COVER_THRESHOLD` logic (only the `hp_percent < 0.4` term changes shape).

**Verify:** `pytest tests/unit/combat/test_tactical_wound_scar_wiring.py::test_scarred_entity_differs_from_unwounded_entity_at_same_hp_ratio -v`, plus regression: Step 3's two tests and `test_retreat_behavior` still pass.

---

### Step 5 — Wire combined wound/scar distress into the PROTECTOR guard branch (AC #2)
**Files:** `src/engine/tactical.py`, `tests/unit/combat/test_tactical_wound_scar_wiring.py`

**Change:** At `tactical.py:497-507` (confirmed exact text via this session's own read, the "5.3
Guarding Logic" branch reached only when `group and role == "PROTECTOR"` inside the
hostiles-present path -- distinct from the no-hostiles branch at lines 312-331 which this step must
not touch):
```python
# Priority 1: Guard Leader if they are interacting or low HP
leader = state.entities.get(group.leader_id)
wounded_ally = None
if leader and leader.id != entity.id:
     hp_ratio = leader.combat.hp / max(1, leader.combat.max_hp)
     if leader.interaction.target_node_id is not None or hp_ratio < 0.8:
          wounded_ally = leader

# Priority 2: Guard any other wounded ally
if not wounded_ally:
     wounded_ally = next((a for a in allies if a.combat.hp / max(1, a.combat.max_hp) < 0.7), None)
```
Change to:
```python
# Priority 1: Guard Leader if they are interacting, low HP, or wound/scar-distressed
leader = state.entities.get(group.leader_id)
wounded_ally = None
if leader and leader.id != entity.id:
     hp_ratio = leader.combat.hp / max(1, leader.combat.max_hp)
     leader_distress = _combined_wound_scar_distress(leader.combat.wounds, leader.combat.scars)
     if (
         leader.interaction.target_node_id is not None
         or hp_ratio < 0.8
         or leader_distress >= PROTECTOR_GUARD_DISTRESS_THRESHOLD
     ):
          wounded_ally = leader

# Priority 2: Guard any other wounded or wound/scar-distressed ally
if not wounded_ally:
     wounded_ally = next(
         (
             a for a in allies
             if a.combat.hp / max(1, a.combat.max_hp) < 0.7
             or _combined_wound_scar_distress(a.combat.wounds, a.combat.scars) >= PROTECTOR_GUARD_DISTRESS_THRESHOLD
         ),
         None,
     )
```
For any leader/ally with empty `wounds`/`scars`, `leader_distress`/the ally's combined distress is
`0.0 < 5.0`, so both predicates reduce to exactly their pre-change form -- additive, not a
replacement (Anti-Drift Hazard).

Add one test per `test_plan.md` item 3, in the same new test file, using the `GroupRecord(id=...,
leader_id=..., member_ids={...}, anchor=..., roles={eid: "PROTECTOR"})` construction pattern from
`tests/unit/social/test_domain_7_social.py::test_protector_guarding` (lines 134-156, confirmed
existing pattern) -- but with `hostiles` populated in `state.entities` (a live enemy entity with
`combat.alive=True` on an opposing faction) so evaluation reaches the 492-519 branch, not the
312-331 no-hostiles branch:
- `test_protector_guards_wound_distressed_ally_over_healthier_ally`: PROTECTOR entity in a group
  with two non-leader allies. Ally X: `hp_ratio` around `0.75` (above both the `0.7` and `0.8`
  thresholds, so would not qualify by hp_ratio alone) but `wounds`/`scars` summing to
  `combined_distress >= 5.0`. Ally Y: `hp_ratio` slightly lower than X's but still `>= 0.7` (so
  also would not qualify by hp_ratio alone) and zero wounds/scars. Assert the PROTECTOR's
  `payload_set["target_id"] == <Ally X's id>` (guarding the distressed ally) with
  `payload_set["reason"] == "GUARDING_ALLY"`, proving wound/scar distress is consulted as an
  independent qualifying signal, not just `hp_ratio`.

**Do NOT touch:** `tactical.py:312-331` (the unrelated no-hostiles PROTECTOR/VANGUARD branch --
`tests/unit/social/test_domain_7_social.py::test_protector_guarding` must keep passing unmodified,
proving this); the bracketing logic at 471-489; `PositioningService.find_guard_position`.

**Verify:** `pytest tests/unit/combat/test_tactical_wound_scar_wiring.py::test_protector_guards_wound_distressed_ally_over_healthier_ally -v`, plus regression: `tests/unit/social/test_domain_7_social.py::test_protector_guarding` still passes unchanged.

---

### Step 6 — Add aggregator-reuse regression guard (AC #4)
**Files:** `tests/unit/combat/test_tactical_wound_scar_wiring.py`

**Depends on:** Steps 3, 4, 5 (needs all three new branches to exist so the spy has call sites to
observe).

**Change:** Add `test_wound_scar_tactical_reads_reuse_woundservice_aggregators` per
`test_plan.md` item 5: use `unittest.mock.patch.object(WoundService, "get_wound_stat_penalties",
wraps=WoundService.get_wound_stat_penalties)` and the same for `get_scar_stat_penalties` (imported
from `src.engine.rpg_depth`), run `evaluate_entity_intent` against a wounded-and-scarred entity
(reusing one of the fixtures from Steps 3-5), and assert both mocks were called at least once.
`wraps=` preserves real return values so the rest of the test's assertions about the resulting
`EntityUpdate` still hold -- this is a spy, not a stub. This guards against a future edit silently
reintroducing inline `w.atk_penalty for w in entity.combat.wounds`-style re-derivation that happens
to produce output-equivalent results to Steps 3-5's tests (which alone would not catch that
regression, since they only assert on the final `EntityUpdate`, not on *how* the number was
computed).

**Do NOT touch:** `WoundService.get_wound_stat_penalties`/`get_scar_stat_penalties` themselves --
`wraps=` must call through to the real implementation, never replace it with a mock return value,
since Steps 3-5's own assertions depend on real penalty numbers.

**Verify:** `pytest tests/unit/combat/test_tactical_wound_scar_wiring.py -v -m "not slow"` (full new file), plus the full scoped regression command from `test_plan.md`:
```
pytest tests/unit/combat/ tests/unit/movement/ tests/unit/tactical/ tests/unit/social/test_domain_7_social.py tests/unit/core/test_rpg_depth.py tests/unit/core/test_read_only_guard.py -v -m "not slow"
```

---

### Step 7 — Document the new tactical-decision consequence in the Mechanics Bible
**Files:** `docs/mechanics/02_combat_laws.md`

**Depends on:** Steps 1-6 (must describe the actual landed thresholds/behavior, not a plan).

**Change:** Section 5 "Wound Infliction" (`docs/mechanics/02_combat_laws.md:70-92`, confirmed via
this session's own read) currently documents the wound/scar penalty formula and permanence but has
zero mention of any tactical-decision consequence -- add a new bullet (or short subsection) after
the existing "Wound Permanence" bullet (line 92) stating: an active wound with summed
`get_wound_stat_penalties` output `>= 9.0` (severity `>= 0.6` for a single wound) independently
triggers `TacticalDecisionSystem`'s cover-seeking/retreat behavior regardless of `hp_percent`;
scars raise that branch's `hp_percent` threshold by `0.01` per aggregate scar-penalty point (capped
at `+0.10`); and PROTECTOR-role allies with combined wound/scar distress `>= 5.0` become an
additional guard-priority signal alongside the existing `hp_ratio` checks. Cite
`src/engine/tactical.py` line ranges for each (Steps 3/4/5's final line numbers once landed).

Also correct a stale, now-contradicted sentence at the end of the existing "Wound Permanence"
bullet (line 90-92, confirmed): "Permanent Scars ... are planned to form via a separate mechanic,
tracked by `TCK-20260824-TACTICAL-WOUND-SCAR-WIRING` (not yet implemented)". This ticket does
**not** implement scar *production* (that remains a settled, separate out-of-scope decision per
`TCK-20260824-WOUND-HEALING-DECISION` and this ticket's own Out of Scope bullet) -- it only adds a
new *consumer* of scars that are hand-constructed by tests. Reword that sentence to stop citing
this ticket as the (not-yet-implemented) scar-production mechanism, since after this ticket lands
that citation would be misleading (a reader would expect scar production to now exist). Do not
otherwise touch the citation's substance (scars still have zero production producers) -- only fix
the misattribution.

**Do NOT touch:** `docs/mechanics/01_entity_anatomy.md` (per investigation.md, its Section 6
"Permanent Scars" covers the data model/permanence decision, not tactical consequences -- out of
scope here); Section 5's existing formula/permanence content beyond the one stale sentence above.

**Verify:** No automated test; verified by doc review against the actual landed code (Steps 1-6)
during the ticket's own Verify phase, and by the "Parity" rule in project CLAUDE.md requiring
doc/code semantic parity.

---

### Step 8 — Add new parity ledger entry, distinct from COMB-268 (AC #5)
**Files:** `docs/parity_ledger/combat_movement.yaml`

**Depends on:** Steps 1-6 (needs real, landed `test_path` values -- this entry must not repeat
COMB-268's `test_path: null` gap, per Anti-Drift Hazard).

**Change:** COMB-268 (`docs/parity_ledger/combat_movement.yaml:2795-2803`, confirmed via this
session's own read: `text: "Low HP affects tactical choice."`, `status: verified`, `priority: P0`,
`test_path: null`) covers only the pre-existing `hp_percent`-based branch and must not be edited or
reused. The highest existing `COMB-` id in this file is `COMB-314` (confirmed via this session's own
grep) -- add a new entry `COMB-315` after it, following the existing YAML entry shape (`id`, `text`,
`status`, `priority`, `legacy_evidence`, `v2_evidence`, `proof_type`, `test_path`,
`divergence_note`):
```yaml
- id: COMB-315
  text: Wound/scar severity affects tactical decision-making (cover-seeking, retreat threshold, and PROTECTOR guard priority), independent of and in addition to raw hp_percent/hp_ratio checks.
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: "TacticalDecisionSystem.evaluate_entity_intent wires WoundService.get_wound_stat_penalties/get_scar_stat_penalties into the cover-seeking/retreat gate and PROTECTOR guard-wounded-ally branch (src/engine/tactical.py)."
  proof_type: unit_test
  test_path: tests/unit/combat/test_tactical_wound_scar_wiring.py
  divergence_note: null
```
(`priority: P1` matches the ticket's own `## Priority` field; adjust `text`/`v2_evidence` wording
only if the actual landed line numbers/behavior differ from this plan by the time Step 8 executes.)

**Do NOT touch:** COMB-268, COMB-269, COMB-072/073/COMB-102/103/104, COMB-290, COMB-314, COMB-296
(all confirmed out of scope per investigation.md's Parity Ledger Overlap section) -- add only the
new entry, never edit an existing one's `status`/`v2_evidence`/`test_path`.

**Verify:** Parity ledger schema validation (whatever `tools/` script the project uses to validate
`docs/parity_ledger/*.yaml` against `schema.json`, run as part of the ticket's Parity phase); no
unit test directly exercises the YAML file itself.

## Scope Guards

- Do not touch `src/engine/combat.py::_get_wound_infliction()` (wound/scar production stays exactly
  as-is).
- Do not touch `src/engine/rpg_depth.py::WoundService.create_wound()`/
  `get_wound_stat_penalties()`/`get_scar_stat_penalties()` (only new callers are added elsewhere).
- Do not touch `src/engine/rpg_depth.py::WoundService` at all, or `src/engine/apply.py`, or
  `WoundPatch.apply()` (`src/engine/patches.py:639`) -- no durable-state mutation paths change.
- Do not wire `speed_penalty` into `SkillScalingService.get_effective_stats()`
  (`rpg_depth.py:341-389`) -- that is a separate, already-flagged follow-up, not this ticket's job.
- Do not touch `tactical.py:312-331` (the unrelated no-hostiles PROTECTOR/VANGUARD "Role-Based
  Obligation" branch) -- `test_protector_guarding` in `tests/unit/social/test_domain_7_social.py`
  must keep passing completely unmodified as proof.
- Do not modify or reinterpret the `COMB-268` parity ledger entry -- add `COMB-315` as a wholly new,
  distinct entry instead.
- Do not construct or mutate `WoundState`/`ScarState`/`WoundUpdate` from inside `tactical.py` at
  any point -- every new read in Steps 3-5 is strictly read-only against
  `entity.combat.wounds`/`.scars` and `ally.combat.wounds`/`.scars`/`leader.combat.wounds`/`.scars`.
- Do not change the underlying `WoundState`/`ScarState` dataclass shape in `src/core/state.py`
  (out of scope per the ticket; those fields were only read, never added to or altered).
- Do not touch `docs/mechanics/01_entity_anatomy.md`.
- Do not widen or alter the existing `hp_percent < 0.15` pure-retreat literal, the `ranged_threats`
  filter, the bracketing logic (471-489), or the intercept logic (521+).

## Dependency Map

- Step 1 (import + constants) -> required by Steps 2, 3, 4, 5 (all reference the constants and/or
  `WoundService`).
- Step 2 (helper functions) -> required by Steps 3 (`_wound_distress`), 4 (`_scar_distress`), 5
  (`_combined_wound_scar_distress`).
- Step 3 -> Step 4 (Step 4 edits the exact `if` line Step 3 produces; cannot be reordered).
- Step 5 is independent of Steps 3-4 (different code region, lines 497-507 vs 442-443) but still
  depends on Steps 1-2.
- Step 6 depends on Steps 3, 4, 5 all being landed (needs real call sites in all three branches to
  spy on).
- Step 7 (docs) and Step 8 (parity ledger) both depend on Steps 1-6 being complete and their exact
  final line numbers/test paths known -- do these last.
- Steps 7 and 8 are mutually independent (different files) and can be done in either order once
  Steps 1-6 are done.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: active WoundState of sufficient severity triggers cover-seeking/retreat independently of hp_percent | Step 1 (constant), Step 2 (`_wound_distress`), Step 3 (gate wiring) | `tests/unit/combat/test_tactical_wound_scar_wiring.py::test_severe_wound_triggers_cover_seeking_at_high_hp`, `::test_unwounded_entity_at_same_hp_does_not_trigger_wound_branch` (negative control), regression `tests/unit/combat/test_engagement_behavior.py::test_retreat_behavior` |
| AC #2: PROTECTOR guard-wounded-ally selection considers ally wound/scar severity as an additional signal | Step 1 (constant), Step 2 (`_combined_wound_scar_distress`), Step 5 (branch wiring) | `tests/unit/combat/test_tactical_wound_scar_wiring.py::test_protector_guards_wound_distressed_ally_over_healthier_ally`, regression `tests/unit/social/test_domain_7_social.py::test_protector_guarding` |
| AC #3: a scarred entity exhibits a durable behavior difference from an unwounded entity at the same hp_ratio | Step 1 (constants), Step 2 (`_scar_distress`), Step 4 (threshold bump wiring) | `tests/unit/combat/test_tactical_wound_scar_wiring.py::test_scarred_entity_differs_from_unwounded_entity_at_same_hp_ratio` |
| AC #4: new reads reuse `WoundService.get_wound_stat_penalties`/`get_scar_stat_penalties` rather than re-deriving inline | Step 2 (helpers wrap the aggregators exclusively), enforced across Steps 3, 4, 5 | `tests/unit/combat/test_tactical_wound_scar_wiring.py::test_wound_scar_tactical_reads_reuse_woundservice_aggregators` (Step 6) |
| AC #5 (Scope bullet): new parity_ledger entry distinct from COMB-268 | Step 8 | Parity ledger schema validation; `COMB-315.test_path` points at the Step 6 test file |

## Anti-Drift Notes

- **Zero-wound/zero-scar entities must be provably unaffected.** Every gate change in Steps 3-5 is
  written as an OR-widening or an additive threshold bump that reduces to exactly the pre-change
  expression when `wounds == []`/`scars == []`. Steps 3 and 4 explicitly re-run
  `test_retreat_behavior` (unwounded, hp_percent=0.1) as a regression check; Step 5 explicitly
  re-runs `test_protector_guarding` (the untouched no-hostiles branch) as a regression check. Do
  not let a future edit "simplify" these OR-conditions into a replacement of the original
  `hp_percent`/`hp_ratio` checks.
- **Never conflate the two PROTECTOR branches.** `tactical.py:312-331` (no-hostiles,
  leader-interacting) is untouched; only `tactical.py:492-519` (hostiles-present, "5.3 Guarding
  Logic") is edited in Step 5. Step 5's new test must populate `hostiles` in `state.entities` with
  a live, opposing-faction entity to actually reach the edited branch -- a test that forgets this
  would silently exercise the wrong, already-covered branch and give false confidence (this exact
  mistake is called out by name in investigation.md's Anti-Drift Hazards).
- **`ScarState` has no `severity` field and no `max_hp_penalty` key in its aggregator output.**
  `_scar_distress`/`_combined_wound_scar_distress` only ever call `.values()` on the dict
  `get_scar_stat_penalties` returns -- never index it by a wound-only key name like
  `"max_hp_penalty"`. Any future edit that tries to read a scar's "severity" or "max_hp_penalty"
  directly is reading a field that does not exist on `ScarState` (`src/core/state.py:104-112`).
- **Scars have zero production producers today.** Every scar used in this ticket's new tests must
  be hand-constructed via `V2EntityBuilder(...).combat(scars=[ScarState(...)])`
  (`src/core/builder.py:238-274`, confirmed to accept the kwarg) -- there is no live code path that
  creates a `ScarState` to exercise instead.
- **`speed_penalty` stays unwired.** Neither `_wound_distress` nor `_scar_distress` special-cases
  `speed_penalty` differently from the other keys -- it is summed into the distress scalar along
  with `atk_penalty`/`def_penalty`(/`max_hp_penalty` for wounds) exactly as
  `get_wound_stat_penalties`/`get_scar_stat_penalties` already compute it. This is *not* the same
  thing as wiring `speed_penalty` into `get_effective_stats()` (a stat-computation change, still out
  of scope) -- summing it into a decision-making distress scalar here is a different, in-scope use
  of an already-computed number.
- **`WoundUpdate`/apply-path tuple-vs-list shape is a non-issue for these reads.** Per
  investigation.md, `get_wound_stat_penalties`/`get_scar_stat_penalties` iterate with a bare `for w
  in wounds`, so they (and by extension the new `_wound_distress`/`_scar_distress` wrappers) are
  agnostic to whether `entity.combat.wounds`/`.scars` is a `list` (test-constructed) or `tuple`
  (real apply-path-committed) -- no special-casing needed in Steps 3-5.

## Unresolved Questions

None. The two open questions investigation.md flagged for this planning phase (AC #1's severity
threshold, AC #2's combination logic) are resolved above under "Resolved Design Decisions," with
concrete values and citations to existing code boundaries (`WoundService.create_wound()`'s
severity-based `kind` selection). No other genuinely undecidable design branch point remains --
the exact test-fixture arithmetic in Step 4's test (which `hp`/`scars` values straddle the bumped
threshold) is left for the implementer to compute precisely against the final constants, but the
*mechanism* and *constants* themselves are fully specified, so this is an implementation detail,
not an open design question.

## Deviations

**Step 1/2's import-scope claim was factually wrong; fixed with a real module-level import.**
Step 2's rationale ("Python resolves free variables at call time against the enclosing module
namespace, the lazy import executed earlier in the same call stack (line 106) will already have
bound `WoundService` into the module globals") does not hold: a `from ... import X` statement
executed *inside* a function body binds `X` into that function's **local** scope, not the module's
global namespace. The module-level helper functions `_wound_distress`/`_scar_distress`/
`_combined_wound_scar_distress` look up `WoundService` in the module's global scope when called --
that name was never actually placed there by the plan's Step 1 change (`from src.engine.rpg_depth
import LeashService, WoundService` inside `evaluate_entity_intent`). Confirmed by running the new
tests before this fix: all 5 failed with `NameError: name 'WoundService' is not defined` at
`tactical.py:46` (inside `_wound_distress`).

**Fix applied**: added a genuine module-level `from src.engine.rpg_depth import WoundService`
import at the top of `tactical.py` (alongside the other top-of-file imports), and reverted the
in-function lazy import back to `from src.engine.rpg_depth import LeashService` only (its original,
pre-ticket form) -- since `WoundService` no longer needs a second, redundant local binding.
Confirmed safe: `src/engine/rpg_depth.py` only imports `src.core.state.TERRAIN_COST` at module
level, so there is no circular-import risk in promoting `WoundService`'s import to module level
(unlike whatever undocumented concern originally motivated deferring `LeashService`'s import,
which Scope Guards required to stay untouched -- and it was left untouched). All 5 new tests and
the full regression suite (227 tests) pass after this fix.

No other deviations. All 8 steps, the 4 threshold constants, all 3 helper functions, both gate
wirings, the PROTECTOR branch wiring, the 5 tests, the Mechanics Bible bullet, and the COMB-315
parity ledger entry match this plan's design exactly, at the exact line numbers/logic described
above (post-edit line numbers shifted by the 8 new lines added at the top of the cover-seeking
gate's `if` condition and by module-level constants/helpers/import, but the code shape is
unchanged from what this plan specified).

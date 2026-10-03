---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260831-READINESS-SPEED-FORMULA
artifact_type: investigation
tags: [combat, progression]
---

# Investigation — TCK-20260831-READINESS-SPEED-FORMULA

## Current Behavior

### `LevelingService.recalculate_combat_stats()` (`src/progression/leveling.py:76-184`)
Full function read. Precedent shape for a new derived-stat formula:
- Signature takes `attributes: AttributeComponent` plus optional `equipment`, `learned_skills`,
  `traits`, `current_role`, and `base_X` numeric defaults (`base_hp=100`, `base_atk=10`,
  `base_def=5`, `base_evasion=0.05`).
- Step 1 (lines 100-103) derives every base stat as `base_X + attribute_term` directly from the
  raw `attributes` argument — no other component (e.g. `CombatComponent`) is read inside this
  function. Existing precedent formulas:
  - `max_hp = base_hp + (vitality * 2) + int(endurance * 0.5)`
  - `atk = base_atk + int(strength * 0.5)`
  - `def_stat = base_def + int(vitality * 0.3)`
  - `evasion = base_evasion + (attributes.agility * 0.001)`
  - `move_cost = max(5.0, 10.0 + (total_weight / 5.0) - (attributes.agility * 0.1))` (Step 4,
    line 154, also agility-derived — same attribute, different sign/direction)
- The function builds and returns one flat `Dict[str, Any]` at the end (lines 176-184):
  `{"max_hp", "atk", "def_stat", "evasion", "range", "move_cost", "tactical_role"}`. **No
  `readiness_speed` key anywhere in this dict** — confirmed, matching Scope's finding. Nothing
  in the function reads or produces `readiness_speed`.
- Naming convention: dict keys mirror `CombatComponent` field names exactly (`max_hp`, `atk`,
  `def_stat`, `evasion`, `move_cost`, `tactical_role`) except `CombatComponent.range` is emitted
  as `"range"` too — a new `readiness_speed` entry should follow the same 1:1 key-name-matches-
  component-field convention.

### `AttributeComponent.agility` (`src/core/state.py:439-450`)
Confirmed field name is literally `agility` (line 442), type `int`, **dataclass default `5`**.
This is the concrete "reference/baseline agility" value: any entity built without an explicit
agility override (raw `AttributeComponent()`, or any `V2EntityBuilder` call that never sets
agility) gets `5`. There is no separate documented "average"/"reference" attribute constant
anywhere else in the codebase — `docs/mechanics/01_entity_anatomy.md` §1 states attributes
"scale from 1 to 99" but names no reference/average point. `data/content/foundation/attributes.yaml`
is a **non-numeric** lore/axis-description file ("STATE: REDESIGNED-CORE", "not runtime stats by
themselves") — it and `data/content/living/races.yaml`'s qualitative `agility: "medium"/"high"/...`
tags do not resolve to any numeric value found in `src/` (no `"medium"` → int mapping exists in
`src/content/`); they are a separate content layer, not the numeric `AttributeComponent.agility`
this ticket's formula reads. **Conclusion: the backward-compatibility reference point is the
dataclass default, `AttributeComponent.agility == 5`.** A formula of the shape
`readiness_speed = 10.0 + (agility - 5) * k` (or equivalent) is required to satisfy AC #2 — unlike
the other Step-1 formulas (which add an attribute term flat on top of `base_X` with no zero
point), this one must special-case around the reference value to preserve `readiness_speed==10.0`
at `agility==5`. Existing hardcoded test fixtures that never set agility explicitly (e.g.
`_build()` in `tests/unit/combat/test_readiness_regen.py:12` builds via `V2EntityBuilder(...)
.combat(...)` without ever calling `.attributes(...)`) get `AttributeComponent()`'s default
`agility=5`, so they are exactly the population Plan must keep passing.

### `CombatComponent.readiness_speed` (`src/core/state.py:311`)
Confirmed `readiness_speed: float = 10.0` (line 311), included in `to_canonical_dict()` (line
333). Currently it is **always** either the dataclass default or whatever a builder/test
explicitly overrides it to (`src/core/builder.py:253,272` — `V2EntityBuilder.combat(readiness_speed=...)`
is a raw pass-through kwarg, no derivation) — it is **never derived from `agility` or any other
attribute anywhere in `src/`.** Flow:
- **Passive accumulation** (`src/engine/apply.py:122-130`): every tick, if
  `comb.readiness < 100.0 and comb.readiness_speed > 0`, `readiness` increases by
  `comb.readiness_speed`, capped at 100.0. This reads whatever value is already stored on
  `CombatComponent` — it does not recompute `readiness_speed` itself.
- **Legality gate** (`src/engine/legality.py:143-220,317`, `LegalityServiceV2.verify_attack_legality`
  / `verify_readiness`): requires `attacker.combat.readiness >= 100.0` (i.e. rejects `< 100.0`)
  for any non-opportunity `ATTACK`. `readiness_speed` only matters here indirectly, by controlling
  how fast `readiness` climbs back to the 100.0 threshold after the `-100.0` reset on a successful
  attack (`docs/mechanics/02_combat_laws.md` §7).

### `get_effective_stats()` / PH8 block — current shape, post-`CLASS-TIER-BRANCHING`
Both read in full, current state:
- `SkillScalingService.get_effective_stats()` (`src/engine/rpg_depth.py:342-392`) now takes a
  `class_id: Optional[str] = None` kwarg (line 355). It applies `BreakthroughService.apply_bonuses()`
  then `ClassTierService.apply_bonuses(class_id, effective_attributes)` (lines 367-368) to produce
  `effective_attributes`, then calls `LevelingService.recalculate_combat_stats(effective_attributes, ...)`
  (lines 369-374) to get `base_stats`, then applies wound penalties, scar penalties, and an evasion
  clamp (lines 377-390), and returns `base_stats` (the same dict object, now amended) — line 392.
  **`get_effective_stats()` never touches `readiness_speed` either** — it has no wound/scar/clamp
  logic for it, and would simply pass through whatever key `recalculate_combat_stats()` adds (dict
  mutation, no allowlist at this layer).
- `ApplyPath._apply_entity_update_to_dict()` PH8 block (`src/engine/apply.py:474-527`): `stats_dirty`
  gate (lines 476-489) unchanged in shape from before this investigation's baseline understanding
  except it now includes the `class_id_set` branch (line 484, added by `CLASS-TIER-BRANCHING`). The
  `get_effective_stats()` call site (lines 497-505) now passes `class_id=new_id.class_id` (line 504).
  **Critically, the `replace(new_com, ...)` call (lines 507-515) is an explicit, hardcoded kwarg
  list**: `max_hp`, `atk`, `def_stat`, `evasion`, `move_cost` (`.get(...)` with fallback), `range`
  (`.get(...)` with fallback), `tactical_role` (`.get(...)` with fallback). **`readiness_speed` is
  absent from this kwarg list.** This confirms the "4th silent-drop point" question directly: if
  `recalculate_combat_stats()`/`get_effective_stats()` is modified to add a `"readiness_speed"` key
  to its returned dict, that key will flow correctly through `derived = SkillScalingService
  .get_effective_stats(...)` (plain dict, no filtering) but will be **silently dropped** at the
  `replace(new_com, ...)` call — `dataclasses.replace()` only changes fields explicitly passed as
  kwargs; any dict key not named in this call site has zero effect on the resulting `CombatComponent`.
  This is the same class of bug as the two prior discoveries this session already found and fixed
  in sibling tickets: `EntityState.to_readonly()`'s hardcoded kwarg list previously dropped
  `readiness_speed` itself (COMB-298's own `v2_evidence`, now fixed — see `src/core/state.py:905`,
  confirmed present) and `ApplyPath._fast_replace_identity()`'s hardcoded `object.__setattr__` list
  (`src/engine/apply.py:529-549+`, per `CREATURE-TERRITORY-LIFECYCLE`'s ticket text). **Plan must
  add `readiness_speed=derived.get("readiness_speed", new_com.readiness_speed)` to the
  `replace(new_com, ...)` call at `apply.py:507-515`, or the new formula will compute correctly but
  never reach the live `CombatComponent`.**

### COMB-298 (`docs/parity_ledger/combat_movement.yaml:3301-3341`)
Full entry read. `text` describes the *passive regeneration mechanism itself* (adding the
`readiness_speed` field and the per-tick regen block, plus the `to_readonly()` silent-drop fix) —
it makes **no claim at all about `readiness_speed` being agility-derived**; it only asserts the
field exists, defaults to 10.0, and is applied every tick. `status: verified`, `priority: P1`.
`test_path` points to `tests/unit/combat/test_readiness_regen.py::test_readiness_regenerates_passively_per_tick,
test_readiness_speed_survives_to_readonly_reconstruction` — both still valid regression tests for
the *mechanism*, unaffected by this ticket's formula change (they explicitly pass an override
`readiness_speed=` value, bypassing any derivation). Since COMB-298's existing text is scoped to
"the field exists and regenerates" rather than "the field is flat," **the ticket's "or a new
entry" alternative is the better fit**: COMB-298 does not need editing (it remains true — the
mechanism it describes is unchanged), but a new entry should be added documenting the
agility-derivation itself, since that is new, distinct, testable behavior with its own real
evidence path.

### `docs/mechanics/02_combat_laws.md` §7 (lines 121-173)
Read in full. The "Passive Regeneration" bullet (lines 135-141) currently states: "every tick, an
entity below 100.0 readiness regenerates by its own `readiness_speed` stat
(`CombatComponent.readiness_speed`, default **10.0/tick**), capped at 100.0" — it documents the
*mechanism and the flat default* but says nothing about where that value comes from beyond "its
own... stat." This needs updating once `readiness_speed` becomes agility-derived: the "default
10.0/tick" framing becomes "10.0/tick at reference/baseline agility (5)" and a new bullet or
inline note should state the formula and cite the new parity entry. Separately, and worth flagging:
`docs/mechanics/01_entity_anatomy.md` §"Core Attributes" (Agility row, line ~21 of that file) and
`attribute_progression_contract.md`'s RPG Meaning / Derived Stat Recalculation Order sections
**already describe** Agility as governing "attack speed (readiness)" and list "All derived stats
(HP, ATK, DEF, evasion, move cost, tactical role)" — this is a pre-existing doc/code mismatch this
ticket happens to close on the code side but does not yet reflect on the doc side (see Docs
Requiring Update below).

## Mechanics / Engine Constraints
- `docs/mechanics/02_combat_laws.md` §7: the readiness gate itself (`>= 100.0` required,
  `-100.0` reset on attack, passive regen capped at 100.0) is unchanged by this ticket — only the
  *source* of the regen rate changes. The gate's numeric thresholds are out of scope.
- `docs/engine/contracts/minimal_kernel.md` §5 ("Readiness-Gated Action Semantics"): documents
  "Entities gain readiness based on their `readiness_speed` (passive)" — already generic enough
  to not require a text change; it does not claim `readiness_speed` is flat.
- `docs/guidelines/intentional_divergences.md` §2.36 ("Readiness Never Regenerated Outside Town
  REST"): documents the *old* behavior (before COMB-298's fix) where no passive regen existed at
  all. Describes the mechanism-existence fix, not the derivation — no change needed for this
  ticket's scope.
- `docs/mechanics/attribute_progression_contract.md`'s "Derived Stat Recalculation Order" section
  (Steps 1-6, lines 135-180) is the authoritative enumerated list of what
  `recalculate_combat_stats()` computes and in what order — this is a second, more detailed
  parity-sensitive doc beyond `02_combat_laws.md` and needs its own update if a new step is added.

## Docs Requiring Update

- `docs/mechanics/02_combat_laws.md`: §7's "Passive Regeneration" bullet (lines 135-141)
  currently documents `readiness_speed` as a flat "default 10.0/tick" stat with no derivation;
  once the formula ships this becomes false as written and must be updated to state the
  agility-derived formula and its reference-value backward-compatibility property, per the
  ticket's own explicit AC.
- `docs/mechanics/attribute_progression_contract.md`: the "Derived Stat Recalculation Order"
  section (Steps 1-6) and the "RPG Meaning" paragraph enumerate exactly what
  `recalculate_combat_stats()` derives ("All derived stats (HP, ATK, DEF, evasion, move cost,
  tactical role)... recalculated deterministically whenever attributes or equipment change") —
  this list is now incomplete once `readiness_speed` becomes a derived stat computed inside the
  same function; the Source Areas/Regression Tests tables should also gain a pointer to the new
  test(s).
- `docs/parity_ledger/combat_movement.yaml`: add a new entry (id in the `COMB-3xx` range,
  following COMB-300's numbering precedent) documenting the agility-derivation, its formula, its
  reference-value backward-compatibility guarantee, and its own `test_path` — see Parity Ledger
  Overlap below for why this is preferred over editing COMB-298 in place.

The `docs/mechanics/01_entity_anatomy.md` Agility row (`"Evasion, movement speed, and attack
speed (readiness)"`, in the Core Attributes table) is not required to change for this ticket: its
wording is already generic/high-level enough to remain true once readiness_speed is
agility-derived (it does not currently claim readiness_speed is flat, unlike `02_combat_laws.md`
§7's explicit "default 10.0/tick" framing) — it can stay as-is unless Plan decides a more specific
formula reference belongs there too, which is a discretionary enhancement, not a parity
requirement.

`docs/engine/contracts/minimal_kernel.md` §5 is not required to change: its "Readiness
Accumulation: Entities gain readiness based on their readiness_speed (passive)" wording already
covers a derived `readiness_speed` without modification — it never asserted the value was flat.

## Parity Ledger Overlap
- **COMB-298** (`combat_movement.yaml:3301-3341`, P1, `verified`): describes the passive-regen
  *mechanism's existence*, not its derivation. Not falsified by this ticket — recommend leaving it
  untouched and adding a new entry instead (per the ticket's own "or a new entry" alternative).
  P1 priority means the new entry should also carry a passing `test_path` per the Authoritative
  Mechanics Rule's P0 requirement — COMB-298 is P1 not P0, but the codebase pattern in this batch
  (COMB-300, race-relations entries) still supplies real `test_path`s for P1 entries as a matter
  of practice; Plan should follow that.
- **COMB-300** (`TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE`, referenced from
  02_combat_laws.md §7 and COMB-298's own `v2_evidence` "UPDATE" note) — same readiness subsystem,
  unaffected by this ticket (movement no longer costs readiness at all, orthogonal to how fast
  readiness regenerates).
- No `progression.yaml` entries currently reference `recalculate_combat_stats()`'s Step 1 formulas
  by name for HP/ATK/DEF/evasion/move_cost — those are covered under
  `stat_recalculation_parity`/`equipment_bonus_application`/etc. inline `VERIFIED v2:` code
  comments rather than individual ledger IDs, so a new `readiness_speed` derivation does not need
  to touch existing HP/ATK/DEF entries.

## Prior Work
- `TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION` — introduced
  `CombatComponent.readiness_speed` and its passive-regen mechanism (COMB-298's origin ticket).
- `TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE` (COMB-300) — removed movement's
  redundant readiness cost; raised real attack-legal rate from 1.3% to 28.5-36.6%.
- `TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK` (done, no code changed) — see Risks below;
  explicitly ruled out rebalancing `readiness_speed`'s default without corpus evidence, and
  confirmed the current 10-tick cooldown rhythm is intentional pacing, not an unintended defect.
- `TCK-20260831-CLASS-TIER-BRANCHING` (done, same batch) — most recent modifier of
  `get_effective_stats()`/the PH8 block; confirmed its exact current post-change shape above.
- `TCK-20260831-METAMORPHIC-LAB-PILOT` (done, same batch) — proved `src/lab/metamorphic.py`'s
  pipeline works end-to-end, but also confirmed `MutationLabOrchestrator`/`MutationEngine` can
  only target `WorldSpec`/`ScenarioSpec` model fields (`target.split(".")[0]` resolution) — a
  Python-code formula constant like this ticket's `k` coefficient is **not** WorldSpec-addressable,
  the same structural blocker `RACE-RELATIONS-MATRIX` hit for content outside those specs. Also
  the origin of the "avoid hollow metric" lesson: its first metric choice (`health_score`) turned
  out not to be causally downstream of the mutated field at all (WatchdogTrip tick-budget
  overruns, unrelated to `regen_rate`), producing a degenerate baseline==compared result that
  required two more re-runs (larger tick count, larger magnitude) to get an honest, real
  divergent measurement instead of silently accepting the degenerate PASSED.
- `TCK-20260831-RACE-RELATIONS-MATRIX` (done, same batch) — hit the identical structural blocker
  (its mutated field, `race_relations.yaml`, is also not WorldSpec-addressable) and established
  the concrete workaround pattern this ticket should reuse: hand-orchestrate two variants directly
  via `ScenarioLabOrchestrator(...).run_lab()` (bypassing `MutationEngine`), read each seed's
  `simulation_events.jsonl`, compute a real rate metric, and call
  `MetamorphicRuleEngine.evaluate_rules()` directly with a hand-built `variant_metrics` dict and an
  `ExpectedRelationshipSpec` (`type="monotonic_non_decreasing"`) rather than the CLI mutation
  pipeline.

  **Metric recommendation for this ticket** (avoiding `METAMORPHIC-LAB-PILOT`'s hollow-metric
  trap): `combat_engagement_started` (used by `RACE-RELATIONS-MATRIX`, real event type,
  `src/observability/event_shapers.py:250`) measures entities entering engagement range, not
  actual attack throughput — it is only loosely downstream of `readiness_speed`. A tighter,
  more causally-direct real metric is **`combat_damage`** (`src/observability/event_shapers.py:
  230-234`), which fires only when `hp_delta < 0 and real_combat is not None` — i.e. only on a
  genuinely resolved attack that has already passed `LegalityServiceV2.verify_attack_legality()`'s
  readiness gate. A `combat_damage`-events-per-tick rate is directly gated by how fast attackers
  regain the 100.0 readiness threshold, so it should show a real, non-degenerate increase for a
  higher-agility variant vs. a reference-agility baseline, unlike `health_score` (unrelated to
  `regen_rate`) in the pilot's first attempt. Since this ticket's change is a pure `src/` code
  formula (not a `WorldSpec` field), the "variant" split should be: baseline = current code
  (pre-change, e.g. `git stash`) vs. compared = post-change code, both run against the same real
  corpus world/seeds — not two on-disk content variants of the same code, since there is nothing
  in content to swap. Plan should pick the concrete world/seed/tick parameters; this investigation
  only confirms the metric and mechanism.

## Risks and Open Questions
- **The exact `k` coefficient is explicitly Plan's decision, not Investigate's** — this
  investigation intentionally does not propose one. Whatever Plan picks changes overall
  readiness-regen pacing for every non-reference-agility entity in the corpus, and
  `TCK-20260809-COMBAT-READINESS-COOLDOWN-BOTTLENECK` already ruled out *rebalancing the default
  value* without corpus evidence — Plan must frame `k` as an agility-derivation, not a default-value
  rebalance, and must corpus-validate per the ticket's own Scope bullet to avoid re-triggering that
  ruling's concern in spirit even though it's a different mechanism (derivation vs. flat rebalance).
- **Open question, not resolved here (flag, do not assume an answer):** should the formula be
  symmetric (agility below 5 also reduces `readiness_speed` below 10.0, e.g. a low-agility monster
  becomes slower to re-attack), or should it floor at some minimum so `readiness_speed` never hits
  0 or negative? `recalculate_combat_stats()`'s other Step-1 formulas do not clamp their outputs
  (e.g. `evasion` is only clamped later, at `get_effective_stats()`'s line 390) — Plan should decide
  whether a similar late-clamp belongs here, especially since `apply.py:127`'s regen block already
  treats `readiness_speed <= 0` as "regen disabled" (`if comb.readiness < 100.0 and
  comb.readiness_speed > 0`), so a formula that can go negative or zero for very-low-agility
  entities has a real, already-existing behavioral consequence (permanent readiness lock) rather
  than a merely cosmetic one.
- **`agi_apt` (`AptitudeComponent.agi_apt`, `src/core/state.py:522`, default `1.0`)** is confirmed
  to exist as a field today but is not read by `recalculate_combat_stats()` or
  `get_effective_stats()` for any stat currently — it is the correct, real field the ticket's
  deferred "agi_apt-modulated multiplier" half refers to, confirming the Out-of-Scope boundary is
  well-grounded (the field exists, sits at a no-op default, and wiring it in is a separate,
  deferred unit of work).

## Anti-Drift Hazards
- **Do not add `readiness_speed` derivation anywhere except `recalculate_combat_stats()`'s Step 1
  block.** `get_effective_stats()` applies wound/scar penalties and an evasion clamp after calling
  `recalculate_combat_stats()` — do not add a parallel readiness_speed wound/scar penalty path
  unless explicitly scoped; `02_combat_laws.md` §5 already documents that wound `speed_penalty` is
  computed but "not yet read by `get_effective_stats()`" as a known, separate, un-scoped gap — this
  ticket's formula must not silently start reading it as a side effect of touching this file.
- **The `replace(new_com, ...)` call in `apply.py:507-515` must gain an explicit
  `readiness_speed=derived.get(...)` kwarg** — this is the single highest-risk silent-failure point
  found (see Current Behavior above). A change that only touches `leveling.py` and `rpg_depth.py`
  will compute the right value and then lose it at this exact line, the same failure mode already
  hit twice before in this subsystem (COMB-298's `to_readonly()` fix, `CREATURE-TERRITORY-LIFECYCLE`'s
  `_fast_replace_identity` fix).
- **Do not touch `move_cost`'s existing agility term** (`10.0 + (total_weight/5.0) -
  (agility*0.1)`, `leveling.py:154`) — it is a separate, already-verified agility-derived stat
  (`encumbrance_movement_scaling`) with its own sign convention (higher agility *lowers* cost);
  mixing it up with the new `readiness_speed` formula (higher agility should presumably *raise*
  `readiness_speed`, i.e. faster regen) is an easy sign-confusion hazard given both read the same
  `attributes.agility` field in the same function.
- **Do not silently touch COMB-298** in place — its text is about the mechanism's existence, is
  still true, and is P1 with a still-valid `test_path`; editing it to also claim the derivation
  would misrepresent what `v2_evidence` for *that* entry actually verified. Add a new entry.
- **Corpus validation is explicitly required by Scope, not optional** — do not ship as "a bare
  unit-tested formula swap" per the ticket's own Scope wording; a unit-test-only PR would fail the
  ticket's own stated bar even if all ACs' literal text were satisfied by unit tests alone.

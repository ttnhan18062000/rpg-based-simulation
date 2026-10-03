---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE
artifact_type: plan
tags: [quests, strategy, world-evolution, pressure]
---

# Plan — TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE

## Decision Record (UQ-1, resolved per orchestrator, not re-litigated here)

**Deterministic weighted-random selection**, drawn via the existing seeded `DeterministicRNG`
mechanism. Rationale (from investigation, confirmed): the current `generate()` already uses
`rng.choice()` for uniform selection among level-band survivors; switching to a *weighted* draw
via the same seeded RNG is a minimal, idiomatic delta, not a new determinism model. It preserves
content variety (a region stuck in one pressure kind for many ticks doesn't always emit the exact
same template) while remaining fully deterministic per (seed, tick, level, pressure) tuple.
Neutral-pressure cases must reduce to today's *exact* uniform behavior, not just approximate it —
see the "collapse to legacy path" design below, which makes this a hard guarantee rather than a
statistical accident.

## Two-Systems Note (to preempt future confusion, per investigation recommendation)

This ticket's `QuestGenerator`/`QuestTemplate`/`GuildAction.visit()` path (Guild-assigned, leveled,
entity-`strategic.projects`-registered quests) is **architecturally distinct** from the
`QuestOpportunity`/`state.quest_registry`/`QuestOpportunityGenerator` path
(`src/domains/world_emergence/services.py`, `src/core/models/quests.py`,
`src/engine/pipeline_phases/quest_opportunity_rewards.py`), which has been pressure-driven since
TCK-20260619-E23A/E23C via a different registry and a different trigger (`WorldEvent` severity, not
Guild NPC visits). Both being "pressure-driven quest systems" after this ticket lands is intentional,
not duplication — they serve different layers (Guild-assigned leveled projects vs. world-triggered
adventure opportunities) and must not be merged. This note will be carried into the ticket's
Implementation Notes and Related Docs on completion.

## Explicit Scope Guards (do not touch)

- `src/systems/world_systems/quest_generator.py` (`generate_for_entity`) — dead code, zero call
  sites, not prior art.
- `state.quest_registry` / `QuestOpportunity` / `QuestOpportunityGenerator` /
  `QuestOpportunityRewardSystem` — separate, already-working, already-pressure-driven system.
- `src/domains/world_emergence/services.py::DynamicQuestSeedService` / `QuestSeed` — abandoned,
  unconsumed scaffold.
- `src/systems/strategic_systems/intelligence.py` — quest-to-project activation chain, already
  fixed for P1-B; this ticket only changes *which* template is selected, not the activation chain.
- `RegionalPressureModel` / `ScarcityModel` / `WorldEmergenceResult` (Phase-8 ephemeral models) —
  not reachable from `GuildAction.visit()`'s call context without out-of-scope plumbing; this
  ticket reads durable `RegionState`/`ResourceNodeState` fields directly instead (see below).

---

## Step 1 — Add `QuestPressureProfile` value object (`src/quests/generator.py`)

Add immediately after the existing `QuestTemplate` dataclass (currently lines 11–21):

```python
@dataclass(frozen=True, slots=True)
class QuestPressureProfile:
    """
    Ephemeral, read-time-derived pressure signals used to WEIGHT (never gate) quest
    template selection. Computed fresh on every GuildAction.visit() call from durable
    RegionState/ResourceNodeState fields -- this profile itself is never persisted
    (mirrors how `Opportunity` in src/world/providers/resources.py is a derived
    read-model, not durable state; see docs/mechanics/05_world_evolution.md for the
    underlying durable trauma/hazard fields and the new "Derived Pressure Signals"
    subsection for the scarcity-ratio formula).

    All fields are conventionally in [0.0, 1.0]. The all-zero default is the neutral
    profile: it must reduce selection to today's exact uniform rng.choice() behavior
    (see QuestGenerator.generate()'s "collapse to legacy path" check).
    """
    trauma: float = 0.0
    hazard: float = 0.0
    scarcity: float = 0.0
```

This is a **derived read-model**, not new durable state, per the Durable State Rule -- it is
recomputed from `RegionState.trauma_score` / `RegionState.hazard_level` /
`ResourceNodeState.remaining_charges/max_charges` on every call and never stored on
`AuthoritativeState`, `EntityState`, or any registry.

---

## Step 2 — Extend `GuildAction.visit()` to resolve region + build the profile (`src/town/guild.py`)

Add imports:
```python
from src.quests.generator import QuestGenerator, QuestPressureProfile
from src.core.registries import ResourceRegistry
```

Before the quest-generation block (current lines 45-57), insert:

```python
# Resolve region for pressure-driven quest selection.
# Mirrors ResourceOpportunityProvider.get_opportunities() exactly:
# src/world/providers/resources.py:40 (region fallback) and :60-66 (node->region match).
region_id = getattr(entity.navigation, "region_id", None) or "hometown"
region = state.regions.get(region_id) if getattr(state, "regions", None) else None

trauma = min(1.0, region.trauma_score / 50.0) if region else 0.0
hazard = region.hazard_level if region else 0.0

# Scarcity ratio: average (1 - remaining_charges/max_charges) across resource nodes
# whose ResourceRegistry definition tags them into this region -- same node/region
# match as src/world/providers/resources.py:60-66, but aggregated into one scalar
# instead of per-node Opportunity objects.
ratios = []
for node in getattr(state, "resource_nodes", {}).values():
    res_def = ResourceRegistry.get(node.kind)
    if not res_def:
        continue
    if region_id in res_def.source_region_tags and node.max_charges > 0:
        ratios.append(node.remaining_charges / node.max_charges)
scarcity = (1.0 - (sum(ratios) / len(ratios))) if ratios else 0.0

pressure_profile = QuestPressureProfile(trauma=trauma, hazard=hazard, scarcity=scarcity)
```

Then pass it through to the existing call:
```python
quests = QuestGenerator.generate_quests(
    seed=state.tick + entity.id,
    level=entity.identity.evolution_level,
    tick=state.tick,
    building_id=building_id,
    count=1,
    pressure_profile=pressure_profile,
)
```

`trauma_score` is normalized by the doc-defined instability threshold (50.0, from
`docs/mechanics/05_world_evolution.md` §2 "If Trauma Score > 50.0, the region enters an unstable
state") rather than an arbitrary constant -- this keeps the normalization anchored to an existing,
documented number instead of inventing a new one.

**Degenerate-data safety**: `state.regions.get(region_id)` on a state with no `regions` dict
attribute access is guarded by `getattr(state, "regions", None)`; missing region key returns
`None` via `.get()`; empty/missing `resource_nodes` yields `ratios == []` -> `scarcity = 0.0`. All
three signals default to `0.0` -- the exact neutral profile -- reproducing
`test_guild_visit_quests`'s no-`regions`, no-`resource_nodes` fixture without a `KeyError`.

---

## Step 3 — Extend `DeterministicRNG` with a weighted draw (`src/platform/rng.py`)

Add immediately after the existing `choice()` method:

```python
def weighted_choice(self, domain: Domain, tick: int, entity_id: int, seq: Any, weights: Any, sub_id: int = 0) -> Any:
    """Stateless, order-independent weighted choice from a sequence."""
    seed = self._composite_seed(self._base_seed, domain, tick, entity_id, sub_id)
    return random.Random(seed).choices(seq, weights=weights, k=1)[0]
```

Same composite-seed mechanism as `choice()`/`sample()` -- no new determinism model, just a second
draw primitive reusing the identical seeding. This keeps the weighting math inside the shared RNG
primitive rather than duplicating stream math locally in `QuestGenerator` (per "shared world
behavior should go through systems/registries, not scattered local hacks").

---

## Step 4 — Extend `QuestGenerator` selection logic (`src/quests/generator.py`)

### 4a. Pressure-to-kind affinity table (module-level, next to `TEMPLATES`)

```python
# Maps each QuestKind to the QuestPressureProfile field it is weighted by.
# EXPLORE has no directional pressure driver -- it stays at baseline weight,
# which is also what keeps a genuinely neutral profile perfectly uniform.
PRESSURE_AFFINITY: Dict[QuestKind, str] = {
    QuestKind.HUNT: "trauma",
    QuestKind.BOUNTY: "trauma",
    QuestKind.LIBERATE: "hazard",
    QuestKind.GATHER: "scarcity",
    QuestKind.EXPLORE: "none",
}
PRESSURE_WEIGHT_SCALE = 2.0  # max additive bonus at signal strength 1.0
```

### 4b. Weight helper (staticmethod on `QuestGenerator`)

```python
@staticmethod
def _pressure_weight(template: "QuestTemplate", profile: Optional["QuestPressureProfile"]) -> float:
    if profile is None:
        return 1.0
    signal_name = PRESSURE_AFFINITY.get(template.kind, "none")
    if signal_name == "none":
        return 1.0
    signal_value = getattr(profile, signal_name, 0.0)
    return 1.0 + PRESSURE_WEIGHT_SCALE * max(0.0, min(1.0, signal_value))
```

### 4c. Signature changes (both safely defaulted -- source-compatible with the one existing call
site and with every test that calls `.generate()`/`.generate_quests()` without the new arg)

```python
@staticmethod
def generate(
    seed: int,
    level: int,
    tick: int,
    existing_ids: Set[str] | None = None,
    pressure_profile: Optional["QuestPressureProfile"] = None,
) -> Optional[QuestState]:
```
```python
@staticmethod
def generate_quests(
    seed: int,
    level: int,
    tick: int,
    building_id: int,
    count: int = 1,
    pressure_profile: Optional["QuestPressureProfile"] = None,
) -> List[QuestState]:
    ...
    q = QuestGenerator.generate(seed + i, level, tick, pressure_profile=pressure_profile)
```

### 4d. Selection change inside `generate()`, replacing the current step 2

```python
# 2. Select template using DeterministicRNG.
rng = DeterministicRNG(seed)
weights = [QuestGenerator._pressure_weight(t, pressure_profile) for t in candidates]

# Collapse-to-legacy-path guarantee: when the profile is None, or every candidate
# resolves to the same weight (neutral profile, or a level band where no candidate's
# QuestKind has a live pressure affinity), draw with the exact same rng.choice() call
# as before this ticket -- byte-identical distribution, not just "approximately
# uniform." Only diverge to the weighted draw when pressure actually differentiates
# the candidates.
if pressure_profile is None or len(set(weights)) == 1:
    template = rng.choice(Domain.QUEST, tick, level, candidates)
else:
    template = rng.weighted_choice(Domain.QUEST, tick, level, candidates, weights)
```

This is the mechanism that makes AC3 ("existing hero-level gating behavior unchanged for
neutral-pressure scenarios") and the investigation's "neutral-pressure cases reduce naturally to
today's uniform behavior" hold **exactly**, not statistically: level-band filtering (step 1,
untouched) remains the sole gate, and the draw call itself is provably identical to the pre-ticket
code path whenever pressure doesn't differentiate the surviving candidates.

No other part of `generate()` changes (reward/goal scaling in steps 3-4 stays level-only, per Out
of Scope: "Changing `QuestTemplate`'s reward/requirement structure").

---

## Step 5 — Fix the pre-existing masked test (`tests/unit/quest/test_quest_generation.py`)

Two functions are both named `test_quest_generation_determinism`:
- Line 11 — tests `QuestGenerator.generate()` (the one relevant to this ticket's determinism AC).
- Line 106 — tests `QuestOpportunityGenerator.from_resource_depleted()` (unrelated E23A system).

Only the second is currently collected by pytest (module-scope shadowing). Rename the first to
`test_quest_generator_determinism` (no other change to its body). Verify the fix with:
```
pytest tests/unit/quest/test_quest_generation.py --collect-only -q
```
and confirm the collected-test count increases by exactly one versus pre-change (the previously
shadowed test becomes newly collectible), before adding any of the new tests in Step 6.

---

## Step 6 — New tests (`tests/unit/quest/test_quest_generation.py`, extend existing file -- it is
well under the ~250-line crowding threshold even after these additions)

All use the tier-2 level band (`level=8`, eligible: `q_wolf_hunt` HUNT 6-12, `q_herb_gather` GATHER
4-10) for the pressure-shift tests, since it's the smallest band containing one trauma-affine and
one scarcity-affine template together (per test_plan.md's own scenario framing).

1. `test_quest_generation_favors_hunt_under_high_trauma` -- `QuestPressureProfile(trauma=1.0)`,
   loop `seed in range(30)` at fixed `level=8, tick=100`, count `QuestKind.HUNT` picks, assert
   `hunt_count > 15` (materially more than half; not "always wins" -- keeps content variety per the
   UQ-1 decision). Deterministic and fast: fixed seed range, no real randomness.
2. `test_quest_generation_favors_gather_under_high_scarcity` -- mirror of (1) with
   `QuestPressureProfile(scarcity=1.0)`, asserting `gather_count > 15`.
3. `test_quest_generation_neutral_profile_matches_legacy_none` -- for `seed in range(30)` at
   `level=8, tick=100`, assert `QuestGenerator.generate(seed, 8, 100).id ==
   QuestGenerator.generate(seed, 8, 100, pressure_profile=QuestPressureProfile()).id` -- proves the
   collapse-to-legacy-path guarantee literally (exact id equality per seed, not just distributional
   similarity).
4. `test_level_gating_overrides_pressure` -- `level=1` (only tier-1 templates eligible:
   `q_slime_cull` HUNT, `q_wood_survey` EXPLORE), profile with `trauma=1.0, hazard=1.0,
   scarcity=1.0`; loop a handful of seeds and assert `q.name` is always one of `["Clear the
   Slimes", "Survey the Woods"]`, never `"Bounty: Bandit Leader"`/`"Liberate the Outpost"` (min_level
   11/15) -- confirms level-band filtering happens before weighting and is unaffected by it.
5. `test_pressure_driven_selection_determinism` -- same `seed=42, level=8, tick=100,
   pressure_profile=QuestPressureProfile(trauma=0.8, scarcity=0.3)` called twice; assert identical
   `id`/`name`/`reward.xp` -- extends the (now-fixed) `test_quest_generator_determinism` pattern to
   explicitly cover the new pressure-input path, satisfying AC "same seed -> same quest selection."
6. `test_quest_generation_missing_region_signal_defaults_neutral` -- call `QuestGenerator.generate()`
   with `pressure_profile=QuestPressureProfile()` (all-zero, the value `GuildAction.visit()` builds
   when `state.regions` is empty/missing) and assert it does not raise and returns a valid quest --
   direct unit coverage of the "no region data" branch at the `QuestGenerator` layer specifically
   (complementing the existing end-to-end guard below).

In `tests/unit/world/test_guild_pipeline.py`, add:

7. `test_guild_visit_quest_reflects_region_pressure` -- construct an `AuthoritativeState` with a
   `RegionState` at the entity's `navigation.region_id` (set via `V2EntityBuilder`) with
   `trauma_score=60.0` (above the doc's 50.0 instability threshold, normalizes to `1.0`) and no
   resource nodes; call `GuildAction.visit()`; assert it still returns exactly one `kind == "quest"`
   project without raising -- an integration-level smoke test proving the region signal actually
   reaches `QuestGenerator` end-to-end. (Frequency/favoring assertions belong at the
   `QuestGenerator`-unit layer above, not here -- `GuildAction.visit()` only ever performs a single
   draw per call, which is the wrong layer for a distributional check.)

**Regression check (no new test needed, just confirm green per test_plan.md item 6):**
`test_guild_visit_quests` (no `regions` entry at all) and `test_guild_visit_determinism` must
still pass unmodified -- they are the existing regression guard for the "zero region data" branch
and for end-to-end reproducibility respectively.

---

## Step 7 — Docs

### 7a. `docs/mechanics/05_world_evolution.md`

Add a new subsection at the end of **§3 Ecology & Replenishment** (after the existing "Decay Laws"
block, before the `---` separator at line ~121):

```markdown
### Derived Scarcity Ratio (Consumer-Facing)
Resource nodes do not carry a separate durable "scarcity" field -- consumers derive one at read
time from `ResourceNodeState.remaining_charges / max_charges`, scoped to nodes tagged into a
region via `ResourceRegistry` definitions' `source_region_tags`. Two consumers use this ratio
today:
*   **`ResourceOpportunityProvider`** (`src/world/providers/resources.py`) uses the raw ratio
    directly as a *reward multiplier* -- opportunities on a near-depleted node are worth less
    (`reward *= 0.5 + 0.5 * depletion_mult`).
*   **`QuestGenerator`** (`src/quests/generator.py`) uses the *inverse* of the region-averaged
    ratio, `scarcity = 1.0 - avg(remaining/max)`, as a *quest-selection weight* -- a region with
    heavily depleted nodes favors `GATHER`-kind quest templates. This is a distinct derived
    signal from the trauma/hazard signals in §2 above, aggregated the same way (read-time, from
    durable per-node fields, never itself persisted).
```

This corrects the ticket's own citation error identified during investigation: `03_economic_laws.md`
has no "§resource pressure" section, and the actual formula this ticket introduces
(`1.0 - avg(remaining_charges/max_charges)`) is a new, simpler node-charge-ratio derivation, not a
reuse of the ephemeral `ScarcityModel.evaluate()` formula in `src/domains/world_emergence/models.py`
(which remains undocumented-here and untouched, per Out of Scope). §3 "Ecology & Replenishment" is
the correct home because it already owns resource-node charge/respawn mechanics; trauma/hazard
(§2) already document the other two signals correctly and need no changes.

### 7b. `docs/plans/audit_fix_plan.md`

Update P1-D from OPEN to RESOLVED in both places, matching the existing P1-B/P1-C/P2-B convention:
- Line 129 header: `### P1-D: Pressure-Driven Quest Generation [M] — RESOLVED — TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE`
  (append a one-line note below the existing finding, same style as the P2-B block, summarizing
  what shipped: region trauma/hazard + node-charge scarcity now weight `QuestGenerator` template
  selection via `QuestPressureProfile`).
- Line 577 table row: `OPEN (verified 2026-07-03)` -> `**RESOLVED** — TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE`.
- Line 634/636 "Still open" list: remove `P1-D` from the enumerated still-open items.

### 7c. Ticket file itself

On completion, correct the ticket's `## Related Docs` / `## Scope` item 2 citation
(`docs/mechanics/03_economic_laws.md §resource pressure` does not exist) to point at
`docs/mechanics/05_world_evolution.md §3 "Derived Scarcity Ratio"` (new, per 7a) instead, and add
the Two-Systems Note (this plan's preamble) to `## Implementation Notes` so a future reader does
not conflate this system with `QuestOpportunity`/`quest_registry`.

---

## Step 8 — Parity Ledger (`docs/parity_ledger/strategic_cognition.yaml`)

Per the Authoritative Mechanics Rule and this ticket's own AC bar:
- Fill real `test_path` values for `STRAT-154`..`STRAT-158` (currently all `null`), pointing at the
  renamed/surviving tests in `tests/unit/quest/test_quest_generation.py`
  (`test_quest_generator_determinism`, `test_level_banding_tier1`, `test_level_banding_tier3`,
  `test_reward_scaling`, `test_duplicate_suppression` as appropriate per each entry's `text`).
- Add one new `P1` entry for the net-new pressure-driven-selection capability itself (`status:
  verified`, `v2_evidence` describing `QuestPressureProfile`-weighted selection,
  `test_path` pointing at `test_quest_generation_favors_hunt_under_high_trauma` and
  `test_quest_generation_favors_gather_under_high_scarcity`).

---

## Step 9 — Scoped test run (per test_plan.md)

```
pytest tests/unit/quest/test_quest_generation.py --collect-only -q   # confirm collected count increased by 1
pytest tests/unit/quest/test_quest_generation.py -v
pytest tests/unit/world/test_guild_pipeline.py -v
```

Do not run the full suite. `src/domains/world_emergence/models.py` and
`src/world/providers/resources.py` are not modified by this plan (read-pattern reused, code path
untouched), so the wider `emergence`/`scarcity`/`pressure` test sweep in test_plan.md is not
required unless implementation discovers a need to touch either file (it should not).

---

## Files Touched (summary)

- `src/quests/generator.py` -- `QuestPressureProfile`, `PRESSURE_AFFINITY`,
  `PRESSURE_WEIGHT_SCALE`, `_pressure_weight`, signature + selection changes to `generate()` /
  `generate_quests()`.
- `src/town/guild.py` -- region resolution + pressure-profile construction in `GuildAction.visit()`.
- `src/platform/rng.py` -- new `DeterministicRNG.weighted_choice()` method.
- `tests/unit/quest/test_quest_generation.py` -- rename fix + 6 new tests.
- `tests/unit/world/test_guild_pipeline.py` -- 1 new integration smoke test.
- `docs/mechanics/05_world_evolution.md` -- new "Derived Scarcity Ratio" subsection under §3.
- `docs/plans/audit_fix_plan.md` -- P1-D marked RESOLVED (2 locations + still-open list).
- `docs/parity_ledger/strategic_cognition.yaml` -- `test_path` fills for STRAT-154..158 + 1 new
  P1 entry.
- Ticket file (`tickets/inprogress/TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE.md`) -- citation
  correction + Two-Systems Note in Implementation Notes, on completion.

## Genuinely Unresolved Questions

None found requiring a human decision. UQ-1 was pre-resolved by orchestrator instruction. All other
forks (normalization anchor for trauma, doc placement for the scarcity formula, weighted-choice
primitive placement, collapse-to-legacy-path mechanism) were resolved with direct evidence from
source (`RegionState` docstrings, `docs/mechanics/05_world_evolution.md`'s own 50.0 threshold,
`ResourceOpportunityProvider`'s existing pattern) rather than left as guesses.

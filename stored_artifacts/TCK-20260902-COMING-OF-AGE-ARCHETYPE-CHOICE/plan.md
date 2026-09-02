---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE
artifact_type: plan
tags: [lifecycle, strategy]
---

# Implementation Plan — TCK-20260902-COMING-OF-AGE-ARCHETYPE-CHOICE

## Summary

Add a new, standalone module `src/ai/coming_of_age.py` that computes a genuinely weighted
(personality + parental-occupation + regional-need) role distribution over
`{SHOPKEEPER, WORKER, GUARD}` and draws from it via the project's existing seeded
`DeterministicRNG.weighted_choice()` API — never Python's unseeded `random`, never a fixed-priority
first-fit like `OccupationChangeGoalScorer`. Wire a single new sibling branch into
`LifecycleSystem.resolve_lifecycle()` next to the existing ELDER-branch precedent, firing exactly
once at the CHILD→ADULT origin transition **and only for `entity.identity.role == EntityRole.CITIZEN`**
(the citizen/humanoid population this mechanism is intended for — see Decision 5), merging one
`IdentityUpdate(role_set=...)` onto the same `EntityUpdate` that already carries `life_stage_set`. Implement the no-birth-record exclusion
now (the Reproduction epic is DONE) using the investigation's proven-safe compound check. Add a
pure, coefficient-parameterized weight function so the required metamorphic test can sweep the
regional-need coefficient independently of the RNG draw. Close with a new `docs/mechanics/
04_strategic_cognition.md` §9 and a new `STRAT-267` parity ledger entry.

## Decisions (resolving the four flagged items)

**1. AC4 no-birth-record exclusion — IMPLEMENT NOW, do not defer.**
The Reproduction epic (`TCK-20260902-EPIC-RPG-M3-REPRODUCTION`) is DONE — all six child tickets are
under `tickets/done/m3-reproduction-epic/` (investigation.md, "Reproduction Epic Status"). The
ticket's own AC4 text ("track as BLOCKED... do not silently omit... implement the eligibility
check as a stub/TODO with this dependency documented, **or** defer") explicitly offers implementing
it now as a valid path once the dependency lands, not only deferral — so implementing it does not
exceed ticket scope, it fulfills AC4 as written. Use the investigation's proven-safe compound check
(`birth_tick == 0 AND parent_a_entity_id is None AND parent_b_entity_id is None`), not the unsafe
`birth_tick == 0`-only shortcut (proven unsafe: a real Humanoid-path child can have `birth_tick==0`
with non-`None` parent ids if two same-`kind` adults are near each other at world genesis —
investigation.md "Risks and Open Questions"). See Step 2.

**2. RNG determinism — use `DeterministicRNG.weighted_choice()`, constructed locally from
`state.seed`, never Python's unseeded `random`.**
Corrects an investigation.md path error: the RNG service lives at `src/platform/rng.py`, not
`src/core/rng.py` (confirmed by `find . -iname rng.py` → `./src/platform/rng.py`; no `src/core/
rng.py` exists). `DeterministicRNG` (`src/platform/rng.py:24-113`) already has exactly the primitive
this ticket needs: `weighted_choice(domain, tick, entity_id, seq, weights, sub_id=0)`
(`src/platform/rng.py:100-103`) — "Stateless, order-independent weighted choice from a sequence,"
internally `random.Random(composite_seed).choices(seq, weights=weights, k=1)[0]`. This is a genuine
stochastic draw proportional to weight, not a deterministic argmax — argmax-over-weights was
considered and rejected: since every same-region child in the same tick shares the same
regional-need term, an argmax would pick the same highest-weight role for every child whenever
personality/parental terms don't break the tie, reproducing `OccupationChangeGoalScorer`'s exact
convergence bug through a different mechanism. `resolve_lifecycle()`'s call site
(`src/engine/pipeline.py:389`) passes only `(state, u)` — no `DeterministicRNG` instance is threaded
through the refinement pipeline today. The confirmed, already-used pattern for this exact situation
(a resolve-style function that only receives `state`) is to construct `DeterministicRNG(state.seed)`
locally inside the function — proven safe because `weighted_choice`/`get_float`/`get_int` are all
stateless and order-independent (reseed each call from `(domain, tick, entity_id, sub_id)`, not
from call order). Precedent, all constructing `rng = DeterministicRNG(state.seed)` inline:
`src/world/raid.py:38`, `src/town/guild.py:43`, `src/systems/world_systems/quest_generator.py:15`.
Use `Domain.STRATEGIC` (`src/core/enums.py:182`) as the domain — a dedicated stream distinct from
`Domain.SPAWN` (entity generation, used by `EntityGenerator`) and `Domain.SOCIAL` (guild lead
selection), appropriate since this fires from `LifecycleSystem`/strategic-cognition-adjacent logic
and the ticket's own `layer: strategy`. Key the draw by `(Domain.STRATEGIC, state.tick, e_id)` —
the same `(tick, entity_id)` keying every other precedent site uses — so a re-run with identical
state/seed reproduces byte-identical `role_set` outcomes (satisfies test 9's determinism-replay
requirement) regardless of `state.entities` dict iteration order.

**3. Weighting formula — fresh design, linear non-negative weights fed directly into
`weighted_choice` (no softmax normalization needed; `random.choices` accepts raw non-negative
weights).**
```
weight(role) = max(WEIGHT_FLOOR,
    BASE_WEIGHT
    + PERSONALITY_COEFF * personality_term(role, entity.identity.personality)
    + PARENTAL_COEFF    * parental_term(role, entity, state)
    + regional_coeff    * regional_need_term(role, entity, state)
)
```
- `entity.identity.personality` is the correct access path — `PersonalityComponent` is nested
  *inside* `IdentityComponent`, not a top-level `EntityState` field (verified by direct read:
  `src/core/state.py:516`, `personality: PersonalityComponent = field(default_factory=
  PersonalityComponent)` inside `class IdentityComponent` at `src/core/state.py:499`; confirmed
  again by the existing read-path `personality=id_comp.personality` at `src/core/state.py:904`).
  Do not write `entity.personality` — that attribute does not exist on `EntityState`.
- `personality_term`: `PersonalityComponent` fields are `greed`, `bravery`, `sociability`,
  `industry` (`src/core/state.py:445-450`). Map `SHOPKEEPER → greed` (trade-biased, mirrors
  `PersonalityService.get_goal_modifiers()`'s `greed → "trade"` mapping, `src/ai/personality.py:
  18-21`), `WORKER → industry` (work-biased, mirrors that same function's `industry → "harvesting"/
  "crafting"` mapping, `src/ai/personality.py:34-38`), `GUARD → bravery` (combat-biased, mirrors
  `bravery → "combat"`, `src/ai/personality.py:23-28`). This is the closest existing numeric-weighting
  style precedent in the codebase (additive term keyed by a `PersonalityComponent` field), applied
  here to a categorical draw instead of goal utility.
- `parental_term(role, entity, state)`: count how many of the entity's resolvable, active parents
  currently hold `identity.role == role` (0, 1, or 2). Resolve via `state.entities.get(parent_id)`
  — the same lookup-and-`None`-check pattern already used at `LifecycleSystem._select_default_heir()`
  (`src/systems/lifecycle_systems/lifecycle.py:27`, `candidate = state.entities.get(target_id)`,
  followed by `if candidate is None or not candidate.lifecycle.active: continue`). Apply identically
  here for both `parent_a_entity_id`/`parent_b_entity_id`.
- `regional_need_term(role, entity, state)`: `max(0.0, target_count(role) - live_count(role))` —
  read-only reuse of `OccupationChangeGoalScorer`'s own region/tally logic as the regional-need
  INPUT signal, not a duplicate of its selection behavior: `region = LegalityServiceV2.
  get_region_for_position(entity.navigation.position, state)` (local import inside the function,
  mirroring `src/ai/goals/occupation_change_scorer.py:36-38`'s own local import to avoid a circular
  import), the same single-pass per-role headcount tally over `state.entities.values()` filtered to
  `other.combat.alive` and matching region id (`occupation_change_scorer.py:46-52`), and
  `target_count = max(MIN_OCCUPATION_SLOTS, int((area / 10000.0) * BASE_OCCUPATION_DENSITY[role]))`
  read verbatim from `src/world/occupation_config.py` (`BASE_OCCUPATION_DENSITY`,
  `MIN_OCCUPATION_SLOTS` — pure config, ticket's own Out-of-Scope explicitly allows reading these).
  If `region is None`, the term is `0.0` for every role (neutral, matches the scorer's own
  `region is None` early-out at `occupation_change_scorer.py:39-40`).
- Constants (module-level, in `src/ai/coming_of_age.py`): `BASE_WEIGHT = 1.0`,
  `PERSONALITY_COEFF = 1.0`, `PARENTAL_COEFF = 1.0`, `DEFAULT_REGIONAL_COEFF = 1.0`,
  `WEIGHT_FLOOR = 0.05`. `WEIGHT_FLOOR` guarantees every role keeps strictly nonzero draw
  probability regardless of how skewed the other three terms get — a structural
  never-fully-collapses guard that directly supports AC3's "must not all resolve to the identical
  occupation role" property (with a floor, `random.choices` can never assign a role exactly 0
  probability, so a same-tick batch of distinct entity ids — each drawing from an independently
  reseeded stream — is very unlikely to land on the same role 100% of the time; this is empirical,
  not a mathematical guarantee, so Step 5 must verify the concrete fixture actually produces a
  non-collapsed result with the chosen seed, and the implementer may tune coefficients/floor, never
  the batch composition, if it doesn't).
- `compute_role_weights(entity, state, *, personality_coeff=PERSONALITY_COEFF,
  parental_coeff=PARENTAL_COEFF, regional_coeff=DEFAULT_REGIONAL_COEFF) -> List[float]` is a **pure**
  function (no RNG) exposing all three coefficients as keyword overrides specifically so the
  metamorphic test (Step 5) can sweep `regional_coeff` independently while holding
  `personality_coeff`/`parental_coeff` fixed, exactly matching AC2's wording.

**4. Missing/inactive/dead parent handling — treat as neutral (zero contribution), never crash,
never default-favor a specific role.**
`parental_term` must resolve each parent id independently: `None` id → skip; `state.entities.get(id)
is None` (parent died and was removed) → skip; `parent.lifecycle.active is False` (deactivated but
still present) → skip. A parentless entity (Natural-Creature path) or an entity whose parents are
both gone/inactive by adulthood yields `parental_term(role) == 0.0` for every role — a flat,
role-neutral contribution, not a fallback to any single occupation. No `KeyError`/`AttributeError`
is possible since every step uses `.get()`/attribute access already guarded by the `is None` check.

**5. Role gate on Step 4's branch — REQUIRED, `entity.identity.role == EntityRole.CITIZEN`.**
Architecture review (2026-09-02) found the original Step 4 branch condition
(`target_stage == LifeStage.ADULT and entity.identity.life_stage == LifeStage.CHILD`) has no
role/species gate, so it also fires for the flag-gated Natural-Creature reproduction path. Confirmed
by direct read of `src/systems/world_systems/generator.py`:
- `spawn_natural_creature_offspring()` (`generator.py:87-120`) builds MONSTER-population children via
  `.identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE, ..., life_stage=LifeStage.CHILD)`
  (`generator.py:112-113`), with `parent_a_entity_id=None, parent_b_entity_id=None` passed to
  `.birth_record(...)`. Because `.birth_record()` is still called with a real, non-zero `birth_tick`
  in the practically-reachable case (camp maturity accrues over many ticks before this offspring
  matures further to ADULT), `is_excluded_no_birth_record()`'s compound check
  (`birth_tick == 0 and parent_a_entity_id is None and parent_b_entity_id is None`, Decision 1/Step 2)
  evaluates `False` — birth-record presence and species/role are orthogonal signals, so the
  no-birth-record exclusion does **not** catch this case. Without a role gate, a MONSTER-role,
  MONSTER_HORDE-faction CHILD crossing the age boundary would get a durable `role_set` overwrite to
  SHOPKEEPER/WORKER/GUARD via the authoritative `IdentityPatch` path, producing an incoherent entity
  (`faction=MONSTER_HORDE` + `role=SHOPKEEPER`).
- By contrast, `spawn_humanoid_offspring()` (`generator.py:172-204`), the real Humanoid reproduction
  path this mechanism is meant to serve, builds via `.identity(role=EntityRole.CITIZEN,
  faction=Faction.TOWN_COUNCIL, ..., life_stage=LifeStage.CHILD)` (`generator.py:194-195`). No other
  CHILD-life-stage construction site exists in `generator.py` (`spawn_magical_demonic_entity` has no
  maturation clock/CHILD stage — it spawns directly at ADULT-equivalent). So every legitimate
  in-scope CHILD is `role == EntityRole.CITIZEN` at construction, and gating on that value excludes
  no real in-scope entity.
- `EntityRole` values are distinct and unambiguous: `HERO=0, SHOPKEEPER=1, MONSTER=2, CITIZEN=3,
  WORKER=4, GUARD=5` (`src/core/enums.py:6-12`).
- Precedent for this exact gate shape: `OccupationChangeGoalScorer.score()` opens with
  `if entity.identity.role != EntityRole.CITIZEN: return GoalScore(..., utility=0.0, ...)`
  (`src/ai/goals/occupation_change_scorer.py:33-34`) — the existing, reviewer-cited mechanism that
  assigns this exact `{SHOPKEEPER, WORKER, GUARD}` role set already gates on the identical condition
  before ever considering a `role_set`-adjacent write (tracked at `STRAT-259`,
  `docs/parity_ledger/strategic_cognition.yaml`). Step 4's branch adopts the equivalent condition —
  `entity.identity.role == EntityRole.CITIZEN` — checked on the pre-tick frozen `entity` (never
  `ent_upd`), alongside the existing life-stage origin check, so both the temporal ("is this the
  CHILD→ADULT transition tick") and the population ("is this entity even part of the intended citizen
  cohort") conditions are enforced independently.
- This gate is additive only: it narrows an already-narrow branch further and does not touch
  `is_excluded_no_birth_record()`, `choose_archetype()`, or `compute_role_weights()` (Steps 1-3) —
  those remain unchanged and are simply never invoked when the new role check fails.

## Steps

### Step 1 — Pure weighting functions in a new module
**Files:** `src/ai/coming_of_age.py` (new file)
**Change:** Create the module with: `_CANDIDATE_ROLES = (EntityRole.SHOPKEEPER, EntityRole.WORKER,
EntityRole.GUARD)` (an independent tuple literal — do not import `OccupationChangeGoalScorer`'s
private `_CANDIDATE_ROLES`, since that name is underscore-prefixed/module-private by convention;
add a comment noting it must be kept in sync with `occupation_change_scorer.py`'s own tuple if that
scorer's candidate set ever changes); the five module constants from Decision 3; `_personality_weight()`,
`_parental_weight()`, `_regional_need_weight()`, and `compute_role_weights()` per Decision 3's exact
formula. Imports needed: `from src.core.enums import EntityRole`, `from src.core.state import
EntityState, AuthoritativeState` (TYPE_CHECKING-only if avoiding a cycle, matching
`occupation_change_scorer.py:5`'s style), `from src.world.occupation_config import
BASE_OCCUPATION_DENSITY, MIN_OCCUPATION_SLOTS`; `from src.engine.legality import LegalityServiceV2`
as a **local import inside `_regional_need_term`**, not module-level (mirrors
`occupation_change_scorer.py:36`'s local import to avoid a circular import — verify this remains
necessary by checking for an import cycle before deciding to hoist it to module level).
**Do NOT touch:** `src/ai/goals/occupation_change_scorer.py` (read its constants/pattern only, do
not import or modify its private `_CANDIDATE_ROLES`); `src/world/occupation_config.py` (read-only).
**Verify:** New direct unit tests on `compute_role_weights()`/`_parental_weight()` covering tests 7
(`test_coming_of_age_handles_missing_or_inactive_parent_entity`) and 8
(`test_coming_of_age_parentless_child_uses_neutral_parental_term`) from test_plan.md, in
`tests/unit/strategic/test_coming_of_age_archetype_choice.py` (new file).

### Step 2 — No-birth-record exclusion check
**Files:** `src/ai/coming_of_age.py`
**Change:** Add `is_excluded_no_birth_record(entity: EntityState) -> bool`, returning
`entity.lifecycle.birth_tick == 0 and entity.lifecycle.parent_a_entity_id is None and
entity.lifecycle.parent_b_entity_id is None` (the compound check from Decision 1; fields confirmed
at `src/core/state.py:163-166`, `LifecycleComponent.parent_a_entity_id`/`parent_b_entity_id`/
`birth_tick`). Add a docstring citing the investigation's evidence: this correctly recognizes a
tick-0 Humanoid-path birth (real parent ids, `birth_tick==0`) as *not* excluded, while excluding a
hypothetical construction-default CHILD with no `.birth_record()` call at all; flag as a
forward-compatibility caveat (not a currently-live gap) that a future reproduction path lacking both
an accumulation gate and tracked parent ids could defeat this check.
**Do NOT touch:** the birth-record write path itself (`src/engine/patches.py`, `src/core/builder.py`,
`src/systems/world_systems/generator.py`'s `.birth_record(...)` call sites) — this function only
reads `LifecycleComponent` fields, never writes them.
**Verify:** test 6, `test_coming_of_age_no_birth_record_exclusion_tracked_or_stubbed`
(`tests/unit/progression/test_lifecycle.py`) — both the construction-default-excluded case and the
Humanoid-tick-0-not-excluded regression case from test_plan.md.

### Step 3 — Seeded weighted-random draw
**Files:** `src/ai/coming_of_age.py`
**Change:** Add `choose_archetype(entity: EntityState, state: AuthoritativeState) -> int`:
constructs `rng = DeterministicRNG(state.seed)` locally (Decision 2), calls
`rng.weighted_choice(Domain.STRATEGIC, state.tick, entity.id, list(_CANDIDATE_ROLES),
compute_role_weights(entity, state))`, and returns `int(result)`. Imports:
`from src.platform.rng import DeterministicRNG`, `from src.core.enums import Domain`.
**Do NOT touch:** `src/platform/rng.py` itself — `weighted_choice` already exists and needs no
changes (`src/platform/rng.py:100-103`). Do not use `import random` / `random.choice` anywhere in
this module.
**Verify:** test 9, `test_coming_of_age_selection_uses_seeded_rng_not_unseeded_random` — two calls
with identical state/seed produce identical output; grep-based guard confirms no unseeded `random`
module usage in `src/ai/coming_of_age.py`.

### Step 4 — Wire into `LifecycleSystem.resolve_lifecycle()`
**Files:** `src/systems/lifecycle_systems/lifecycle.py`
**Change:** Immediately after the existing ELDER branch (lines 63-68) and before
`refined_entity_updates[e_id] = ent_upd` (line 70), add a sibling `if` block, **with the role gate
required by Decision 5**:
```python
if (
    target_stage == LifeStage.ADULT
    and entity.identity.life_stage == LifeStage.CHILD
    and entity.identity.role == EntityRole.CITIZEN
):
    if not ComingOfAgeService.is_excluded_no_birth_record(entity):
        archetype_role = ComingOfAgeService.choose_archetype(entity, state)
        ent_upd = replace(ent_upd, identity=replace(ent_upd.identity, role_set=archetype_role))
```
This mirrors the exact `replace(ent_upd, identity=replace(existing_identity, ...))` pattern already
used two lines above for `life_stage_set` (lines 59-61) rather than introducing a separate
`.merge()`-based `EntityUpdate` the way the ELDER branch does — since this only sets one additional
field on the identity update that already exists on `ent_upd` at this point in the function, `replace()`
is the smaller, more consistent diff. The explicit `entity.identity.life_stage == LifeStage.CHILD`
origin check (read from the pre-tick frozen `entity`, never from `ent_upd`) is what guarantees
"fires exactly once": `is_forward_transition()` already prevents re-firing on the same tick, and once
the durable `life_stage_set=ADULT` write lands, the entity's *next* frozen snapshot has
`life_stage == ADULT`, so this branch's origin check no longer matches on subsequent ticks — do not
gate on `target_stage == ADULT` alone (investigation's anti-drift hazard: `get_stage_for_age` is a
pure re-derivation checked every tick, not a one-shot event). The added
`entity.identity.role == EntityRole.CITIZEN` condition is the population gate from Decision 5 —
mirrors `OccupationChangeGoalScorer.score()`'s own `entity.identity.role != EntityRole.CITIZEN` early
return (`src/ai/goals/occupation_change_scorer.py:33`, inverted to a positive match here), and is what
prevents this branch from firing for a MONSTER-role CHILD produced by
`spawn_natural_creature_offspring()` (`generator.py:112-113`, `role=EntityRole.MONSTER`) — that path's
`is_excluded_no_birth_record()` check alone does NOT exclude it, since that function is called with a
real non-zero `birth_tick` (Decision 5). Both the life-stage-origin check and the role check read from
the pre-tick frozen `entity`, never `ent_upd`. Add imports:
`from src.ai.coming_of_age import ComingOfAgeService` (or plain module-level functions —
implementer's choice of a thin static-method wrapper class vs. free functions, matching whichever
reads more consistently with `LifeStageService`'s existing staticmethod-class style at
`src/ai/life_stage.py:12`), and `from src.core.enums import EntityRole` — confirmed not already
imported in `src/systems/lifecycle_systems/lifecycle.py` (current imports at lines 1-8 cover
`StateUpdate`/`EntityUpdate`/`LifecycleUpdate`/`InventoryUpdate`/`IdentityUpdate` from
`src.core.updates`, `LifeStage` from `src.core.state`, `LifeStageService`, and
`compute_elder_attribute_update`; no `src.core.enums` import exists yet).
**Do NOT touch:** lines 63-68 (the ELDER branch and `compute_elder_attribute_update` call) — this is
an explicit anti-drift hazard from investigation.md; lines 37-61 (age computation and the
`life_stage_set` write) beyond adding the new sibling block after them; lines 72-162 (death/succession
handling) — unrelated, must not be touched; `spawn_natural_creature_offspring()`/
`spawn_humanoid_offspring()` (`src/systems/world_systems/generator.py`) — read-only evidence for the
role gate, not a change target.
**Verify:** tests 1, 2, 3 — `test_coming_of_age_fires_exactly_once_on_child_to_adult_transition`,
`test_coming_of_age_does_not_fire_for_already_adult_or_elder_entities`,
`test_coming_of_age_role_set_uses_authoritative_identity_patch_path` (all in
`tests/unit/progression/test_lifecycle.py`); regression: `test_life_stage_transition_is_monotonic_forward_only`
(`tests/unit/progression/test_lifecycle.py:339-372`) must remain green (it does not assert
`role_set is None`, so it is unaffected but now incidentally exercises the new branch); **test 10
(NEW, regression for the role-gate fix)** —
`test_coming_of_age_monster_role_child_role_untouched_on_transition`: construct a CHILD entity the
same way `spawn_natural_creature_offspring()` does (`identity.role == EntityRole.MONSTER`,
`identity.faction == Faction.MONSTER_HORDE`, `identity.life_stage == LifeStage.CHILD`,
`lifecycle.parent_a_entity_id is None`, `lifecycle.parent_b_entity_id is None`,
`lifecycle.birth_tick` set nonzero, `lifecycle.age_ticks` fast-forwarded to just below the
CHILD/ADULT boundary), run one `resolve_lifecycle()` tick that crosses the boundary, and assert the
resulting `EntityUpdate.identity.role_set is None` (or, if no `IdentityUpdate` is produced at all for
role, that no `role_set` write exists) and — if applying the update — that
`EntityState.identity.role` remains `EntityRole.MONSTER` after apply. Location:
`tests/unit/progression/test_lifecycle.py`, beside test 6's no-birth-record fixtures.

### Step 5 — Metamorphic and no-collapse regression tests
**Files:** `tests/unit/strategic/test_coming_of_age_archetype_choice.py` (new file; test-only, no
`src/` changes in this step)
**Change:** Add the new `TestComingOfAgeMetamorphicConvergenceGuard` (or similarly named) test class
with:
- Test 4, `test_coming_of_age_metamorphic_regional_need_weight_increases_variance`: build a
  same-tick, same-region batch of CHILD-at-boundary entities sharing **fixed, identical**
  personality and parentless (or identically-parented) state so `personality_coeff`/`parental_coeff`
  contribute a constant, non-zero, single-role-favoring skew (e.g. uniformly high `bravery` biasing
  every entity toward GUARD) — this creates a genuinely low-variance baseline at `regional_coeff=0`
  to sweep away from, rather than an already-near-uniform baseline that cannot show a variance
  *increase*. Seed the region's live headcount tally so the real regional shortfall is concentrated
  in a *different* role than the personality bias (e.g. WORKER understaffed relative to target,
  GUARD already at/above target) — call `compute_role_weights(entity, state, regional_coeff=W)` (not
  the full `resolve_lifecycle()`) at ≥2 distinct `regional_coeff` values (e.g. `0.0` and `5.0`),
  convert each resulting weight vector to a probability distribution (`w_i / sum(w)`), compute
  variance or Shannon entropy over the distribution, and assert
  `entropy(regional_coeff=5.0) > entropy(regional_coeff=0.0)` strictly. This calls the **pure**
  Step 1 function directly — no RNG involved — so the assertion is on the shape of the distribution
  itself, matching the AC's "distribution" language precisely.
- Test 5, `test_coming_of_age_same_tick_batch_does_not_collapse_to_identical_occupation`: build N≥5
  same-tick, same-region CHILD-at-boundary entities under one fixed nonzero-regional-need
  configuration, run them through the full `LifecycleSystem.resolve_lifecycle()` (exercising Steps
  1-4 together, going through the real RNG draw), and assert `len({u.identity.role_set for u in
  resulting entity_updates.values()}) > 1`. If the first attempt collapses to one role, tune
  `WEIGHT_FLOOR`/coefficient constants in `src/ai/coming_of_age.py` (Step 1) — never the batch
  fixture — until the deterministic seed produces a non-collapsed result, then leave it as a fixed,
  permanently-passing regression test.
**Do NOT touch:** `OccupationChangeGoalScorer` or its own test file
(`tests/unit/strategic/test_occupation_change_scorer.py`) — re-run it unmodified per test_plan.md's
anti-drift guard to confirm zero behavioral drift.
**Verify:** both tests pass; `tests/unit/strategic/test_occupation_change_scorer.py` still passes
byte-for-byte unmodified.

### Step 6 — Docs: Mechanics Bible §9 and parity ledger STRAT-267
**Files:** `docs/mechanics/04_strategic_cognition.md`, `docs/parity_ledger/strategic_cognition.yaml`
**Change:** Append a new `## 9. Coming of Age Archetype-Choice Roll (idea 34)` section after §8
(which currently ends at `docs/mechanics/04_strategic_cognition.md:1017`), following §8's own
Gate/Direction/Durable-record/Out-of-scope/Source format exactly (§8 example read at lines 959-1017):
document the trigger site (CHILD→ADULT origin check beside the ELDER-branch precedent), the
weighting formula and its three terms plus `WEIGHT_FLOOR`, the seeded-RNG mechanism
(`DeterministicRNG.weighted_choice`, `Domain.STRATEGIC`), the no-birth-record compound-check
exclusion and its forward-compatibility caveat, and the convergence-risk metamorphic guard as a
named, permanent property of the mechanism (not just a test artifact). Add a new
`docs/parity_ledger/strategic_cognition.yaml` entry `id: STRAT-267` (next available ID after
`STRAT-266`, confirmed the max existing ID in this file per investigation.md and direct read at
`docs/parity_ledger/strategic_cognition.yaml:3920`), `status: verified`, `priority: P1` (not `P0` —
this is not a hard-conservation/determinism-critical law the way `STRAT-266`'s durable-record
plumbing is, though it does have its own determinism test coverage via test 9), `v2_evidence` citing
`src/ai/coming_of_age.py` and the `resolve_lifecycle()` sibling branch, `test_path` pointing at the
metamorphic test (test 4) as the primary regression anchor.
**Do NOT touch:** any other section of `04_strategic_cognition.md` or any other entry in
`strategic_cognition.yaml` (in particular, do not edit `STRAT-266`).
**Verify:** doc parity check (manual read-through against the implemented formula); no automated
test covers doc content directly, but `docs/REGISTRY.yaml` regeneration (Finalize phase) will pick
up the doc edit.

## Scope Guards

- Do not modify `OccupationChangeGoalScorer`'s selection logic, `_CANDIDATE_ROLES` tuple, or
  `_ROLE_APTITUDE_ATTR` (`src/ai/goals/occupation_change_scorer.py`) — read-only reuse of its
  regional target-count *pattern* only, via an independently-defined weighting module.
- Do not modify `BASE_OCCUPATION_DENSITY`/`MIN_OCCUPATION_SLOTS` (`src/world/occupation_config.py`)
  — read-only.
- Do not modify the ELDER-branch code inside `resolve_lifecycle()` (lines 63-68) or
  `compute_elder_attribute_update()` (`src/domains/demographics/cohort.py`) — the new branch is an
  independent sibling, not a change to that branch.
- Do not modify `LifeStageService`/`src/ai/life_stage.py` — no changes to age-boundary literals or
  `is_forward_transition()`.
- Do not modify `src/core/updates.py`/`IdentityUpdate` schema — `role_set` already exists
  (`src/core/updates.py:226`); no new field is needed.
- Do not register a new `GoalKind`/`GoalScorer` — Coming of Age stays a direct `LifecycleSystem`
  write, never a goal-hierarchy candidate evaluated by
  `StrategicIntelligenceSystem.evaluate_strategic_intent()`.
- Do not touch the birth-record write path (`src/engine/patches.py`, `src/core/builder.py`,
  `src/systems/world_systems/generator.py`'s `.birth_record(...)` sites, or any
  `LifecycleUpdate.birth_tick_set`/`parent_a_entity_id_set` write) — this ticket only reads those
  fields.
- Do not use Python's unseeded `random` module anywhere in `src/ai/coming_of_age.py` — must go
  through `DeterministicRNG` (`src/platform/rng.py`).
- Do not widen scope into idea 38's long-run corpus population-pressure convergence property — the
  metamorphic test is a bounded single-tick synthetic batch only.
- Do not modify `docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md` or
  `docs/brainstorm/rpg_feature_atlas.html` — both already correctly describe idea 34; this ticket
  fulfills the plan rather than revising it (per investigation.md's explicit finding).
- Do not modify `spawn_natural_creature_offspring()`, `spawn_humanoid_offspring()`, or any other
  entity-construction function in `src/systems/world_systems/generator.py` — Step 4's role gate
  (`entity.identity.role == EntityRole.CITIZEN`) is a read-only condition check against fields those
  functions already set; it must never rewrite how those functions construct entities.

## Dependency Map

- Step 1 (pure weight functions) — no dependencies, foundational.
- Step 2 (no-birth-record check) — no dependencies on Step 1's weight logic; same new file, so
  sequence after Step 1 to avoid file-content races, but functionally independent.
- Step 3 (RNG draw) — depends on Step 1 (`compute_role_weights`).
- Step 4 (lifecycle.py wiring) — depends on Step 2 and Step 3 (calls both
  `is_excluded_no_birth_record` and `choose_archetype`).
- Step 5 (metamorphic + no-collapse tests) — depends on Step 1 (direct pure-function calls for the
  metamorphic test) and Step 4 (full `resolve_lifecycle()` path for the no-collapse test).
- Step 6 (docs) — depends on Steps 1-5 being finalized (documents the actual shipped formula and
  behavior); sequence last.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — fires exactly once, one `IdentityUpdate` via authoritative `role_set` path, only for the intended citizen population | Steps 3, 4 | tests 1, 2, 3, 10 |
| AC2 — metamorphic: increasing regional-need weight strictly increases distribution variance/entropy | Steps 1, 5 | test 4 |
| AC3 — same-tick batch does not collapse to identical occupation when regional-need weight nonzero | Steps 1, 3, 5 | test 5 |
| AC4 — no-birth-record hard exclusion tracked/implemented, not silently omitted | Step 2, 4 | test 6 |
| AC5 — new unit tests following existing conventions, new test class for metamorphic/stochastic selection | Steps 1-5 | tests 1-9 collectively |
| AC6 — `docs/mechanics/04_strategic_cognition.md` §9 + `docs/parity_ledger/` STRAT-267 entry | Step 6 | manual doc parity check |

## Anti-Drift Notes

- The ELDER-branch precedent (`resolve_lifecycle()` lines 63-68) and `OccupationChangeGoalScorer`
  are both **read as structural precedent only** — never edited. Any diff touching either is
  out-of-scope drift.
- `entity.identity.personality`, not `entity.personality` — `PersonalityComponent` is nested inside
  `IdentityComponent` (`src/core/state.py:499-521`). Getting this access path wrong is a likely
  implementer mistake given `PersonalityService.get_goal_modifiers()`'s signature takes a bare
  `PersonalityComponent` and could mislead toward assuming a top-level field.
- The RNG service module path is `src/platform/rng.py`, not `src/core/rng.py` — the investigation
  brief cited the wrong path; this plan corrects it with a direct `find`-confirmed check.
- `resolve_lifecycle()` receives no `DeterministicRNG` instance from its caller
  (`src/engine/pipeline.py:389` passes only `(state, u)`) — constructing `DeterministicRNG(state.seed)`
  locally inside `choose_archetype()` is the established, already-used pattern for this exact
  situation (three other precedent sites cited in Decision 2), not a novel workaround.
- The origin-stage check (`entity.identity.life_stage == LifeStage.CHILD`, read from the pre-tick
  frozen `entity`) is what guarantees "exactly once" — do not weaken it to `target_stage == LifeStage.ADULT`
  alone, which would re-match on every subsequent tick once `get_stage_for_age` re-derives ADULT
  forever after the transition.
- `WEIGHT_FLOOR` and the metamorphic-test fixture design (Step 5) are structural aids toward AC2/AC3,
  not proofs — the implementer must empirically confirm the chosen seed/fixture actually produces
  non-collapsed, monotonically-increasing-entropy output, and may tune coefficients/floor (not batch
  composition) if the first attempt doesn't.
- Every CHILD-life-stage entity in the current live codebase already carries a real birth record (both
  CHILD-construction call sites — `generator.py:115`, `generator.py:185` — unconditionally chain into
  `.birth_record(...)`) — so the Step 2 exclusion currently excludes zero real entities. This is
  expected and correct: it is forward-looking correctness for a hypothetical future bare-construction
  CHILD path, not evidence the check is dead code to skip.
- **Birth-record presence and entity role/species are orthogonal signals — do not conflate them.**
  `is_excluded_no_birth_record()` (Step 2) does NOT catch the flag-gated Natural-Creature reproduction
  path: `spawn_natural_creature_offspring()` (`src/systems/world_systems/generator.py:87-120`) builds a
  `role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE, life_stage=LifeStage.CHILD` entity and still
  calls `.birth_record(parent_a_entity_id=None, parent_b_entity_id=None, birth_tick=<real nonzero
  tick>, ...)` — a nonzero `birth_tick` in the practically-reachable case, so the compound exclusion
  check evaluates `False` (not excluded). Step 4's branch is only made safe against this case by the
  separate, explicit `entity.identity.role == EntityRole.CITIZEN` gate added per Decision 5 — never
  assume the no-birth-record check alone is sufficient population scoping.

## Unresolved Questions

None. All four flagged decision points (AC4 scope, RNG mechanism, weighting formula, parent-resolution
fallback) are resolved above with direct source citations; no genuine architectural conflict requiring
a human call was found during verification.

**Revision (2026-09-02, post architecture-review NEEDS_CHANGES):** added Decision 5 — a role gate
(`entity.identity.role == EntityRole.CITIZEN`) on Step 4's branch, closing a blocking gap the review
found: the original branch had no role/species gate and would have fired for MONSTER-role CHILD
entities from the flag-gated Natural-Creature reproduction path
(`spawn_natural_creature_offspring()`), overwriting `role_set` to a citizen occupation on an
incoherent MONSTER_HORDE-faction entity. Resolved with direct evidence, not left open: see Decision 5,
Step 4, Scope Guards, and Anti-Drift Notes above. No other part of the plan changed.

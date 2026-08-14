---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY
artifact_type: investigation
tags: [cognition, strategy]
---

# Investigation — TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY

## Current Behavior

**`AdventureDecisionPhase.apply()`** (`src/domains/adventure/phase.py:73-77`):

```python
heroes = [
    e for e in state.entities.values()
    if e.identity.role == EntityRole.HERO and e.combat.alive and e.lifecycle.active
]
```

`EntityRole.HERO = 0` (`src/core/enums.py:6-12`, `IntEnum`). This is the sole role/cognition axis
of the eligibility filter today (alive/active/lock-status are the other three, retained unchanged
per the design). `EntityRole` is never imported for any other purpose in `phase.py`, so removing
this check will leave the `from src.core.enums import EntityRole` import (`phase.py:14`) unused —
a cleanup item, not a behavior concern.

**`CognitionProfileDefinition`** (`src/content/schema.py:91-100`) currently has 8 optional
qualitative string fields (`planning_depth`, `abstraction`, `memory_span`, `language_capacity`,
`tool_reasoning`, `social_reading`, `social_reasoning`, `risk_modeling`) and no boolean/behavioral
field. `data/content/living/cognition_profiles.yaml` defines exactly 7 profiles:
`practical_humanoid`, `instinctive_animal`, `opportunistic_humanoid`, `disciplined_guard`,
`trade_pragmatist`, `arcane_scholar`, `undead_fixated`.

**`CapacityService.derive_profile()`** (`src/strategy/cognition_capacity.py:14-56`) — confirmed by
direct read — computes the live `CognitionProfile` (max_active_projects, max_leads,
interruption_resistance, etc.) purely from `entity.attributes` (intelligence/wisdom/perception),
`entity.identity.personality`, and `entity.biological`. It never reads
`entity.identity.properties["cognition_profile_id"]` or any `CognitionProfileDefinition` field.
This confirms the design doc's "dormant mechanism" claim for this specific consumer, but does
**not** by itself confirm eligibility-side zero-regression (see Risks below — a separate consumer
gap was found).

**`cognition_profile_id` resolution path — three distinct entity-construction paths exist, and
they do NOT resolve `cognition_profile_id` uniformly:**

1. **Archetype-native path** (`src/content/resolver.py::EntityArchetypeResolver` →
   `src/entities/contract_builder.py::resolved_archetype_to_contract` →
   `src/entities/archetype_factory.py::ArchetypeEntityFactory.build_entity`, lines 56-57): sets
   `properties["cognition_profile_id"] = contract.cognition_profile_id` whenever
   `contract.cognition_profile_id is not None`. This is the path used by
   `data/content/entities/populations.yaml`-driven spawns (e.g. `apprentice_mage`,
   `lizardfolk_shaman`).
2. **World-assembly role-based path** (`src/worldassembly/resolver.py::ProfileResolutionEngine
   .resolve()`, lines 969-1032, feeding `src/worldassembly/entity_spawner.py
   ::WorldEntitySpawner._spawn_legacy_guard`, lines 101-141): used whenever a
   `population_recipes` entry specifies `role:`/`faction:`/`count:` with **no `archetype_id`** —
   this is exactly the shape of `data/content/world_modules/hero_adventurers.yaml`
   (`role: "hero"`, no `archetype_id`), the module that actually spawns HERO entities in real
   worlds (`hero_guild_routing`, `simq_routing_test`, and 7 others via `module_refs`). In this
   branch, `resolved_arch` is `None` (no `archetype_id` to resolve), so `ResolvedEntityProfile` is
   built via the `else` branch (`resolver.py:1020-1032`) which **never sets
   `cognition_profile_id`** (Pydantic default `None`, `worldassembly/models.py:32`).
   `_spawn_legacy_guard` (`entity_spawner.py:118-127`) then builds
   `identity.properties = {"archetype_id": None, "race_id": None, "role_id": None,
   "faction_id": None}` — **`cognition_profile_id` is not even a key in this dict.**
   `identity.role` is still correctly set to `EntityRole.HERO` (via
   `RoleSemanticsService.get_legacy_entity_role("hero")`, independent of this gap), which is
   exactly why today's role-only check works for these entities but a `cognition_profile_id`
   lookup would not.
3. **Legacy `WorldSpec` compiler path** (`src/worldbuilding/compiler.py::get_role_enum`,
   `WORLD-050/051/052`): `grep` of the whole file confirms zero references to
   `cognition_profile` anywhere — this path also never threads a `cognition_profile_id`.

**Test fixtures**: `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`
and the sibling `tests/unit/domains/adventure/test_phase3_*` files construct hero entities via bare
`V2EntityBuilder(...).identity(evolution_level=..., personality=...)` with no `properties=` at
all — `identity.role` defaults to `0` (`HERO`) via `archetype_factory.py:74`'s `... else 0`
pattern, but `identity.properties` is empty, so `cognition_profile_id` is absent there too.

**Architectural constraint on resolution (`WORLD-CAT-004`)**: `src/engine/kernel.py:320-326,
351-358` and `src/content/repository.py` (`ContentHotPathViolation`, `_tick_context_active`)
enforce that `CatalogRepository.load_all()` must never be called from inside `tick_once()`.
`ContentWarmupService.warmup()` (`src/content/warmup.py`) is called once in `Kernel.__init__`
(before the tick loop) and installs a pre-loaded catalog into module-level singletons via
`configure_faction_semantics_service()` and `configure_behavior_consumers()`
(`src/engine/behavior_consumers.py`). The established pattern for tick-loop code that needs
catalog reads (`get_perception_gate()`, `get_pressure_resolver()` in `behavior_consumers.py:33-46`)
is: a module-level singleton, configured once via `ContentWarmupService.warmup()`, accessed via a
`get_*()` accessor with an `_auto_init()` fallback for tests. No such singleton exists yet for
cognition-profile lookups — this must be added following the same pattern, not a raw
`CatalogRepository(...).load_all()` call inside `AdventureDecisionPhase.apply()`.

## Mechanics / Engine Constraints

- `docs/simulation/domains/adventure_contract.md` §"Engine Phase" documents the eligibility table
  as `Role: EntityRole = 0 (hero)` plus alive/active/lock-status — the doc this ticket's code
  change diverges from (update owned by sibling ticket TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-
  DOCS, not this one).
- `docs/parity_ledger/strategic_cognition.yaml` `STRAT-243` (see below) directly documents the
  current role-only enforcement as `verified` — this ticket makes its `text`/`v2_evidence`
  inaccurate (ledger update also owned by the sibling docs ticket).
- `WORLD-CAT-004` (`src/content/repository.py`, `src/content/warmup.py`) — hard runtime guard
  against `CatalogRepository.load_all()` inside the tick loop; directly constrains *how* the new
  eligibility check may resolve `CognitionProfileDefinition` (see Current Behavior above).
- No `docs/mechanics/` chapter documents `CapacityService.derive_profile()`'s own
  attribute-only formula as intentionally excluding `cognition_profile` — the design doc's
  "dormant mechanism" framing is a real, confirmed finding, not a documented divergence yet.

## Docs Requiring Update

- `docs/mechanics/content_usage_matrix.md`: the `living/cognition_profiles` row (line 36) lists
  "Runtime Consumer Evidence: None yet" and Compile/Runtime Consumer limited to
  `CompileContext, WorldCompiler` — this ticket adds `AdventureDecisionPhase` as a genuine new
  runtime consumer of the profile (via `supports_adventure_routing`), making that cell stale. This
  is distinct from the mechanics/adventure_contract/parity-ledger updates owned by the sibling
  docs ticket (TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS) — it is the content-family
  wiring-status ledger, not simulation-law documentation.

## Parity Ledger Overlap

- **`STRAT-243`** (`docs/parity_ledger/strategic_cognition.yaml:2803-2824`), status `verified`,
  priority `P1`. Text: "AdventureDecisionPhase.apply() eligibility filter enforces all four
  documented criteria: Role = EntityRole.HERO (0), combat.alive = True, lifecycle.active = True,
  and project-lock gating." `test_path`:
  `tests/unit/systems/test_spawn_lock_condition.py::TestLockHeldWhenThreatActive`. This entry's
  `text`/`v2_evidence` become inaccurate the moment `phase.py:76`'s role check is replaced; its
  `test_path` must keep passing post-fix (it does not test role directly, only lock-release
  behavior, so it should be unaffected by the eligibility-axis change itself). Not P0, so a
  passing `test_path` isn't a hard *gate* requirement, but it is directly, substantively touched
  by this ticket's own scope — flagging per the "Parity Ledger Overlap" contract even though the
  actual YAML edit is owned by the sibling docs ticket per this ticket's Out-of-Scope section.
  No other `strategic_cognition.yaml` entry references `AdventureDecisionPhase`,
  `cognition_profile`, or the eligibility filter by name (checked via full-file grep).

## Prior Work

- **`TCK-20260703-ADVENTURE-ELIGIBILITY-ROLE-FILTER`** (`tickets/done/`, no stored artifacts —
  hotfix tier): introduced the `EntityRole.HERO` check this ticket now replaces. Originally the
  role criterion was documented but *not* enforced in code at all (any alive/active entity of any
  role was routed as a hero) — that hotfix added the missing enforcement and the `STRAT-243`
  ledger entry. Also fixed two dependent test fixtures
  (`test_spawn_lock_condition.py::_make_hostile`, `test_decision_trace.py
  ::test_adventure_decision_phase_wires_writer`) to explicitly set non-HERO/HERO role.
- **`TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF`** (`tickets/done/`,
  `stored_artifacts/TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF/`): confirmed
  `ENABLE_ADVENTURE_ROUTING` defaults OFF corpus-wide by a deliberate, ratified Design Authority
  ruling (`TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`) — routing is per-world opt-in, not a baseline.
  Only **2 of 20** real corpus worlds currently opt in: `hero_guild_routing` and
  `simq_routing_test` — both of which use the `hero_adventurers` world module (role-based,
  no `archetype_id`), i.e. both of the only two worlds that actually exercise
  `AdventureDecisionPhase.apply()` today go through the `cognition_profile_id`-less spawn path
  identified above. That ticket also found a real, separate FACTION/INFORMATION RNG-coupling
  regression when testing a third opt-in candidate (`frontier_marches`) — reverted, tracked as
  `TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING`, unrelated to this ticket's own
  scope but a reminder that this code path has a recent history of hidden coupling issues.
- **`TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`** (`tickets/inprogress/`,
  `staging_artifacts/`, sibling in-flight ticket): the investigation that produced the design doc
  this ticket implements; not yet DONE, so no `stored_artifacts/` to cross-reference beyond the
  design doc itself.

## Risks and Open Questions

1. **[BLOCKING — requires a Plan-level decision] `cognition_profile_id` is absent from
   `identity.properties` for the exact real-world entities the design doc claims "zero
   regression" for.** The design doc's own regression analysis (`## Rollout risk`) only verified
   the archetype-native corpus (`populations.yaml`/`packs/`). It did not check the
   `hero_adventurers` world-module spawn path, which is the actual mechanism that puts HERO
   entities into the two real worlds where `ENABLE_ADVENTURE_ROUTING` is ON today
   (`hero_guild_routing`, `simq_routing_test`). Those entities have `identity.role == HERO` (still
   works under the old check) but **no `cognition_profile_id` key at all** in
   `identity.properties` (confirmed via `_spawn_legacy_guard`,
   `src/worldassembly/entity_spawner.py:118-127`). A naive "resolve `cognition_profile_id` from
   properties, look up the catalog, default to ineligible if missing" implementation would
   silently zero out adventure routing for every hero in both currently-opted-in worlds — the
   opposite of "zero regression." The same gap affects most existing unit/integration test
   fixtures in `tests/unit/domains/adventure/` and `tests/integration/domains/adventure/`, which
   build entities via bare `V2EntityBuilder` with no `properties=`. **This must be resolved by
   Plan, not assumed here**: options include (a) giving `_spawn_legacy_guard`/`ProfileResolutionEngine`
   a `cognition_profile_id` fallback derived from the role's `default_cognition_profile`
   (`RoleDefinition.default_cognition_profile` — `roles.yaml`'s `hero` role already declares
   `default_cognition_profile: "practical_humanoid"`, mirroring the exact fallback pattern
   `EntityArchetypeResolver._resolve_from_definition` already uses at `resolver.py:460-462`), or
   (b) having the new eligibility check itself fall back to the role's default when
   `cognition_profile_id` is missing, or (c) some other explicit policy. Whichever is chosen must
   also keep the archetype-native corpus's own explicit `cognition_profile_id` values authoritative
   (i.e., not silently override an archetype's explicit choice with a role default).
2. **The design doc's "only human/practical_humanoid is compatible with the hero role today"
   claim is narrower than the real corpus.** `roles.yaml` shows `mage`, `hunter`, and `shaman`
   roles also carry `legacy_engine_role: "HERO"`, and `contract_builder.py:30`
   (`_try_role(arch.legacy_engine_role)`) means any archetype using those roles gets
   `identity.role == EntityRole.HERO` too — not just the `hero`-role `adventurer_hero` archetype.
   Of the archetypes with a legacy-HERO role, only `apprentice_mage` (`arcane_scholar` profile)
   and `lizardfolk_shaman` (`practical_humanoid` profile, explicit override) are actually spawned
   in real content (`populations.yaml:70,91,99`, `packs/swamp_border_pack.yaml`) —
   `adventurer_hero`, `bandit_cutpurse`, `dwarven_hunter`, `arcane_mage`, `moon_cult_sorcerer` are
   defined but not referenced by any population recipe or world module (confirmed via
   repo-wide grep; the only hits outside `entity_archetypes.yaml` are catalog-validation report
   JSON files that enumerate the full catalog, not per-world spawn lists). Both real spawned
   profiles (`arcane_scholar`, `practical_humanoid`) are ones the design doc already plans to mark
   `True`, so this narrower claim does not itself break "zero regression" for the archetype-native
   path — but it means the design doc's own stated evidence for that claim is incomplete, and the
   authored `supports_adventure_routing` values must still be evaluated against this wider set of
   role/profile combinations, not just `hero`/`practical_humanoid`.
3. **`disciplined_guard`/`trade_pragmatist` authoring is a real judgment call with concrete
   evidence now gathered, not yet decided.** `disciplined_guard` is `default_cognition_profile`
   for `guard`/`ranger` roles and explicitly set on `frontier_guard`/`forest_ranger` archetypes;
   `trade_pragmatist` is `default_cognition_profile` for `shopkeeper`/`merchant` roles and
   explicitly set on `traveling_merchant`. None of these archetypes carry a legacy-HERO role
   today, so marking either profile `True` is a pure *expansion* (no existing eligible entity
   loses eligibility) but does newly make real, currently-spawned entities
   (`frontier_guard`, `forest_ranger`, `traveling_merchant`) adventure-eligible — consistent with
   Goal 1's "regardless of role" intent, but a real behavioral change to flag explicitly in Plan,
   not silently default to `False`.
4. **Marking `practical_humanoid`/`arcane_scholar` `True` expands eligibility beyond the "hero"
   role for non-hero races too**, e.g. `dwarf`/`lizardfolk` (both `practical_humanoid`) and
   `dragonkin`/`spirit` (both `arcane_scholar`) — none currently HERO-role, all become eligible
   post-fix if their current role/lock/alive/active state qualifies. This is the design's
   explicitly intended Goal 1 behavior, not a bug, but is a large surface-area change worth the
   implementer being aware of for the zero-regression test's scope (it should assert the *existing*
   hero scenario is unchanged, not that *no* new entity ever becomes eligible).
5. Open question already flagged by the design doc itself (score-scale mismatch between System A's
   ≈2.9 max and System B's 100 max, and `AdventureDecisionPhase` never calling
   `evaluate_project_switch()`) belongs to the sibling interruption-bypass ticket (C2,
   `intelligence.py`), explicitly out of scope here — noted only so it isn't conflated with this
   ticket's own eligibility-only change during review.

## Anti-Drift Hazards

- **Do not touch `src/domains/adventure/scoring.py` lines 161/252** — the two other
  `EntityRole.HERO` checks (QUEST_OPPORTUNITY capability-match scaling and the group
  class-synergy 1.10x multiplier) are explicitly out of scope; they live in the same file family
  and a reviewer/implementer could easily conflate "eligibility" with "scoring" here.
- **Do not touch `src/systems/strategic_systems/intelligence.py::evaluate_project_switch`** — the
  generic interruption-bypass generalization is C2's scope, a separate ticket.
- **Do not hand-edit `docs/mechanics/04_strategic_cognition.md`,
  `docs/simulation/domains/adventure_contract.md`, or
  `docs/parity_ledger/strategic_cognition.yaml`** even though they are the most obviously
  "correct" docs to touch — they are explicitly owned by
  `TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS` per this ticket's own Out-of-Scope section.
- **Do not implement the eligibility resolution via a raw `CatalogRepository(...).load_all()`
  call inside `AdventureDecisionPhase.apply()`** — this violates `WORLD-CAT-004` and will raise
  `ContentHotPathViolation` in production ticks (though not necessarily in isolated unit tests
  that don't set `_tick_context_active`, which could let a violation slip through unnoticed in
  Test if the test doesn't run through `Kernel.tick_once()`).
- **Do not assume `cognition_profile_id` is always present in `identity.properties`** — see Risk
  1. Any implementation that does `entity.identity.properties["cognition_profile_id"]` (KeyError)
  or silently treats a missing key as "not eligible" without an explicit, reviewed fallback
  decision will regress the only two real worlds that exercise this phase today.
- **The `hero` role's own `default_cognition_profile` is `"practical_humanoid"`
  (`roles.yaml:6`)** — if a fallback-to-role-default approach is chosen (Risk 1, option a/b), this
  is the concrete value that preserves today's behavior for `hero`-role entities; do not invent a
  different default.

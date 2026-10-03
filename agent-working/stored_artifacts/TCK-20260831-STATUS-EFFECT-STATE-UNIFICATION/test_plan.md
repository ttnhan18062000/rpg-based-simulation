---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION
artifact_type: test_plan
tags: [architecture]
---

# Test Plan — TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION

## Regression Surface

### Unit — status_frozen / status_stunned (all currently construct entities via direct
`identity.properties={"status_frozen": True}` / `{"status_stunned": True}` dict literals — every one
of these must keep passing with the same assertions after the fixture construction is switched to
the new typed `StatusEffectState` shape; a failing test here means behavior changed, not just
storage):
- `tests/unit/combat/test_phase5_combat_legality.py` (line 62 — `status_frozen` fixture)
- `tests/unit/combat/test_combat_legality_regression.py` (line 51 — `status_frozen` fixture)
- `tests/unit/combat/test_rpg_core_recovery.py` (line 188 — `status_frozen` fixture)
- `tests/unit/combat/test_phase5_negative_cases.py` (lines 184, 194, 255 — both `status_stunned` and
  `status_frozen` fixtures)
- `tests/unit/combat/test_tactical_hardening.py` (line 30 — `status_stunned` fixture)
- `tests/unit/strategic/test_status_hardening.py` (lines 22, 45 — both keys; test names
  `test_frozen_actor_skips_strategic_intent`, `test_stunned_actor_skips_strategic_concerns`,
  `test_staggered_frequency_distribution` — these directly cover 2 of the 3
  `intelligence.py` call sites, 848/918)
- `tests/unit/core/test_hardening_e5.py` (line 65 — `status_stunned` fixture; test name
  `test_negative_case_stunned_actor_rejection` — covers `actor_validity.py`)
- `tests/unit/combat/test_direct_combat_outcomes.py` — covers `combat.py`'s
  `calculate_tactical_multipliers` including the SHATTER path; must confirm this file is grepped for
  `status_frozen`/SHATTER coverage during Plan/Implement (not directly confirmed by this
  investigation's grep list above — grep it before relying on it).

### Unit — interaction_kind / InteractionComponent:
- `tests/unit/world/test_town_services.py` — `town_service.py` (`"inn"`/`"tavern"`/`"guild"` kinds)
- `tests/unit/world/test_guild_intel.py` — `guilds.py` (`"guild"` kind, line 12 fixture)
- `tests/unit/world/test_chest_lifecycle.py` — `chests.py` (`"chest"` kind, line 14 fixture)
- `tests/integration/kernel/test_resource_conservation_v2.py` and
  `tests/integration/kernel/test_resource_conservation.py` — exercise `interaction_kind` through
  real harvest/loot atomic-conservation paths (production-writer-backed, unlike chest/guild/inn/
  tavern — these are the closest thing to an end-to-end trace for `interaction_kind` and should be
  weighted heavily as regression evidence)
- harvest/loot action + system pairs have no dedicated named test file found in this investigation's
  grep pass — before Plan finalizes, grep `tests/` for `HarvestAction`/`HarvestSystem`/`LootAction`/
  `LootSystem` directly to confirm coverage beyond the resource-conservation integration tests above.

### Architecture / determinism:
- `tests/unit/domains/optimization/test_component_patches.py` — covers the `ComponentPatch`/
  `extract_patches` family (`IdentityPatch`, `WoundPatch`, `InteractionPatch`, and the new
  `StatusEffectPatch`/`InteractionPatch` `kind` extension land here conceptually) — must be extended,
  not just kept green, if Plan adds a new patch class.
- Any existing canonical-hash / determinism replay test that exercises `EntityState.to_canonical_dict()`
  (search `tests/` for `to_canonical_dict` or `canonical_dict` before Implement) — required because
  moving `status_frozen`/`status_stunned`/`interaction_kind` off the `identity.properties` dict
  changes what feeds the `"properties"` key at `state.py:796`; a canonical-hash regression test
  guards against silently dropping this state from the determinism hash (see investigation.md Risk
  #1).

## New Tests Required

- **`StatusEffectState` typed-record schema test**
  Category: unit
  Verifies: the new frozen dataclass has the fields Plan settles on, is immutable (`frozen=True`),
  and (if it follows the `WoundState`/`ScarState` shape) serializes via `asdict`/`to_canonical_dict`
  consistently with the existing component pattern.
  Location: `tests/unit/core/test_state_status_effect.py` (new file, mirrors no exact existing file —
  closest sibling is wherever `WoundState`/`ScarState` schema is tested, if such a file exists; grep
  `tests/` for `WoundState` schema-level assertions before Plan finalizes file location).

- **Behavior-provably-unchanged: no active status → all 5 consumers behave identically**
  Category: unit / regression-parity
  Verifies: for an entity with *no* `StatusEffectState` entries (the default/empty case — this is
  the production-realistic case per investigation.md's "no production writer" finding), each of the
  5 consumer files (`legality.py` x4 call sites, `combat.py`, `actor_validity.py`,
  `work_queue.py`, `intelligence.py` x3 call sites) produces the exact same result as before
  migration (legal/not-blocked, no SHATTER multiplier, not skipped from work queue/strategic cycles).
  This is the specific "behavior provably unchanged for entities with no active status" case AC #2
  calls out by name.
  Location: extend the existing files in Regression Surface above in place (add a no-status
  baseline case next to each existing frozen/stunned-active case) rather than a new file, so the
  before/after contrast lives next to the existing positive-case test.

- **Behavior-provably-unchanged: active status (frozen/stunned) → all 5 consumers still block/gate
  identically**
  Category: unit / regression-parity
  Verifies: constructing an entity via the new typed `StatusEffectState` (instead of the old dict
  literal) reproduces the exact same blocked/gated outcome the existing 13 test-fixture sites
  currently assert. This is effectively "port the existing fixtures to the new construction API and
  confirm the assertions are unchanged" — covered by keeping the Regression Surface tests above green
  after their fixture lines are updated, not a new test per se, but flag explicitly as a required
  verification step distinct from just "tests still pass" (a fixture that silently stops constructing
  an active status would make these tests pass for the wrong reason — false negative risk).

- **SHATTER multiplier exact-value regression**
  Category: unit
  Verifies: `defender.status_frozen` (post-migration typed form) still yields exactly `atk_mult *=
  1.5` and `trace["SHATTER"] = 1.5` in `CombatResolutionSystem.calculate_tactical_multipliers`, and
  that `status_stunned` alone (frozen absent) does **not** trigger SHATTER (asymmetry check — only
  `combat.py:84` reads `status_frozen`, never `status_stunned`, for this specific multiplier).
  Location: `tests/unit/combat/test_direct_combat_outcomes.py` (extend) or wherever the existing
  SHATTER/`COMB-122`/`test_shatter_combo` coverage lives — locate it first via grep, do not assume.

- **`interaction_kind` migrated onto `InteractionComponent`/`InteractionUpdate` — reset clears kind**
  Category: unit
  Verifies: after `InteractionUpdate(reset=True)` is applied, the resulting `InteractionComponent`'s
  `kind` (or wherever Plan lands the field) is cleared/default, matching the new
  `InteractionComponent()` reset semantics — an explicit test for the behavior noted in
  investigation.md's "Reset/staleness note" (the old dict-based `interaction_kind` never cleared on
  reset; this is a provably-inert side effect since no consumer reads `interaction_kind` when
  `target_node_id is None`, but the new clearing behavior should be pinned by a test rather than left
  implicit).
  Location: `tests/unit/domains/optimization/test_component_patches.py` (extend, alongside existing
  `InteractionPatch` coverage) or a new `tests/unit/core/test_interaction_component.py` if no such
  file exists — check first.

- **`interaction_kind` value-set parity for all 7 closed values**
  Category: unit
  Verifies: each of `"harvest"`, `"ground_item"`, `"corpse"`, `"chest"`, `"guild"`, `"inn"`,
  `"tavern"` still routes to the correct consumer system after migration, including the 4 values
  (`"chest"`, `"guild"`, `"inn"`, `"tavern"`) that have no production writer today and are only
  exercised via test fixtures — confirm the fixture-construction API change (dict literal → typed
  field) doesn't accidentally drop coverage for these test-only paths.
  Location: extend `test_town_services.py`, `test_guild_intel.py`, `test_chest_lifecycle.py` in
  place.

- **Determinism/canonical-hash coverage guard**
  Category: architecture guard
  Verifies: `EntityState.to_canonical_dict()` output for an entity with an active `StatusEffectState`
  entry (or a live `interaction.kind`) differs from the same entity with that state cleared — i.e.
  the new typed field(s) actually feed the canonical hash the way `identity.properties` used to,
  closing the gap flagged in investigation.md Risk #1. A silent no-op here (hash unchanged whether or
  not the field is set) is the specific regression this guard exists to catch.
  Location: wherever existing canonical-hash coverage lives for `WoundState`/`ScarState` (grep
  `to_canonical_dict` in `tests/` first) — add a sibling case, or a new
  `tests/unit/core/test_canonical_hash_status_effect.py` if no natural home exists.

## Scoped Pytest Commands

```bash
# Status-flag consumers (legality, combat, actor_validity, strategic/intelligence, work_queue)
pytest tests/unit/combat/test_phase5_combat_legality.py tests/unit/combat/test_combat_legality_regression.py \
       tests/unit/combat/test_rpg_core_recovery.py tests/unit/combat/test_phase5_negative_cases.py \
       tests/unit/combat/test_tactical_hardening.py tests/unit/combat/test_direct_combat_outcomes.py \
       tests/unit/strategic/test_status_hardening.py tests/unit/core/test_hardening_e5.py -v

# interaction_kind consumers (world/economy/social systems)
pytest tests/unit/world/test_town_services.py tests/unit/world/test_guild_intel.py \
       tests/unit/world/test_chest_lifecycle.py -v

# Resource-conservation integration coverage (production-backed interaction_kind trace)
pytest tests/integration/kernel/test_resource_conservation.py tests/integration/kernel/test_resource_conservation_v2.py -v

# Component patch / typed-update architecture layer (extract_patches, new patch classes)
pytest tests/unit/domains/optimization/test_component_patches.py -v

# Broader combat domain sanity sweep (do NOT run pytest tests/ — scope to the domain)
pytest tests/unit/combat/ -m "not slow" -v

# Broader strategic domain sanity sweep
pytest tests/unit/strategic/ -m "not slow" -v
```

Never `pytest tests/`. Always scope to the directories/files above; add the new test file(s) to the
same scoped commands once Plan settles their exact paths.

## Anti-Drift Test Guards

- A test asserting `status_sleeping` behavior in `actor_validity.py` must still pass unmodified using
  the old untyped-dict read — if a test starts failing there after this migration, it's a sign the
  migration accidentally touched `status_sleeping` (out of scope, see investigation.md Anti-Drift
  Hazards).
- A test asserting `harvest_duration` behavior in `harvesting.py`/`harvest.py` must still pass
  unmodified using the old untyped-dict read — same guard, for the other adjacent-but-out-of-scope
  property key.
- The SHATTER-asymmetry test (frozen triggers it, stunned alone does not) guards against an
  accidental "simplify to one flag" refactor during the typed migration that would silently change
  combat balance.
- The four never-produced `interaction_kind` values (`"chest"`, `"guild"`, `"inn"`, `"tavern"`)
  should each keep exactly zero production writers after this migration — if Implement adds a real
  writer for any of them "while in the area," that's new functionality/scope creep this ticket did
  not authorize; a diff-review guard (not an automated test) should catch this at Verify.
- `EmotionUpdateService`/`EmotionalModel`/`hardening.py` should show zero diff in `git status` after
  this ticket — any touch there is out of scope (see investigation.md).

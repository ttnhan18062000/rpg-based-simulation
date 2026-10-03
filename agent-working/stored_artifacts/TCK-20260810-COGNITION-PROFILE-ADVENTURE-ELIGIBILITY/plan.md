---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY
artifact_type: plan
tags: [cognition, strategy]
---

# Implementation Plan — TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY

## Summary

Replace the hardcoded `entity.identity.role == EntityRole.HERO` eligibility gate in
`AdventureDecisionPhase.apply()` with a check against the entity's resolved
`CognitionProfileDefinition.supports_adventure_routing`. The critical design decision — confirmed
by Investigate, not re-opened here — is that `cognition_profile_id` is genuinely absent from
`identity.properties` for every entity spawned by the `hero_adventurers` world module (the only
mechanism populating the two real corpus worlds that have `ENABLE_ADVENTURE_ROUTING` on today:
`hero_guild_routing`, `simq_routing_test`). A naive "missing profile = ineligible" implementation
would silently zero out routing for both worlds. This plan therefore builds a two-tier resolution:
(1) an entity's explicit `identity.properties["cognition_profile_id"]` always wins when present;
(2) when absent, resolve via `identity.properties["role_id"]` → `RoleDefinition
.default_cognition_profile`, mirroring `EntityArchetypeResolver`'s existing archetype-or-role-
default pattern (`src/content/resolver.py:460-462`); (3) when `role_id` is *also* absent (the
confirmed real-corpus gap for `hero_adventurers`-spawned entities — see Step 4), fall back through
the legacy `EntityRole` enum for the one evidenced case (`EntityRole.HERO` → the `"hero"` role's
own `default_cognition_profile`, `"practical_humanoid"`, `data/content/social/roles.yaml:6`). All
catalog reads go through two new pure-reader accessor functions added to the existing
`src/engine/behavior_consumers.py` singleton (already populated by `ContentWarmupService.warmup()`
before the tick loop per `WORLD-CAT-004`), never a fresh `CatalogRepository(...).load_all()` call
inside `apply()`.

The 7 `supports_adventure_routing` values are authored directly from the qualitative cognition
fields already present in `data/content/living/cognition_profiles.yaml` (read in full during this
planning pass) and the role/archetype cross-reference evidence gathered in `investigation.md`
Risks 2–4: `practical_humanoid`, `opportunistic_humanoid`, `disciplined_guard`, `trade_pragmatist`,
`arcane_scholar` → `True` (all have `language_capacity` ≥ `medium` and `tool_reasoning` ≥ `medium`,
i.e. tool-using, language-capable "civilized" cognition); `instinctive_animal`, `undead_fixated` →
`False` (both have the lowest tier on every field — `very_low`/`none`/`low`/`fragmented` — matching
the ticket's own "instinctive/simple races... never are" framing).

## Steps

### Step 1 — Add `supports_adventure_routing` field to the schema
**Files:** `src/content/schema.py`
**Change:** Add `supports_adventure_routing: bool = Field(False)` to `CognitionProfileDefinition`
(currently 8 optional string fields, no boolean field — confirmed by direct read,
`src/content/schema.py:91-100`). Insert it as a new field on that class, e.g. after
`risk_modeling` (line 100), before the class ends. Use `Field(False)` (not
`Optional[bool] = None`) so every profile that omits the key still resolves to a concrete,
non-`None` boolean — this matters because Step 4/5's eligibility check does a plain truthiness
test on the resolved definition's field, and a `None` default would make "profile omitted the
field" indistinguishable from "profile explicitly set it False" in a way that could silently
admit an unauthored profile.
**Do NOT touch:** the other 8 existing fields on `CognitionProfileDefinition`, or any other
class in `schema.py` (e.g. `DriveProfileDefinition` at line 86, `StatsProfileDefinition` at line
103 — same file, not in scope).
**Verify:** `test_schema_supports_adventure_routing_field` (new, per test_plan.md item 6) —
schema-acceptance half only at this step; the full-catalog-parses-with-values half depends on
Step 2.

### Step 2 — Author `supports_adventure_routing` values for all 7 profiles
**Files:** `data/content/living/cognition_profiles.yaml`
**Change:** Add `supports_adventure_routing: true` or `false` to each of the 7 existing profile
blocks (`practical_humanoid` line 3, `instinctive_animal` line 14, `opportunistic_humanoid` line
25, `disciplined_guard` line 36, `trade_pragmatist` line 47, `arcane_scholar` line 58,
`undead_fixated` line 69 — all line numbers confirmed by direct read of the full file this
session). Authored values, with the qualitative-field evidence backing each (all field values
below are cited from the same direct read):
  - `practical_humanoid` → `true`. Existing `hero` role default (`roles.yaml:6`); zero-regression
    baseline. Fields: `planning_depth: medium, language_capacity: high, tool_reasoning: medium`.
  - `instinctive_animal` → `false`. This is the ticket's own named negative-case profile (AC:
    "instinctive_animal-profile entity with role artificially set to HERO is NOT included").
    Fields: `planning_depth: very_low, language_capacity: none, tool_reasoning: none` — the only
    profile with `none` on two axes.
  - `opportunistic_humanoid` → `true`. Fields: `planning_depth: low_medium, language_capacity:
    medium, tool_reasoning: medium, social_reasoning: medium` — humanoid-tier cognition (used by
    `scout`/`raider`/`leader`/`brute` roles per `roles.yaml`), consistent with the ticket's
    "regardless of role" goal; this is a real eligibility expansion for those roles, not a
    zero-regression concern (none of them carry `legacy_engine_role: HERO` today).
  - `disciplined_guard` → `true`. Per investigation.md Risk 3: `default_cognition_profile` for
    `guard`/`ranger` roles, explicit on real archetypes `frontier_guard`/`forest_ranger`. Fields:
    `planning_depth: medium, language_capacity: high, risk_modeling: medium_high` — pure
    expansion, no existing HERO-role entity uses this profile.
  - `trade_pragmatist` → `true`. Per investigation.md Risk 3: `default_cognition_profile` for
    `shopkeeper`/`merchant` roles, explicit on real archetype `traveling_merchant`. Fields:
    `planning_depth: medium_high, language_capacity: high, social_reasoning: high, risk_modeling:
    high` — the single highest-scoring profile on most axes; pure expansion.
  - `arcane_scholar` → `true`. Real spawned archetypes `apprentice_mage` and `lizardfolk_shaman`
    both use `legacy_engine_role: HERO` roles (`mage`, `shaman` — investigation.md Risk 2). Fields:
    `planning_depth: high, abstraction: very_high, tool_reasoning: high` — highest-cognition
    profile in the catalog.
  - `undead_fixated` → `false`. Fields: `planning_depth: low, memory_span: fragmented,
    language_capacity: low, tool_reasoning: low` — the only profile with `fragmented` memory;
    used only by the `sentinel` role (`legacy_engine_role: MONSTER`), never HERO-legacy.
**Do NOT touch:** `data/content/living/races.yaml` (listed in ticket's Related Code Areas but this
plan makes no change there — races reference cognition profiles by ID only, no field to add) or
any other `data/content/` file.
**Verify:** `test_schema_supports_adventure_routing_field` (test_plan.md item 6) — full pass,
asserting all 7 profiles parse with their intended non-default value (no profile silently left
at the `False` schema default by omission).

### Step 3 — Add cached catalog accessors for cognition profile and role lookups
**Files:** `src/engine/behavior_consumers.py`
**Change:** Add two new pure-reader functions following the exact existing pattern of
`get_perception_gate()`/`get_pressure_resolver()` (lines 33-46) and their shared `_auto_init()`
(lines 49-58):
```python
def get_cognition_profile_definition(profile_id: str):
    """Return the named CognitionProfileDefinition via the warmed catalog singleton."""
    global _catalog
    if _catalog is None:
        _auto_init()
    return _catalog.get_cognition_profile(profile_id)


def get_role_definition(role_id: str):
    """Return the named RoleDefinition via the warmed catalog singleton."""
    global _catalog
    if _catalog is None:
        _auto_init()
    return _catalog.get_role(role_id)
```
These reuse the **existing** `_catalog` module global (already set by `configure_behavior_consumers()`,
line 22, and by `_auto_init()`, lines 55-56) — no new singleton, no new warmup wiring, no change to
`ContentWarmupService.warmup()` (`src/content/warmup.py`) is required, since it already calls
`configure_behavior_consumers(repo)` (`warmup.py:38,42,48`) which populates `_catalog` before the
tick loop starts. `CatalogRepository.get_cognition_profile()`/`get_role()`
(`src/content/repository.py:447-448, 468`) are confirmed plain `dict.get()` lookups — O(1), no
scan.
**Other writers of `_catalog` to account for (all pre-existing, unmodified by this step):**
`configure_behavior_consumers()` (line 17-24, called from `ContentWarmupService.warmup()` at
kernel init and directly by tests); `_auto_init()` (line 49-58, lazy fallback for code paths that
never went through warmup, e.g. isolated unit tests); `reset_behavior_consumers()` (line 27-30,
test-only teardown, asserted test-only by `ContentWarmupService.reset()`'s own guard). The two new
functions in this step are **read-only** against `_catalog` — they never assign to it outside the
existing `_auto_init()` call, so they introduce no new writer and no new race: whichever of the
three existing writers ran last (warmup, auto-init, or a test's explicit
`configure_behavior_consumers()` call) is simply the value these functions read, identical to how
`get_perception_gate()`/`get_pressure_resolver()` already behave.
**Do NOT touch:** `_perception_gate`, `_pressure_resolver`, `get_entity_signals()` (lines 61-79),
or `src/content/warmup.py` itself — no change needed there per above.
**Verify:** Exercised indirectly by Step 9's caching test; no standalone new test required for
this step alone (it is pure plumbing over an already-tested catalog getter).

### Step 4 — Add the two-tier `cognition_profile_id` resolution + eligibility helper
**Files:** `src/domains/adventure/phase.py`
**Change:** Add two new private module-level functions, following the file's existing
`_threat_resolved()` helper style (lines 25-44), placed above `AdventureDecisionPhase`:
```python
def _resolve_cognition_profile_id(entity: EntityState) -> Optional[str]:
    """
    Resolve the cognition profile governing this entity's adventure eligibility.

    Tier 1: explicit identity.properties["cognition_profile_id"] (archetype-native spawn path,
    ArchetypeEntityFactory.build_entity, src/entities/archetype_factory.py:56-57) always wins.
    Tier 2: identity.properties["role_id"] -> RoleDefinition.default_cognition_profile, mirroring
    EntityArchetypeResolver._resolve_from_definition's own archetype-or-role-default pattern
    (src/content/resolver.py:460-462).
    Tier 3: entities spawned via the hero_adventurers world module (WorldEntitySpawner
    ._spawn_legacy_guard, src/worldassembly/entity_spawner.py:101-141, fed by the no-archetype_id
    else-branch of ProfileResolutionEngine.resolve(), src/worldassembly/resolver.py:1020-1032)
    have BOTH cognition_profile_id and role_id absent/None in identity.properties -- confirmed by
    direct read this session (ResolvedEntityProfile.role_id defaults to None, and the else-branch
    never sets it). identity.role (the legacy EntityRole enum) is still reliably HERO for these
    entities (RoleSemanticsService.get_legacy_entity_role), so fall back through the enum for
    this one evidenced real-corpus gap only.
    """
    props = entity.identity.properties  # always a dict, never None: src/core/state.py:490
    explicit = props.get("cognition_profile_id")
    if explicit:
        return explicit
    role_id = props.get("role_id")
    if role_id:
        role_def = get_role_definition(role_id)
        if role_def and role_def.default_cognition_profile:
            return role_def.default_cognition_profile
    if entity.identity.role == EntityRole.HERO:
        role_def = get_role_definition("hero")
        if role_def and role_def.default_cognition_profile:
            return role_def.default_cognition_profile
    return None


def _supports_adventure_routing(entity: EntityState, cache: Dict[str, bool]) -> bool:
    """Eligibility predicate: does entity's resolved cognition profile allow adventure routing?

    `cache` is a per-apply()-call dict keyed by cognition_profile_id, so the catalog accessor is
    invoked at most once per distinct profile id encountered in a tick, not once per hero
    (see Step 5's call site and Step 9's caching test).
    """
    profile_id = _resolve_cognition_profile_id(entity)
    if not profile_id:
        return False
    if profile_id not in cache:
        profile_def = get_cognition_profile_definition(profile_id)
        cache[profile_id] = bool(profile_def and profile_def.supports_adventure_routing)
    return cache[profile_id]
```
Add the import `from src.engine.behavior_consumers import get_cognition_profile_definition,
get_role_definition` near the top of the file, alongside the existing imports (lines 13-22).
**Important — do not remove the existing `from src.core.enums import EntityRole` import
(`phase.py:14`).** Investigation flagged this import as "would become unused" under a naive
role-check removal; this plan's design still uses `EntityRole.HERO` inside
`_resolve_cognition_profile_id`'s Tier-3 fallback, so the import stays live and must not be
deleted.
**Do NOT touch:** `_threat_resolved()` (lines 25-44) or anything below `AdventureDecisionPhase
.apply()`'s existing route-generation/scoring body (line 100 onward) — this step is additive only.
**Verify:** Exercised by Steps 6-9's tests (no standalone test for the helpers in isolation is
required by test_plan.md, since they are direct implementation of the AC-facing behavior tested
end-to-end there).

### Step 4a — Read Ch04 for strategic-cognition law consistency (architecture-review requirement)
**Files:** none changed — verification/judgment step only, performed before writing Step 5's code.
**Change:** Read `docs/mechanics/04_strategic_cognition.md` §§1-2 ("Goal Hierarchy &
Prioritization", "Interruption Resistance") in full before implementing Step 5. Confirm the new
cognition-profile-driven eligibility axis (Steps 1-4) does not conflict with any documented law in
that chapter — specifically: the chapter's own goal-hierarchy model does not currently mention
role-based or cognition-profile-based *eligibility for a routing subsystem* at all (it documents
interruption resistance and goal scoring, a different concern than "which entities get evaluated
by AdventureDecisionPhase in the first place"), so this plan's design is additive/orthogonal to
the chapter's existing laws, not a divergence from them. Record this confirmation (one sentence)
in the ticket's own Implementation Notes at Implement time. If Implement finds a real conflict
during this read that this Plan did not anticipate, stop and flag it rather than silently
resolving it — that would be a new Unresolved Question, not a plan deviation to implement around.
**Do NOT touch:** `04_strategic_cognition.md` itself — reading only, no edit. The sibling docs
ticket (`TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS`) owns adding a new eligibility-axis
section to this chapter's own text.
**Verify:** N/A (judgment/documentation step, not a test).

### Step 5 — Replace the eligibility filter in `AdventureDecisionPhase.apply()`
**Files:** `src/domains/adventure/phase.py`
**Change:** Replace lines 73-77:
```python
        # Avoid processing if no heroes exist
        heroes = [
            e for e in state.entities.values()
            if e.identity.role == EntityRole.HERO and e.combat.alive and e.lifecycle.active
        ]
```
with:
```python
        # Avoid processing if no eligible entities exist
        _profile_eligibility_cache: Dict[str, bool] = {}
        heroes = [
            e for e in state.entities.values()
            if _supports_adventure_routing(e, _profile_eligibility_cache)
            and e.combat.alive and e.lifecycle.active
        ]
```
Also update the docstring at lines 64-68 ("Eligible entities are: - Heroes (EntityRole = 0)...")
to read "- Cognitively adventure-capable (resolved cognition_profile.supports_adventure_routing =
True)" instead of the role-based line — this is a code comment, not one of the sibling docs
ticket's owned files, so updating it here is in scope (keeps the docstring truthful to the code
it documents, per the same file).
**Reconciling this step with AC2's literal wording:** AC2 says the eligibility filter "no longer
references `EntityRole.HERO`" — this plan satisfies that at the filter expression itself (the
`e.identity.role == EntityRole.HERO` comparison is fully removed from line 76's list
comprehension, replaced by `_supports_adventure_routing(e, ...)`). `EntityRole.HERO` remains
referenced elsewhere in the same file, inside `_resolve_cognition_profile_id`'s Tier-3 fallback
(Step 4) — that is a different code location (the resolution helper, not "the eligibility
filter"), and is required precisely to make AC2's second half true in practice ("a HERO-role
entity whose profile has `supports_adventure_routing=False` is excluded" — this only holds if
HERO-role entities' profiles resolve to something at all instead of crashing/defaulting away
silently, per investigation.md's anti-drift hazard on silent-missing handling).
**Do NOT touch:** anything from line 78 (`if not heroes:`) onward in `apply()` — route
generation, scoring, target selection, and strategic-alignment logic are unaffected by this
change; the variable name `heroes` is kept unchanged to minimize the diff surface (renaming it
to something eligibility-neutral is a legitimate style improvement but not required by any AC —
skip it to avoid unrelated churn).
**Verify:** `test_eligibility_resolves_via_cognition_profile_not_role`,
`test_hero_role_with_ineligible_profile_excluded` (test_plan.md new tests 1-2).

### Step 6 — Zero-regression test: archetype-native hero scenario
**Files:** `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`
**Change:** Add `test_zero_regression_human_practical_humanoid_hero` (test_plan.md new test 3,
archetype-native half). Construct a hero entity via the archetype-native shape — `identity.role =
EntityRole.HERO`, `identity.properties = {"archetype_id": "adventurer_hero", "role_id": "hero",
"cognition_profile_id": "practical_humanoid", ...}` (matching `ArchetypeEntityFactory
.build_entity`'s real output shape, `src/entities/archetype_factory.py:48-57`) — run
`AdventureDecisionPhase.apply()` at a fixed seed/tick count pre- and post-fix conceptually (i.e.
assert the post-fix `StateUpdate`/outcome matches what the pre-fix role-only check would have
produced for this exact entity, since `practical_humanoid.supports_adventure_routing=True` per
Step 2 and `identity.role == HERO` also true — both old and new checks agree this entity is
eligible).
**Do NOT touch:** other tests in the same file unrelated to eligibility (route-generation/scoring
assertions further down the file, e.g. anything exercising `test_filters_out_locked_projects` and
siblings should only need `properties=` additions if they currently omit them — see Step 11, not
this step).
**Verify:** the new test itself, run via `pytest tests/integration/domains/adventure/ -q`.

### Step 7 — Zero-regression test: `hero_adventurers`-module-shaped legacy-guard scenario
**Files:** `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py` (or the
new `tests/unit/domains/adventure/test_eligibility_cognition_profile.py` file introduced in Step 8
— implementer's choice, test_plan.md allows either location for the missing-profile guard test)
**Change:** Add the second half of `test_zero_regression_human_practical_humanoid_hero` /
`test_cognition_profile_id_missing_does_not_crash` (test_plan.md new tests 3 and 4 — these two
ACs converge on the same scenario and may be implemented as one test or two, implementer's
judgment): construct a hero entity via the **legacy-guard shape** — `identity.role =
EntityRole.HERO`, `identity.properties = {"archetype_id": None, "race_id": None, "role_id": None,
"faction_id": None}` (matching `WorldEntitySpawner._spawn_legacy_guard`'s real output shape,
`src/worldassembly/entity_spawner.py:118-127`, i.e. **no** `cognition_profile_id` key and
`role_id` explicitly `None`, not absent) — run `AdventureDecisionPhase.apply()` and assert the
entity IS included in the eligible set (Tier-3 fallback resolves it to `"practical_humanoid"` via
the `"hero"` role default, matching old-code behavior for this exact real-corpus shape) and that
no exception is raised. This is the single highest-value new test given the real-corpus gap found
in Investigate (investigation.md Risk 1) — it is the only test in this plan that would fail loudly
if the Tier-3 fallback in Step 4 were omitted or implemented incorrectly.
**Do NOT touch:** `src/worldassembly/entity_spawner.py` or `src/worldassembly/resolver.py`
themselves — this step only constructs a test fixture that *mirrors* their real output shape; it
does not modify those files (they are not in this ticket's Related Code Areas or Scope).
**Verify:** the new test itself.

### Step 8 — Negative-case test
**Files:** `tests/unit/domains/adventure/test_eligibility_cognition_profile.py` (new file, per
test_plan.md new tests 1, 2, 4)
**Change:** Add `test_hero_role_with_ineligible_profile_excluded` (test_plan.md new test 2):
construct an entity with `identity.role = EntityRole.HERO` and `identity.properties =
{"cognition_profile_id": "instinctive_animal"}` (explicit Tier-1 override — this is the
"role artificially set to HERO" case named in the ticket's own AC, and must use an *explicit*
`cognition_profile_id` rather than relying on any fallback tier, since Tier-3's fallback for
`role_id`-absent HERO entities always resolves to `"practical_humanoid"`/`True`, which would make
this test pass for the wrong reason if it omitted the explicit override). Assert the entity is
EXCLUDED from `AdventureDecisionPhase.apply()`'s eligible set. Also add
`test_eligibility_resolves_via_cognition_profile_not_role` (test_plan.md new test 1) in the same
file: a non-HERO-role entity (`role=EntityRole.CITIZEN`) with `identity.properties =
{"cognition_profile_id": "practical_humanoid"}` IS included.
**Do NOT touch:** `tests/unit/domains/adventure/test_hero_quest_scoring.py` — it constructs
HERO-role entities for `scoring.py`'s own (out-of-scope) HERO checks; this ticket's eligibility
change must not alter that test's inputs or assertions.
**Verify:** both new tests, run via `pytest tests/unit/domains/adventure/ -q`.

### Step 9 — Caching/performance verification test
**Files:** `tests/unit/domains/adventure/test_eligibility_cognition_profile.py` (same new file
as Step 8)
**Change:** Add `test_cognition_profile_id_resolution_is_cached_not_reloaded_per_hero`
(test_plan.md new test 5): construct N (e.g. 5) hero entities all sharing the same explicit
`cognition_profile_id="practical_humanoid"`, monkeypatch/spy
`src.domains.adventure.phase.get_cognition_profile_definition` (the Step 3 accessor, imported
into `phase.py` in Step 4), call `AdventureDecisionPhase.apply()` once, and assert the spy was
called at most once (O(unique profile ids) = 1, not O(N) = 5) — directly closing the ticket's own
AC bullet ("`cognition_profile_id` resolution is confirmed cheap/cached per-tick"). This proves
the `_profile_eligibility_cache` dict introduced in Step 5 is actually doing its job, not just
present in the code.
**Do NOT touch:** `src/content/repository.py`'s `get_cognition_profile()`/`get_role()`
themselves — they are already confirmed O(1) dict lookups (`repository.py:447-448, 468`); this
test targets the call-count at the `phase.py` call site, not the underlying dict performance.
**Verify:** the new test itself.

### Step 10 — Verify existing test fixtures remain unmodified and passing
**Files:** none changed by this step — verification only, run against the full adventure/
strategic/content/observability test surface named in test_plan.md's "Regression Surface" and
"Scoped Pytest Commands" sections.
**Change:** Run the full scoped pytest commands from test_plan.md:
```
pytest tests/unit/domains/adventure/ tests/integration/domains/adventure/ -q
pytest tests/unit/systems/test_spawn_lock_condition.py -q
pytest tests/unit/strategic/ -q
pytest tests/unit/content/ -q
pytest tests/unit/observability/test_decision_trace.py -q
pytest tests/integration/scenarios/test_balance_regression.py -q
```
Confirm the bare-`V2EntityBuilder`-with-no-`properties` fixtures identified in investigation.md
("Test fixtures" section, lines 77-81) and test_plan.md ("Integration — adventure domain" section)
continue to pass **without modification**. This is expected to hold because such fixtures default
`identity.role` to `0` — confirmed directly at the dataclass level, not inferred from
`archetype_factory.py`: `IdentityComponent.role: int = 0  # EntityRole.HERO`
(`src/core/state.py:473`), which is what `V2EntityBuilder(...).identity(...)` with no `role=`
argument ultimately constructs (`role: int | EntityRole | None = None` at
`src/core/builder.py:166`, passed through to `IdentityComponent`'s own default when unset) — and
have empty `identity.properties`,
which Tier-3 of Step 4's fallback resolves to `"hero"`'s `default_cognition_profile` =
`"practical_humanoid"` = `supports_adventure_routing=True`. If any fixture fails, per
test_plan.md's Anti-Drift Test Guard, any pre-existing assertion of the form "only HERO-role
entities are ever routed" must be updated deliberately with a comment referencing this ticket, not
silently worked around — but no such fixture edit is expected to be *required* by this plan's
design, only possibly by an assertion that was itself asserting the old, now-intentionally-changed
behavior.
**Do NOT touch:** `tests/unit/systems/test_spawn_lock_condition.py::_make_hostile` (already sets
`role=EntityRole.MONSTER` explicitly, unaffected) or `test_adventure_routing_defaults_off` (flag
default sentinel, untouched by this ticket).
**Verify:** all commands above exit 0; zero unexpected fixture edits.

### Step 11 — Update the content usage matrix doc
**Files:** `docs/mechanics/content_usage_matrix.md`
**Change:** Update the `living/cognition_profiles` row (line 36, confirmed by direct read this
session) — the "Compile/Runtime Consumer" cell currently reads `CompileContext, WorldCompiler`;
append `AdventureDecisionPhase` (e.g. `CompileContext, WorldCompiler, AdventureDecisionPhase`).
The "Runtime Consumer Evidence" cell currently reads `None yet`; change it to something like
`AdventureDecisionPhase.apply() reads supports_adventure_routing for eligibility (TCK-20260810-
COGNITION-PROFILE-ADVENTURE-ELIGIBILITY)`. This is the one genuinely new, ticket-specific doc gap
identified in investigation.md's "Docs Requiring Update" section — distinct from
`docs/mechanics/04_strategic_cognition.md`, `docs/simulation/domains/adventure_contract.md`, and
`docs/parity_ledger/strategic_cognition.yaml`, all of which are explicitly owned by the sibling
docs ticket (see Scope Guards below). Note the doc's own header states it is "generated
dynamically" (line 16), but no generator script was found in `tools/` or `Makefile` referencing
`content_usage_matrix` during this planning pass — treat as hand-maintained for this edit; if
implementation discovers an actual generator, regenerate via that instead of hand-editing.
**Other writers of this doc to account for:** no other in-flight ticket touches
`content_usage_matrix.md` (confirmed: the sibling docs ticket's Out-of-Scope/owned-files list does
not include it; investigation.md's Parity Ledger Overlap section only names
`strategic_cognition.yaml`, a different file). No collision expected.
**Do NOT touch:** any other row in the same table (the table has ~15+ rows for unrelated content
families — only the `living/cognition_profiles` row changes).
**Verify:** `tests/unit/content/test_content_usage_matrix.py` — per test_plan.md, "if this test
parses/validates the matrix doc's row structure, confirm it doesn't hard-fail on the
`living/cognition_profiles` row text changing." Run this test after the edit.

### Step 12 — Minimal same-session `STRAT-243` correction (architecture-review requirement)
**Files:** `docs/parity_ledger/strategic_cognition.yaml`
**Change:** Architecture review (NEEDS_CHANGES, 1st and 2nd pass) correctly found that leaving
`STRAT-243` factually stale — even temporarily, pending a separate sibling ticket — violates
CLAUDE.md's Authoritative Mechanics Rule ("If logic changes, update the corresponding doc AND the
parity ledger entry in the same session"). The 2nd-pass review caught that the first draft of this
step only fixed the entry's FIRST sentence — its SECOND sentence ("Non-hero entities (monsters,
shopkeepers, citizens, workers, guards) are never routed through hero decision-making, even if
alive and active.") also becomes false once Step 2's `disciplined_guard=True`/
`trade_pragmatist=True` authoring lands, since `guard`/`ranger` roles (default profile
`disciplined_guard`) and `shopkeeper`/`merchant` roles (default profile `trade_pragmatist`) become
newly eligible — directly contradicting the two example categories that sentence names by name.
This step now replaces the ENTIRE `text` field (both sentences), not a substring, precisely to
avoid this exact class of partial-fix miss recurring a third time:
- `text` (full replacement): `"AdventureDecisionPhase.apply() eligibility filter enforces:
  cognition_profile.supports_adventure_routing = True (resolved via a 3-tier fallback: explicit
  cognition_profile_id, role_id -> RoleDefinition.default_cognition_profile, or legacy
  EntityRole.HERO -> the 'hero' role's own default), combat.alive = True, lifecycle.active = True,
  and project-lock gating. Entities whose resolved cognition profile has
  supports_adventure_routing = False (e.g. instinctive_animal, undead_fixated — monsters, wildlife)
  are never routed through hero decision-making, even if alive and active; entities with
  supports_adventure_routing = True are eligible regardless of role, including non-hero-role
  guard/shopkeeper archetypes whose default cognition profile qualifies
  (TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY)."` — this replaces BOTH original
  sentences: the first (role criterion) and the second (non-hero-entities-never-routed claim,
  now correctly scoped to profile-ineligible entities specifically, not role generally, and no
  longer naming "shopkeepers"/"guards" as a blanket-excluded category since that is no longer true.
- The other two still-unchanged documented criteria (`combat.alive = True`, `lifecycle.active =
  True`, project-lock gating) are unchanged by this ticket and keep their existing text verbatim.
- `v2_evidence`: replace the `phase.py:73-76` role-comparison citation with a citation of the new
  `_supports_adventure_routing`/`_resolve_cognition_profile_id` helpers and the new
  `phase.py:73-77`-equivalent filter line (exact line numbers confirmed at Implement time, since
  Steps 1-5 shift line numbers from what Investigate originally cited).
- `test_path`: add the new Step 8 tests (`test_eligibility_resolves_via_cognition_profile_not_role`,
  `test_hero_role_with_ineligible_profile_excluded`) alongside the existing
  `test_spawn_lock_condition.py::TestLockHeldWhenThreatActive` reference (that existing test
  covers the still-unchanged lock-gating criterion — do not remove it).
- `status`: stays `verified` (the criterion is still true, just implemented differently) —
  this is a factual-content correction, not a status change to `divergent`.
**This step deliberately does NOT**: add new `STRAT-25X` entries for the generalized-eligibility
concept as a whole, rewrite `docs/mechanics/04_strategic_cognition.md`'s own narrative text, or
touch `docs/simulation/domains/adventure_contract.md`'s eligibility table — all of that remains
the sibling docs ticket's own, larger-scoped job (a full narrative pass across 3 files, informed
by both this ticket's AND C2's landed code). This step's own scope is strictly "keep STRAT-243
factually true," nothing broader.
**Do NOT touch:** any other `STRAT-*` entry in the same file.
**Verify:** `tests/tools/test_parity_ledger_scan.py`, `tests/tools/test_parity_index.py` continue
to pass after the edit (schema/index integrity, not content correctness — content correctness is
verified by direct review against the Step 5 diff).

## Scope Guards

- **`src/domains/adventure/scoring.py` lines 161, 252** — the two other `EntityRole.HERO` checks
  (QUEST_OPPORTUNITY capability-match scaling, group class-synergy 1.10x multiplier) are
  out of scope. No step in this plan touches `scoring.py`.
- **`src/systems/strategic_systems/intelligence.py::evaluate_project_switch`** — C2's
  interruption-bypass generalization. No step in this plan touches `intelligence.py`.
- **`docs/mechanics/04_strategic_cognition.md`, `docs/simulation/domains/adventure_contract.md`**
  — owned by the sibling docs ticket `TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS` (the full
  narrative rewrite, informed by both this ticket's and C2's landed code). No step in this plan
  edits either file.
- **`docs/parity_ledger/strategic_cognition.yaml`** — Step 12 makes a minimal, same-session
  factual correction to `STRAT-243` only (per architecture-review requirement — see Step 12).
  Any broader parity-ledger pass (new entries for the eligibility concept as a whole, entries
  covering C2's own bypass-generalization logic) remains the sibling docs ticket's job.
- **`docs/audits/D22_dormant_content_wiring.md`** — owned by `TCK-20260810-D22-DORMANT-WIRING-
  AUDIT`. No step touches it.
- **`src/worldassembly/entity_spawner.py`, `src/worldassembly/resolver.py`** — not in this
  ticket's Related Code Areas or Scope. This plan's Step 4/7 fallback design deliberately resolves
  the `cognition_profile_id`-and-`role_id`-absent gap on the **read side** (inside
  `AdventureDecisionPhase.apply()`'s resolution helper) rather than the **write side** (spawn-time
  threading of `role_id`/`cognition_profile_id` through `_spawn_legacy_guard`/
  `ProfileResolutionEngine`), specifically to avoid touching this sensitive subsystem — investigation.md's
  Prior Work section notes a recent unrelated FACTION/INFORMATION RNG-coupling regression in this
  exact area (`TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING`).
- **`data/content/living/races.yaml`** — listed in the ticket's Related Code Areas but no step in
  this plan modifies it (races reference cognition profiles by ID only; no new field belongs
  there).
- **`src/strategy/cognition_capacity.py`** — listed in Related Code Areas as background context
  (investigation confirmed `CapacityService.derive_profile()` never reads
  `cognition_profile_id`/`CognitionProfileDefinition` at all, and this ticket does not change
  that). No step touches this file.
- **`ContentWarmupService.warmup()` (`src/content/warmup.py`)** — no step modifies this file; Step
  3's new accessors reuse the `_catalog` global that `warmup()` already populates via its existing
  `configure_behavior_consumers(repo)` call.

## Dependency Map

- Step 1 (schema field) is a prerequisite for Step 2 (authoring values) — the field must exist
  before it can be set in YAML.
- Steps 1+2 together are a prerequisite for Step 5 (the eligibility check reads
  `supports_adventure_routing`, which does not exist until Step 1, and defaults `False` for every
  profile until Step 2 authors real values).
- Step 3 (catalog accessors) is a prerequisite for Step 4 (the resolution helper calls
  `get_role_definition`/`get_cognition_profile_definition`).
- Step 4 (resolution + eligibility helper) is a prerequisite for Step 5 (the filter calls
  `_supports_adventure_routing`).
- Steps 1-5 are all prerequisites for Steps 6-9 (tests exercise the finished code path) and Step
  10 (regression verification runs against the finished code path).
- Step 4a (Ch04 read) is a prerequisite for Step 5 — must be done before writing the eligibility
  filter code, not after.
- Step 11 (content_usage_matrix.md update) is independent of all other steps — it can be done at
  any point, though doing it last (after the runtime consumer actually exists) keeps the doc
  accurate to landed code rather than planned code.
- Step 12 (STRAT-243 correction) is a prerequisite for Finalize — it depends on Step 5's own final
  line numbers/helper names being settled, so it must be done after Step 5 lands, but before this
  ticket's own Verify/Finalize phases (same-session requirement).
- Steps 6, 7, 8, 9 are independent of each other (different test scenarios, no shared fixture
  dependency) and can be implemented in any order once Steps 1-5 are complete.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `CognitionProfileDefinition` gains `supports_adventure_routing: bool = False`; all 7 profiles get explicit authored values | Step 1, Step 2 | `test_schema_supports_adventure_routing_field` (Step 1/2) |
| `AdventureDecisionPhase.apply()`'s eligibility filter no longer references `EntityRole.HERO`; non-hero+True included, HERO+False excluded | Step 3, Step 4, Step 5 | `test_eligibility_resolves_via_cognition_profile_not_role`, `test_hero_role_with_ineligible_profile_excluded` (Step 8) |
| Zero-regression: human/practical_humanoid hero scenario identical outcome pre/post fix | Step 4 (Tier-1/Tier-3 fallback design), Step 5 | `test_zero_regression_human_practical_humanoid_hero` (Step 6, Step 7 — both archetype-native and legacy-guard shapes) |
| Negative case: instinctive_animal-profile entity with role artificially HERO is NOT included | Step 4, Step 5 | `test_hero_role_with_ineligible_profile_excluded` (Step 8) |
| `cognition_profile_id` resolution confirmed cheap/cached per-tick | Step 3, Step 4, Step 5 (per-`apply()`-call cache dict) | `test_cognition_profile_id_resolution_is_cached_not_reloaded_per_hero` (Step 9) |

## Anti-Drift Notes

- **Do not implement Tier-3's fallback as a literal hardcoded `"practical_humanoid"` string.**
  Resolve it via `get_role_definition("hero").default_cognition_profile` (a catalog lookup), not a
  string literal — this keeps the fallback correct if `roles.yaml`'s `hero` role default ever
  changes, and mirrors `EntityArchetypeResolver`'s own pattern of reading
  `RoleDefinition.default_cognition_profile` rather than inlining profile IDs
  (`src/content/resolver.py:460-462`).
- **Do not collapse the "missing key" and "resolves to `False`" cases.** A `KeyError`,
  uncaught `AttributeError`, or a bare `.get("cognition_profile_id", "practical_humanoid")` default
  are all explicitly the wrong shape per investigation.md's anti-drift hazards — the resolution
  must go through the three explicit tiers in Step 4, in order, with the Tier-3 gate being
  `identity.role == EntityRole.HERO` specifically (not "any role"), since that is the only
  evidenced real-corpus gap.
- **`EntityRole.HERO` legitimately remains referenced in `phase.py` after this change** — inside
  `_resolve_cognition_profile_id`'s Tier-3 fallback, not in the eligibility filter itself. Do not
  "clean up" this reference or the `from src.core.enums import EntityRole` import thinking it is
  dead code; investigation.md's note that the import "would become unused" was written before this
  plan's Tier-3 fallback design was decided, and no longer applies.
- **`opportunistic_humanoid`/`undead_fixated` values were not explicitly flagged as judgment calls
  in investigation.md** (only `disciplined_guard`/`trade_pragmatist` were named there) — this
  plan's Step 2 makes an evidence-based call for all 7 profiles using the qualitative fields
  directly, consistent with the ticket's own "instinctive/simple races... never are" framing. If
  Review disagrees with the `opportunistic_humanoid=True` or `undead_fixated=False` calls
  specifically, that is a content-authoring disagreement to raise then, not a sign the plan skipped
  evidence-gathering — the qualitative-field citations are in Step 2 for exactly this reason.
- **The bare-`V2EntityBuilder` test-fixture default role is confirmed `EntityRole.HERO`/`0`**
  directly at `IdentityComponent.role: int = 0  # EntityRole.HERO` (`src/core/state.py:473`) —
  not merely inferred from `archetype_factory.py:74` (a different, archetype-native code path)
  as investigation.md's citation might suggest. Step 10's "fixtures pass unmodified" expectation
  rests on this confirmed default plus Tier-3's fallback (Step 4); still run the tests to confirm,
  since a dataclass default is necessary but not sufficient evidence that every fixture's call
  path reaches it unmodified.
- **Do not add a new file under `src/worldassembly/`** for this fix — see Scope Guards. The
  fallback is entirely a read-side concern inside `src/domains/adventure/phase.py`.
- **`STRAT-243` in `docs/parity_ledger/strategic_cognition.yaml` is expected to go stale as a
  direct, known side effect of Step 5** — this is not a bug to fix in this ticket; it is the
  sibling docs ticket's job.

The one item that could have been left open — the `cognition_profile_id`-missing fallback
policy — has a concrete, evidence-based resolution built into Steps 3-5 per the investigation's own
findings, and the `supports_adventure_routing` authoring judgment calls (Step 2) are resolved here
with explicit qualitative-field citations rather than deferred.

## Deviations (recorded at Implement time)

1. **Step 11 — `content_usage_matrix.md` is generator-backed, not hand-maintained.** Step 11
   assumed (per an Investigate-time check of `tools/` and `Makefile`) that no generator writes
   this file, with an explicit fallback clause: "if implementation discovers an actual generator,
   regenerate via that instead of hand-editing." Implement discovered
   `tests/unit/content/test_content_usage_matrix.py::test_generate_and_save_report` regenerates
   the entire file from `src/content/matrix.py`'s `CONTENT_USAGE_MATRIX` dict every time
   `tests/unit/content/` is run — which Step 10's own required regression command does. Per the
   plan's own sanctioned fallback, Implement edited the `living/cognition_profiles` entry in
   `src/content/matrix.py` (adding `AdventureDecisionPhase` to `compile_runtime_consumer` and
   replacing `runtime_consumer_evidence`'s `"None yet"` with the real evidence sentence) instead
   of hand-editing the markdown, then regenerated `docs/mechanics/content_usage_matrix.md` via
   `generate_matrix_report()` and reattached the file's pre-existing frontmatter block (bumping
   `last_verified` to today) — the generator itself does not emit frontmatter, a pre-existing,
   out-of-scope quirk unrelated to this ticket (confirmed by diffing against the committed
   version before any change). `src/content/matrix.py` is therefore an additional changed file
   beyond the plan's original Step 11 file list (`docs/mechanics/content_usage_matrix.md` only).
2. **Step 11 fallout — `tests/unit/content/test_content_usage_matrix.py` required an update.**
   `test_living_family_marked_resolved_partially_until_runtime_consumer` asserted
   `living/cognition_profiles.runtime_consumer_evidence == "None yet"` as part of a group of
   living-family "no runtime consumer yet" guards. This assertion became false as the direct,
   intended consequence of Step 11's edit — exactly the class of pre-existing assertion
   test_plan.md's Anti-Drift Test Guards pre-authorized updating "deliberately (with a comment
   referencing this ticket)," not silently working around. `living/cognition_profiles` was split
   out of that group's loop into its own assertion confirming `implementation_state` is still
   `RESOLVED_PARTIALLY` (unchanged) but `runtime_consumer_evidence` now names
   `AdventureDecisionPhase`.
3. **`tests/unit/observability/test_decision_trace.py::test_adventure_decision_phase_wires_writer`
   required a fixture fix, as test_plan.md's own Regression Surface section flagged as
   needing verification, not assumed.** The mocked hero's `identity.properties` was a bare
   `MagicMock()`; `.get("cognition_profile_id")` on it returns a truthy `Mock`, which then fails
   the real catalog lookup in `get_cognition_profile_definition` and silently excludes the mocked
   hero (0 eligible entities), breaking the test's own premise. Fixed by setting
   `hero.identity.properties = {"cognition_profile_id": "practical_humanoid"}` explicitly, with a
   comment referencing this ticket.
4. **Steps 6 and 7's zero-regression tests were both placed in the integration test file**
   (`tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`) rather than
   splitting Step 7 into the new unit test file — the plan explicitly left this an implementer's
   choice ("Location: ... or the new `tests/unit/domains/adventure/test_eligibility_cognition_profile.py`
   file introduced in Step 8 — implementer's choice").
5. **A real `PARITY_INCOMPLETE` gate hit at the Parity phase, not anticipated by the plan at
   all.** `src/content/matrix.py` (edited per deviation 1 above) maps to
   `docs/parity_ledger/substrate.yaml`/`infrastructure.yaml` via `cross_reference_touched()`'s own
   deterministic mapping — derived from 2 prior, unrelated tickets' existing `v2_evidence`
   citations of `src/content/matrix.py` (`SUB-373`: the `_auto_discover_extra_entries` mechanism
   for unregistered content families; `INFRA-328`: registering a brand-new non-catalog file).
   Neither prior claim's own subject matter overlaps with this ticket's real change (a manual
   text-field edit on an already-hand-registered row — not auto-discovery, not new-file
   registration), so the parity-updater agent correctly judged neither warranted a new/updated
   entry — but the deterministic gate still hard-failed since no ledger file was touched to prove
   that judgment. Resolved with real substance, not a stretch-fit or a gate-dodge: extended
   `SUB-373`'s own `support_boundary` field (a schema field designed exactly for scoping an
   existing claim, not asserting a new one) to state explicitly that its auto-discovery claim
   does not cover hand-registered-row maintenance, citing this ticket's own diff as the concrete
   example. `cross_reference_touched()` re-run confirms all 4 files now PASS (ANY-of-candidates
   semantics — only one of `matrix.py`'s two candidate files needed touching).

None of the above are architectural deviations: (1) and (2) are the plan's own pre-authorized
"discover a real generator, use it instead" contingency firing as designed; (3) is a predicted,
pre-authorized fixture fix; (4) is an explicitly open implementer choice in the plan text; (5) is
a real, unplanned gate hit, resolved with a genuinely evidenced ledger clarification rather than
routing around the check.

---
ticket_id: TCK-20260701-SANDBOX-MONSTER-BALANCE
phase: investigation
date: 2026-07-01
---

# Investigation: sandbox_world monster stat differentiation

## Current Behavior (file:line refs)

**Root cause confirmed: `role: monster` in `data/worlds/sandbox_world/world.yaml` is not a
catalog-registered role ID.** It silently falls through to global engine defaults instead of
any monster-appropriate stat profile.

Trace, in resolution order:

1. `data/worlds/sandbox_world/world.yaml:39-44` — monster population declared as
   `role: monster, count: 5, faction: monsters, spawn_distribution: {type: region_random,
   region: woods}`. `schema_version: worldtemplate.v1`.

2. `src/worldbuilding/recipe.py` — `WorldTemplateExpander.expand()` (L110-260) converts the
   template into a `WorldSpec`. Each population recipe (`PopulationRecipeSpec`, L31-47) is
   expanded into a plain dict with only `id, count, role, faction, spawn_region`
   (L191-197) — **`stats_profile`, `inventory_profile`, `cognition_profile` fields that exist
   on `PopulationRecipeSpec` (L45-47) are silently dropped and never copied into the expanded
   `WorldSpec.entities` dict.** This means, for a `worldtemplate.v1` world, there is no way to
   set an explicit per-population stat profile in `world.yaml` even though the recipe schema
   appears to support it — `role` is the *only* field that reaches stat resolution.

3. `src/worldassembly/schema.py` / `src/worldbuilding/schema.py:52-63` — the expanded dict
   validates against `PopulationSpec`, which has no `stats_profile` field at all (only
   `id, count, role, faction, spawn_region, archetype_id`). `archetype_id` stays `None` for
   template-expanded worlds (never set by the expander).

4. `src/worldassembly/resolver.py` — `CompileProfileResolver.resolve()` (L917) iterates
   `spec.entities`. For each `pop_spec`, `archetype_id` is `None` (step 3), so the
   `resolved_arch` branch (L969-1004, uses `EntityArchetypeResolver`) is never entered for
   sandbox_world entities. Stats instead come from `_resolve_entity_stats()` (L1045-1079):
   - Step 1: explicit `stats_profile_id` param — `None` (no `population_recipes` dict is
     passed for template-based worlds; not relevant here in any case since step 2 drops it).
   - Step 2: `getattr(pop_spec, "stats_profile", None)` — always `None`, `PopulationSpec` has
     no such field (confirmed step 3).
   - Step 3: `self.role_semantics.get_default_stats_profile(pop_spec.role)` →
     `src/content_semantics/role.py:48-50` → `self.repo.get_role("monster")`.
   - **`data/content/social/roles.yaml` has no entry with `id: "monster"`.** Registered roles
     with `legacy_engine_role: MONSTER` are: `predator_hunter`, `alpha`, `raider`, `leader`,
     `sentinel`, `brute`, `dragon_champion`, `scout` (scout maps to GUARD legacy role). None of
     these are named `"monster"` — `"monster"` is a bare fallback string used only by
     `RoleSemanticsService.get_legacy_entity_role()`'s string-heuristic (see below), not a
     first-class catalog role ID.
   - `repo.get_role("monster")` → `None` → `get_default_stats_profile` returns `None`.
   - Falls through to **Global Defaults Fallback** (`_resolve_entity_stats` L1071-1078) →
     `DefaultSemanticsService.get_entity_combat_defaults()`
     (`src/content_semantics/defaults.py:17-36`) → hardcoded `hp=100, atk=10, def=0` (used
     because `repo.defaults` has no matching definition, or the catalog default definition
     also yields these exact numbers — either path lands on hp=100/atk=10/def=0, identical to
     `citizen`/`commoner_base`).

5. Legacy role/faction bucketing is unaffected by this bug: `get_legacy_entity_role("monster")`
   (`src/content_semantics/role.py:18-41`) does NOT depend on catalog registration — it has a
   string-heuristic fallback (`"MONSTER" in role_id.upper()` → `EntityRole.MONSTER`,
   L28-29) that fires for the literal string `"monster"`. So sandbox_world's monsters are
   correctly bucketed as `EntityRole.MONSTER` for engine/legacy purposes — **only their
   stat_profile resolution is broken**, not their role classification. This is confirmed by an
   existing passing test: `tests/unit/content_semantics/test_semantics.py:43`
   (`test_role_semantics`) — `service.get_legacy_entity_role("monster") ==
   EntityRole.MONSTER`, testing exactly this fallback path (not a registered-role lookup).
   **This test is unaffected by the planned fix and must keep passing.**

6. Result: sandbox_world's 5 monsters (entities 16-20, spawned in `woods`) resolve to
   identical stats as its 15 citizens and 3 heroes (hp=100/atk=10/def=0) with zero combat
   edge. D20 audit confirms the consequence: **all 5 monsters (entities 16-20) killed at
   tick 8** in a fresh 200-tick seed 42 run (`docs/audits/D20_simq_integration.md`, "Notable
   worst events — Seed 42" table, L104-108) — one `early_extinction` −10 COMBAT penalty
   (`src/simulation_quality/scorers/combat.py` L82-90, fires once, entity 16) plus 4×
   `attrition` −1 events (entities 17-20, same tick).

## Mechanics/Engine Constraints

- `src/simulation_quality/scorers/combat.py::CombatScorer` (`early_extinction`, L82-90) and
  `config/simulation_quality/detection_params.yaml:16`
  (`early_extinction_before_tick: 10`) are confirmed correct and **out of scope** — the
  ticket's own root-cause finding (ticket L36-39) is verified true by this investigation. No
  scorer change needed.
- `docs/mechanics/02_combat_laws.md` — combat resolution formula itself (damage,
  hit/miss, durability decay) is unaffected; this bug is purely in the content-layer stat
  *assignment*, not the combat *resolution* pipeline. Confirmed correct per D04 §2 (below).
- No `WorldValidator` rule validates `role` strings against the catalog
  (`src/worldbuilding/validator.py` has no `role`-related checks) — an unregistered role like
  `"monster"` compiles silently with no warning. This is why the bug was never caught by
  `make world-validate`.

## Parity Ledger Overlap (IDs + status)

- Searched `docs/parity_ledger/*.yaml` for `sandbox_world`, `monster`, `default_stats_profile`,
  role-default entries. No entry references sandbox_world entity counts, monster stat
  resolution, or the role-default-stats-profile mechanism. The only `monster`-adjacent hits
  are in `strategic_cognition.yaml` (`test_influence_shifts_on_monster_death`, unrelated —
  influence-on-death mechanic, not stat assignment).
- **No parity ledger entry exists for this behavior; none needs updating.** This is a
  content-authoring bug, not an engine-logic parity divergence — confirmed by D04 §2's framing
  ("world content parameters are the primary balance lever, not per-combat constants... the
  authoring layer is uncalibrated").

## Prior Work

- `stored_artifacts/TCK-20260627-P1I-WORLD-BALANCE-FIX/` — same category of fix
  (world-balance / entity-count tuning), different worlds (dungeon_crawl,
  wilderness_survival). Established pattern: **content-only YAML changes**, no engine/src
  logic touched, verified via `make world-validate WORLD=<x>` +
  `tests/integration/worldassembly/test_real_content_world_compositions.py`. That ticket
  operated on `worldcomposition.v1` worlds (module_refs); this ticket's target,
  `sandbox_world`, is a `worldtemplate.v1` world (different schema/expansion path — see
  Current Behavior step 2), so the equivalent regression tests differ (see test_plan.md).
- Existing catalog precedent for monster/hostile stat differentiation: `data/content/entities/
  entity_archetypes.yaml` defines full archetypes (`hungry_wolf`, `alpha_wolf`, `goblin_scout`,
  `goblin_raider`, `goblin_warlord`, `cave_spider`, `orc_brute`, `undead_sentinel`, `swamp_troll`,
  `dragon_cult_champion`, etc.) each pairing race/faction with a *registered* role
  (`predator_hunter`, `alpha`, `scout`, `raider`, `leader`, `sentinel`, `brute`) and an explicit
  `stat_profile` from `data/content/entities/stat_profiles.yaml`. These are consumed via
  `data/content/entities/populations.yaml` population recipes (e.g. `wolf_pack_small`:
  `hungry_wolf x4, alpha_wolf x1`; `goblin_raiding_party`: `goblin_scout x2, goblin_raider x4,
  goblin_archer x2, goblin_warlord x1`) referenced by `worldcomposition.v1` module files (e.g.
  `data/content/world_modules/goblin_camp_conflict.yaml`, used by `dungeon_crawl`). **This
  confirms a reusable monster-archetype pattern already exists in the catalog** — the ticket's
  Scope item 2(a) preference ("reuse rather than invent") is satisfiable without adding new
  catalog content.
  - However, sandbox_world's simpler `worldtemplate.v1` schema does not consume population
    recipes/archetypes the way `worldcomposition.v1` module worlds do (see Current Behavior
    step 2 — `stats_profile` is dropped by the expander). The only lever reachable from
    sandbox_world's `world.yaml` is the population's `role` field, matched against
    `data/content/social/roles.yaml`'s `default_stats_profile`. Reuse in this ticket therefore
    means: **point `role:` at an existing registered monster role** (e.g. `predator_hunter`,
    which is the role used by the `hungry_wolf` archetype — the catalog's baseline "generic
    wilderness monster" — with `stat_profile: wolf_predator_base`, hp=45/atk=12/def=3), not
    referencing an `entity_archetypes.yaml` entry directly (that plumbing doesn't exist for
    `worldtemplate.v1`).
  - `data/content/entities/stat_profiles.yaml` also defines a `monster_base` profile
    (id `monster_base`, L24-30) but it is numerically **identical to the current buggy
    defaults** (hp=100/atk=10/def=0) — it is not attached to any registered role's
    `default_stats_profile` and would not fix the differentiation problem even if reachable.
- `tests/integration/scenarios/test_entity_differentiation.py` (`_build_differentiation_spec`,
  L37-93) builds its own synthetic `worldspec.v1` world with `role: "monster"` for its 4-monster
  population — **this is a separate, self-contained world spec, not sandbox_world, and is
  unaffected by any change to `data/worlds/sandbox_world/world.yaml`.** Confirms this ticket's
  fix is correctly scoped to sandbox_world only (per ticket Out of Scope).
- `tests/unit/worldbuilding/test_world_recipes.py` (L34, L84) also uses a generic
  `role: "monster"` string as a template-expansion test fixture, testing the expansion
  mechanism itself (id/count/role/faction passthrough), not sandbox_world or catalog role
  registration. Unaffected by this fix.

## Risks and Open Questions

- **Calibration regression surface (real, must be handled, not blocking):**
  `tests/simulation_quality/test_grade_regression.py` reads committed calibration reports from
  `data/calibration/sandbox_world_seed{42,137,999}_200t/quality_report.json` and
  `data/calibration/sandbox_world_seed42_1000t/quality_report.json`, compared against anchors
  in `tests/simulation_quality/fixtures/grade_anchors.json` (±1 letter-grade band). Current
  anchors: `COMBAT: B` for all four sandbox_world keys (raw combat score 6.0/0.030 normalized
  per D20 audit, driven partly by the `early_extinction` −10 hit). Removing the total-wipe event
  will very likely **raise** the COMBAT score (fewer/no early_extinction+attrition-cluster
  penalties), which stays within the ±1 band (`B`→`A` is within tolerance) but the calibration
  reports themselves are stale after this change and must be regenerated
  (`tools/calibrate_simq.py`, referenced by D20 audit's own P1 action item) so committed data
  reflects the new sandbox_world behavior, per the fixture's own update instructions
  (`test_grade_regression.py` docstring L15-20: re-run `make calibrate`, inspect new grades,
  update `grade_anchors.json`, commit both together).
- **Exact stat-profile/role choice needs empirical validation, not just theory-crafting.**
  Wolf/goblin-family stat profiles (the closest "generic monster" catalog entries) actually have
  *lower* raw HP than the current buggy default (e.g. `wolf_predator_base` hp=45 vs current 100)
  though higher ATK/DEF. Whether this reduces or worsens the tick-8 wipe depends on simulated
  combat dynamics (trade ratio, DEF mitigation, engagement frequency), not just nominal HP. This
  is exactly why ticket Scope item 3 requires re-running the seed 42/137 200-tick scenario after
  the change — the plan below treats stat-profile selection as verify-and-iterate, not
  guess-once.
- **`docs/guidelines/intentional_divergences.md` is the actual file path** — the project
  CLAUDE.md and ticket reference `docs/guidelines/v2_intentional_divergences.md`, which does
  not exist. The real file is `docs/guidelines/intentional_divergences.md` (confirmed via
  `find`). Ticket AC #4 should be satisfied against the real file. This is a doc-naming
  drift unrelated to this ticket's scope — noted, not fixed here (out of scope: renaming/fixing
  unrelated doc references).

## Anti-Drift Hazards

- Do **not** touch `WorldTemplateExpander.expand()` (`src/worldbuilding/recipe.py`) to make it
  propagate `stats_profile`/`inventory_profile`/`cognition_profile` from
  `PopulationRecipeSpec` — that is a real gap (see Current Behavior step 2) but fixing the
  expander is an engine/schema-layer change affecting every `worldtemplate.v1` world, not a
  content-layer fix scoped to sandbox_world. Out of scope per ticket ("content-layer, not
  engine-layer"); would also require re-validating every existing template-based world.
- Do **not** touch `_resolve_entity_stats()` or `CompileProfileResolver` in
  `src/worldassembly/resolver.py` — the resolution priority chain (explicit → role default →
  global default) is correct engine behavior; the bug is purely that sandbox_world's `role:
  monster` doesn't match a catalog ID, not that the resolver logic is wrong.
  `src/content/resolver.py::EntityArchetypeResolver` is likewise correct and not on the actual
  resolution path taken by sandbox_world (see Current Behavior step 4) — do not modify it.
- Do **not** modify `data/content/social/roles.yaml` or `data/content/entities/
  stat_profiles.yaml` to add a role literally named `"monster"` — this is the "invent a new
  archetype system" trap the ticket explicitly warns against (ticket L58-59, "Prefer (a) if a
  monster archetype concept already exists elsewhere in the catalog... reuse rather than invent
  a new one"). A registered monster role already exists (`predator_hunter` et al.) — reuse it.
- Do **not** modify any other world's `world.yaml`, module, or composition file — ticket Out of
  Scope explicitly excludes rebalancing other worlds. `dungeon_crawl`, `wilderness_survival`,
  etc. are read-only reference material for this investigation only.
- Do **not** change `early_extinction_before_tick` or any `CombatScorer` weight/threshold in
  `config/simulation_quality/detection_params.yaml` or `src/simulation_quality/scorers/
  combat.py` — confirmed correct, explicitly out of scope.
- After changing `world.yaml`, `data/worlds/sandbox_world/world_compile_report.json`
  (committed artifact, contains `state_hash`) will go stale and must be regenerated
  (`make world-compile WORLD=sandbox_world`) — leaving it stale would be an
  inconsistent-repo-state violation (Definition of Done: "Repo state is consistent").

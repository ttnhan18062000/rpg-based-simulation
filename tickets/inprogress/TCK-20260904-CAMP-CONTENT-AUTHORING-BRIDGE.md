---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE
phase: open
date: 2026-09-04
tags: [content, world]
---

# TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE

## Title
Author real Camp/Nest/Lair content so state.camps and LAIR-kind Places are actually populated in compiled worlds

## Status
BLOCKED

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Three M4 tickets (`TCK-20260904-CAMP-NEST-CLASSIFICATION`, `TCK-20260904-CAMPSTATE-PLACE-BRIDGE`,
`TCK-20260904-LAIR-ENTITY-ANCHOR`) and one downstream ticket
(`TCK-20260904-FACTION-EXPAND-DIRECTIVE`) all built real, tested, production-ready mechanisms for
Camp/Nest/Lair gameplay — but every one of them is currently inert in every real compiled world,
because no world-module content on disk actually sets the opt-in fields (`PlaceRecipeSpec.creature_kind`
for Camp/Nest, a LAIR-kind Place with a real occupant precedent) that would activate them. This is
purely a content-authoring gap, not a missing mechanism — this ticket closes it by authoring real
content and confirming end-to-end activation.

## Scope
- Author `creature_kind` values (from the confirmed 6-race set: `goblin`, `orc`, `wolf`, `spider`,
  `troll`, `slime`) on at least one real CAMP-kind and one real NEST-kind Place in the existing world
  corpus (`data/content/world_modules/`), using the classification table from
  `docs/mechanics/05_world_evolution.md` §6 (Camp/Nest Classification & Nest Spread) to pick a
  race-appropriate placement — do not invent new content wholesale where an existing CAMP-kind Place
  (e.g. `goblin_camp_conflict.yaml`) can simply gain the field.
- Author at least one real LAIR-kind Place with a `dragonkin` occupant precedent in the world corpus
  (per `TCK-20260904-LAIR-ENTITY-ANCHOR`'s own finding that no real corpus world has one today) —
  either add to an existing world module or justify a new one.
- Recompile the affected world(s) and verify via `canonical_state_hash`/`WorldCompiler.compile()`
  re-run that `state.camps` is genuinely non-empty and the Lair occupant spawns correctly, following
  the same isolation-verification pattern idea 66's own migration tickets used (diff scoped to the
  regions/places/camps changed, no unrelated state drift).
- Confirm `CampService.process_camps()` genuinely fires (raid/spawn/Nest-spread branches) against the
  newly-real camp content in at least one real simulation run, and that
  `FactionDecisionPhase`'s `EXPAND_TERRITORY` → `CampService` maturity-boost consumption path
  (`TCK-20260904-FACTION-EXPAND-DIRECTIVE`) is observably reachable for the first time.
- Update the parity-ledger entries that explicitly flagged this inertness as a limitation
  (`WORLD-109`, `WORLD-124`, and any `FAC-003` divergence-note language) to reflect that real content
  now exists, via `tools/parity_ledger_writer.py` — do not hand-edit YAML.

## Out of Scope
- Any change to the classification rule, `CampService` mechanism, `PlaceState`/`CampState` schema, or
  `FactionDecisionPhase`/`EXPAND_TERRITORY` logic itself — all four are already correct and tested;
  this ticket only authors content and verifies activation.
- City-ownership/idea 35 implementation, Camp/Nest-as-conquest-target logic, or any other scope
  explicitly deferred by the sibling tickets above — those remain their own future work.
- Migrating every world in the corpus — one real, verified activation per Camp/Nest/Lair kind is
  sufficient to close this gap; broader corpus-wide migration (if desired) is a separate, larger
  follow-up.

## Acceptance Criteria
- At least one real, compiled world has `state.camps` non-empty (at least one CAMP-kind and one
  NEST-kind camp) after this ticket, verified by a real compile+inspect, not a synthetic test fixture.
- At least one real, compiled world has a real LAIR-kind Place with a live `dragonkin` occupant,
  verified the same way.
- A real simulation run against the updated content shows `CampService.process_camps()`'s raid,
  spawn, and Nest-spread branches all reachable (not just unit-tested in isolation).
- `EXPAND_TERRITORY`'s CampService maturity-boost consumption branch is shown reachable in a real run
  for the first time.
- `WORLD-109`, `WORLD-124`, and FAC-003's divergence notes are updated to drop the "inert against real
  content" caveat where it's no longer true, with fresh `v2_evidence` citing the new content.
- No unrelated state drift in the affected world(s) — isolation verified via `canonical_state_hash`
  diffing at multiple entity-count scales, matching idea 66's own migration-ticket precedent.

## Related Tickets
- TCK-20260904-CAMP-NEST-CLASSIFICATION
- TCK-20260904-CAMPSTATE-PLACE-BRIDGE
- TCK-20260904-LAIR-ENTITY-ANCHOR
- TCK-20260904-FACTION-EXPAND-DIRECTIVE
- TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD
- TCK-20260902-PLACE-MIGRATION-STAGE-B-ROLLOUT

## Related Docs
- docs/mechanics/05_world_evolution.md (§6 Camp/Nest Classification & Nest Spread)
- docs/world/raid_boss_camp_contract.md
- docs/world/compiler_contract.md
- docs/parity_ledger/world_dynamics.yaml (WORLD-109, WORLD-124)
- docs/parity_ledger/faction.yaml (FAC-003)

## Related Stored Artifacts
- stored_artifacts/TCK-20260904-CAMP-NEST-CLASSIFICATION/
- stored_artifacts/TCK-20260904-CAMPSTATE-PLACE-BRIDGE/
- stored_artifacts/TCK-20260904-LAIR-ENTITY-ANCHOR/
- stored_artifacts/TCK-20260904-FACTION-EXPAND-DIRECTIVE/

## Related Code Areas
- data/content/world_modules/ (real content to author)
- src/world/camp.py
- src/world/boss.py
- src/worldbuilding/compiler.py
- src/worldbuilding/recipe.py, src/worldbuilding/schema.py (creature_kind field)
- src/engine/faction_decision.py

## Assumptions / Open Questions
- Whether to extend an existing world module or author a new one is a real content-design call left
  to this ticket's own investigation/plan — the sibling tickets deliberately declined to migrate real
  content to keep their own scope narrow and behavior-neutral; this ticket exists specifically to make
  that call.
- Totem/stockpile/palisade magnitudes (typed scaffolding added by `TCK-20260904-CAMP-NEST-CLASSIFICATION`,
  still unpopulated by any production writer) are a related but distinct gap — this ticket does not
  need to populate them unless doing so is trivial alongside the content authoring above.

## Implementation Notes

**Content authored (the ticket's own real deliverable) — done and verified:**

1. `data/content/world_modules/goblin_camp_conflict.yaml` — added `creature_kind: "goblin"` to the
   already-existing `goblin_camp_place` (CAMP-kind). This is the "existing CAMP-kind Place can
   simply gain the field" path the ticket's own Scope preferred over inventing new content.
2. `data/content/world_modules/wolf_den_near_forest.yaml` — new NEST-kind Place `wolf_den_nest`
   (`creature_kind: "wolf"`, in `CampService.NEST_RACE_KINDS`), centroid of `wolf_den`'s own
   `grid_bounds`. Matches that module's existing `wild_beast_pack`/`wolf_pack_small` theming.
3. `data/content/world_modules/moon_cult_ruins.yaml` — new LAIR-kind Place `moon_cave_lair`. **Not**
   placed in `mountain_pass_zone`, which was the first candidate: a real regression guard
   (`tests/unit/worldbuilding/test_place_wiring.py::test_hero_guild_routing_real_content_produces_
   expected_non_uniform_place_kinds`) caught that as a violation of a deliberate prior content
   decision — `mountain_pass_zone` is authored as intentionally place-free "pure transit terrain",
   idea 66's own "or none at all" case. Relocated to `moon_cave` instead, which is a strictly better
   fit anyway: a cave at the corpus's top `hazard_level` (4.0), so it accrues regional trauma faster
   than any lower-hazard candidate — directly relevant to the Lair spawn gate (see blocker below).
   The guard was left untouched; the content moved.
4. Recompiled all 16 worlds that compose any of these 3 modules (not just the verification target)
   so no checked-in `resolved/` artifact is left stale against its own module source.
5. Parity ledger updated via `tools/parity_ledger_writer.py` (never hand-edited): `WORLD-109`
   (divergence_note: the "no real content sets creature_kind" claim is now false; camp_constructed
   remains blocked only by the unchanged, separate "CampService has no event recorder" code gap —
   plus a new support_boundary carrying the measured reachability numbers), `WORLD-124`
   (support_boundary: real Nest content now exists; Nest-spread branch still unreached, with
   measured numbers), `FAC-003` (support_boundary: the EXPAND_TERRITORY→CampService consumption path
   is content-reachable for the first time, with its own downstream-gate caveat).

**Verified activation (real compile + real Kernel ticks, not synthetic fixtures):**
Against `simq_scale_stress_seed42` (composes all 3 modules) and `lifecycle_full_coverage_world`:
- `state.camps` is genuinely non-empty for the first time — 2 entries: `goblin_camp_place`
  (`kind='goblin'`, CAMP) and `wolf_den_nest` (`kind='wolf'`, NEST). It was `{}` in every compiled
  world before this ticket.
- `moon_cave_lair` is present in `state.places` with `kind=LAIR`.
- `CampService.process_camps()`'s **spawn branch fires for real**, confirmed at tick 1 for both
  camps (monsters-near-camp count 0 → 1) in a real `Kernel.tick_once()` loop.

**REAL BLOCKER FOUND — maturity calibration, not content (this is why the ticket is BLOCKED, not
DONE):**
Acceptance Criteria 3 (raid + Nest-spread branches reachable in a real run), 4 (EXPAND_TERRITORY
maturity-boost consumption reachable in a real run), and the occupant half of AC2 (a *live*
dragonkin in the LAIR) are **not satisfiable by content authoring at all**, and are not satisfiable
in any practical run length:
- Both the raid branch and the Nest-spread branch gate on `camp.maturity >= RAID_MATURITY_THRESHOLD`
  (80.0). `CampService.MATURITY_PER_TICK = 0.05` is **misleadingly named**: it accrues once per
  `world_dynamics` *invocation*, not per tick, and `world_dynamics` runs on a cadence of 100 in
  `PROD_SMALL` (`src/config/profiles.py:93`). Effective rate: **0.0005 maturity/tick** →
  **~160,000 ticks** to reach the threshold (~32,000 even at the fastest profile cadence of 20).
  Measured directly, not estimated: 1,000 real ticks moved both camps from 0.00 to **0.50**.
- The Lair occupant additionally needs `state.maturity >= 50.0` (world maturity, incremented +1 per
  calamity in `src/world/calamity.py:32`) and `region.trauma_score >= 20.0`. Measured over 1,000
  real ticks: world maturity stayed **0**, max region trauma reached **4.95**.
- For scale: the repo's own calibration runs are 200–3,000 ticks, and its long-run tooling defaults
  to ~5,000. All three gates are 1–2 orders of magnitude beyond that.

This is a pre-existing mechanism-calibration gap in `CampService`/`BossService`, fully independent of
this ticket's content work — the content is now correct and the mechanisms are correctly wired to it;
they simply cannot fire within any realistic run. Fixing it means changing a real balance constant
(`MATURITY_PER_TICK`, `RAID_MATURITY_THRESHOLD`, or the cadence divisor), which is squarely inside
this ticket's own **Out of Scope** ("Any change to the classification rule, `CampService` mechanism
... itself"). Escalated rather than silently redefining the ACs or quietly leaving them unmet.

## Test Summary
- `pytest tests/unit/worldbuilding/ tests/unit/worldassembly/ tests/tools/test_corpus_registry.py
  tests/unit/world/ tests/unit/rendering/test_variants.py tests/unit/strategic/test_opportunities.py
  tests/unit/observability/test_provenance_lookup.py tests/unit/content/ -m "not slow"` —
  **917 passed, 0 failed** (33 deselected).
- That sweep is what caught the `mountain_pass_zone` placement error, on a genuine pre-existing
  regression guard; the content was moved rather than the guard edited.
- Real `Kernel.tick_once()` runs (1,000 ticks against `lifecycle_full_coverage_world`; 100 ticks
  against `simq_scale_stress_seed42`) supplied every number quoted above — no estimates.
- `python3 -m src.worldbuilding.cli resolve` succeeded for all 16 affected worlds;
  `... validate lifecycle_full_coverage_world` shows only the 4 pre-existing, unrelated
  `WORLD-UNEXPECTED-SECTION` warnings shared by every world of this shape.

**Follow-up pass, 2026-09-08:**
- `pytest tests/unit/worldbuilding/ tests/unit/worldassembly/ tests/tools/test_corpus_registry.py
  tests/unit/world/ tests/unit/content/ -m "not slow"` — **881 passed, 0 failed** (33 deselected),
  confirming the `compiler.py` `CampState.maturity` fix causes no regression.
- `pytest tests/unit/ -k "camp" -m "not slow"` — **195 passed, 0 failed** (all camp-related tests
  repo-wide).
- Real `Kernel.tick_once()` runs (510 ticks against the new dedicated `camp_maturity_calibration_
  pilot` world) proved: both camps' maturity crosses 80.0 at tick ~500 (seeded content + the
  compiler fix, not an estimate); the Nest-spread branch fires and produces a real `life_stage=
  CHILD` entity at the nest's own compiled position; the raid branch's `maturity_delta=-20.0`/
  `last_raid_tick_set` bookkeeping applies for both camps at the same tick despite the raid branch
  itself never spawning visible raiders (the discard bug documented above).
- `python3 -m src.worldbuilding.cli resolve/validate camp_maturity_calibration_pilot` — succeeds,
  only the same class of pre-existing `WORLD-UNEXPECTED-SECTION` warnings every unit-tier world of
  this shape has.

## Files Changed
- `data/content/world_modules/goblin_camp_conflict.yaml` (creature_kind on existing CAMP Place)
- `data/content/world_modules/wolf_den_near_forest.yaml` (new NEST-kind Place)
- `data/content/world_modules/moon_cult_ruins.yaml` (new LAIR-kind Place)
- `data/worlds/*/resolved/` for 16 worlds composing those modules (regenerated, not hand-edited)
- `docs/parity_ledger/world_dynamics.yaml` (WORLD-109, WORLD-124 — via `parity_ledger_writer.py`)
- `docs/parity_ledger/faction.yaml` (FAC-003 — via `parity_ledger_writer.py`)
- `tickets/inprogress/TCK-20260904-CAMP-CONTENT-AUTHORING-BRIDGE.md` (this ticket)

**Follow-up pass, 2026-09-08:**
- `src/worldbuilding/compiler.py` (real bugfix: thread `p_spec.maturity` into `CampState`, not just
  the companion `PlaceState`)
- `data/content/world_modules/camp_maturity_calibration_pilot.yaml` (new dedicated module)
- `data/worlds/camp_maturity_calibration_pilot/` (new dedicated world + resolved artifacts)
- `config/simulation_quality/profiles/camp_maturity_calibration_pilot.yaml` (new calibration
  profile, `ENABLE_CAMP_NEST_SPREAD: "ON"`)
- `data/content/world/biomes.yaml`, `data/content/world/ecologies.yaml`, `data/content/world/
  runtime_regions.yaml` (new catalog entries for the dedicated calibration region — required by the
  resolver, isolated to this one region, no existing entries touched)

## Completion Summary
STILL NOT DONE — BLOCKED again, deliberately, after real follow-up progress. Summary of the full
picture across both passes:
- **Done and verified**: content authored (CAMP/NEST/LAIR places exist in real compiled worlds,
  `state.camps` non-empty for the first time, spawn branch fires); a real compiler bugfix
  (`CampState.maturity` threading) that benefits any future maturity-seeded content repo-wide, not
  just this ticket; a dedicated calibration world proving the Nest-spread branch fires with a real
  offspring entity in a practical 510-tick run.
- **Newly found, real, deeper blockers** (not resolvable within this ticket's own content-authoring
  scope): the raid branch's own code silently discards its computed raiders regardless of maturity
  or timing (a pre-existing, self-documented incomplete stub in `CampService`); `EXPAND_TERRITORY`
  can never fire for any faction in any real world because `FactionState.territory` is never seeded
  or derived anywhere in production code; the Lair-occupant gates have no compile-time seed path
  and need ≥250,000 ticks naturally.
- Three real decisions are now needed (see the Decision section above) before this ticket — or a
  follow-up ticket it should split into — can close for real.

The content-authoring half of this ticket (its original own deliverable) is complete and verified
against real compiled worlds: `state.camps` is non-empty for the first time ever (one real CAMP +
one real NEST), a real LAIR-kind Place exists for the first time, and `CampService`'s spawn branch
demonstrably fires in a real Kernel run. Parity ledger entries that claimed "no real content sets
creature_kind" are corrected.

What blocks closure is not content: the raid, Nest-spread, EXPAND_TERRITORY-boost, and Lair-occupant
branches all gate on maturity thresholds that need ~160,000 ticks (camps) or an unreached world
maturity/trauma floor (Lair) — 1–2 orders of magnitude beyond any run this repo actually performs,
measured directly rather than estimated. That is a balance-constant problem inside this ticket's own
Out of Scope, so it needs a real decision (retune the constants, lower the thresholds for a
dedicated corpus world, or formally accept these branches as long-horizon-only and amend ACs 2-4)
rather than a unilateral fix here.

### Decision, 2026-09-08 (real user decision, via `AskUserQuestion`, orchestrator-initiated)
**Dedicated corpus world with lowered thresholds** — a small calibration-only world/profile that
overrides the maturity gate (via whatever override mechanism the corpus/profile system already
supports — e.g. a calibration-profile-scoped constant override, not a change to
`CampService.RAID_MATURITY_THRESHOLD`/`MATURITY_PER_TICK` themselves) so the raid, Nest-spread, and
EXPAND_TERRITORY-boost branches can be genuinely proven reachable in a real, practical-length run —
without touching real production game-balance constants used by every other world. The real
production `CampService`/`BossService` mechanism and constants stay exactly as they are; only this
one dedicated calibration world sees a lowered gate.

### Follow-up implementation, 2026-09-08 — real progress, plus 3 new, deeper blockers found

**No profile-level constant-override mechanism exists.** Investigated `tools/calibrate_simq.py`'s
`_load_profile_feature_flags()` and the calibration profile YAML schema — only `feature_flags:`
(ON/OFF/SHADOW toggles) and `campaign_episodes:` are supported; there is no generic per-world
numeric-constant override. Content-seeding was the only viable path, not a config toggle.

**Real, additive fix required and made (in scope, not a mechanism/threshold change):**
`PlaceRecipeSpec.maturity` (`src/worldbuilding/schema.py`) is a real, already-documented,
content-authorable field ("CAMP/NEST-kind: growth-over-time value... reused from
`CampState.maturity`"), and `WorldCompiler.compile()` already threads it into the companion
`PlaceState.maturity` — but a real compiler bug meant it was **never threaded into the parallel
`CampState`** that `CampService.process_camps()` actually reads (`src/worldbuilding/compiler.py`,
`CampState(...)` constructor was missing `maturity=p_spec.maturity`). Content-authored maturity was
therefore silently inert for every CAMP/NEST place in every world, not just this one. Fixed with a
1-line additive change (`**({"maturity": p_spec.maturity} if p_spec.maturity is not None else {})`)
— defaults unchanged for every place that doesn't set it; verified via full
`tests/unit/worldbuilding/ tests/unit/worldassembly/ tests/tools/test_corpus_registry.py
tests/unit/world/ tests/unit/content/` sweep (881 passed) plus all camp-related tests repo-wide
(195 passed). This was necessary for the ratified decision to be implementable via content at all
— without it, seeded maturity values are silently discarded and the calibration-world approach is
impossible.

**New dedicated world built and verified**: `camp_maturity_calibration_pilot`
(`data/worlds/camp_maturity_calibration_pilot/`, `data/content/world_modules/
camp_maturity_calibration_pilot.yaml`) — composes `frontier_village_core` +
`camp_maturity_calibration_pilot`, seeding a CAMP (`goblin`) and NEST (`wolf`) both at
`maturity: 79.9` (isolated to this one dedicated world only — `goblin_camp_conflict`/
`wolf_den_near_forest`'s own shared, production-default-maturity content is untouched, so none of
the 16 worlds composing those modules is affected). Required 3 small catalog registrations
(`data/content/world/{biomes,ecologies,runtime_regions}.yaml`) since the resolver requires every
region/biome/ecology referenced by a module to exist in the shared catalog even for a
single-purpose calibration world — routine content plumbing, not a design decision.
Calibration profile: `config/simulation_quality/profiles/camp_maturity_calibration_pilot.yaml`
(`ENABLE_CAMP_NEST_SPREAD: "ON"`).

**AC3's Nest-spread branch: PROVEN reachable, real offspring entity confirmed.** Ran a real,
practical 510-tick `Kernel.tick_once()` loop (not a synthetic fixture): both camps' maturity
crossed 80.0 at tick ~500 (`79.9 + 10×0.05 = 80.4`, consistent with the ticket's own documented
0.0005/tick effective rate), and `state.tick - camp.last_raid_tick >= 500` (default `0`) was
satisfied at the same tick. The wolf nest's Nest-spread branch (`camp.kind in NEST_RACE_KINDS`,
flag ON) fired: a new entity (id 24) appeared at tick ~501, positioned exactly at the nest's own
compiled position `(180, 180)`, `role=MONSTER`, **`life_stage=CHILD`** — the real, distinguishing
signature of `generator.spawn_natural_creature_offspring()` (adult `spawn_monster()` calls don't
produce `CHILD` entities). Maturity dropped from 80.15 → 60.15 for both camps at the same tick
(the -20.0 cost), confirming the branch condition and cost-application both executed correctly.

**AC3's Raid branch: a real, separate, pre-existing bug found — camp-triggered raids are silently
discarded, independent of maturity or timing.** `CampService.process_camps()`'s own raid-reuse code
(`src/world/camp.py`, the `else:` branch under "Trigger a raid from this camp!") calls
`RaidService.check_for_raid(state, generator)` and receives a real `raid_update` with computed
raider entities in `raid_update.entities_add` — but then the code's own pre-existing comment block
says *"We can't easily mutate the update list, so we just add them but in a real system we'd pass
the origin. For now, let's just mark the last_raid_tick."*, followed by a `for mob in
raid_update.entities_add: ... pass` loop that **does nothing** — the computed raiders are never
appended to the outer `entities_add` list `process_camps()` actually returns. `camp_updates[c_id]`
still gets `maturity_delta=-20.0, last_raid_tick_set=state.tick` unconditionally, so the *internal
bookkeeping* silently proceeds as if a raid happened, even though **zero raiders are ever actually
spawned by this code path, regardless of maturity or timing** — a self-documented, pre-existing
incomplete stub, not something content authoring (or this ticket's own scope) can fix. Separately,
this camp-triggered call is *also* gated a second time by `RaidService.check_for_raid()`'s own
independent `state.tick % raid_interval_ticks == 0` condition (`raid_interval_ticks = 500`, same
constant as `src/engine/world_dynamics.py`'s own **unrelated, global, camp-agnostic** periodic raid
trigger) — meaning even if the discard bug were fixed, the camp-triggered raid would still only
ever produce visible raiders on a tick that happens to be an exact multiple of 500, a second,
narrower compounding gate. (The `raid_party_spawned` event observed in an earlier calibration run
at tick 501 was independently confirmed to be this *unrelated* global trigger, not
`CampService`'s own branch — a red herring in this investigation's own earlier pass, corrected
here before reporting.)

**AC4 (EXPAND_TERRITORY) and the Lair-occupant half of AC2: confirmed genuinely unreachable by any
means available to this ticket, for reasons deeper than originally scoped:**
- `FactionState.territory` (`src/core/state.py`, `Tuple[str, ...] = ()`) is **never seeded at
  compile time and never derived by any runtime phase** — confirmed via `grep -rn "territory_add"
  src/` (only ever read in `apply.py`'s merge logic and observability shapers, never emitted by any
  real producer) and by direct inspection of `WorldCompiler.compile()`'s own `FactionState(...)`
  construction (only `faction_id`/`tension_level` set). `region.owner_faction_id` *is*
  compile-time-seedable (`context.region_ownership`), but nothing propagates that into the
  corresponding faction's own `territory` tuple. `FactionDecisionPhase.execute()`'s own
  `EXPAND_TERRITORY` gate (`if fs.territory: ...`) can therefore never be true for any faction in
  any real compiled world today — this is a separate, real dormant-mechanism gap, independent of
  camp/maturity content, and squarely outside this ticket's own content-authoring scope to fix (it
  needs either a compile-time territory-derivation step or a runtime seeding phase — a real
  mechanism decision, not a content change).
- The Lair-occupant gates (`state.maturity >= 50.0`, world-level, +1 per calamity; `region.
  trauma_score >= 20.0`) have no compile-time content-seed path in the schema (confirmed: no
  `RegionSpec`/`WorldComposition`-level field for either). Natural accrual: `CalamityService`'s own
  `CALAMITY_FORCE_INTERVAL = 5000` guarantees a calamity at most every 5000 ticks, so reaching
  `state.maturity >= 50` needs **≥250,000 ticks** minimum — even deeper than the camp-maturity gate
  this ticket already found, and with no calibration-world workaround available without adding a
  new schema field (a real, additive mechanism change beyond pure content authoring).

**Disposition**: left BLOCKED (not DONE) again, deliberately. Real, verified progress on AC3's
Nest-spread half; a real, valuable, independently-useful compiler bugfix now benefits every world's
future maturity-seeded content, not just this one; 3 new, well-evidenced findings escalated rather
than worked around or decided unilaterally — matches this fork's own explicit directive to stop
and report a genuinely new, different blocker rather than invent a fix. Real decisions needed:
(1) is the raid-discard bug worth fixing now as its own hotfix (a real, small, self-contained
`camp.py` fix distinct from this ticket's own content-authoring scope), (2) should EXPAND_TERRITORY's
territory-seeding gap be scoped as its own ticket (a real mechanism decision, not resolvable here),
(3) should the Lair-occupant gate be formally accepted as long-horizon-only (matching the same
disposition class as the camp-maturity gate before this ticket's own fix) or get a new
compile-time-seedable schema field.

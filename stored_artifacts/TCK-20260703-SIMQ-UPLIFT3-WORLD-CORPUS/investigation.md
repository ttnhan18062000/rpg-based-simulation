---
ticket_id: TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS
phase: investigation
date: 2026-07-04
---

# Investigation: Diversify the SimQ calibration world corpus

## Current Behavior

### Diversity audit table (all 10 worlds in `data/worlds/`)

Entity/region/resource counts read from each world's `world_compile_report.json`. "In corpus"
means the world has ≥1 entry in `tests/simulation_quality/fixtures/grade_anchors.json` (25 total
entries, all belonging to 4 worlds).

| World | Entities | Regions | Res. nodes | Modules | In anchored corpus? |
|---|---|---|---|---|---|
| wilderness_survival | 11 | 4 | 4 | forest_deep_ecology, wolf_den_near_forest, undead_battlefield, survivor_camp_shelter | No |
| sandbox_world | 18 | 3 | 5 | frontier_village_core, wolf_den_near_forest | **Yes** (5 anchors) |
| highland_traverse | 18 | 5 | 3 | mountain_pass, river_crossing, nomadic_herd, settled_quarter | No |
| swamp_border_world | 26 | 4 | 7 | frontier_village_core, wolf_den_near_forest, sunken_swamp_border | No |
| simq_routing_test | 30 | 3 | 5 | frontier_village_core, old_mine_resource_loop, goblin_camp_conflict, hero_adventurers | **Yes** (3 anchors) |
| urban_political | 30 | 3 | 3 | frontier_village_core, trading_company_hub, bandit_road_trade_pressure, hero_adventurers | **Yes** (7 anchors) |
| dungeon_crawl | 32 | 4 | 3 | ruins_mystery_quest, goblin_camp_conflict, old_mine_resource_loop, scalable_bandit_camp | **Yes** (10 anchors) |
| generated_frontier_3_42 | 44 | 6 | 9 | frontier_village_core, old_mine_resource_loop, bandit_road_trade_pressure, goblin_camp_conflict, moon_cult_ruins, orc_clan_territory | No |
| frontier_living_world | 46 | 7 | 9 | frontier_village_core, wolf_den_near_forest, goblin_camp_conflict, old_mine_resource_loop, bandit_road_trade_pressure, undead_battlefield | No |
| frontier_extended | 56 | 10 | 13 | + orc_clan_territory, forest_warden_grove (8 modules total) | No |

**Entity-count range of the full 10-world corpus: 11–56.** But the *anchored* subset (the only
worlds that actually run in `make evaluate`/CI) is clustered tightly at **18–32** — sandbox_world
(18), simq_routing_test (30), urban_political (30), dungeon_crawl (32). Nothing below 18 or above
32 is anchored. The three worlds ≥44 entities (generated_frontier_3_42, frontier_living_world,
frontier_extended) and the one world at 11 entities (wilderness_survival) all exist and compile
cleanly but have **zero** anchor entries — `docs/simulation_quality/eval_matrix_results.md`
explicitly excluded all of them as "zero-pillar" (see Prior Work below).

### Module content-variety audit (20 modules in `data/content/world_modules/`)

Cross-referencing module usage against the 4 anchored worlds only:

- **Used somewhere in the anchored corpus (9 modules):** `frontier_village_core`,
  `wolf_den_near_forest`, `ruins_mystery_quest`, `goblin_camp_conflict`, `old_mine_resource_loop`,
  `scalable_bandit_camp`, `trading_company_hub`, `bandit_road_trade_pressure`, `hero_adventurers`.
- **Never used in any anchored world (11 of 20 — 55%):** `forest_deep_ecology`,
  `forest_warden_grove`, `moon_cult_ruins`, `mountain_pass`, `nomadic_herd`, `orc_clan_territory`,
  `river_crossing`, `settled_quarter`, `sunken_swamp_border`, `survivor_camp_shelter`,
  `undead_battlefield`.

**Concrete gap:** the entire "highland/river/nomad" content family (`mountain_pass`,
`river_crossing`, `nomadic_herd`, `settled_quarter` — all 4 only exist in the unanchored
`highland_traverse`) and the "cult/mystery" family (`moon_cult_ruins` — only in the unanchored,
non-corpus `generated_frontier_3_42`) produce **zero** calibration signal today. `undead_battlefield`
(danger-zone/ruins theme) is used in 3 worlds (`frontier_extended`, `frontier_living_world`,
`wilderness_survival`) — all 3 unanchored.

### Per-world pillar reachability (structural, cross-referenced against feature-flag gates)

Per `docs/audits/D20_simq_integration.md` and `docs/plans/audit_fix_plan.md`, four pillars are
gated behind mechanisms that only 2 of the 10 worlds currently satisfy:

| Pillar | Structural requirement | Worlds that satisfy it |
|---|---|---|
| AGENCY | `ENABLE_ADVENTURE_ROUTING=ON` (env var, not a profile field) | `simq_routing_test` only |
| FACTION | Compile-time `faction_tension_overrides` (compiler extension, TCK-20260702-SIMQ-UPLIFT2-FACTION) | `urban_political` only |
| INFORMATION | `information_source_profiles` + `pending_information_responses` seed + `ENABLE_BELIEF_ASSIMILATION=ON` | `urban_political` only |
| SOCIAL | `ENABLE_SOCIAL_COOPERATION=ON` (profile `feature_flags:` block) | `urban_political` only |

COMBAT, NARRATIVE, PROGRESSION, WORLD are structurally reachable by any world with hostile
encounters, quests, XP-granting combat, and hazard/ecology regions respectively — i.e. all 10
worlds can produce signal for these 4 pillars (empirically confirmed below for the 3
previously-excluded worlds). ECONOMY requires a Gini>0.7 trigger (needs merchant NPCs / non-symmetric
trade) and COGNITION requires a non-survival project + DANGER urgency>0.7 combination — both are
duration/content-sensitive rather than flag-gated, and currently only demonstrated in
`urban_political` (1000t+) and `sandbox_world` (seed123, long runs).

**Consequence for this ticket's scope:** per the ticket's own Out-of-Scope line ("Seeding
FACTION/INFORMATION-specific content ... into the new worlds — that's a natural follow-on ... not
part of this ticket's own scope"), any new worlds authored under this ticket will **also** be
structurally blind to AGENCY/FACTION/INFORMATION/SOCIAL unless they reuse `simq_routing_test`'s
env-var pattern or `urban_political`'s compiler-seeding pattern. This is not a defect introduced
by this ticket — it is an explicit, already-documented scope boundary. The new worlds should be
evaluated as diversifying the COMBAT/NARRATIVE/PROGRESSION/WORLD (+ECONOMY/COGNITION where
duration allows) signal across new entity-count/region-count/module shapes, not as closing the
4-pillar gate (that is `TCK-20260703-SIMQ-UPLIFT3-*` follow-on territory per the ticket's Related
Tickets and its own Out of Scope section).

## Mechanics/Engine Constraints

- World compilation is `WorldAssemblyResolver.assemble()` (source modules →
  `data/worlds/{name}/resolved/world.resolved.yaml`) followed by `WorldCompiler.compile(spec, seed)`
  (resolved spec → `AuthoritativeState`). Both steps are content/compile-time, not runtime — a
  fix landing in the resolver or compiler does **not** retroactively apply to a world's *already
  resolved* YAML on disk. Each world must be **recompiled** (assembly re-run) to pick up resolver
  fixes.
- `RegionState.hazard_kind` (typed exemption key, `docs/mechanics/05_world_evolution.md`,
  `TCK-20260701-HAZARD-NATIVE-IMMUNITY` / `TCK-20260701-HAZARD-KIND-RESOLVER-GAP`) is the
  mechanism that exempts native/immune fauna from environmental hazard-drain in their own habitat.
  Absent `hazard_kind`, hazard-drain applies unconditionally to every entity standing in a
  hazardous region regardless of role/faction.
- `SpawnService.process_spawns()` (`src/world/spawn.py`) implements a two-tier cadence
  (`base_spawn_batch_size=1` before tick 500, `late_spawn_batch_size=2` at/after tick 500 —
  `SpawnConfig` in `src/world/spawn_config.py`, parity entry WORLD-103). This is a **late-run**
  mechanism only; it cannot affect population dynamics before tick 500 by construction.

## Parity Ledger Overlap

- `docs/parity_ledger/world_dynamics.yaml::WORLD-103` — SpawnService two-tier cadence (verified,
  code inspection in this investigation confirms it is present and functioning as documented).
- Hazard-kind/native-immunity fixes are tracked under the sandbox_world-specific tickets
  (`TCK-20260701-HAZARD-NATIVE-IMMUNITY`, `TCK-20260701-HAZARD-KIND-RESOLVER-GAP`) — no parity
  ledger entry currently states these fixes apply corpus-wide; this investigation found they do
  **not** apply corpus-wide because 8 of 10 worlds were never recompiled since the fixes landed.

## Prior Work

- `TCK-20260702-SIMQ-EVAL-MATRIX` (done) — built the 3-seed × 2–4-tick matrix for the 4
  already-signal-producing worlds; explicitly excluded `wilderness_survival`,
  `highland_traverse`, `swamp_border_world`, `frontier_extended`, `frontier_living_world` as
  "zero-pillar" / early-terminating.
- `TCK-20260627-P2B-SPAWN-CADENCE` (done, 2026-06-27) — added the two-tier spawn cadence described
  above. Verified `alive_avg >= 12` for a 1,000-tick **urban_political** run at seeds 42/137. This
  ticket's scope was always urban_political-specific late-run attrition; it was never validated
  against `frontier_extended`/`frontier_living_world`.
- `TCK-20260701-SANDBOX-MONSTER-BALANCE` (done) — root-caused and fixed a 3-part chain for
  `sandbox_world` specifically: (1) flat catalog stats for `worldtemplate.v1`, fixed by migrating
  to `worldcomposition.v1`; (2) hazard-drain lacking native/immune-fauna exemption, fixed via
  `hazard_kind`/`hazard_immunities`; (3) a resolver plumbing gap not forwarding `hazard_kind`,
  fixed in `TCK-20260701-HAZARD-KIND-RESOLVER-GAP`. **This investigation found the same 3-part bug
  class is still live in `frontier_extended`/`frontier_living_world`/`wilderness_survival` because
  those worlds were never recompiled after the fix landed** — see Findings below.

## Findings — P2-B Independent Re-Verification

**Re-verification method:** read `src/world/spawn.py` + `src/world/spawn_config.py` in full, then
independently re-ran `frontier_extended` (56 entities), `frontier_living_world` (46 entities), and
`wilderness_survival` (11 entities) at 200/300/1000 ticks via `tools/calibrate_simq.py` and a
direct `Kernel.tick_once()` driver script, sampling `AuthoritativeState.entities[*].combat.alive`
at checkpoints.

**Finding 1 — the original P2-B (urban_political late-run spawn/attrition imbalance) is genuinely
RESOLVED.** Code inspection confirms `SpawnService.process_spawns()` implements the documented
two-tier cadence exactly as `TCK-20260627-P2B-SPAWN-CADENCE` describes: `batch_size` doubles from
1 to 2 per region per 50-tick interval once `state.tick >= late_spawn_threshold_tick` (500),
capped by the region's density deficit. This is present in the current `src/world/spawn.py`
(post-relocation) unchanged in logic from the original fix. The "UNVERIFIED" tag in
`docs/plans/audit_fix_plan.md` (2026-07-03) reflected file-relocation churn, not a logic
regression — the fix is intact.

**Finding 2 — the "early termination" recorded for `frontier_extended`/`frontier_living_world`
(tick 159) and `wilderness_survival` (tick 101) in the 13-run corpus table does NOT reproduce as a
literal engine halt.** Direct re-run of all three worlds for far longer than their recorded
termination tick (`frontier_extended` to 1000t, `frontier_living_world` to 200t,
`wilderness_survival` to 300t) completed with **zero exceptions, zero watchdog-triggered aborts,
and a full tick count reached** in every case:

```
frontier_extended  seed42  200t  -> overall_grade=A, COMBAT=S, ran to completion
frontier_extended  seed42 1000t  -> overall_grade=B, ran to completion
frontier_living_world seed42 200t -> overall_grade=A, ran to completion
wilderness_survival seed42  300t -> overall_grade=B, ran to completion
```

`tools/calibrate_simq.py`'s tick loop (`for _ in range(ticks): kernel.tick_once()`) has no
early-exit/break condition and none was found anywhere in `src/engine/kernel.py`. So whatever
originally produced "159†"/"101‡" in the 13-run corpus table was **not** a hard simulation stop —
it was very likely the run being manually curtailed once population had already collapsed to a
tiny residual (see Finding 3), which reads externally as "terminated early" but is not an engine
behavior that exists in the current code.

**Finding 3 — the real, still-live problem is NOT spawn cadence — it is a stale, pre-hazard-fix
world compilation causing catastrophic *early*-tick (not late-tick) population collapse.**
Directly driving `frontier_extended` via `Kernel.tick_once()` and sampling alive-entity count:

| Tick | Total entities | Alive |
|---|---|---|
| 0 | 56 | 56 |
| 50 | 56 | 13 |
| 159 | 56 | 13 |
| 500 | 56 | 12 |
| 700 | 59 | 15 |
| 1000 | 59 | 4 |

**43 of 56 entities (77%) die between tick 0 and tick 50** — this is an *early*-run collapse, the
opposite end of the timeline from what P2-B describes (P2-B is specifically about tick 800–1000
attrition outpacing a tick-500-triggered spawn tier). Inspecting the 43 dead entities: 39 role
`CITIZEN` / faction `NEUTRAL`, 4 role `GUARD` / faction `TOWN_COUNCIL`. Inspecting one dead
entity's full record (region `haunted_battlefield`, hazard_level 4.0): `archetype_id=None`,
`combat.hazard_immunities=None`, `hp=100` (flat default) — i.e., these are the same
"flat-stat, unresolved-archetype, no hazard exemption" entities that `TCK-20260701-SANDBOX-MONSTER-BALANCE`
found and fixed for `sandbox_world`'s `wolf_pack_small` population, just showing up under a
generic `CITIZEN`/`NEUTRAL` fallback identity in this world instead.

**Root cause confirmed via provenance manifests:** every world's `resolved/provenance_manifest.json`
records a `created_at` compile timestamp. Only 2 of 10 worlds have been recompiled since the
hazard-kind fixes landed (2026-07-01):

| World | `created_at` (compile time) | Recompiled after 2026-07-01 fixes? |
|---|---|---|
| simq_routing_test | 2026-06-30T16:40 | No |
| dungeon_crawl | 2026-06-30T18:18 | No |
| generated_frontier_3_42 | 2026-06-30T18:18 | No |
| frontier_extended | 2026-06-30T18:44 | No |
| frontier_living_world | 2026-06-30T18:47 | No |
| swamp_border_world | 2026-06-30T18:47 | No |
| highland_traverse | 2026-06-30T18:47 | No |
| wilderness_survival | 2026-06-30T18:47 | No |
| **sandbox_world** | **2026-07-02T01:28** | **Yes** |
| **urban_political** | **2026-07-03T17:45** | **Yes** |

`data/worlds/frontier_extended/resolved/world.resolved.yaml` has **no `hazard_kind` field on any
region** (confirmed by grep — not even `wolf_den`, whose source module
`data/content/world_modules/wolf_den_near_forest.yaml` explicitly sets
`hazard_kind: "NATURAL_TERRAIN"`). By contrast, `sandbox_world`'s resolved YAML — recompiled
2026-07-02 — does carry `hazard_kind: PHYSICAL`/`NATURAL_TERRAIN` per region. This is staleness,
not a code regression: the resolver fix works, but 8 of 10 worlds' on-disk resolved YAML predates
it and was never regenerated.

**Finding 4 — recompiling alone would only partially fix `frontier_extended`.** Of the 5
non-core modules composing it, only `goblin_camp_conflict`, `wolf_den_near_forest`, and
`forest_warden_grove` declare `hazard_kind` in source YAML. `orc_clan_territory`,
`bandit_road_trade_pressure`, and `old_mine_resource_loop` declare `hazard_level` (2.0–3.0) with
**no `hazard_kind` field at all** — their native populations (`orc_clan_warband`,
`bandit_ambush_group`, `merchant_caravan`, `old_mine_spider_cluster`) would still lack a
hazard-immunity pairing and remain exposed to lethal drain in their own habitat even after a fresh
recompile. Fully fixing this world's population stability requires **both** a recompile **and**
adding `hazard_kind` + matching archetype `hazard_immunities` to those 3 modules — the same
content pattern already proven for `wolf_den_near_forest`/`wolf_pack_small`.

`wilderness_survival` uses `undead_battlefield` (no `hazard_kind` in source) and
`wolf_den_near_forest` (has `hazard_kind`, but the world was never recompiled) — same root cause,
same fix pattern required.

**Conclusion:** P2-B's own scope (urban_political late-run spawn/attrition) is resolved and
should be marked so in `docs/plans/audit_fix_plan.md`. The symptom attributed to P2-B for
`frontier_extended`/`frontier_living_world`/`wilderness_survival` in the 13-run corpus table was a
**misattribution** — it is actually the hazard-native-immunity bug class (already fixed in code,
not yet propagated to these worlds' compiled state). This is a distinct, already-diagnosed-elsewhere
root cause, not a new unknown, and not something this ticket's scope obligates fixing (per Out of
Scope: "Fixing any SimQ pillar's underlying scoring/emission logic discovered to be broken by the
new worlds" should be filed as a follow-up, and this is analogous — a pre-existing content/compile
gap, not new breakage caused by this ticket).

## UQ-1 Resolution — new compositions vs. rework existing early-terminating worlds

**Recommendation: prefer new compositions for filling shape/size gaps; treat
`frontier_extended`/`frontier_living_world`'s population-collapse bug as an explicit, separate
sub-blocker ticket — do not fold its fix into this ticket's world-authoring work.**

Rationale:
1. The "early termination" premise motivating UQ-1 does not hold as stated — these worlds do not
   terminate early (Finding 2). The real defect (Finding 3/4) is a population-collapse content/compile
   bug requiring (a) recompiling 8 stale worlds and (b) adding `hazard_kind` to 3 more modules — this
   is a well-scoped, independent unit of work matching this ticket's own Out-of-Scope pattern
   ("file a follow-up ticket instead").
2. Even after that fix, `frontier_extended`/`frontier_living_world` would still only diversify the
   COMBAT/NARRATIVE/PROGRESSION/WORLD signal at the 44–56 entity band — useful, but it does not by
   itself close the "no world between 32 and 44 entities" gap, nor does reworking these 2 worlds
   touch the currently-unused module families (`mountain_pass`/`river_crossing`/`nomadic_herd`/
   `settled_quarter`, `moon_cult_ruins`).
3. Reworking existing worlds trades effort against a *known-additional* content gap (3 modules need
   `hazard_kind` added) with no guarantee of a clean population curve afterward (needs re-verification
   post-fix); authoring new, smaller/targeted compositions from the already-diverse 20-module catalog
   is more directly aimed at the diversity gaps this ticket exists to close, and does not depend on
   an engine/content fix landing first.

**Concrete recommendation for the 2–4 new/extended worlds this ticket should add:**
- One new world in the **38–44 entity band** (fills the 32→44 gap) built from currently-anchored-corpus-adjacent
  modules plus at least one never-anchored module (e.g. `undead_battlefield` or `orc_clan_territory`)
  to add module diversity without inheriting `frontier_extended`'s full 8-module stale-compile risk.
  Must be freshly compiled (created after this ticket's work, so it inherits the hazard-kind fixes
  by construction) and must include `hazard_kind` on every non-zero-hazard region it introduces.
- One new small world in the **20–26 entity band using `highland_traverse`'s unused module family**
  (`mountain_pass`, `river_crossing`, `nomadic_herd`, `settled_quarter`) or a variant, to bring that
  content family into the anchored corpus (currently 0 anchor entries use it).
- Optionally extend `swamp_border_world` (26 entities, `sunken_swamp_border` — currently unanchored)
  with 1–2 more entities/regions and anchor it directly, since it already compiles cleanly with no
  hazard-kind gap reported (not independently re-verified in this investigation — recommend a quick
  re-run before anchoring, following the same checkpoint-sampling method used above for the other 3
  worlds).
- File a separate ticket for the `frontier_extended`/`frontier_living_world`/`wilderness_survival`
  recompile + 3-module `hazard_kind` fix (P2, `layer: world`), referencing this investigation's
  Finding 3/4 evidence, rather than doing it inside this ticket.

## UQ-2 Resolution — "good enough" target: proposed coverage matrix

Given the structural pillar-reachability constraints (Findings above — AGENCY/FACTION/INFORMATION/
SOCIAL are gated behind mechanisms only 2 worlds implement, and this ticket explicitly excludes
extending those mechanisms to new worlds), a coverage target must be scoped to what is achievable
without violating this ticket's own Out-of-Scope line.

**Proposed target — "shape coverage," not "pillar coverage":**

| Dimension | Target |
|---|---|
| Entity-count bands in anchored corpus | At least one anchored world in each of: <20, 20–35, 35–50 (currently: <20 has 1 [sandbox_world], 20–35 has 3, 35–50 has 0) |
| Region-count spread | At least one anchored world with ≥6 regions (currently max anchored region count is 4, `dungeon_crawl`) |
| Module-family coverage | Every one of the 20 modules appears in ≥1 anchored world at least once (currently 11/20 never appear) |
| COMBAT/NARRATIVE/PROGRESSION/WORLD | ≥2 anchored worlds of different entity-count bands producing non-C grades (already satisfied — do not regress) |
| ECONOMY/COGNITION | At least 1 anchored world outside `urban_political` demonstrating activation at long tick counts, if achievable without new flags (stretch goal, not a hard gate) |
| AGENCY/FACTION/INFORMATION/SOCIAL | Explicitly out of target for this ticket — tracked as a known, documented gap, not silently ignored (per ticket's Out-of-Scope) |

This is deliberately a **shape/content-diversity** target, not a claim that every pillar becomes
reachable everywhere — that would require reversing this ticket's own scope boundary. Acceptance
criterion 1 ("current corpus diversity audited and gaps documented") is satisfied by this document;
acceptance criterion 2 ("≥2 new/extended worlds") should be planned against the module-family and
entity-band gaps identified above, not against pillar-activation (which is separately gated).

## Risks and Open Questions

- The `frontier_extended`/`frontier_living_world` staleness fix (recompile + 3-module `hazard_kind`
  addition) is tempting to bundle into this ticket since the code path is well understood, but doing
  so risks scope creep into what the ticket's own template explicitly warns against ("do not silently
  work around it by only adding small worlds" — the corollary is also true: do not silently absorb an
  unrelated content-repair job into a corpus-diversity ticket). Recommend filing it separately and
  referencing it as a Related Ticket if the planner disagrees with deferring it.
- `swamp_border_world` was not independently re-verified for early-tick collapse in this
  investigation (time-boxed); if it is chosen as an extend-and-anchor candidate, re-run the same
  checkpoint-sampling method used for `frontier_extended`/`frontier_living_world`/`wilderness_survival`
  before committing anchors.
- No human decision is required to proceed with investigation-stage conclusions — UQ-1 and UQ-2 are
  resolved above with evidence. The one item that does warrant a planner/human check-in before
  implementation is whether to file the stale-compile fix as its own ticket now (recommended) or
  fold a minimal version into this ticket's scope — this is a scope-boundary call, not a technical
  unknown.

## Anti-Drift Hazards

- Any new world composition must be recompiled (assembly step) **after** this investigation's date
  so it does not silently inherit the stale-compile gap described in Finding 3 — verify
  `resolved/provenance_manifest.json::created_at` postdates 2026-07-01 for every new/re-anchored
  world.
- Any module reused from the "never anchored" list that declares `hazard_level > 0` must also
  declare `hazard_kind`, or its native population must not be entities without matching
  `hazard_immunities` — otherwise the new world will reproduce Finding 3's collapse pattern by
  construction.
- Do not anchor a new world's grades from a single seed/tick run — follow
  `TCK-20260702-SIMQ-EVAL-MATRIX`'s established multi-seed pattern for any world added to
  `grade_anchors.json`.
- If `docs/plans/audit_fix_plan.md`'s P2-B row is updated to "RESOLVED" based on this investigation,
  do not conflate it with the frontier_extended/frontier_living_world symptom — add a distinct note
  (or a new tracked item) for the hazard-kind staleness finding so a future reader does not assume
  P2-B's resolution also covers that world's population collapse.

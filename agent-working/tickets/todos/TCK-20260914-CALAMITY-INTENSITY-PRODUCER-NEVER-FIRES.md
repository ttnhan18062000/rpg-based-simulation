---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES
phase: open
date: 2026-09-14
tags: [world]
---

# TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES

## Title
`calamity_intensity` never left `0.0` in any region across a real 5000-tick run — the entire
calamity-intensity system (both its producer and its propagator) appears to be inert in practice,
not just the maturity-independent `world_boss` spawn path that consumes it

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Found while investigating `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`'s Finding 4/5.
A real, instrumented 5000-tick `Kernel.tick_once()` simulation against `frontier_living_world`
(seed=42), tracking `region.calamity_intensity` on every tick for every region, found it **never
moved off `0.0` for the entire run** — not "never crossed the 0.3 spawn-gate threshold," never
changed at all, in any region, at any tick.

`src/world/calamity.py` has two real (non-dead-code) mechanisms for producing/spreading
`calamity_intensity`:
- `CalamityService.apply_calamity_consequences()` — the sole producer: `+0.05` per `entity.kind ==
  "hero"` death specifically inside a `region.hazard_level > 0.5` region, capped at `1.0`.
- `CalamityPressurePropagator.propagate_seasonal()` — spreads *existing* intensity (above
  `PROPAGATION_THRESHOLD = 0.10`) to adjacent regions every `SEASONAL_PROPAGATION_INTERVAL = 500`
  ticks; it cannot create intensity from nothing.

If the sole producer never fires in a real run (no hero died in a `hazard_level > 0.5` region
during the 5000-tick probe — not separately confirmed, but consistent with the observed flat zero),
the propagator has nothing to spread regardless of how many propagation cycles pass. This is the
same silence-as-failure-mode shape found repeatedly this week (a 7th instance): a whole subsystem
that looks wired and tested in isolation, but whose only real trigger condition never occurs in
practice, so the system as a whole is functionally dead without anything erroring or looking broken
in a static read.

This is a separate, deeper finding than the `world_boss` spawn path's own gate
(`calamity_intensity > 0.3` at `tick % 5000 == 0`) — even if that gate's own interval/tick
requirement were made reachable, the intensity value it checks would still never be nonzero.

## Scope

> **SCOPE SUPERSEDED BY OWNER DECISION 10 / CATALOG RULE `ENV-06`, 2026-10-05.** The bullets below
> are kept as the record of the original diagnosis — they were a correct investigation of the wrong
> producer. Read this block first; where it conflicts with a bullet below, this block wins.
>
> Lane B's investigation (findings committed at `d2724b1bb`, no code change) established that
> `CalamityService.apply_calamity_consequences` has **zero callers**, and that nothing in Bible 05
> L457 or `environment.md:51` said what *raises* `calamity_intensity` — both only read it. The
> planner ruled against wiring the existing method, because doing so would invent the rule by
> implication and its only visible effect would be flipping
> `tests/architecture/test_calamity_intensity_producer_unwired.py` with no behavioural change. The
> question went to `world-rule-catalog-design`, which drafted four options; the owner chose one.
>
> **`ENV-06` (`docs/world_rules/space-environment/environment.md`, commit `043ebb30d`, parked on
> `origin/calamity-rule-decision`):**
> - Calamity intensity rises **only while a region stays above the instability threshold for a
>   sustained period**. The threshold reuses Bible 05 §2's `trauma_score > 50.0`.
> - It **decays slowly** once the region calms.
> - **No single event raises it directly** — not a death, not a hero's death, not one battle.
> - Trauma is the acute per-event measure; calamity measures its **persistence**. No double
>   counting, and "deaths raise calamity" is **explicitly not adopted**.
> - Window, rise rate, decay rate and cap are engineering choices, to be recorded in Bible 05 and the
>   parity ledger **at implementation**.
> - Seasonal propagation is kept.
> - `CALAMITY_RANDOM_CHANCE` **stays unwired**; any later probabilistic onset must be conditioned on
>   this escalation (`CAUSE-01`).
>
> **So the existing single-`kind=="hero"`-death method is NOT the producer to wire.** The producer is
> the escalation. `test_calamity_intensity_producer_unwired.py`'s welcome failure flips when that
> lands, legitimately.
>
> **Sequencing: `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` goes first.** `ENV-06` is
> observable only once trauma accumulates, and the Rule records that order deliberately. Do not start
> this ticket before that one lands.
>
> **WORLD BOSS IS DEFERRED** (owner, mid-decision, 2026-10-05). `ENV-06` does not list world-boss
> emergence as a consumer. The boss filter at `calamity.py:42` and the magical/demonic spawn riding
> on it (flag OFF) **stay untouched**. Implementing `ENV-06` must **not** use a boss spawn as
> evidence, and must neither tune nor retire the boss branch.
>
> **The owed evidence is a scenario, not a boss spawn:** a region held above threshold escalates; a
> single death spike does **not**; a calmed region decays. Three assertions.
>
> **Two stale claims to fix in the same pass.** `docs/world/ecology_and_calamity_contract.md:92`
> still reads "Hero death in a region with `hazard_level > 0.5` raises that region's
> `calamity_intensity` by **+0.05** per death. Intensity decays naturally if the region stabilises" —
> the first half is now **contradicted by `ENV-06`** and the second describes decay code that does
> not exist. The contract also claims calamity **increases** `trauma_score`, which
> `process_world_dynamics` does not do; that second claim is UNCONFIRMED beyond `calamity.py` itself
> and should be verified before being corrected or removed.
>
> **Registry:** `calamity_intensity`'s entry carries a pointer to rebind `implemented_by` once the
> producer exists. `registries/mechanisms.yaml` content is not this ticket's to edit — report the
> rebind to the planner.

- Confirm directly (not inferred) whether any hero ever died in a `hazard_level > 0.5` region
  during a real run of realistic length — check `region.hazard_level` distributions across the
  corpus's real worlds, and whether hero deaths in high-hazard regions are themselves rare/absent
  for a separate reason (e.g. heroes avoid high-hazard regions by design, or hazard levels are
  themselves miscalibrated/never reach 0.5).
- Determine whether the producer's trigger condition (`hero` kind + `hazard_level > 0.5`) is too
  narrow to ever fire in practice, and if so, propose a realistic wiring fix — a broader trigger
  condition, a lower hazard threshold, or an additional real producer — as a wiring fix, not a
  balance/tuning change.
- Check whether `region.hazard_level` itself is a live, populated stat or another dead/always-zero
  field — if hazard levels themselves never exceed 0.5 anywhere in the corpus, that's the real root
  cause and this ticket's scope should include it.
- Investigation-first is not required to be pre-registered as blocking here (no explicit "no
  implementation until reviewed" instruction was given for this ticket specifically) — but given
  this affects a whole subsystem, bring findings + a proposed fix for review before implementing,
  following this arc's established pattern for reachability defects of this size.

## Out of Scope
- The `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY` maturity/trauma gate itself — a
  separate, already-being-fixed reachability defect, not this ticket's concern.
- Balance/tuning of the `0.05`/`0.15`/`0.10`/`0.3` constants themselves, beyond what's needed to
  make the producer fire at all in a realistic run.

## Acceptance Criteria
- [ ] A real, evidence-backed root cause for why `calamity_intensity` never moves in practice —
      either the trigger condition is too narrow, or `hazard_level` itself never crosses the
      required threshold, or both.
- [ ] A proposed wiring fix (not yet built without review) that would make at least one region's
      `calamity_intensity` demonstrably nonzero within a realistic corpus run length.
- [ ] Findings brought to peer/user review before any implementation, matching this week's
      established pattern for reachability-defect tickets of this size.

## Related Tickets
- `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY` (the investigation that surfaced this)
- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` (names the general pattern this ticket is a
  third confirmed instance of: mechanics whose preconditions depend on world geometry/composition
  that nothing validates)
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (sibling instance — the dangling-
  region-reference and spatial-isolation findings)

## Related Docs
- `docs/plans/deferred_tuning_decisions_register.md` (candidate for a new entry once root cause is
  confirmed)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/world/calamity.py` (`CalamityService.apply_calamity_consequences()`,
  `CalamityPressurePropagator.propagate_seasonal()`)
- Wherever `region.hazard_level` is set/computed (not yet located — first investigation step)

## Assumptions / Open Questions
- Whether hero deaths in high-hazard regions are rare because of correct emergent behavior (heroes
  successfully avoid dangerous regions) versus a defect (hazard levels miscalibrated, or heroes
  never enter high-hazard regions at all due to an unrelated routing issue) is not yet known.

## Implementation Notes
**2026-09-15, checked directly against the "mechanics whose preconditions depend on world
geometry that nothing validates" pattern named in `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-
ACCUMULATES` — confirmed as a third instance, and a doubly-clean one.**

**First, confirmed `region.hazard_level` itself is a live, real, populated stat** — ruling out
that part of the ticket's own Scope immediately. Grepped every `world_modules/*.yaml`: real,
nonzero hazard levels exist throughout the corpus (`bandit_road`: 2.0, `goblin_camp`: 3.0,
`undead_battlefield`: 4.0, `moon_cave`: 4.0, etc.) — several well above the `> 0.5` threshold this
ticket's own producer checks. Not the root cause.

**Second, checked whether any `entity.kind == "hero"` entities exist at all in
`frontier_living_world`** (the exact world this ticket's own 5000-tick probe used) — compiled it
directly and inspected the real entity roster. **Zero.** `frontier_living_world`'s own module
composition (`frontier_village_core`, `wolf_den_near_forest`, `goblin_camp_conflict`,
`old_mine_resource_loop`, `bandit_road_trade_pressure`, `undead_battlefield`,
`trading_company_hub`) does not include `hero_adventurers` — the only module in this corpus that
produces `kind == "hero"` entities at all. Every other entity kind present
(`worker`/`guard`/`merchant`/`blacksmith`/`scout`/`raider`/`leader`/`predator_hunter`/`sentinel`/
`alpha`) is a non-hero role. **The producer's trigger condition cannot fire in this world for any
value of `hazard_level`, because the required entity kind never exists there at all** — not a
spatial-isolation question at all, an even more basic "the precondition's other half was never
composed into this world" gap.

**Third, checked a world that DOES compose `hero_adventurers`** (`crowded_frontier`) to see
whether the pattern is spatial isolation there instead, matching the lair/merchant instances:
confirmed 3 real `hero`-kind entities exist, but `hero_adventurers.yaml`'s own
`population_recipes` hardcode `spawn_region: "hometown"` for **all three**, unconditionally —
`"hometown"` (`frontier_village_core`'s own region) has `hazard_level: 0.0`. Even in a world where
heroes exist at all, their own module never composes them anywhere near a `hazard_level > 0.5`
region at spawn. Whether AI-driven wandering/questing later moves a hero into a hazardous region
during a real run is a separate, unconfirmed question — but the starting composition never puts
them there, and this session did not trace whether in-run movement closes that gap.

**Conclusion: this is a real, third confirmed instance of the named pattern, and arguably the
cleanest one yet** — two independent, compounding reasons (the entity kind the mechanic needs
often doesn't exist in a world's composition at all; and where it does, its own module hardcodes
it away from every region the mechanic needs it to visit). This gives the pattern three real
instances across three separate mechanics (Lair-occupant spawning, cross-faction combat volume,
calamity-intensity production), each with a distinct specific composition gap but the same shape:
a mechanic's precondition depends on spatial/compositional co-location that nothing in the compile
path validates.

**Parked here, per the same investment cap applied to the sibling tickets in this cluster — not
proposing or building a fix.** Two candidate directions, both design decisions:
1. Compose `hero_adventurers` (or an equivalent hero-kind population) into more worlds, and/or
   change its own `spawn_region` to include (or patrol into) at least one real hazard-bearing
   region, rather than hardcoding all three heroes to `"hometown"`.
2. Broaden the producer's own trigger condition (a different/additional entity kind, a lower
   hazard threshold, or a different triggering event entirely) so it doesn't depend on a specific
   role existing in a specific place — the mechanic-design-level fix, mirroring the lair ticket's
   own second candidate direction.

**2026-09-20, a stronger finding, correcting this ticket's own prior framing**
(`TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION`, batch 2 of the
mechanism-registry unbound-claims program). While attempting to bind `calamity_intensity`'s own
registry entry to `CalamityService.apply_calamity_consequences()`, `mechanism_state_caller_check.py`
flagged zero real callers for the method entirely. Re-checked directly: `grep -rn
"apply_calamity_consequences" src/` finds only its own definition and one unrelated *comment* in
`displacement.py` — never a real call, anywhere, under any circumstances.
`CalamityService.process_world_dynamics()` (the method this ticket's own investigation never
separately checked, and the one actually called from `world_dynamics.py:133`) only *reads*
`region.calamity_intensity` for boss-spawn region selection — it never calls
`apply_calamity_consequences()` or otherwise writes the stat.

**This means the real defect is one level more fundamental than this ticket's own 2026-09-15
conclusion assumed.** The 2026-09-15 investigation correctly found that the producer's own trigger
condition (hero-kind death in a `hazard_level > 0.5` region) never fires in practice — but that
finding implicitly assumed the producer is at least *reachable*, i.e. that something calls
`apply_calamity_consequences()` and lets its own internal condition check run and fail. That is not
what's happening: nothing calls the method at all, so its internal trigger condition is never even
evaluated. **This is a wiring gap (dead code, zero callers), not a data/composition gap
(reachable code, unsatisfiable precondition)** — closer in shape to `resource_harvesting`'s own
already-registered `orphan` classification than to the "correct code, starved by world data" family
this ticket was filed under.

**Both findings are real and compound, not contradictory**: even if `apply_calamity_consequences()`
were wired to a real caller, the 2026-09-15 finding shows its own trigger condition still wouldn't
fire in the exact worlds tested (no hero-kind entities, or heroes never composed near hazard
regions). Fixing the wiring gap alone would not be sufficient; the composition gap this ticket
already found would still need addressing. This ticket's own Scope should be read as now covering
both: (1) NEW — wire `apply_calamity_consequences()` into a real caller (or confirm deliberately
retired/superseded), (2) EXISTING — the composition gap already found and parked below. Not
resolved here; both findings are reported for the roadmap session, per the same investment-cap
discipline already applied to this cluster.

### 2026-09-30 — verdict recorded via `TCK-20260929-UNREACHABLE-CLASSIFY-WAVE-CONFIRM` (epic `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION`, child `T04`): `DEFECT`, from PR #258 — recorded, not re-investigated

**Source of the verdict.** `TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING` (`J1`), merged in PR #258
(`35806b1ed`); exit claim `DEFECT` at `agent-working/stored_artifacts/TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING/investigation.md`
(line 55) and that ticket's Completion Summary: `CalamityService.apply_calamity_consequences()` has zero real
callers, so the producer of `calamity_intensity` can never run. The wave recorded the exit claim as a
**recommendation only**; the registry-side write is routed to
`TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION`, which owns that entry. Nothing in this epic
touches `registries/mechanisms.yaml`.

**One freshness check, not a re-derivation.** At branch tip `3dbdff48a` the only references to
`apply_calamity_consequences` are its definition (`src/world/calamity.py:80`), one unit test
(`tests/unit/world/test_calamity_raid.py:88`) and the wave's own pin
(`tests/architecture/test_calamity_intensity_producer_unwired.py`), which fails if a production caller appears.
`calamity.py` has no commit since the wave. The verdict has not drifted.

`T01` lists this ticket by shape (zero-caller group) but does **not** classify it; this note is its single
disposition.

### 2026-10-05 — `rpg-implementer-2` re-check before any build: stopped at the rule owner, nothing implemented

Dispatched with "first locate where `region.hazard_level` is set". Located, and re-verified the producer on the current tree:
- **`hazard_level` is set in three places:** authored on the region spec and copied by `src/worldbuilding/compiler.py:476`
  (`hazard_level=getattr(r_spec, "hazard_level", 0.0)`); generated worlds scale it by `danger_level`
  (`src/worldgeneration/generator.py:107,114`); and `src/engine/world_dynamics.py:119-123` raises it by `+0.01`
  (cap `1.0`) **only while the region's trauma exceeds 50**. Authored values above `0.5` are common (the 2026-09-15
  note), so the `> 0.5` half of the producer's condition is reachable from authoring alone.
- **The runtime growth path is itself starved by the sibling ticket:** trauma above 50 is what
  `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` says never happens, so hazard does not grow at runtime either.
- **Producer still has zero callers:** `grep -rn apply_calamity_consequences src/` returns only its definition
  (`src/world/calamity.py:80`) and one comment (`src/world/displacement.py:27`).
- **No governing rule exists for the producer.** `docs/mechanics/05_world_evolution.md` mentions `calamity_intensity` only
  as the `> 0.3` spawn filter (L457); `docs/world_rules/space-environment/environment.md:51` only *reads* it for the
  hazard drain; no accepted catalog Rule says what raises it. So "wire the dead method" would be inventing a
  world-semantics rule, and wiring the narrow `hero death in hazard > 0.5` trigger would still leave it starved in the
  worlds measured (no heroes composed, or heroes hard-coded to a zero-hazard `hometown`).
- `tests/architecture/test_calamity_intensity_producer_unwired.py` is a deliberate "welcome failure": wiring a caller
  flips it and obliges the registry-label correction owned by `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION`.

Decision requested from the rule owner (via the planner), per this ticket's own acceptance criteria: define what raises
`calamity_intensity`, or retire the chain. Options and a recommendation are in the message that accompanied this note.
No code was changed.

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
**Parked by explicit user decision, not abandoned or unresolved.** The root cause is fully known
and doubly confirmed: the reference world the original probe used has zero `hero`-kind entities
composed into it at all, and even a world that does compose heroes hardcodes their spawn region
to a zero-hazard area. Both facts confirmed by direct inspection of the real compiled entity
roster and the authored content, not inferred. Two real candidate fix directions are recorded
above. The user's explicit decision, given the investment cap on this cluster, was to record the
finding and not build a fix now — "we know exactly why this doesn't fire and chose not to fix it
now" is the accurate state, distinct from "this doesn't fire and we don't know why." See
`docs/plans/world_composition_precondition_gap_finding.md` for the durable record of this finding
alongside its two sibling instances.

**Status update, 2026-09-20**: a stronger, compounding finding was added above (zero real callers
for the producer at all, not merely an unreachable trigger condition) — still parked, not fixed,
but this ticket's own eventual scope needs to cover both the wiring gap and the composition gap
when picked up, not the composition gap alone.

**Verdict as of 2026-09-30: `DEFECT`** (from PR #258, recorded not re-investigated); see Implementation Notes. Still `OPEN`.

---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER
phase: open
date: 2026-10-05
tags: [world, documentation]
---

# TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER

## Title
`allow_overlapping_regions` is declared, set to `false` by all 24 corpus worlds, and read by no
production code — the Mechanics Bible's "strictly disjoint by default, enforced" claim is enforced
nowhere, and `frontier_living_world` resolves with 9 overlapping region pairs

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found while answering a world-semantics question `rpg-implementer-2` raised when closing
`TCK-20260915-WORLDBUILDING-DUPLICATE-REGION-ID-ACROSS-MODULES` as stale-premise. It asked whether
overlapping region bounds are intended or should be a rule. The answer turned out to be that the
repo already decided — and then never implemented the decision.

**What the Bible says.** `docs/mechanics/06_worldbuilding_foundation.md:32`:

> **Overlap Policy**: By default, regional bounds are strictly disjoint (no overlapping). This is
> enforced unless `allow_overlapping_regions` is explicitly enabled in the validation spec.

**What the code does.** `allow_overlapping_regions` exists at
`src/worldbuilding/schema.py:245` as `bool = Field(False, ...)` and **nothing reads it.** A sweep of
`src/`, `tools/` and `codebase/` finds exactly two non-test occurrences: that declaration, and
`src/lab/workflows/generate_simulation_setup.py:332` which *writes* it into a generated
`ValidationSpec`. There is no overlap check anywhere in `src/worldbuilding/` or `src/worldassembly/` —
`grep -rniE overlap` over both packages returns only the `Field` description itself. Every other
occurrence in the repo is a test asserting the field's own value, a lab fixture, or
`tests/unit/lab/test_mutation_engine.py` using `validation.allow_overlapping_regions` as a mutation
*target*, which exercises the mutation engine rather than any validation.

**The measured consequence.** All 24 `data/worlds/*/resolved/world.resolved.yaml` set
`allow_overlapping_regions: false`. `rpg-implementer-2` measured the resolved
`frontier_living_world` and found **9 overlapping region pairs** — among them
`bandit_road`/`trading_hometown`, `trading_hometown`/`near_forest`, `near_forest`/`wolf_den`,
`goblin_camp`/`haunted_battlefield`. So a world that declares overlap forbidden assembles with nine
overlaps and nothing notices.

**This is not the region-id defect.** Region *ids* are genuinely safe: `resolver.py:359` and
`schema.py:319` both raise on a duplicate id, and #335's namespace prefixing means
`trading_company_hub` composes as `trading_hometown`, so all 24 compositions assemble with 0
collisions. The ids are distinct; the *geometry* overlaps. Two separate properties, and only the
first one is enforced.

**Why P1 rather than a tidy-up.** A declared validation knob that nothing reads is indistinguishable
from a validation that passes, which is precisely the "executes without effect" shape the owner moved
into foundation scope (`roadmap.md` §8 work-order item 6 addendum). Worse than the three instances
cited there: those mechanisms at least *ran*. This one never runs and its `false` value is read by
nobody, so every world in the corpus carries a false assurance.

## Scope
1. Establish and record whether anything in the simulation depends on a position belonging to **at
   most one** region. `RegionState` lives in `src/core/state.py`; find every place that maps a
   position to a region and record what each does when two regions contain the point — first match,
   last match, or undefined. **This is the question that decides how serious the overlap is**, and it
   is not answered yet. Do this before proposing any fix.
2. Record what the Bible already defines for the overlap case so it is not re-derived:
   `06_worldbuilding_foundation.md:37` gives a paint-order rule — `WorldSpec.regions` is iterated in
   declaration order and each region's terrain write is a plain dict-key overwrite, so a later region
   unconditionally overwrites an earlier one for a shared tile. So overlap is *contemplated* for
   terrain and declaration order is the documented priority mechanism. Whether that rule extends to
   anything other than terrain is open.
3. Reconcile doc and code in whichever direction the owner chooses (see Assumptions — **this ticket
   must not pick the direction unilaterally**). Either implement the enforcement the Bible claims, or
   amend `:32` to state what is actually true and record the change in
   `docs/guidelines/intentional_divergences.md`.
4. Whichever direction is chosen, `allow_overlapping_regions` stops being a dead field: it is either
   read by a real check, or removed from the schema and from the 24 resolved specs with a note saying
   why.
5. Update the parity ledger. `docs/parity_ledger/substrate.yaml` is the subsystem file; add or correct
   the entry covering the overlap policy, since the current state is a documented-but-absent
   behaviour.

## Out of Scope
- Region **id** collisions and the namespace-prefix rule. Settled by #335; the doc gap for it is
  `TCK-20261005-ASSEMBLY-CONTRACT-OMITS-REGION-ID-COLLISION-RULE`.
- Correcting the bounds of any specific corpus world. That is a content change whose blast radius is
  every measurement taken on that world, and it is gated on Scope 3's direction.
- `src/rendering/` and the visual consequence of overlapping terrain. Unowned area; route to the
  planner if it comes up.
- The lab mutation engine's use of the field as a mutation target.

## Acceptance Criteria
- [ ] Scope 1's position-to-region audit is recorded in `investigation.md`, naming every call site and
      its behaviour on an ambiguous point. "Nothing maps a position to a region" is a valid and very
      important answer if true.
- [ ] The chosen direction is the **owner's**, recorded with who decided and when, before any code or
      Bible edit lands.
- [ ] `allow_overlapping_regions` is either read by a real check or gone. It does not survive this
      ticket as a declared-and-unread field.
- [ ] If enforcement is implemented: the 9 `frontier_living_world` pairs are resolved or the world
      explicitly opts in, and **every** corpus world is checked, not just that one — a check that
      aborts assembly on worlds the whole corpus is measured against is a blast radius that must be
      reported before it lands, not discovered by CI.
- [ ] If the Bible is amended instead: `:32` states what the code does, the divergence is recorded in
      `intentional_divergences.md` with a rationale class and a verification path, and `:37`'s
      paint-order rule is checked for consistency with the amended text.
- [ ] `docs/parity_ledger/substrate.yaml` reflects the outcome.
- [ ] `make knowledge-index-update` run, since `docs/` changed.

## Related Tickets
- `TCK-20260915-WORLDBUILDING-DUPLICATE-REGION-ID-ACROSS-MODULES` — closed stale-premise by #335's
  namespacing; this ticket is the residue its closure surfaced, and is **not** the same defect.
- `TCK-20261005-ASSEMBLY-CONTRACT-OMITS-REGION-ID-COLLISION-RULE` — the sibling doc gap.
- `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION` (#335) — established the namespace rule.
- `TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP` — this is a fifth instance of the
  "declared but has no effect" shape and a candidate validation case for that instrument. Not a child
  of it.

## Related Docs
- `docs/mechanics/06_worldbuilding_foundation.md:32` (the claim), `:37` (the paint-order rule), `:114`
  (which lists "out-of-bounds spatial overlaps" as an ERROR that aborts compilation — check whether
  that refers to this policy or to something else; the two may already contradict each other)
- `docs/world/assembly_contract.md` — assembly-time collision contract
- `docs/parity_ledger/substrate.yaml`
- `docs/guidelines/intentional_divergences.md`

## Related Stored Artifacts
_(none yet — Scope 1's audit will produce the first)_

## Related Code Areas
- `src/worldbuilding/schema.py:245` — the unread field
- `src/worldbuilding/resolver.py:359`, `src/worldbuilding/schema.py:319` — the id-collision raises,
  for contrast with the absent geometry check
- `src/worldbuilding/compiler.py::WorldCompiler` — where a check would attach
- `src/core/state.py::RegionState` — **contested surface**, and currently held in part by Lane A for
  an unrelated region of that file. Claim before editing.
- `src/lab/workflows/generate_simulation_setup.py:332` — the only non-test writer

## Assumptions / Open Questions
- **The fix direction is the owner's, not this ticket's.** Implementing the enforcement the Bible
  claims would abort assembly on at least `frontier_living_world`, i.e. on a world the corpus is
  measured against — a blast radius that may be larger than the defect. Amending the Bible instead is
  cheap but ratifies overlapping regions as world law.

  **Owner decision, 2026-10-05: audit first, decide after.** Put to the owner by the planner with
  four options (audit first / enforce / amend the Bible / route to the rule catalog). The owner chose
  to see Scope 1's position-to-region audit before picking a direction, on the ground that it is the
  one fact that changes the answer: if nothing in the simulation depends on a position belonging to
  at most one region, overlap is near-harmless and amending `:32` is right; if the kernel resolves
  "which region is this" anywhere, this is a live correctness bug and not a documentation defect.
  **So Scope 1 is the whole of the first pass. Do not propose a direction in the same breath as the
  audit — report the audit, then ask.**
- **RESOLVED, 2026-10-05: the double-count hypothesis below is FALSIFIED, and overlap's real measured
  effect is the opposite — it *shadows* regions.** `rpg-implementer-2` compared the two trauma series
  tick-by-tick over 10000 ticks (`frontier_living_world`, seed 42, `PROD_SMALL`) rather than the
  maxima. The series are **not** identical (max |diff| 2.0005) and the two regions **never jump on the
  same tick**: each has exactly 116 jumps totalling 116.9, every `goblin_camp` jump matched by an equal
  `bandit_road` jump exactly **one tick later**, and the deaths on those ticks are **distinct
  entities**, each counted once. So no shared accumulation. My hypothesis was wrong and the
  discriminator settled it.

  **Scope 1's central question is therefore already answered: FIRST MATCH.**
  `SpatialQueryService.get_region_at` (`src/engine/spatial_query.py:168-190`) walks the spatial index
  cell's region list and `return`s the **first** region whose half-open bounds contain the point. With
  overlap, exactly one region is credited and the rest get nothing.

  **The measured consequence, on `frontier_living_world` over 10000 ticks:** `near_forest` had **118**
  deaths inside its bounds, `wolf_den` **93**, `trading_hometown` **15** — and **all three ended at
  `trauma_score` 0.0**. Death positions genuinely lie in several overlapping regions at once (one death
  at tick 3 was inside `bandit_road`, `near_forest` and `wolf_den` by bounds). Overlap does not inflate
  a region's trauma; it **starves the shadowed region of its own events**.

  That is a wrong-world-truth defect, not untidiness, and it **reaches the lair gate**: a lair region
  shadowed by a neighbour can never accrue the trauma its own gate reads. See the `(e)` link below.

  Two caveats the measurement names and this ticket keeps: the shadowing was **inferred** from zero
  trauma beside deaths-in-bounds using a closed-bounds check against the lookup's half-open bounds, so
  the counts are approximate and **no individual lookup was traced**. Scope 1 should trace one.

- **CONFIRMED by cause-and-credit disambiguation, 2026-10-05. Shadowing is real; this is a
  wrong-world-truth defect and the priority stands at P1.** The shadowing reading above had a rival
  explanation — the separately-discovered passive-death gap, where a `PassiveDeathCause` death carries
  no `combat.alive_set is False` and so adds no trauma regardless of credit. `rpg-implementer-2` ran
  one pass recording, per death, the regions whose bounds contain it, the region `get_region_at`
  credits, **and** the lifecycle cause (`frontier_living_world`, seed 42, `PROD_SMALL`, 5000 ticks,
  141 deaths — a separate, shorter run than the 10000-tick one, so counts are about half the earlier
  118/93/15):

  | region | deaths in bounds | credited to | causes |
  |---|---|---|---|
  | `near_forest` | 51 | `bandit_road` 49, self 1, `trading_hometown` 1 | HAZARD 48, STARVATION 3 |
  | `wolf_den` | 46 | `bandit_road` 30, `goblin_camp` 14, `near_forest` 1, `trading_hometown` 1 | HAZARD 41, DEFEAT 1, STARVATION 4 |
  | `trading_hometown` | 11 | `bandit_road` 10, self 1 | HAZARD 10, STARVATION 1 |

  **HAZARD deaths do carry `alive_set False` and do add trauma**, and they are the overwhelming
  majority here — so the passive-death gap does **not** explain these zeros. The deaths are credited
  to an overlapping **earlier-declared** neighbour. All three regions end at `trauma_score` 0.0 while
  `bandit_road` and `goblin_camp` end at 47.1.

- **The inverse consequence, which matters more than the zeros: `bandit_road`'s trauma is INFLATED by
  deaths that are not its own.** Its ~47 is not "about 50 deaths in `bandit_road`"; it is its own
  deaths plus those shadowed from `near_forest`, `wolf_den` and `trading_hometown`. That refines the
  earlier 116-jumps reading, and it has a consequence nobody has drawn yet:

  > **Catalog Rule `ENV-06` reuses `trauma_score > 50.0` as its instability threshold, and the
  > measurement that showed the threshold IS reachable (`bandit_road` crossing 50 at tick ~5211,
  > reaching 111.0 by tick 10000) was taken on the inflated value.** Fixing overlap redistributes
  > that trauma across four regions instead of concentrating it in one — so **`ENV-06`'s threshold may
  > become unreachable again once this ticket lands**, and the "nothing needs re-deciding on the
  > threshold" conclusion of 2026-10-05 is **provisional on this defect persisting.** Whoever fixes
  > overlap must re-run the trauma measurement and report whether any region still crosses 50, and
  > tell the planner so the owner can be told if it does not. Do not treat `ENV-06` as settled.

- **A second bounds defect found in the same run, unexplained: 20 of 141 deaths (14%) are credited to
  NO region at all.** `get_region_at` returned `None`, so their trauma is lost entirely — neither
  shadowed nor recorded. `rpg-implementer-2` did not diagnose it; its candidates are the half-open
  upper bound (`x_min <= pos < x_max`, so a death exactly on a region's far edge falls out) and the
  global-bounds quick exit at `spatial_query.py:173-176`. **Add this to Scope 1**: it is the same
  family (bounds handling losing authoritative events) and may be cheaper to fix than overlap itself.

- **Measurement caveats carried from the source, both real:** positions are **end-of-tick**, not the
  tick-start position the trauma block actually uses; and the credited region was inferred by calling
  `get_region_at` on that end-of-tick position rather than by tracing the block's own call. Neither
  undermines the direction of the finding — a 49-of-51 misattribution rate is not a rounding artifact
  — but Scope 1 should still trace one real call.

- **New sub-question raised by that answer, and it is sharp.** `get_region_at` returns the first match
  in the **spatial index cell's** list order. Bible `06_worldbuilding_foundation.md:37` states that for
  overlapping regions **declaration order** is "the deliberate priority mechanism" for terrain writes.
  **Does the index's order equal declaration order?** If it does not, the Bible's documented priority
  mechanism does not govern region *lookups* at all, and which region is credited for a death is
  deterministic but arbitrary. Answer this in Scope 1 — it decides whether shadowing is a documented
  consequence authors can control or an undocumented one they cannot.

- **Superseded hypothesis, kept as the record.** The paragraph below was my reading of the same
  measurement before the series comparison existed. It was wrong, and the shape of the error is worth
  keeping: two regions holding equal *maxima* looked like shared accumulation and was in fact a
  mirrored death pattern one tick apart. `rpg-implementer-2` also flagged, and did **not** explain, a
  periodic death pattern roughly every 300 ticks (entities 52/53 and 54/55 dying at ticks 302/303 and
  602/603, with no check of whether they die on the tick they spawn). Treat that as an unexplained
  observation, not a finding — it is not this ticket's subject.

- ~~**A candidate measured consequence on a durable field — 2026-10-05, UNVERIFIED, and it would change
  this ticket's priority if it holds.**~~ `rpg-implementer-2`, measuring trauma for
  `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`, found `bandit_road` and `goblin_camp` on
  `frontier_living_world` reading **exactly the same** `trauma_score` max of **47.1** at 5000 ticks.
  Its own hypothesis, which it flagged as unverified and did **not** check: their bounds overlap, so
  **one death counts in both regions**. Two regions holding bit-identical values for a field driven by
  per-event accumulation is not what independent accumulation looks like.

  If that holds, overlap is not an untidy-geometry question — it **corrupts a durable, authoritative
  field** that `world_dynamics.py:119-123` reads to drive `hazard_level`, that catalog Rule `ENV-06`
  reuses as its instability threshold, and that the lair-spawn gate reads at `8.0`. **This is Scope 1's
  first and cheapest check**, and it has a clean discriminator: are the two regions' trauma series
  identical tick-by-tick (shared accumulation), or merely equal at the maximum (coincidence)? Sample
  both per tick and compare the series, not the maxima.

  Do not treat it as established until that is done — it is a peer's unverified hypothesis about its
  own measurement, and the equality may be an artefact of the death-attribution path rather than of
  geometry. But if confirmed, raise this ticket's priority and say so, because a double-counted
  per-event measure is a wrong-world-truth defect rather than a missing validator.
- One concrete consumer to include in Scope 1, which is not obvious from a grep for "region":
  `SocialComponent.regional_reputation` is `Dict[RegionID, float]` (`src/core/models/social.py:48`)
  and is already in both the canonical dict (`src/core/state.py:987`) and the replay fingerprint
  (`src/replay/fingerprint.py:72`). Nothing produces a delta today, so the map is empty and
  contributes nothing — but it is a *region-keyed* durable field on the determinism surface, so if
  narrower reputation scopes are ever built (parked by owner decision 4, 2026-10-05) they will need
  exactly the position-to-region answer this audit produces. Record it as a future consumer, not a
  current one.
- No accepted world-rules catalog Rule governs region-bounds geometry. Checked
  `docs/world_rules/places-culture/` and the `PLACE-*`/`SETT-*` families: nothing addresses extent or
  overlap. So the Bible is the authority here and nothing outranks it — but that also means the
  question has never been put to the catalog, and arguably should be.
- The 9 overlapping pairs are `rpg-implementer-2`'s measurement of the resolved
  `frontier_living_world`. Reproduce it before building on it, and state the commit — the resolved
  specs changed in #335.
- Whether `:114`'s "out-of-bounds spatial overlaps" ERROR is the same policy under a different name is
  unchecked. If it is, the Bible contradicts itself in one chapter and that is its own small finding.

## Implementation Notes
_(not started)_

### 2026-10-05 — Scope 1 audit by `rpg-implementer-2`: findings only, no direction proposed

Read-only. All simulation numbers are real `Kernel.tick_once()` runs, `PROD_SMALL`, seed 42.

**Headline (sets this ticket's priority): one first-match lookup silently decides roughly 40 subsystems' notion of where things are.**
`SpatialQueryService.get_region_at`, reached mostly through `LegalityServiceV2.get_region_for_position`, is the only live position-to-region
lookup, and every consumer of it credits only the **first-declared** region at an ambiguous point: trauma, influence (`influence.py:42,103`),
ecology, spawn, camps, displacement, creature territory, boss, routine, market, vacancy, coming-of-age, goal scorers, lead location,
`apply_plan`, legality and movement (about 40 call sites, table below). The trauma shadowing measured on `frontier_living_world` is one
visible instance of that, not the whole of it.

**1. Position-to-region lookups (src/, excluding api/).** Five implementations exist; one is the live path.
| function | bounds | on ambiguous point | outside all regions | production callers |
|---|---|---|---|---|
| `SpatialQueryService.get_region_at` (`spatial_query.py:168`) | half-open `[min,max)` | **first** match in the grid-cell list; that list is built from `state.regions` insertion = declaration order | `None` | 7 direct, plus the delegation below |
| `LegalityServiceV2.get_region_for_position` (`legality.py:46`) | delegates to the above | same | `None` | **~35**: camp, spawn, calamity, ecology, displacement, influence, creature_territory, boss, routine, market, vacancy, coming_of_age, goal scorers, lead_location, apply_plan, legality, movement |
| `WorldDynamicsSystem._get_region_for_pos` (`world_dynamics.py:306`, the trauma writer) | delegates to the first | same | `None` | 2 (hazard loop L33, trauma block L66) |
| `DomainView.get_region_for_position` (`engine/domain/view.py:49`) | **closed** `[min,max]` | first match in `state.region_list` / `state.regions` order | `None` | `get_region_trauma` (the trauma **readers**: goal scorers, `tactical.py`, `shop.py`, `cognition.py`), plus a cache-warm call at `executor.py:281` |
| `RegionService.find_region_at` (`world/regions.py:16`) | **closed** | first match | **nearest region centre** (never `None`) | **none** |
So essentially one lookup governs ~40 consumers, and **every one of them credits only the first-declared region at an ambiguous
point**: trauma, but also influence (`influence.py:42,103`), ecology, spawn, camps, sovereignty-adjacent reads. The trauma writer (half-open)
and the trauma readers (closed) use different boundary conventions for the same field; that is a code finding, **not measured** to
differ in a run. `RegionalSovereigntyService` (`regional_sovereignty.py:46,67`) calls `.id` on a lookup that can be `None`, but nothing calls
that class, so it is latent.

**Separate defect, independent of overlap: the trauma writer and its readers disagree about region membership at a boundary.** The writer
(`WorldDynamicsSystem._get_region_for_pos` -> `SpatialQueryService.get_region_at`) uses **half-open** `[min,max)` bounds; the readers
(`get_region_trauma` -> `DomainView.get_region_for_position`, used by goal scorers, `tactical.py`, `shop.py`, `cognition.py`) use **closed**
`[min,max]` bounds. One field, two membership conventions. It would survive whatever this ticket decides about overlap. Not measured to differ in a run.

**Dead and latent paths, recorded so they are not rediscovered (recorded here, not in `TCK-20261005-WORLD-ASSEMBLY-LATENT-AND-DEAD-PATHS`):**
- `RegionService.find_region_at` (`src/world/regions.py:16`): closed bounds **plus a nearest-region-centre fallback** (never `None`), zero callers. That
  fallback is a **third membership convention** alongside the half-open and closed lookups.
- `RegionalSovereigntyService` (`src/world/regional_sovereignty.py:46,67`) calls `.id` on a lookup that can return `None`; nothing calls the class, so it is latent.

**2. One real trauma-block call, traced** (`frontier_living_world`, 1,500 ticks, `_get_region_for_pos` wrapped, call site identified by
line, compared to the trauma delta that landed): at state tick 3 an entity at `(87.0, 50.0)`, a point inside `bandit_road`, `near_forest` and
`wolf_den` by bounds, goes through the trauma block's lookup, which returns `bandit_road`; the next tick's delta is `bandit_road +1.0` and
nothing for the other two. Of 30 trauma-block lookups in the run, 12 hit a point lying in more than one region and **all 12 returned
the first-declared region**; 10 of 30 returned `None`. This removes the "inferred from an end-of-tick position" caveat on the 49-of-51
finding for this mechanism, and it uses the tick-start position the block really uses.

**3. Deaths credited to no region: explained, and mostly not this ticket's.** `frontier_living_world`, 5,000 ticks, 141 deaths: **20 (14%)** are
credited to no region on `origin/main` (`94f7a3fe3`); 10,000 ticks: 23 of 275 (8%). They lie outside every region even under a closed-bounds test,
clustered around the map origin (`(5,2) (3,3) (6,8) (0,1) (1,-1) (-3,0) (9,10)`), 10 `DEFEAT` and 10 passive `STARVATION`. My two original
candidates (far-edge half-open bound, global-bounds quick exit) were wrong, and `town_center` is `(25,25)` so it is not a default town centre.
**Cause, tested (suggested by the planner): the four hardcoded `(0.0, 0.0)` retreat/wander targets in `src/engine/tactical.py`**
(`:141`, `:247`, `:483`, `:542` on `main`) that `TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN` removes in PR #342.
Same world, seed and tick count, three trees:
| tree | deaths | credited to no region | near origin | causes of the uncredited |
|---|---|---|---|---|
| `main` `94f7a3fe3` | 141 | **20** | 20 | 10 DEFEAT, 10 STARVATION |
| Lane A tip `1cadb5fa1` (based exactly on `94f7a3fe3`) | 141 | **1** | 0 | 1 DEFEAT |
| Lane A tip with **only** `src/engine/tactical.py` reverted to `main` | 141 | **21** | 21 | 10 DEFEAT, 11 STARVATION |
The third row isolates the effect: with the rest of Lane A's 16 commits kept, restoring only the four origin targets brings the cluster straight back,
and the all-death cause mix then equals `main` exactly (98 HAZARD, 14 DEFEAT, 29 STARVATION). So the origin cluster is a **stranding defect owned
by that ticket**, not an overlap or bounds defect, and it gives that ticket corpus evidence it had to downgrade. One seed, one world, 5,000 ticks.
What remains is relevant here: **trauma from deaths in no region is lost outright** (not shadowed), and the one surviving uncredited death on the
fixed tree is at `(29, 40)`, which is exactly `hometown`'s `y=40` exclusive upper edge (`[10,10,40,40]`, half-open): a genuine far-edge case of
the half-open bound, one death in 141. That, and nothing else, is the measured instance of the "falls off the far edge" candidate. Also, 10 of 30
traced trauma-block lookups on `main` returned `None` because of the same cluster, so that figure is inflated by the stranding defect.

**4. Declaration-order contradiction (finding against Bible 06 line 37).** The paint-order rule gives a shared tile's **terrain** to the
**later**-declared region. The live region lookup returns the **earlier**-declared one. For the same tile, terrain priority and region-credit
priority run in opposite directions. Not tested by reordering regions.

**5. `ENV-06` reachability after redistribution (arithmetic on recorded deaths; NOT a re-simulation, and a fix may change dynamics).**
`frontier_living_world`, 10,000 ticks, 275 deaths (23 in no region). Current first-match result: `bandit_road` 111.0, `goblin_camp` 111.0, every
other region 0.0. Deaths physically inside each region by bounds, and each death split equally among the regions containing it:
| region | deaths inside | split equally |
|---|---|---|
| bandit_road | 121 | 48.6 |
| near_forest | 118 | 45.6 |
| goblin_camp | 117 | 105.0 |
| wolf_den | 93 | 34.6 |
| trading_hometown | 15 | 4.8 |
| hometown / haunted_battlefield / old_mine | 7 / 5 / 3 | 7.0 / 3.5 / 3.0 |
Decay removes at most 5.0 per region over the run. So: if **every containing region is credited**, four regions stay above 50
(`goblin_camp`, `bandit_road`, `near_forest`, `wolf_den`); if each death is **shared once**, only `goblin_camp` stays above 50 and
`bandit_road` falls to about 44 net. Which rule applies is the owner's choice and is not proposed here. The threshold does not become
unreachable under either rule on this world at 10,000 ticks, but under a shared-once rule it is reachable in **one** region, not two, and
later in the run. One world, one seed.

**Not done:** no fix direction chosen; nothing in `src/` changed; `src/core/state.py` not touched; `allow_overlapping_regions` untouched.

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_

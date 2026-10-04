---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP
phase: open
date: 2026-09-19
tags: [combat, faction, root-cause]
---

# TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP

## Title
Repo-wide sweep for the raw legacy-`Faction`-enum hostility anti-pattern
(`TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS` fixed 4 instances; this sweep
found at least 7 more real, load-bearing ones across combat, cognition, cooperation, and
strategic subsystems — triage and prioritize, do not fix all at once)

## Status
INPROGRESS (implementation landed, awaiting Verify/Finalize)

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Per peer review of `TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS`: before that
fix merged, swept `src/` for the same anti-pattern *by shape* (raw `identity.faction`
comparisons), not by grepping the fixed function's own name, since the fix's own 4th instance
(`AuthoritativeState._has_hostiles_or_dead_cache`) was a structurally different function
independently computing the same thing, found only because a test failed — a grep for
`get_engaged_hostiles` would never have found it.

**The sweep found this is not a 1-off or a 4-off pattern — it is systemic.** One instance was
already known and ticketed (`TCK-20260915-SENSORY-FILTER-SALIENCY-USES-LEGACY-FACTION-ENUM`,
`src/engine/cognition.py:44`, `SensoryFilter.filter_saliency`, still OPEN, P2, measured at 0.5%
real impact for its own specific consumer). **At least 7 more real, load-bearing sites** use the
identical `entity.identity.faction != other.identity.faction` (or `==`) raw-enum comparison for a
hostility- or allegiance-adjacent decision, none of them measured or ticketed before this sweep:

**A new divergence this arc's own fix created — recorded before merge, per peer review, as a
predicted consequence rather than something discovered later.** Before
`TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS` landed, the movement path
(`get_engaged_hostiles_at_pos()`) and `CombatEngageScorer.score()` were both wrong about
hostility, *the same way* — consistently wrong, but coherent with each other. After that fix,
the movement path reads real catalog semantics and the scorer still reads the raw enum: **they
now disagree.** Concretely, `CombatEngageScorer` can judge combat viable (score `COMBAT_ENGAGE`
above zero) against an entity the movement/attack path will now correctly refuse to engage,
because the scorer's raw-enum-based "hostile" and the attack path's catalog-based "hostile" are
no longer the same predicate. An entity could pursue a combat goal that cannot execute. This is
not a new bug independent of the fix — it is the fix correctly changing one of two previously-
matched consumers and not the other, the exact partial-fix risk this whole arc has been guarding
against, just at the cross-subsystem scale rather than the intra-function or dual-call-site scale
the fix itself already handled. Not a reason to have withheld the fix (preserving a coherent
wrongness to avoid this would have been the wrong trade), but a real, predicted follow-on this
ticket exists partly to close.

1. **`src/ai/goals/scorers.py:108`, `CombatEngageScorer.score()`.** Determines whether
   `GoalKind.COMBAT_ENGAGE` is even considered as a viable goal for an entity, building its own
   `hostiles` list with the raw enum (reusing `SensoryFilter.filter_saliency`, the already-known
   candidate).

   **The one-line finding, for a cold reader**: a winning `COMBAT_ENGAGE` goal produces a
   `reach_location` objective; `DEFEAT_ENEMY` is unreachable from the combat goal path entirely.
   The decision layer does not fail to *choose* combat — it chooses combat and the choice is
   discarded at dispatch, a dead branch by construction. No amount of work on perception,
   hostility semantics, posture, or readiness could ever have reached it, because nothing
   downstream of the goal-competition winner ever asks what `COMBAT_ENGAGE` itself found.

   **Investigated (not fixed — see status below): the downstream gate is found, and it is
   structural, not a detection-accuracy problem at all.** Traced where a winning
   `GoalKind.COMBAT_ENGAGE` candidate actually goes after `GoalRegistry.get_all_scores()`
   (`src/ai/goals/base.py:46`, its one real caller is
   `src/systems/strategic_systems/intelligence.py:1503`). The winner-consumption code
   (`intelligence.py:1558` onward) has **special-cased branches** for specific `GoalKind` values —
   `ADVENTURE_ROUTE` (line 1570), `SOCIAL_CONTRACT` (1598), `REGION_STABILIZATION` (1635),
   `OCCUPATION_CHANGE` (1670) — each materializing its own real `ProjectKind`/`ObjectiveKind`.
   `COMBAT_ENGAGE` has **no special case** and falls through to the generic `else:` branch
   (line 1701), which **hardcodes `kind="reach_location"`** for the resulting `ObjectiveState`
   (line 1705) — not derived from `best_candidate.kind` at all.

   **This means `CombatEngageScorer` winning the goal competition can never produce a
   `DEFEAT_ENEMY` objective, regardless of how accurate or inaccurate its own `hostiles` list
   is.** `ObjectiveKind.DEFEAT_ENEMY` is created **exclusively** through the `ADVENTURE_ROUTE`
   branch, specifically when `RouteToProjectMapper.map_to_states()` resolves a
   `RouteFamily.HUNT_WEAK_ENEMY` family (`src/domains/adventure/mapper.py:37`) — an entirely
   separate scorer (`AdventureGoalScorer`, `src/ai/goals/adventure_scorer.py`) with its own
   cognition-profile eligibility gating (`_resolve_cognition_profile_id`,
   `_supports_adventure_routing`), unrelated to `CombatEngageScorer` or its hostility test.

   **This resolves the counterintuitive-direction tension raised in peer review, decisively, not
   by picking a side of the original hypothesis.** The raw enum's own error direction (heavy
   over-detection, per `TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION`'s numbers)
   is irrelevant to the zero-`DEFEAT_ENEMY` finding either way — `CombatEngageScorer`'s hostility
   test was never the binding constraint on objective assignment, under either semantics. **The
   real gate for the arc's own standing "why does the decision layer never engage" question is
   `AdventureGoalScorer`'s own eligibility/routing logic and whatever governs `HUNT_WEAK_ENEMY`
   ever being proposed and winning — not this scorer, and not this ticket's own anti-pattern.**
   Not chased further here (the eligibility system is its own real, separate mechanism — out of
   this sweep's scope to fully resolve).

   **Status: the divergence this arc's own fix created here is real but currently inert, per peer
   review, and this site is deferred, not fixed.** Winning `COMBAT_ENGAGE` produces only a generic
   `reach_location` objective regardless of which hostility semantics the scorer uses, so
   correcting its `hostiles` list changes *which* entity a `reach_location` project targets, not
   whether any `DEFEAT_ENEMY` objective gets created — a real but currently-unobservable-in-
   practice effect while objective assignment for combat produces zero real `DEFEAT_ENEMY`
   objectives across the sampled corpus regardless. **It becomes a live, observable defect the
   moment someone fixes `AdventureGoalScorer`'s own gate** (or any other future path that lets
   `COMBAT_ENGAGE` matter) — recorded here explicitly so whoever does that work knows this
   divergence is waiting for them, rather than rediscovering it.
2. **`src/engine/legality.py:451`, inside a flanking-bonus check (`has_hostile_at`)** — raw enum,
   unconditional, no fallback to catalog at all (unlike the nearby `verify_attack_legality`'s own
   `has_clean` fallback structure at line 265-269, which already prefers `is_hostile_compat()` and
   only falls back to the raw enum when clean identity data is unavailable — a narrower, lower-
   priority gap than line 451's).
3. **`src/engine/combat.py:538`, AOE/splash-damage friendly-fire exclusion** — raw enum "same
   faction, skip" check for splash targeting.
4. **`src/systems/world_systems/intake.py:30`** — "Nearby Combat Threat" danger-concern
   generation for AI, raw enum.
5. **`src/systems/world_systems/intake.py:44`** — ally-death grief/trauma detection, raw enum
   (inverse direction: same-faction, not hostility, but the same root pattern).
6. **`src/engine/cognition.py:117`**, "Faction Ratio (Outnumbered)" panic/morale computation —
   raw enum, in the same file as the already-known candidate 4 but a different function.
7. **`src/domains/cooperation/providers.py:50`** — "Exclude hostiles" filter for cooperation-
   partner candidate selection, raw enum.
8. **`src/systems/strategic_systems/intelligence.py:149` and `:439`** — raw enum in lead-
   confirmation/observation-based intel logic.

**Checked and judged likely benign (grouping/indexing utilities or single-entity checks, not
pairwise hostility determinations) — not fixed, not counted above, but recorded so they aren't
re-swept from scratch:**
- `src/world/environment.py:83` — single-entity check against one specific faction constant.
- `src/certification/harness.py` (3 occurrences) — certification/testing tooling.
- `src/engine/semantic_entity_index.py:163` (`_build_faction_index`) — a lookup-index builder
  keyed by raw legacy bucket; whether any of ITS consumers misuse the coarse grouping as if it
  were real per-faction data is a separate question, not checked here.
- `src/domains/campaigns/orchestrator.py:612` — campaign carry-forward state tracked at legacy-
  bucket granularity, possibly an intentional coarse design choice at that layer, not obviously a
  bug.
- `src/api/presenters/state_presenter.py`, `src/entities/identity_resolver.py:119` — display
  layer and the resolver's own internal legacy-compat mapping table respectively; expected to
  reference the raw enum, not a bug.

## Scope
- **Investigation/triage first, do not fix all 7+ in one pass.** For each of the 8 numbered sites
  above: confirm the finding by direct code read (already done for this filing, re-verify before
  building), measure real-world impact where feasible (matching the discipline
  `TCK-20260915-SENSORY-FILTER-SALIENCY-USES-LEGACY-FACTION-ENUM` already used — a real
  instrumented measurement, not a guess), and rank by real consequence.
- **Priority-order update, 2026-09-19**: `ai/goals/scorers.py:108` was investigated first (see
  its own numbered entry above for the full finding) and found **inert** — deferred, not fixed,
  since winning `COMBAT_ENGAGE` cannot produce a `DEFEAT_ENEMY` objective regardless of its own
  hostility semantics. **Per user direction, this sweep track itself is now paused** in favor of
  completing the mechanism-registry/system-membership program
  (`TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION` and its own sequence). The remaining 6
  sites (2-7 below) are unranked and unstarted — whoever resumes this ticket should re-derive
  priority order fresh rather than trust a stale recommendation, since the one site actually
  investigated turned out lower-urgency than assumed going in.
- Determine whether a shared, reusable hostility-check helper (mirroring
  `LegalityServiceV2._is_engagement_hostile()`, the helper this arc's own fix just built) should
  be extracted to a common module and reused across all of these, rather than each subsystem
  reimplementing its own copy — the repeated-reimplementation pattern itself is arguably the root
  cause, not any one site.
- Fix low-risk, well-measured sites as scoped, standalone units of work (following
  `TCK-20260915-SENSORY-FILTER-SALIENCY-USES-LEGACY-FACTION-ENUM`'s own precedent of "measure
  first, and be honest if impact turns out small").

## Out of Scope
- `TCK-20260915-SENSORY-FILTER-SALIENCY-USES-LEGACY-FACTION-ENUM` itself — already filed,
  already measured (0.5% impact), not re-investigated here, just cross-referenced.
- The 4 sites already fixed by `TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS`.
- The "likely benign" sites listed above — not in scope unless a future pass finds a real
  consumer misusing them.
- Building the shared helper extraction itself in this ticket — a design question to answer, not
  pre-decided.

## Acceptance Criteria
- Each of the 8 numbered sites has either a real measurement of its practical impact (matching
  the saliency-filter ticket's own precedent), or an explicit note that measurement wasn't
  feasible and why.
- `ai/goals/scorers.py:108` specifically gets a real, instrumented before/after check (does
  fixing it change real `COMBAT_ENGAGE` goal-selection rates in the corpus worlds this arc has
  already been sampling) — not assumed to matter or not matter.
- A decision recorded on whether a shared hostility-check helper is worth extracting.
- Any site fixed as part of this ticket is measured before/after per the same discipline as
  `TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS` (real `Kernel.tick_once()` runs,
  per-world reporting, not aggregated).

## Related Tickets
- `TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS` (closed — fixed the first 4
  instances found; this ticket is the sweep peer review asked for before that one merged)
- `TCK-20260915-SENSORY-FILTER-SALIENCY-USES-LEGACY-FACTION-ENUM` (open, P2 — the one already-
  known instance, same bug shape, `cognition.py:44`, measured at 0.5% impact for its own narrow
  consumer)
- `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` (closed — found the decision-
  driven `ATTACK` path rarely fires; **checked against this ticket's own finding and resolved,
  not merely a candidate anymore**: that investigation asked why the decision layer never
  *chooses* to engage; this ticket's own `scorers.py:108` finding answers a deeper, adjacent
  question — even when `COMBAT_ENGAGE` *is* chosen, the choice is discarded at dispatch, a dead
  branch by construction. See that ticket's own addendum for the cross-reference.)
- `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` (epic, `EPIC_SCOPED`, open — its own title,
  "combat is incidental, not decisional," is this ticket's own `scorers.py:108` finding one level
  down: `COMBAT_ENGAGE` losing to `reach_location` at dispatch is a second, independent reason
  combat stays incidental in this epic's own chain, alongside the epic's already-tracked
  `resolve_multi_attack()`-dominance finding. **2026-09-20**: this cross-reference was deferred
  when first written (2026-09-19) because the epic's own file sat in PR #222's still-open branch;
  completed now that #222 has merged — cross-reference added to that epic's own Related Tickets in
  the same pass.)
- `TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION` and
  `TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS` — **belong in the same
  conversation as this finding, whenever either is scoped further, per peer review**: that fix
  already removed 85-96% of phantom combat, the only real combat these worlds had. If this
  ticket's own `scorers.py`/`AdventureGoalScorer` gate is ever connected, real catalog-driven
  combat becomes possible in these worlds for the first time — a fix to one makes the other
  materially more consequential, not independent improvements.

## Related Docs
- `docs/engine/contracts/combat_contract.md`

## Related Stored Artifacts
_(none yet — filed as a sweep finding, not yet investigated per-site)_

## Related Code Areas
- `src/ai/goals/scorers.py` (`CombatEngageScorer.score`)
- `src/engine/legality.py` (flanking-bonus `has_hostile_at`, line ~451)
- `src/engine/combat.py` (AOE/splash friendly-fire exclusion, line ~538)
- `src/systems/world_systems/intake.py` (lines ~30, ~44)
- `src/engine/cognition.py` (line ~117, "Faction Ratio" panic computation)
- `src/domains/cooperation/providers.py` (line ~50)
- `src/systems/strategic_systems/intelligence.py` (lines ~149, ~439)
- `src/engine/legality.py::_is_engagement_hostile` (the reference pattern this arc just built,
  candidate shared-helper implementation)

## Assumptions / Open Questions
- Whether all 8 sites share the same "should be fully catalog-aware" answer, or whether some
  (e.g. panic/morale "outnumbered" computation, which may legitimately want a cruder, faster
  proxy for "is this a different group" rather than exact catalog hostility) have a real reason
  to stay coarse — not assumed here, a real per-site judgment call for whoever investigates.
- Whether the "likely benign" sites are genuinely benign or just not yet found to have a real
  consumer that misuses them — left open, not asserted as settled.

## Implementation Notes

### 2026-10-04 — implemented (all three groups, measured per group)

**Shared helper: established by item 1, not this ticket.** `TCK-20261002-GOAL-WINNER-CONSUMPTION-...` had already
landed `are_entities_hostile(source, target, context)` in `src/content_semantics/faction.py`; every fix below consumes
it, and no second helper was created. This ticket added only `are_entities_allied` (same resolved catalog faction) and
a private `_resolve_faction_id` that both functions share.

**Sites fixed** (each takes the real Manhattan distance and `combat_engaged=True`, as item 1's scorer does):
- A1 `combat.py` `resolve_aoe_attack`: skip a splash victim when the catalog says **not hostile** (so catalog-allies
  *and neutrals* are spared, matching the primary-target Friendly-Fire Law).
- A2 `intake.py` `danger`: catalog-hostile neighbour only. `trauma_dead_ally`: `are_entities_allied`.
  **Predicate decision (1c): "allied" = same resolved catalog faction id, not `not hostile`**, so a dead neutral is
  not grieved. **Id decision (1d): the `trauma_dead_ally_<id>` literal is left unchanged** - with the predicate fixed
  the id's claim ("ally") is now true, so no durable meaning is misplaced and no second hash movement was introduced.
- A3 (promoted from Group C, see below) `cooperation/providers.py` and `intelligence.py` lead-observation hostiles.
- B `legality.py` `check_flanking.has_hostile_at`: `are_entities_hostile` with the real distance.
- C `cognition.py` `filter_saliency` and the outnumbered ratio (allies = `are_entities_allied`, hostiles =
  `are_entities_hostile`, a neutral counts as neither), `intelligence.py` `_threat_resolved`.
- Not touched: `scorers.py:108` (item 1), `legality.py:269`/`:524`, the benign sites.

**Promotion to Group A (plan Step 3 instruction).** Checked durability before fixing C3/C4: `providers.py` candidates
feed contract proposal (`cooperation/services.py`, `phase.py`) and the `intelligence.py:439` hostiles gate lets
`BeliefCycleSystem.process_observation` write `leads_add_or_update`/`beliefs_add_or_update` - both durable, so they were
fixed and measured in the Group A stage. `intelligence.py:149` (`_threat_resolved`) is a transient lock-release input
and stayed Group C.

**Deviation (also in plan.md).** B did **not** copy the `:265-269` `has_clean` shape. `is_hostile_compat` already
falls back to the legacy-bucket `is_hostile` itself when clean data is missing, and the shared helper reaches it, so
the explicit raw-enum `else:` would re-introduce the over-detection (any two different buckets "hostile") that this
ticket removes. `:269` itself is untouched.

**Measurement.** Real `Kernel.tick_once()`, `PROD_SMALL` with `max_tick_budget_ms=1e9`, `audit_mode=True`,
`LocalSequentialExecutor()`, seed 42, 2000 ticks, one run at a time, sha256 of every entity's canonical dict, each arm
repeated. An earlier non-audit pass was discarded (the throttle made repeats differ). The probe lived in the session
scratchpad only. Stages: s0 baseline (HEAD incl. item 1), s1 = A, s2 = A+B, s3 = A+B+C.

Raw-enum vs catalog disagreement at baseline, % of evaluated pairs (over = raw said enemy/ally, catalog says not;
under = the reverse), crowded_frontier / frontier_living_world:

| site | evaluated | over | under |
|---|---|---|---|
| `intake.py:30` danger (alive, <=3 tiles) | 6426 / 7596 | 9.7% / 11.5% | 1.5% / 11.0% |
| `intake.py:44` dead neighbour (ally test) | 1572 / 3435 | 40.8% / 31.7% | 0 / 0 |
| `cognition.py:44` saliency | 21295 / 23069 | 15.6% / 15.1% | 0.5% / 7.9% |
| `cognition.py:117` ratio pairs | 16682 / 8995 | 10.4% / 12.0% | 0.3% / 4.5% |
| `legality.py:451` flanking | 214 / 432 | 10.3% / 2.1% | 13.6% / 31.5% |
| `providers.py:50` partner pool | 307162 / 644292 | 16.9% / 4.4% | 7.7% / 14.9% |
| `intelligence.py:149` threat-resolved | 16 / 0 | 25.0% / n/a | 0 / n/a |
| `combat.py:507` splash | **0 / 0 AoE attacks in 2000 ticks** | unmeasurable | unmeasurable |
| `intelligence.py:439` lead observation | **0 / 0 confirmations; 0 location leads ever tested** | unmeasurable | unmeasurable |

**The plan's expectation was wrong.** It predicted under-detection (monster-vs-monster conflict) would dominate.
Over-detection (allies/neutrals treated as enemies) dominates at four of the seven measurable sites in both worlds;
under-detection dominates only flanking and partner exclusion in `frontier_living_world`. Reported as a finding.

Durable consequences, baseline s0 to all-fixed s3, per world (counts per 2000 ticks):

| | crowded_frontier | frontier_living_world |
|---|---|---|
| `danger` concerns emitted | 1025 to 485 | 2078 to 2091 |
| `trauma_dead_ally` concerns emitted | 742 to 100 | 1315 to 42 |
| contracts held at end | 110 to 554 | 825 to 537 (modal) |
| partner candidates produced | 30065 to 24491 | 82449 to 80617 |
| flanked results / flank checks | 9/129 to 10/97 | 18/200 to 8/172 |
| panic flag cleared / raised (shadow, s0) | 191 / 8 | 17 / 87 |
| splash victims, deaths from splash | 0, 0 (site never runs) | 0, 0 |

Group A alone already carries nearly the whole `danger`/`trauma` change in crowded_frontier (486 and 100 at s1).

**C1 re-measured, not inherited.** `filter_saliency` raw-vs-catalog disagreement was 16.2% (crowded_frontier) and
23.0% (frontier_living_world) of evaluated pairs, versus the inherited 0.5% (a drop-from-top-5 rate for another
consumer). Different quantity, not a contradiction; the inherited figure should not be cited for this ticket.

**Determinism.** Entity canonical hashes: s0 reproducible 6/6 on frontier_living_world; crowded_frontier reproducible at
every stage. **`frontier_living_world` is bimodal across repeats at stages s2/s3** (two outcomes, 512c.../534b...; the
modal 534b... in 9 of 11 runs; s2 and s3 share the same two outcomes). Not attributable to this change on the evidence
here - it is the already-filed class `TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE` - and it
was not seen at s0 (6/6) or s1 (2/2); reported, not explained. Moved hashes are explained as "these concerns are no
longer generated / these entities are now eligible partners", per the plan's rule; no recorded-hash fixture moved
(no test failed on a hash).

**Other observation, not chased:** every entity is `alive == False` at tick 2000 in both worlds at baseline too.

**Pre-existing failures, verified at HEAD behaviour** (stage 0): `tests/integration/scenarios/test_entity_differentiation.py::test_bravery_quartile_combat_rate_2x` (seed 4 population guard, n_alive=7) and `tests/integration/world/test_long_run_stability.py::test_long_run_stability` (conftest timeout) fail identically without this change.

**Not done / honest gaps.** T4b (clean-data-unavailable flanking fallback) is not applicable after the deviation above.
`intelligence.py:439` has no direct unit test (it lives inside the several-hundred-line `evaluate_strategic_intent`);
it is covered by the shared-helper identity test only. `resolve_aoe_attack` has no corpus firing, so its measured
effect is nil and its proof is the unit tests alone.

### 2026-10-02 — RESUMED as work-order item 2. Site inventory re-verified; three corrections.

Resumed under owner decision 7's approved work order (`docs/plans/systemic_world/roadmap.md` §8, item
2), which classes this as a hard bug. Site inventory re-verified against `origin/main` **`4c133297b`**
by shape (`identity.faction [!=]= *.identity.faction`), not by name, the same way the original sweep was
done. Full record in `agent-working/staging_artifacts/TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP/investigation.md`.

**The inventory holds — 9 real sites, no new ones, none disappeared.** Three corrections:

1. **`src/engine/combat.py`'s splash site has drifted: `538` → `507`.** Every other cited line number
   below is still exact. Cite `:507`.
2. **Site 1 (`scorers.py:108`) is no longer this ticket's.** It is claimed by
   `TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND` (work-order item 1), which
   must fix it *in the same batch* as the dispatch defect — the two are mutually load-bearing. **Do not
   fix `scorers.py:108` here.** Note `SensoryFilter.filter_saliency` is called on the line immediately
   above it (`:107`) and **does** remain this ticket's (site 6-adjacent, `cognition.py:44`).
3. **This ticket's own "deferred because inert" rationale for site 1 is obsolete, and its stated root
   cause was wrong.** The 2026-09-19 note below concluded: *"The real gate for the arc's own standing
   'why does the decision layer never engage' question is `AdventureGoalScorer`'s own
   eligibility/routing logic … not this scorer, and not this ticket's own anti-pattern."* **Measurement
   on 2026-10-02 disproves that.** The real gate is winner-consumption hardcoding `reach_location`,
   exactly as the note's own trace found — `AdventureGoalScorer` is a red herring for this question and
   nobody should spend a cycle on it. The note also predicted the divergence "becomes a live,
   observable defect the moment someone fixes `AdventureGoalScorer`'s own gate (or any other future path
   that lets `COMBAT_ENGAGE` matter)". That prediction was right; the trigger is item 1, not
   `AdventureGoalScorer`.

   Measured evidence (real `Kernel.tick_once()`, seed 42, 2000 ticks, `crowded_frontier` +
   `frontier_living_world`): `COMBAT_ENGAGE` is the **most frequent** goal winner (485/1767 and
   568/1744), **100%** of its objectives are `reach_location` across 111 114 samples, and the raw enum
   disagrees with the catalog on **54.0%** and **33.6%** of the targets the scorer actually selected
   (both **floors**). So this site was never "0.5%-impact" inert — it was high-volume and masked.

**Also checked and found NOT a problem, recorded so nobody re-chases it:** `intelligence.py:83` imports
`ConcernIntakeSystem` from `src.systems.world_systems.intake` while `:861` imports it from
`src.systems.intake`. That is **not** a duplicate class — `src/systems/intake.py` is a 3-line
re-export shim with one `__all__`. Sites 4 and 5 are **one** fix location each, not two.

### 2026-09-19 — original investigation (superseded in part by the above)

**`ai/goals/scorers.py:108` investigated, paused, sweep track suspended per user
direction.** No code changed — investigation only, matching this ticket's own explicit scope
against fixing sites without measurement first.

The decisive trace: `GoalRegistry.get_all_scores()` → `intelligence.py:1503` → winner-consumption
dispatch (`intelligence.py:1558+`) → generic `else:` branch (`intelligence.py:1701-1719`, the
branch `GoalKind.COMBAT_ENGAGE` falls into, since it has no special case) → hardcoded
`kind="reach_location"` at `intelligence.py:1705`. `ObjectiveKind.DEFEAT_ENEMY` only exists via
`RouteToProjectMapper.map_to_states()` under the `ADVENTURE_ROUTE` special case
(`intelligence.py:1570-1597`), consuming `RouteFamily.HUNT_WEAK_ENEMY`
(`src/domains/adventure/mapper.py:37`) — a completely different scorer
(`src/ai/goals/adventure_scorer.py`) with its own cognition-profile eligibility gate. The two
systems (`CombatEngageScorer`'s goal-competition entry and `AdventureGoalScorer`'s route-
eligibility system) do not interact.

This closes the arc's own standing "why does the decision layer never engage" question at the
`CombatEngageScorer` layer specifically: **it was never the mechanism.** The real remaining
question — why `AdventureGoalScorer` never proposes or never wins a `HUNT_WEAK_ENEMY` route — is
a separate, real investigation this ticket does not open.

**Sweep track paused per explicit user direction (relayed 2026-09-19)**: prioritize completing
the mechanism-registry/system-membership program instead. This ticket stays open with 6 of 8
numbered sites still unranked and uninvestigated, plus the already-known
`TCK-20260915-SENSORY-FILTER-SALIENCY-USES-LEGACY-FACTION-ENUM` sibling — resumable later, not
closed, since real work remains and the finding above is valuable and durable regardless of when
the rest resumes.

## Test Summary
New `tests/unit/combat/test_catalog_hostility_sweep.py`: 15 tests, 12 fail at HEAD and all 15 pass after (both error
directions per site, a neutral case, an inversion guard for splash, shared-helper identity). Scoped runs after the
change: `tests/unit` + `tests/engine` 6199 passed, 3 skipped; `tests/integration` + `tests/mechanic_scenarios` +
`tests/architecture` (not slow) 1205 passed, 2 failed - both failures reproduce identically at HEAD behaviour (see
Implementation Notes).

## Files Changed
- `src/content_semantics/faction.py`
- `src/engine/combat.py`
- `src/engine/legality.py`
- `src/engine/cognition.py`
- `src/systems/world_systems/intake.py`
- `src/systems/strategic_systems/intelligence.py`
- `src/domains/cooperation/providers.py`
- `tests/unit/combat/test_catalog_hostility_sweep.py` (new)
- `docs/mechanics/02_combat_laws.md`
- `docs/mechanics/04_strategic_cognition.md`
- `docs/guidelines/intentional_divergences.md` (new Section 2.65)
- `docs/parity_ledger/combat_movement.yaml` (COMB-326; the writer re-wrapped some neighbouring entries' YAML line breaks)
- `docs/parity_ledger/strategic_cognition.yaml` (STRAT-275)
- `agent-working/tickets/inprogress/TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP.md`
- `agent-working/tickets/done/TCK-20260915-SENSORY-FILTER-SALIENCY-USES-LEGACY-FACTION-ENUM.md` (moved from `todos/`, closed as folded)
- `agent-working/staging_artifacts/TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP/plan.md` (Deviations section)

## Completion Summary
Eight raw legacy-`Faction`-enum hostility/allegiance sites (splash, flanking, concern intake x2, saliency, outnumbered
ratio, cooperation partner pool, intelligence threat-resolved and lead observation) now ask the content catalog
through the single shared `are_entities_hostile` helper item 1 created, plus a new `are_entities_allied` for the one
ally test. Measured per group on two corpus worlds: over-detection, not the predicted under-detection, dominates;
splash and lead observation never run in the corpus, so they are proven by unit tests only. 15 new tests; the
sibling saliency ticket is closed as folded. Open: `frontier_living_world` is bimodal across repeats from Group B on
(not attributed), and two integration tests fail identically at HEAD.

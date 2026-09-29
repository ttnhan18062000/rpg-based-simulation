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
OPEN

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
**2026-09-19, `ai/goals/scorers.py:108` investigated, paused, sweep track suspended per user
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
_(none — investigation only, no code changed)_

## Files Changed
_(none — investigation only, no code changed)_

## Completion Summary
**Not closed — paused.** One of 8 numbered sites (`ai/goals/scorers.py:108`,
`CombatEngageScorer`) investigated in full: found and recorded the real downstream gate that
makes this arc's own "why doesn't the decision layer engage" question independent of this
scorer's own hostility-detection accuracy — winning `COMBAT_ENGAGE` structurally cannot produce a
`DEFEAT_ENEMY` objective under the current code, regardless of semantics, because the generic
goal-winner-consumption branch hardcodes a `reach_location` objective kind rather than deriving
it from the winning goal. The cross-subsystem divergence this arc's own fix created here is real
but currently inert as a result — recorded explicitly for whoever eventually fixes
`AdventureGoalScorer`'s own eligibility gate, since that is the point at which this divergence
would start to matter. Remaining 7 sites (6 new + the known sibling) not yet investigated; sweep
track paused per explicit user direction to prioritize the mechanism-registry/system-membership
program.

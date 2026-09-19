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

1. **`src/ai/goals/scorers.py:108`, `CombatEngageScorer.score()`** — determines whether
   `GoalKind.COMBAT_ENGAGE` is even considered as a viable goal for an entity, building its own
   `hostiles` list with the raw enum (reusing `SensoryFilter.filter_saliency`, the already-known
   candidate). **Potentially the most significant of the new findings**: this arc has spent
   multiple investigations asking why the decision-driven path rarely selects combat-related
   goals (`TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION`) — if the *goal scorer
   itself* under-detects real hostiles the same way the movement path did, that is a second,
   independent contributor to the same symptom, not yet measured.
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
- **Priority-order recommendation, not binding**: start with
  `ai/goals/scorers.py:108`'s `CombatEngageScorer` given its direct relevance to this arc's own
  standing open question about why decision-driven combat goals rarely fire — measure whether
  fixing it changes real `COMBAT_ENGAGE` goal-selection rates before assuming it's low-impact like
  the saliency-filter sibling turned out to be.
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
  driven `ATTACK` path rarely fires; `ai/goals/scorers.py:108`'s own finding here is a candidate
  contributor to that same symptom, not yet checked against it)
- `TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION` (closed — the original
  investigation that started this whole thread)

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
_(none yet — sweep only, no fixes applied in this ticket)_

## Test Summary
_(none yet)_

## Files Changed
_(none yet)_

## Completion Summary
_(none yet — filed as the sweep peer review requested before `TCK-20260919-COMBAT-ENGAGED-
HOSTILES-UNIFY-CATALOG-SEMANTICS` merged; that ticket's own PR is not blocked on this one closing,
per peer's own framing: "report what you find even if it's nothing... better now than after
merge" — reporting here, not gating the merge on fixing all of it.)_

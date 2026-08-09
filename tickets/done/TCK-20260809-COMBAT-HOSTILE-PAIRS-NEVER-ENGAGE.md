---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE
phase: open
date: 2026-08-09
tags: [combat, simulation-quality]
---

# TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE

## Title
Real, genuinely-hostile faction pairs (`bandit_company` vs. every other faction) never once
trigger an attack-legality check across a full 2000-tick corpus run — deliberate combat is
effectively zero in `dungeon_crawl`/`urban_political`, and the cause is upstream of every
legality/readiness fix already shipped this session

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Direct follow-up to the user's own request to continue combat work along 3 threads (per-attack
tactical trace, why real combat volume is low, pillar-scoring for the new lifecycle events). This
ticket covers the second thread, which turned out to be far deeper than originally framed.

**Starting point**: `TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY` (2026-08-06)
already ruled out `ENABLE_COMBAT_ENGAGEMENT` as the blocker (deliberate ruling, DEV-002; the flag
gates posture assessment, not damage resolution). This session's own
`TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION` and
`TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE` then raised the real, live
`is_attack_legal` probe rate from 0% to 28.5%/36.6% (readiness double-cost fix, `intruding=False`
hardcode fix). That work's own methodology sampled `is_attack_legal()` at real decision points
during a real `Kernel.tick_once()` loop — real, not synthetic.

**This ticket's own real, live 2000-tick re-verification** (during
`TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY`'s Test phase, then investigated further here) found:
`combat_damage`/`combat_initiated`/`entity_killed` all recorded **zero** occurrences in a full
2000-tick run of either `dungeon_crawl` or `urban_political` — a materially different picture than
the 28.5%/36.6% legal-rate figure would suggest. Investigated why, with real, live instrumentation
(monkey-patched `LegalityServiceV2.verify_attack_legality`/`verify_action_legality`,
`TacticalDecisionSystem.evaluate_entity_intent`, `FactionSemanticsService.is_hostile_compat`,
`CombatActions.execute_attack` — probe scripts lived in scratchpad, matching this whole session's
own established methodology), against the same real compiled worlds (seed 42).

## Scope
1. **Re-confirm every finding below against current source** (git history since 2026-08-06 has
   touched `tactical.py`/`legality.py`/`movement.py` several times this session — confirm nothing
   has silently drifted).
2. **Trace the exact reason `hostiles` never contains a `bandit_company`-involved pair** despite:
   (a) real, confirmed hostile relationships existing in the corpus's own faction data
   (`bandit_company` → every other faction present, both worlds — `enemy`-labeled, unconditional),
   (b) at least one `bandit_company` entity starting within perception radius (10.0) of a hostile
   target at tick 0 in both worlds (min distance 4-5), (c) `evaluate_entity_intent` genuinely being
   called for `bandit_company` entities at real, non-trivial volume (439 calls/2000 ticks in
   `dungeon_crawl`) — ruling out "never evaluated at all." The likely candidates, not yet
   distinguished: the perception gate (`get_perception_gate().can_perceive`), neighbor
   detection/saliency filtering (`SimulationDomainLogic.get_neighbor_view` /
   `SensoryFilter.filter_saliency`, capped at `max_targets=5`), or goal-competition never
   selecting `GoalKind.COMBAT_ENGAGE` for this specific role/faction combination even when a real
   hostile is detected.
3. **Determine whether this is a code bug or a real world-design/spatial-pacing limitation** (e.g.
   `bandit_company` entities patrol/wander away from their initial position faster than hostile
   targets approach) — per the Uncertainty Rule, do not collapse to a specific fix before the
   evidence narrows it.
4. Produce a concrete recommendation (fix vs. document as a known corpus limitation vs. split into
   a further-scoped follow-up), consistent with this session's own established
   investigate-then-decide precedent.

## Out of Scope
- The already-shipped readiness/friendly-fire/`intruding` fixes from the 2 sibling tickets — not
  revisited, confirmed still correct and not the cause of this deeper finding.
- The `hero_guild`↔`town_council` "100% `FRIENDLY_FIRE_ILLEGAL`" volume observed during
  investigation — confirmed to be `CombatResolutionSystem.resolve_multi_attack()`'s own routine
  opportunity-attack-during-movement scan checking legality against every nearby entity (allied or
  not); correctly rejects allied pairs. **Not a bug** — a red herring ruled out with real evidence
  (stack-trace-captured call site, `is_hostile_compat` returning `False` for this exact faction
  pair across 10 real samples at distances 1-10), documented here so it is not re-chased.
- Building any new hostility/spatial-pacing mechanic from scratch — this ticket traces the real
  cause first; a fix ticket may follow depending on what's found.
- `TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY`'s own scope (already DONE, unaffected) — that
  ticket's new `combat_engagement_started`/`ended` events are correct as built; this ticket
  explains why they were observed firing at near-zero deliberate-combat volume in the same
  re-verification run, not a defect in that ticket's own work.

## Acceptance Criteria
- [x] investigation.md re-confirms, against current source, that real hostile faction pairs exist
      in both worlds' compiled state and that at least one is within initial perception range
- [x] The exact point in the pipeline where a real hostile `bandit_company` pair fails to reach
      `hostiles`/`legal_attack_targets` is identified with a specific, cited function and
      real, live-instrumented evidence — not assumed (`EntityIdentityResolver.resolve()` Path 1
      collapsing real `faction_id` to `"neutral"` when `role_id` is absent)
- [x] A concrete recommendation is produced (fix now vs. follow-up ticket vs. documented
      limitation), with reasoning — fixed now (resolver-side, minimal, additive)
- [x] `docs/audits/D21_entity_lifecycle_foundation_layers.md` (or a successor doc) is updated if
      this investigation supersedes or extends its "Combat legality always false" finding
- [x] If a fix lands in this ticket: real corpus re-verification shows non-zero
      `combat_damage`/`entity_killed`/`combat_engagement_started` volume in at least one of the two
      2000-tick worlds — **partially met, disclosed honestly**: the fix produces real, verified,
      non-zero `is_attack_legal` checks for genuinely hostile pairs that were never checked at all
      before (0 → 26+3+2 real checks across both worlds), but every one still fails on
      `OUT_OF_RANGE` in this specific 2000-tick window — a distinct, downstream pursuit/
      range-closing bottleneck, not this ticket's own bug. `combat_damage`/`entity_killed` remain
      zero in this run; not forced into a false "fully resolved" claim. Follow-up filed:
      `TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE`.

## Related Tickets
- TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE (filed as a follow-up — the newly
  surfaced pursuit/range-closing bottleneck this fix exposed)
- TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY (DONE — ruled out
  `ENABLE_COMBAT_ENGAGEMENT`, filed the push-observability epic this session built on)
- TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION,
  TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE (DONE, same session — raised the
  `is_attack_legal` probe rate 0%→28.5%/36.6%; this ticket's own finding shows that rate did not
  translate into real executed attacks for the corpus's actual hostile pairs)
- TCK-20260809-COMBAT-LIFECYCLE-OBSERVABILITY (DONE, same session — the real 2000-tick
  re-verification during its own Test phase is what surfaced this finding)

## Related Docs
- `docs/audits/D21_entity_lifecycle_foundation_layers.md` ("Combat legality always false" section)
- `docs/engine/contracts/combat_contract.md` §4 (Opportunity Attacks — `resolve_multi_attack`'s
  own real scope)
- `docs/simulation/domains/combat_engagement_contract.md` (posture assessment, confirmed separate
  from damage resolution)

## Related Stored Artifacts
None yet — will be created at
`staging_artifacts/TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE/` during implementation.

## Related Code Areas
- `src/engine/tactical.py` (`evaluate_entity_intent`'s hostile-detection loop, lines ~139-182)
- `src/engine/legality.py` (`verify_attack_legality`, `verify_action_legality`)
- `src/content_semantics/faction.py` (`FactionSemanticsService.is_hostile_compat`)
- `src/engine/combat.py` (`resolve_multi_attack` — confirmed the real source of the
  `hero_guild`↔`town_council` friendly-fire volume, a red herring, not this ticket's real target)
- `src/engine/behavior_consumers.py` (`get_perception_gate`, `get_entity_signals` — untraced
  candidate)
- `src/engine/domain_logic.py` (`SimulationDomainLogic.get_neighbor_view`,
  `SensoryFilter.filter_saliency` — untraced candidate, `max_targets=5` cap)

## Assumptions / Open Questions
- Whether the perception gate or neighbor/saliency filtering is the actual blocker, vs. a
  goal-competition issue where `GoalKind.COMBAT_ENGAGE` never wins for `bandit_company`'s own role
  configuration even when a hostile is genuinely detected — left open per the Uncertainty Rule,
  Investigate phase must distinguish these with real evidence, not assume either.
- Whether `bandit_company` entities' own wander/patrol AI moves them away from their hostile
  targets faster than any approach mechanism closes the gap (a spatial-pacing question distinct
  from a legality/detection bug) — also open.

## Implementation Notes
- `src/entities/identity_resolver.py::EntityIdentityResolver.resolve()` Path 1
  (`clean_metadata`): changed the gate from `if faction_id and role_id:` to `if faction_id:`,
  deriving `role_id` from the existing `_ROLE_COMPAT` legacy-role compat map (`props.get("role_id")
  or _ROLE_COMPAT.get(entity.identity.role)`) when the caller didn't supply one, falling back to
  the literal string `"unresolved"` only if the legacy role enum itself doesn't map either. `source`
  stays `"clean_metadata"` since the identity itself is real/content-driven.
- Root cause: `worldbuilding/compiler.py` (the real compile path for `dungeon_crawl`/
  `urban_political`) sets `identity.properties["faction_id"]` but never `["role_id"]`. Previously
  this meant EVERY such entity fell through Path 1 and Path 2 to Path 3
  (`compatibility_projection`), which maps the entity's raw *legacy* 4-value `Faction` `IntEnum`
  (`HERO_GUILD`/`MONSTER_HORDE`/`TOWN_COUNCIL`/`NEUTRAL`) to a string — any content-driven faction
  outside those 4 buckets (set to `Faction.NEUTRAL` at spawn time as the closest legacy default)
  got silently collapsed to `faction_id="neutral"`, discarding the entity's own already-correct
  `faction_id` string. Confirmed via direct corpus measurement: 100% of `dungeon_crawl`'s roster,
  43% of `urban_political`'s.
- `tactical.py`'s own hostile-detection loop (`evaluate_entity_intent`) reads
  `EntityIdentityResolver.resolve(entity).faction_id`, not the more common `get_faction_id_str()`
  helper used elsewhere in the codebase (including this session's own faction-semantics tooling
  and the 2 prior legality-hardening tickets) — this is why the bug was invisible to those
  tickets' own investigation.
- Chose the resolver-side fix over a compiler-side `role_id` population (rejected alternative,
  documented in `plan.md`): the resolver is the single identity-access layer whose own job is to
  gracefully degrade on partial data; fixing only the compiler would leave the same gate
  exploitable by any other current or future caller that sets `faction_id` without `role_id`.
  Confirmed via grep that `ResolvedEntityIdentity.role_id` has zero real consumers anywhere in
  `src/` (only `.faction_id`/`.archetype_id` are ever read), so a derived-not-authored `role_id`
  carries no downstream risk.

## Test Summary
- 2 new unit tests in `tests/unit/entities/test_entity_identity_resolver.py`
  (`test_faction_id_alone_resolves_clean_not_collapsed_to_neutral`,
  `test_faction_id_alone_with_unmappable_legacy_role_gets_unresolved_role`) — all 10 tests in that
  file pass (8 pre-existing + 2 new), confirming both the fix and zero regression to the existing
  clean/legacy/mixed resolution paths.
- Full scoped re-run: `tests/unit/entities/ tests/unit/tactical/ tests/unit/combat/
  tests/unit/strategic/ tests/unit/core/` — 551 passed, zero regressions.
- Real corpus re-verification (2000-tick live `Kernel.tick_once()` loop, `dungeon_crawl_seed42` +
  `urban_political_seed42`, corpus-default feature flags): before the fix, `is_hostile_compat` was
  never once called with `bandit_company` involved across either full run (0 calls). After the fix,
  real hostile-pair legality checks fire for the first time: `goblin_warband`→`undead_remnants`
  (26), `bandit_company`↔`wild_beast_pack` (3), `bandit_company`↔`merchant_league` (2) — a genuine,
  falsifiable, confirmed improvement. Honestly disclosed: every one of these newly-reachable checks
  still fails on `ReasonCode.OUT_OF_RANGE` (attacker `combat.range=1`, checked at real distances
  2-12); `readiness=100.0` in every sampled case, ruling out the already-fixed readiness bottleneck.
  `combat_damage`/`entity_killed` remain zero in this specific 2000-tick window — not claimed as
  fully resolved. Follow-up filed: `TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE`.

## Files Changed
- `src/entities/identity_resolver.py` — Path 1 gate relaxed, derives `role_id` when absent.
- `tests/unit/entities/test_entity_identity_resolver.py` — 2 new tests.
- `docs/audits/D21_entity_lifecycle_foundation_layers.md` — 2026-08-09 update to the "Combat
  legality always false" section.
- `docs/parity_ledger/combat_movement.yaml` — COMB-303.
- `tickets/todos/TCK-20260809-COMBAT-PURSUIT-NEVER-CLOSES-TO-MELEE-RANGE.md` — new follow-up ticket.

## Completion Summary
Traced "why is real per-entity combat still near-zero" all the way to its actual root: an entity-
identity-resolution bug (`EntityIdentityResolver.resolve()` requiring `role_id` alongside
`faction_id`, which the real SimQ-corpus compile path never sets) was silently collapsing most of
the corpus's real, content-driven faction identities to a generic `"neutral"` bucket — destroying
hostility detection for 100%/43% of the two worlds' rosters, and rendering this session's own
already-shipped readiness/friendly-fire legality fixes moot for those entities (they never even
reached a legality check). Fixed with a minimal, additive, resolver-side change verified to have
zero real downstream consumers of the derived field. Real corpus re-verification confirms the fix
genuinely works — hostile pairs are detected and legality-checked for the first time — while
honestly disclosing that a further, distinct bottleneck (pursuit not converging to melee range)
remains and is not yet fixed, filed as its own follow-up rather than folded into or hidden by
this ticket's own claimed scope.

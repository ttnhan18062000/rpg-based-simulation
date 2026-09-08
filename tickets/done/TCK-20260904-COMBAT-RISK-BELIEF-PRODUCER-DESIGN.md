---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN
phase: done
date: 2026-09-04
tags: [content]
---

# TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN

## Title
Design and wire a real producer for entity.strategic.beliefs["combat_risk"] -- a tested consumer with
no production writer

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`TCK-20260904-COMBAT-RISK-BELIEF-DEAD-READ` investigated `src/domains/cooperation/evaluators.py:47`'s
`entity.strategic.beliefs.get("combat_risk")` read and found it is **not dead code** — it's a real,
deliberately designed, tested consumer with no production producer. Confirmed via direct grep: 5 test
files (`tests/unit/domains/cooperation/test_phase7_help_need_evaluator.py`,
`tests/integration/domains/cooperation/test_phase7_cooperation_phase.py`,
`tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py` (x2),
`tests/perf/test_phase7_social_cooperation_budget.py`) manually construct
`entity.strategic.beliefs["combat_risk"] = {"level": RiskLevel.HIGH}` to exercise
`HelpNeedEvaluator.evaluate()`'s HIGH/EXTREME-risk branch — proving the consumer contract is real and
intentional, not leftover cruft. No code anywhere in `src/` writes this key in a live gameplay path;
only tests construct it artificially.

Checked the two most obvious candidate existing signals as a possible reused producer — neither fits
directly:
- `src/systems/strategic_systems/belief.py::estimate_threat()` — also has zero real callers anywhere,
  and models **regional** danger (concerns/leads about a region), not an entity's own personal
  in-combat risk. A different concept, not a drop-in producer.
- No other existing "combat danger assessment" computation was found.

## Scope
- Design what should actually determine an entity's `combat_risk` level (`LOW`/`NORMAL`/`HIGH`/
  `EXTREME`) — candidate signals include recent HP loss/trend, nearby hostile entity count/strength,
  active combat engagement duration, or some combination. This needs real design-authority input, not
  an invented formula — deliberately not decided in this ticket.
- Once designed, implement the producer and wire it into whichever phase should compute it (likely
  strategic cognition or combat-adjacent, given `HelpNeedEvaluator` already runs in Phase 7
  cooperation).
- Confirm the 5 existing tests' manually-constructed `combat_risk` dict shape (`{"level": RiskLevel}`)
  matches whatever the real producer emits — do not silently change the consumer contract without
  updating those tests in the same ticket.

## Out of Scope
- `src/systems/strategic_systems/belief.py::estimate_threat()`'s own separate zero-caller status — a
  distinct finding (regional threat, not personal combat risk), not part of this ticket unless design
  review decides to actually reuse/extend it.
- Any other `StrategicComponent.beliefs` key or the `BeliefEntry`/`KnowledgeFact` reconciliation
  question — already decided separately (`TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION`).

## Acceptance Criteria
- [x] Real combat-risk-assessment design confirmed with design-authority input, not invented
      unilaterally. — Ratified by the real user via `AskUserQuestion` (Option 2, recorded below);
      the `death_risk` source signal and its RiskLevel cutoffs are derived from constants already
      live in `EngagementRiskEvaluator`, not invented.
- [x] A real producer writes `entity.strategic.beliefs["combat_risk"]` in a live gameplay path. —
      `CombatEngagementPhase.apply()` (Phase 4, runs every tick).
- [x] All 5 existing tests that manually construct this belief still pass (or are updated in step with
      a confirmed, deliberate contract change). — All 5 updated to construct a real `BeliefEntry`
      via the production helper; test intent unchanged in every case.
- [x] `HelpNeedEvaluator.evaluate()`'s combat-support-need logic is verified to actually fire in a real
      simulation run at least once, not just in hand-constructed unit tests. —
      `tests/integration/domains/test_combat_risk_belief_end_to_end.py`.

## Related Tickets
- TCK-20260904-COMBAT-RISK-BELIEF-DEAD-READ (the investigation that found this gap)

## Related Docs
- `docs/simulation/belief_and_detour_contract.md` (`BeliefEntry` data model)
- `docs/parity_ledger/strategic_cognition.yaml` (`STRAT-272`, added by this ticket)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN/`

## Related Code Areas
- `src/domains/combat_engagement/phase.py` (`CombatEngagementPhase.apply()` — the new producer)
- `src/domains/cooperation/evaluators.py` (`HelpNeedEvaluator.evaluate()` — the consumer)
- `src/systems/strategic_systems/belief.py` (`BeliefEntry` schema; `estimate_threat()` checked but
  not a direct fit — untouched, still zero-caller, out of scope)
- `src/core/strategic.py` (`RiskLevel`)
- `src/engine/patches.py` (`merge_dict()` — keys `beliefs` by `item.id`)

## Assumptions / Open Questions
- What real signal(s) should determine `combat_risk` level is the central open design question this
  ticket must resolve before implementation — deliberately not decided here.

## Implementation Notes

### Investigation, 2026-09-08 (orchestrator-directed fork — design options only, no code written, no decision made here)

**Findings re-confirmed, still accurate.** `grep -rn "combat_risk" src/ tests/` finds exactly the
same 6 hits the ticket already cites: one consumer read
(`src/domains/cooperation/evaluators.py:47`, `combat_belief.get("level", RiskLevel.NORMAL)`) and 5
tests manually constructing `entity.strategic.beliefs["combat_risk"] = {"level": RiskLevel.HIGH}`.
Zero real producers anywhere. `estimate_threat()` (`src/systems/strategic_systems/belief.py`) is
still a poor fit — regional, not personal, still zero real callers of that specific function.

**New finding #1 — `HelpNeedEvaluator.evaluate()` already reads `entity.combat.hp`/`.max_hp`
directly in a separate branch** (`# 2. Low HP creates healer/protection need`). This means
`combat_risk` is meant to capture something *beyond* current HP — most plausibly ambient/impending
threat exposure (how dangerous is my current surroundings), not a restatement of health state
already checked elsewhere in the same function.

**New finding #2 — a real, already-computed, already-live signal exists that fits exactly:**
`CombatEngagementPhase.apply()` (`src/domains/combat_engagement/phase.py`, Phase 4, runs every
tick) already queries nearby hostiles via a real spatial grid
(`grid.query_radius(actor.navigation.position, 10.0)`, capped at 3 targets) and, for each one,
calls `CombatEngagementDecisionService.evaluate()` → `EngagementRiskEvaluator.evaluate()`, which
computes a real `EngagementRiskEvaluation.death_risk` float in `[0.0, 1.0]`
(`src/domains/combat_engagement/risk_evaluator.py:63-67`) per (actor, target) pair — including a
`>= 0.9` override when the actor has a `near_death` condition. This is genuinely the same concept
`combat_risk` is meant to represent (personal danger from nearby hostiles), already computed with
zero new spatial query or new state needed — just not currently written anywhere.

**New finding #3 — a real write-path complication, not previously flagged in the ticket.** The
generic typed belief-write mechanism (`StrategicUpdate.beliefs_add_or_update`, merged via
`merge_dict()` in `src/engine/patches.py:442-450`) requires each item to be an object with a real
`.id` attribute used as the dict key. Every real production caller
(`src/systems/strategic_systems/belief.py`, `src/systems/strategic_systems/intelligence.py`,
`src/systems/social_systems/guilds.py`) puts a `BeliefEntry` (`id, subject, claim, certainty,
source, ...` — no `level` field, no `.get()` method) through this path. The 5 existing tests'
`{"level": RiskLevel.HIGH}` plain-dict shape is **not** `BeliefEntry`-compatible — `combat_risk`'s
real consumer contract is a separate, bespoke mini-schema that doesn't fit the generic typed
belief-update path at all. Any real producer needs its own dedicated write path, not
`beliefs_add_or_update`.

**Two real candidate approaches, not decided here:**

1. **Minimal (matches existing test contract, recommended as the lower-risk default)**: add a new
   dedicated `StrategicUpdate` field (e.g. `combat_risk_set: Optional[Dict[str, Any]]`, applied as a
   direct assignment in `patches.py` — the same shape as other single-value `_set` fields already on
   `StrategicUpdate`, not routed through `beliefs_add_or_update`/`merge_dict`). Write it from
   `CombatEngagementPhase.apply()`: take the max `death_risk` across all targets evaluated for an
   actor this tick, map it to `RiskLevel` via real thresholds (e.g. `<0.2` LOW, `0.2-0.5` NORMAL,
   `0.5-0.8` HIGH, `>0.8` EXTREME — exact cutoffs need real tuning, not invented here), write
   `{"level": mapped_level}`. Preserves the 5 existing tests and the consumer's `.get("level", ...)`
   call completely unchanged — zero contract change.
2. **Architecturally cleaner, bigger, real contract change**: migrate `combat_risk` onto the real
   `BeliefEntry` system (e.g. `claim` carries the risk level as a string). Fixes the
   generic-belief-schema inconsistency this investigation surfaced, but requires changing
   `HelpNeedEvaluator.evaluate()`'s own read (`.get("level", ...)` → a `BeliefEntry` lookup +
   `claim`/`certainty` interpretation) and updating all 5 existing tests' construction pattern in the
   same ticket, per this ticket's own Scope. Bigger, more invasive, needs explicit sign-off since it
   deliberately changes an existing tested contract rather than just filling a producer gap.

**Recommendation, not a decision**: Option 1, wired into `CombatEngagementPhase.apply()` using
`death_risk`. It reuses a real, already-computed, already-live-every-tick signal with zero new
spatial query or state, requires no test changes, and directly represents "personal danger from
nearby hostiles" — the gap `HelpNeedEvaluator`'s separate HP-based branch doesn't already cover.
Real threshold tuning (the 4 cutoff values) still needs a real decision or at minimum a documented,
evidenced starting point — not invented unilaterally by whoever implements this.

**Decision NOT made here per this fork's directive** — brought back to the orchestrator/user.

### Decision, 2026-09-08 (real user decision, via `AskUserQuestion`, orchestrator-initiated)
**Option 2 — migrate `combat_risk` onto the real `BeliefEntry` system properly**, not the minimal
dedicated-field approach. This is the bigger, more invasive change: `HelpNeedEvaluator.evaluate()`'s
own read (`.get("level", ...)`) must change to a `BeliefEntry` lookup + `claim`/`certainty`
interpretation, and all 5 existing tests' construction pattern must be updated in the same ticket,
per the ticket's own Scope. The real `death_risk` signal from `CombatEngagementPhase.apply()` →
`EngagementRiskEvaluator.evaluate()` (already confirmed live-every-tick) is still the right source
signal to write from — this decision only changes *how* it's written (through the generic
`BeliefEntry`/`beliefs_add_or_update` path, not a new bespoke `StrategicUpdate` field), not *what*
computes it. Threshold tuning (mapping `death_risk` float to a `RiskLevel`/claim value) still needs
a real, evidenced starting point during implementation, not invented arbitrarily.

### Implementation, 2026-09-08

Implemented the ratified Option 2. Three real findings from the implementation pass, beyond what
the prior investigation recorded (full detail in
`stored_artifacts/TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN/investigation.md`):

1. **The `BeliefEntry.id` must literally be `"combat_risk"`.** `merge_dict()`
   (`src/engine/patches.py`) keys the beliefs dict by `item.id`, and the consumer looks up
   `beliefs.get("combat_risk")` — so the id *is* the key. A stable (non-tick-suffixed) id is
   deliberate: this is a *current* assessment replaced in place each tick, unlike the
   rumor/observation precedent's tick-suffixed ids, which here would grow the dict without bound
   every tick an actor stands near a hostile. Covered by a dedicated regression test.
2. **`CombatEngagementPhase.apply()` evaluates exactly ONE target, not three** — it computes
   `targets_to_evaluate = targets[:3]` but the loop body ends in `break  # evaluate first target
   only`. This corrects the prior investigation's "max `death_risk` across all targets evaluated"
   phrasing. Deliberately left as-is: evaluating all 3 would triple this phase's evaluation cost in
   a phase whose own comments call out staying "strictly within strategic budget", and changing
   engagement-evaluation breadth is outside this ticket. The single existing evaluation is reused at
   **zero** added cost.
3. **Real threshold precedent found — no invented numbers.** The cutoffs come from constants already
   live in `EngagementRiskEvaluator.evaluate()`, which computes
   `death_risk = clamp((1.0 / power_ratio) * 0.4, 0.0, 1.0)`:
   `power_ratio` 2.0 (actor twice as strong) → 0.20; 1.0 (evenly matched) → 0.40; and `> 0.80` is
   that evaluator's **own** `hp_critical_safety_lock` cutoff, where its `near_death`
   `max(0.9, ...)` floor deliberately lands. Hence `<=0.20` LOW, `<=0.40` NORMAL, `<=0.80` HIGH,
   `>0.80` EXTREME — an evidence-anchored starting point, documented as tunable, not a final
   calibrated answer.

Consumer contract change (required by the ratified decision): `HelpNeedEvaluator.evaluate()` no
longer calls `.get("level", ...)` on a plain dict — `BeliefEntry` is a frozen slots dataclass with
no `.get()`. It now reads `.claim` and parses it back into a `RiskLevel`, degrading to `NORMAL` on
an absent or unparseable claim rather than raising (the `beliefs` dict is generically typed, so a
foreign entry under this key must not break Phase 7).

### Correction (2026-09-08)

A post-merge peer review (`rpg-feature-planning`) of this ticket found a real correctness bug in
`CombatEngagementPhase.apply()`'s target-selection logic (item 2 above), independent of the
budget-cost tradeoff already documented there:

- **No hostility filter at all.** `targets` was built from `grid.query_radius()` (or the fallback
  range scan) filtering only on `alive`/`lifecycle.active` — any nearby entity qualified,
  including an ally, a villager, or a child. The method's own docstring ("Evaluate eligible actors
  on hostiles entering sensory visibility") was not actually true of the code.
- **`targets[:3]` was dead code.** The unconditional `break  # evaluate first target only` fired
  after the first loop iteration regardless of that slice, so in practice `combat_risk` was always
  written from whichever entity happened to come first in the unordered candidate list — not
  necessarily the nearest, and not necessarily hostile.
- **Consequence:** `combat_risk` could silently under-report an actor's real danger (e.g. read as
  LOW because a harmless neighbor happened to be evaluated instead of an adjacent lethal hostile),
  exactly the failure mode `HelpNeedEvaluator.evaluate()`'s HIGH/EXTREME-only trigger (see the
  "Consumer contract change" paragraph above) is meant to catch.

**Fix**, scoped to `src/domains/combat_engagement/phase.py` only: candidates are now filtered
through `FactionSemanticsService.is_hostile_compat()` (`src/content_semantics/faction.py`) — the
same hostility-check precedent `src/engine/legality.py`/`tactical.py`/`combat_rewards.py` already
use for this exact question, reused rather than reinvented — and exactly the nearest hostile
candidate is evaluated. The dead `[:3]`/`break` pattern is removed; item 2's own "single evaluation
at zero added cost" budget property is preserved unchanged (still one `evaluate()` call per actor
per tick), only *which* target gets evaluated changed. Docstring/comments updated to describe the
corrected behavior.

A new regression test (`test_combat_risk_is_written_from_the_nearest_hostile_not_an_arbitrary_neighbor`
in `tests/unit/domains/combat_engagement/test_combat_risk_belief_producer.py`) reproduces the exact
scenario: a harmless NEUTRAL neighbor sits closer to the actor than a genuine MONSTER_HORDE threat.
6 pre-existing tests across 4 files (`test_combat_risk_belief_producer.py`,
`test_fused_loop.py`, `test_phase4_combat_engagement_phase.py`,
`test_combat_risk_belief_end_to_end.py`) relied on entities defaulting to the same (NEUTRAL)
faction and therefore being treated as hostile purely by accident of the missing filter — updated
to construct explicit `Faction.HERO_GUILD`/`Faction.MONSTER_HORDE` pairs, which is what they always
should have needed. One test (`test_combat_engagement_caps_candidates`) was renamed to
`test_combat_engagement_evaluates_exactly_one_nearest_hostile_among_many` since its own name/intent
(capping a 3-target evaluation) no longer matched what the corrected code does (select one, from
real hostile candidates). Full `tests/unit/` + `tests/integration/` sweep re-run after the fix
(`-m "not slow"`): both combat_engagement-related failures fixed and passing; the remaining 9
sweep failures were independently confirmed pre-existing/unrelated (7 are `tests/unit/domains/
progression/` test-order-dependency artifacts that pass when run in a smaller isolated batch; 2 are
`TimeoutError` resource-limit failures — `test_entity_differentiation.py::
test_bravery_quartile_combat_rate_2x` and `test_long_run_stability.py::test_long_run_stability` —
confirmed to fail identically on the unmodified pre-fix code, so not a performance regression from
this change).

## Test Summary
19 new tests added across 2 files; all 5 pre-existing tests migrated to construct a real
`BeliefEntry` via the production helper (`build_combat_risk_belief`) rather than duplicating the
shape — so they now fail loudly if the producer's own contract drifts. Test intent unchanged in
every migrated case.

- `tests/unit/domains/combat_engagement/test_combat_risk_belief_producer.py` (new, 20 tests):
  threshold-boundary mapping (9 parametrized cases at each cutoff ±0.01, plus the `near_death` 0.9
  floor), producer contract shape, certainty clamping, real-phase emission, no-emission when no
  hostile is nearby, durable-state landing under the consumer's lookup key through the real
  `ApplyPath`, replace-not-accumulate across repeated ticks, and consumer parsing including the
  malformed-claim and absent-belief degrade paths.
- `tests/integration/domains/test_combat_risk_belief_end_to_end.py` (new, 2 tests): **AC #4** — a
  real 3-tick `AuthoritativeApplyPipeline.refine()` + `ApplyPath.apply_generation()` loop with both
  gating flags ON. The multi-tick span is load-bearing: `cooperation` runs *before*
  `combat_engagement` in `refine()`, so a belief written this tick is only visible to the consumer
  next tick — a single-tick test would pass vacuously. Verified genuinely non-vacuous before
  finalizing: the run produces `BeliefEntry(claim='HIGH', certainty=0.66)` and
  `HelpNeedEvaluator` returns `combat_support_needed`. The level assertion is made **directly**
  rather than guarded behind an `if`, so it cannot silently skip if the formula drifts. Plus a
  negative control (isolated entity → no belief fabricated).

Results: ticket-scoped suite **89 passed, 0 failed**. Broader regression sweep
(`tests/unit/strategic/`, `tests/unit/domains/`, `tests/integration/domains/`,
`tests/integration/scenarios/`, `tests/architecture/`, `-m "not slow and not extra_slow"`):
**1537 passed, 1 skipped, 0 failed**.

## Files Changed
- `src/domains/combat_engagement/phase.py` (producer: `COMBAT_RISK_BELIEF_ID`,
  `death_risk_to_level()`, `build_combat_risk_belief()`, wired into `apply()`)
- `src/domains/cooperation/evaluators.py` (consumer: `BeliefEntry.claim` read + safe parse)
- `tests/unit/domains/cooperation/test_phase7_help_need_evaluator.py` (migrated)
- `tests/integration/domains/cooperation/test_phase7_cooperation_phase.py` (migrated)
- `tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py` (migrated, 2 sites)
- `tests/perf/test_phase7_social_cooperation_budget.py` (migrated)
- `tests/unit/domains/combat_engagement/test_combat_risk_belief_producer.py` (new)
- `tests/integration/domains/test_combat_risk_belief_end_to_end.py` (new)
- `docs/parity_ledger/strategic_cognition.yaml` (new `STRAT-272`, written via
  `tools/parity_ledger_writer.py`, not hand-edited)
- `stored_artifacts/TCK-20260904-COMBAT-RISK-BELIEF-PRODUCER-DESIGN/` (investigation, plan,
  test_plan)

**Correction (2026-09-08):**
- `src/domains/combat_engagement/phase.py` (hostility filter via `is_hostile_compat()`,
  nearest-hostile selection, dead `[:3]`/`break` removed, docstring corrected)
- `tests/unit/domains/combat_engagement/test_combat_risk_belief_producer.py` (3 tests updated with
  explicit factions; 1 new regression test)
- `tests/integration/domains/test_fused_loop.py` (1 test renamed and rewritten)
- `tests/integration/domains/combat_engagement/test_phase4_combat_engagement_phase.py` (1 test
  updated with explicit factions)
- `tests/integration/domains/test_combat_risk_belief_end_to_end.py` (1 test updated with explicit
  factions)

## Completion Summary
`entity.strategic.beliefs["combat_risk"]` had a real, deliberately-designed, tested consumer
(`HelpNeedEvaluator.evaluate()`) and **zero** production producer — only tests constructed it, using
a bespoke `{"level": RiskLevel}` plain dict that was never `BeliefEntry`-compatible in the first
place. Per the real user's ratified decision (Option 2, the bigger migration rather than the minimal
bespoke-field workaround), `combat_risk` now lives on the real `BeliefEntry` system: written every
tick by `CombatEngagementPhase.apply()` from the `death_risk` that phase already computes, and read
back by the consumer via `.claim`. The generic-belief-schema inconsistency the investigation
surfaced is resolved rather than worked around, and the previously-unreachable
`combat_support_needed` branch is now proven to fire in a real multi-tick engine run. Threshold
cutoffs are derived from the risk evaluator's own live constants and documented as a tunable
starting point, not presented as final calibration.

---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION
phase: open
date: 2026-09-14
tags: [faction, grand-strategy]
---

# TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION

## Title
Sieges, territory transfer, and `EXPAND_TERRITORY` all require a formal `DiplomaticState.WAR` between factions that no observed run has ever produced — the user has reversed the prior "accepted long-horizon divergence" disposition; find whether any real design declares when war should happen before building anything

## Status
BLOCKED

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
`docs/plans/deferred_tuning_decisions_register.md`'s own D-06 entry: siege progression, territory
transfer, and `EXPAND_TERRITORY` are all live, wired code
(`src/engine/military_conflict.py`) gated on a formal `DiplomaticState.WAR` between two factions.
No WAR was declared in any observed run, including a real 200-tick `campaign_life_arc` episode.
Siege completion itself is fast once war exists (~20-34 ticks) — **the bottleneck is war never
starting, not siege being slow.** `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT`
and `TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION` (both done) originally accepted this as a
disclosed long-horizon divergence.

**The user has reversed that disposition** — same as the sibling maturity-gate ticket
(`TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`), filed from the same decision. Per
D-06's own caveat: "how *often* factions should go to war is tuning; whether they *ever* do in a
real run is reachability."

## Scope
- **Investigation first, no implementation until peer has reviewed the design question.**
- **The central question, per explicit instruction: find whether any real design declares WHEN a
  faction should go to war.** A first pass already located a real candidate —
  `DiplomaticStateMachine.compute_transitions()` (`src/domains/faction/diplomatic_state_machine.py`)
  — a tension/military-strength-driven state machine (`NEUTRAL → TENSE` at `pair_tension > 0.4`,
  `TENSE → HOSTILE` at `pair_tension > 0.7` or shared territory, `HOSTILE → WAR` at a >20%
  military-strength imbalance). **This needs real verification, not assumption**: is this a real,
  intentional design answering "when should war happen," or is it itself unreachable/decorative
  (matching this week's own repeated pattern of mechanisms that exist in code but never fire in
  practice)? Check what real `tension_level`/`military_strength`/`territory` values actually look
  like across a real run, and whether the WAR-transition thresholds are ever actually approached.
- If `DiplomaticStateMachine` is confirmed to be a real, working design that simply never reaches
  its own thresholds in practice (a reachability problem, same shape as D-05), investigate why —
  which of `pair_tension`, `shared_territory`, or `military_strength` imbalance is the actual
  blocker, and whether a realistic run could ever produce it.
- **If no real design exists for when war should happen** (i.e., if `DiplomaticStateMachine` turns
  out to be dead/decorative, or if there's no other real trigger anywhere), **stop and bring that
  finding to peer/user rather than choosing a trigger condition** — inventing when factions go to
  war is real game design, the same category of decision as per-enemy danger ratings were treated
  as this arc, not an implementation detail to decide unilaterally.

## Out of Scope
- Actually building or changing any war-declaration trigger — investigation only, per explicit
  instruction, regardless of which of the two outcomes above the investigation finds.
- The lair/world-boss maturity gate (D-05) — sequenced separately, own ticket
  (`TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`), different shape of problem (that one
  already has a real, working trigger design; this one's own design status is what's in question).
- Siege mechanics/territory transfer/`EXPAND_TERRITORY` themselves — already confirmed live, wired
  code per D-06's own text; not what's broken here.

## Acceptance Criteria
- [ ] A real, evidence-backed answer on whether `DiplomaticStateMachine.compute_transitions()` (or
      any other mechanism) constitutes a genuine, working design for when war should happen, versus
      being itself unreachable or absent.
- [ ] If a real design exists but is unreachable in practice: real evidence (not assumption) on
      which precondition (tension, territory, military-strength imbalance) is the actual blocker.
- [ ] If no real design exists: the finding is brought to peer/user explicitly as a design question,
      not decided or built here.
- [ ] No implementation without that review, regardless of which outcome the investigation finds.

## Related Tickets
- `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT` (done — one of the two tickets
  that originally deferred this)
- `TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION` (done — the other)
- `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY` (filed alongside this one, from the
  same user decision — sequenced first, different shape of problem)

## Related Docs
- `docs/plans/deferred_tuning_decisions_register.md` § D-06 (the entry this ticket investigates)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/domains/faction/diplomatic_state_machine.py` (`compute_transitions()` — the candidate real
  design for war-declaration timing, not yet verified as reachable or intentional)
- `src/engine/military_conflict.py` (`MilitaryConflictPhase` — consumes an already-WAR relation for
  siege/territory logic; confirmed not itself the producer of a WAR declaration)
- `FactionState.tension_level`/`.military_strength`/`.territory` (the real inputs
  `compute_transitions()` reads — their own real producers/typical values not yet traced)

## Assumptions / Open Questions
- Whether `DiplomaticStateMachine` is a real, reachable design or another dormant mechanism is the
  central open question this ticket exists to answer — not assumed either way here.

## Implementation Notes
**2026-09-14: investigation complete, no code changed — bringing findings to peer/user review
before any implementation, per this ticket's own explicit instruction.** Full detail in
staging_artifacts/investigation.md. Summary:
- **Central question answered: a real design exists.** `DiplomaticStateMachine.compute_transitions()`
  is a real, deliberate, deterministic 4-step state machine (NEUTRAL→TENSE→HOSTILE→WAR→NEUTRAL),
  genuinely wired into the real tick pipeline (`src/engine/pipeline.py:260`, called every tick).
  This is not the "no design exists" outcome.
- **But it's unreachable in practice, via three independent, partly-circular blockers**, confirmed
  via a real 3000-tick simulation (`urban_political`, seed=42, 16 factions):
  1. `military_strength` is mathematically frozen at `1.0` for every faction, always — the only
     real producer (a WAR-exhaustion drain) only applies to factions already at war. The `WAR`
     transition's own `>20% imbalance` precondition can never be satisfied from real pre-war state.
  2. `territory` is circularly blocked — no world spec ever seeds it at compile time (confirmed:
     zero references to `territory` anywhere in `WorldCompiler`), and the only real runtime
     producer (siege-won territory transfer) itself requires an existing WAR to fire. `shared_territory`
     can never be the thing that triggers a *first* war.
  3. `tension_level`'s only real runtime producer is *also* gated on territory (a `RESOURCE_DEPLETED`
     event must land inside the faction's own territory) — so it's blocked by the same root cause
     as #2. The only way any faction ever gets nonzero tension is compile-time authoring (2 of 16
     factions in the real corpus, seeded at 0.5), which clears `NEUTRAL→TENSE` (>0.4) but falls
     short of `TENSE→HOSTILE` (>0.7) and never moves further — confirmed empirically, every such
     pair got stuck at TENSE for the full 3000-tick run.
- **Not "just slow" — not one large number.** Fixing this cleanly likely needs at least one new
  real mechanism (military-strength divergence before war, and/or a territory/tension producer
  that doesn't itself require war to exist first), not just reachable threshold values — a real
  design decision, flagged explicitly rather than assumed to be the same shape as the sibling
  maturity-gate ticket (D-05).

## Test Summary
_(none — investigation only; findings verified via direct probes against a real, instrumented
3000-tick simulation and direct code/grep evidence, not committed as test files, since no fix has
been chosen yet)_

## Files Changed
_(none — investigation only, per this ticket's own explicit instruction)_

## Completion Summary
_(not complete — investigation delivered a real, evidence-backed answer per the ticket's own
acceptance criteria; awaiting peer/user review before any implementation proceeds)_

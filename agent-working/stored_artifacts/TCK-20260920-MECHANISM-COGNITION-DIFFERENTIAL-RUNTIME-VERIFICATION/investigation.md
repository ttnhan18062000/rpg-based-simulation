---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION
artifact_type: investigation
tags: [simulation-quality, testing, cognition]
---

# Investigation — TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION

## Context scan
`mcp__knowledge-search__search_docs` + `graphify query` run first, per Context Scan. Key prior art
found and reused rather than reinvented:

- `docs/plans/mechanic_verification_scenarios_proposal.md` — the design doc for the differential
  scenario component. §3.2 (real compile path, not synthetic `V2EntityBuilder` fixtures), §3.3
  (mandatory differential structure — a scenario that can't fail proves nothing, the exact lesson
  from the combat-judgement scenario's own first naive attempt).
- `tests/mechanic_scenarios/test_action_pacing_readiness_gate.py` +
  `TCK-20260916-ACTION-PACING-READINESS-SCENARIO-VERIFICATION` — the only prior real use of this
  component. Pattern reused directly: compile a real world via `WorldRepository` +
  `WorldCompiler.compile()`, stage the precondition via `dataclasses.replace()` on compiled
  entities, dispatch through a real `Kernel.tick_once()`, assert on the real observable outcome
  (not a mocked one), always as two conditions (precondition present vs. absent) on the same
  dispatch.
- `registries/mechanisms.yaml`'s 20 `cognition`-system entries — all `code_trace`, 0/20
  runtime-backed (`runtime_verified_share` for this group is 0.0), confirmed directly via a script
  read of the registry, not assumed from the summary rollup.

## Candidate selection (per the peer's explicit criteria — done deliberately, not defaulted)

1. **A `done` mechanism that genuinely matters.** Peer named `goal_hierarchy`, `perception`, or
   `belief_cycle`. Chose **`belief_cycle`** over `goal_hierarchy`: `resolve_lead_staleness()` is a
   single, pure, threshold-gated decision function
   (`src/systems/strategic_systems/belief.py::BeliefCycleSystem.decay_stale_leads`, `stale_threshold:
   int = 50`) with one real, unconditional (`feature_flag=None`), always-on pipeline entry point
   (`src/engine/pipeline.py:408`,
   `run_phase("belief_staleness_decay", update, lambda u: u.merge(BeliefCycleSystem.resolve_lead_staleness(state)))`).
   `goal_hierarchy`'s own 5 methods are entangled in a 1782-line multi-concern class with
   cadence-gated dispatch and multi-field preconditions (`interruption_resistance`,
   `resistance_multiplier`, per-kind score-scale normalization) — a materially larger surface to
   get right on the first, harness-proving batch, for no added confidence about whether the harness
   itself works. `belief_cycle` proves the same thing (a real `done`, load-bearing, always-on
   mechanism) with the smallest honest surface.

2. **One where a contradiction is genuinely plausible.** Investigated `perception` first (not
   picked in advance) specifically because peer named it as an equally valid "matters" candidate —
   and found a real, unexpected problem: `PerceptionFilterService.filter()`
   (`src/domains/perception/filter.py`) has exactly one caller in all of `src/`,
   `PerceptionUpdatePhase.run()` (`src/domains/perception/phase.py:43`) — and **`PerceptionUpdatePhase`
   itself has zero callers anywhere in `src/`** (confirmed by grep across the whole tree, not just
   `pipeline.py`). Nothing else in `src/` constructs a `PerceptionModel` or writes
   `perceived_entities`/`perceived_threats`/etc. either. `perception`'s own `verified` block
   (`instrument: code_trace, verdict: observed`) cites "called from
   `src/domains/perception/phase.py:43`, a real, non-test integration into the per-tick pipeline" —
   but line 43 is *inside* `phase.py` itself; the class that would call it from the real tick loop
   is never instantiated by `src/engine/pipeline.py` or anywhere else. This is exactly the shape
   `mechanism_state_caller_check.py` cannot catch: it confirms `PerceptionFilterService` has a real
   caller (`phase.py`) without checking whether that caller's own caller is itself reachable — a
   one-level-deep check missing a two-level-deep dead chain. Moved `perception` into this slot
   instead of a second "safe" pick, per the explicit instruction not to reproduce §3.3's own
   selection effect in this very next program.

3. **A known negative, for calibration.** `quest_generation_sourcing` — already `state: orphan`,
   `verdict: contradicted` (code_trace), from this session's own earlier batch: `QuestGenerationSystem`
   (`src/systems/world_systems/quests.py`) has zero real callers for any of its 3 methods,
   independently re-confirmed by a fresh grep this pass (no output). `generate_from_scar(region,
   current_tick)` is a simple, pure, single-precondition function (`region.trauma_score > 0.3`) —
   easy to stage a real "trigger condition present" world and confirm the harness reports the
   correct negative rather than a false positive.

## What "differential" means for each of the three

- **`belief_cycle`**: stage a `LeadState` (`certainty=APPROXIMATE`, `discovered_tick=0`) on a real
  compiled entity. Run one real `Kernel.tick_once()` at `state.tick=50` (precondition met — `50 - 0
  >= stale_threshold(50)`) vs. `state.tick=10` (precondition not met). Assert the lead's certainty
  demotes to `VAGUE` only in the first case.
- **`perception`**: stage a real compiled world with a genuinely perceivable candidate (another
  live entity in range) and run several real `Kernel.tick_once()` calls. If the mechanism is real,
  `entity.cognition.subjective.perception.perceived_entities` should populate. Also wrap
  `PerceptionFilterService.filter` with a call counter (same technique as the readiness-gate test's
  `CombatActions.execute_attack` wrapper) as a second, independent signal — not just an absence of
  a field, since §5.2 of the proposal warns a passing-looking absence can still be a scenario-design
  gap rather than a real finding. Both signals must be checked before concluding `contradicted`.
- **`quest_generation_sourcing`** (calibration): a real compiled world with a region forced to
  `trauma_score = 0.9` (clears the real `0.3` threshold `generate_from_scar` itself checks) run for
  several real ticks, wrapping all 3 `QuestGenerationSystem` methods with call counters. Positive
  control: call `QuestGenerationSystem.generate_from_scar()` directly (bypassing the Kernel) against
  the same region to confirm the code itself does produce a `QuestTemplate` when invoked — so a
  zero-call result from the real Kernel run is attributable to "never invoked," not to the trauma
  precondition being wrong or the function itself being broken.

## Governing constraint
Per explicit instruction: if an instrument contradicts a claim, record the contradiction and stop —
do not wire `PerceptionUpdatePhase` into `pipeline.py` to make the claim true. Any real fix is filed
as its own ticket, not built here.

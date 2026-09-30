---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED
phase: open
date: 2026-09-20
tags: [simulation-quality, cognition]
---

# TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED

## Title
Design decision needed: which of three perception-shaped things in this codebase is meant to be
the real one? (Not a wiring bug — a scope-of-concept question for the roadmap session.)

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Found by `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION`'s differential
runtime scenario, not fixed there per that program's explicit governing constraint (record the
contradiction, do not fix the code to make an old claim true in the same pass), and explicitly
reframed here per peer review before it could ossify into a "just wire it up" bug ticket: **this
codebase currently has three real, distinct, perception-shaped things, and nothing declares which
one is meant to be the entity's actual perception.**

1. **A designed abstraction nothing consumes**: `src/domains/perception/filter.py::
   PerceptionFilterService` + `src/domains/perception/phase.py::PerceptionUpdatePhase`. Real,
   correct code — scores candidate signals, budget-clamps them into a ranked `PerceptionModel`
   (`perceived_entities`/`perceived_threats`/`perceived_resources`/`perceived_services`/
   `perceived_opportunities`). But `PerceptionUpdatePhase` is never instantiated anywhere in `src/`
   outside its own file (confirmed by full-tree grep and a real differential Kernel-run scenario,
   `tests/mechanic_scenarios/test_perception_pipeline_wiring.py`: zero real `.filter()` calls and
   an empty `perceived_entities` across 5 real ticks against a world with an adjacent, perceivable
   entity; a positive control proves the code itself works when called directly). And even if it
   were wired in, **nothing downstream reads its output either** — zero real code anywhere in
   `src/` reads any `PerceptionModel` field outside this dead chain itself, independently confirmed
   while investigating why `perception` has zero registry `depends_on` dependents.
2. **A direct bypass strategic cognition actually uses instead**: `goal_hierarchy`'s own verified
   note documents `StrategicIntelligenceSystem` sourcing situational awareness through a direct
   `SpatialQueryService.nearby_entities()` spatial query — real, wired, load-bearing, but a
   completely different mechanism from the `PerceptionModel` abstraction above, with no budget
   clamp, no salience ranking, no "what does the entity consciously notice" concept at all.
3. **A live, unregistered gate doing raw sense-detection**: `src/world/perception/gate.py::
   PerceptionGate`, real and wired (`src/engine/tactical.py:181,199`, initialized via
   `src/content/warmup.py`), but scoped narrowly to "can this entity detect that specific neighbor
   at all" (vision/hearing/smell/etc. against a target's emitted signals) for `TacticalDecisionSystem`'s
   own targeting — upstream of a decision, not itself a notice-and-remember abstraction.

The registry's own `perception` entry (state `done` → `orphan`, verdict → `contradicted`) has
already been corrected to reflect that thing #1 specifically is dead. This ticket is not "fix thing
#1" — a fix there would leave things #2 and #3 exactly as unresolved as they are now, and might not
even be the right thing to fix. **This is a design question about which of the three is meant to be
canonical**, or whether they're meant to coexist with distinct, non-overlapping scopes that just
need to be declared as such.

## Scope
For the roadmap/planning session to decide, not to implement here:
1. Is `PerceptionModel` (thing #1) meant to be the real strategic-cognition-facing perception layer,
   with `goal_hierarchy`'s direct spatial-query bypass (thing #2) meant to be replaced or folded
   into it? Or was the direct bypass always the intended design, making thing #1 a superseded,
   removable abstraction?
2. Should `PerceptionGate` (thing #3) be registered as its own mechanism (its scope — raw
   detection capability — is real and narrower than either of the above), and if so, does it
   belong under `cognition` or a different system?
3. Whichever direction is chosen, what should happen to the other(s): remove, repurpose, or
   explicitly scope them apart with a registry note (the same "declare the boundary, don't erase
   the history" treatment `tactical_decision`'s own entry now gives `PerceptionGate`)?

## Out of Scope
- Implementing any of the above — this ticket exists to get a decision, not to make one
  unilaterally.
- Re-verifying the finding itself — already confirmed by a real differential scenario and a direct
  full-tree grep for consumers, not to be re-litigated here without new evidence.
- Any other `cognition` mechanism, or the broader registry-completeness scope-gap question this
  investigation also surfaced (tracked separately:
  `TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP`).

## Acceptance Criteria
1. A real design decision from the roadmap session on which perception-shaped thing (or
   combination) is canonical.
2. Once decided: either a real implementation ticket scoped to that decision, or an explicit
   "coexist, here's why" registry note update — never a silent code change made to match a guess
   at what the decision would have been.

## Related Tickets
- `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION` — found this, did not fix it
- `TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP` — the broader "how much other live code
  isn't in the registry" question `PerceptionGate` surfaced, tracked separately

## Related Docs
None yet.

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/domains/perception/phase.py::PerceptionUpdatePhase`
- `src/domains/perception/filter.py::PerceptionFilterService`
- `src/domains/perception/salience.py::WorldSignal`
- `src/systems/strategic_systems/intelligence.py` (the `SpatialQueryService.nearby_entities()` bypass)
- `src/world/perception/gate.py::PerceptionGate`
- `src/engine/pipeline.py`
- `src/engine/tactical.py`

## Assumptions / Open Questions
None outstanding on the investigation side — the three things and their real/dead/scope status are
all directly confirmed, not assumed. The open question is purely the design call in Scope above.

## Implementation Notes
(none yet — not started; awaiting the design decision this ticket exists to request)

### 2026-09-30 — classified via `TCK-20260930-UNREACHABLE-CLASSIFY-PERCEPTION-AUTHORITY` (epic `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION`, child `T05`): verdict `UNDECLARED` (confirmed); the decision needs a human and is not made here

**Facts re-checked at branch tip `d96abd0d5`; nothing has changed since filing** (no commit to `src/domains/perception`,
`src/world/perception` or `pipeline.py` since 2026-09-20).
- `PerceptionUpdatePhase` has no reference in `src/` outside its own file; `tests/mechanic_scenarios/test_perception_pipeline_wiring.py` — 2 passed.
- No reader of any `PerceptionModel` field exists outside `src/domains/perception/` and the dataclass itself (`src/core/cognition.py:75-93`).
- **A second missing piece the ticket did not name:** the phase's input, `world_signals`, has no production producer either. The
  only `WorldSignal` constructor outside the domain is `LegendFactService.to_world_signal` (`src/domains/fame/legend.py:76-92`), which
  has no production caller (two unit tests only). Wiring the phase alone would still feed it nothing.
- Thing #2 is `intelligence.py:144` (`nearby_entities(..., radius=10.0)`); thing #3 is consumed by `tactical.py:198-202` as a
  per-target detection test whose exceptions fall through permissively (`except Exception: pass`).

**The ticket's premise is partly wrong: things *are* declared — twice, and the declarations conflict.**

| Source | Authority / date | What it says perception is |
|---|---|---|
| `docs/mechanics/04_strategic_cognition.md` §5 | Certified Level 1; section last changed 2026-07-02 | a `10.0`-unit radius neighbor view; the "Salience Filter" is "within the perception radius"; cites `domain_logic.py`, `view.py`, `intelligence.py` — thing #2 |
| parity `STRAT-238` | `verified`, P1, `test_path: null` | pins the `10.0` radius in those files — thing #2 |
| `docs/simulation/domains/perception_contract.md` | `status: active`, P1; created 2026-06-13, `last_verified` 2026-09-01 | each entity's budget-clamped `PerceptionModel`, produced by the Perception Update stage after `PerceptionGate`; "downstream consumers (adventure routing, strategy) act on the populated `PerceptionModel`" — thing #1 (+ #3 as an upstream prerequisite). Its own header admits zero call sites; it never mentions thing #2 |
| `docs/world/opportunity_providers_contract.md` | active | the gate "runs before the perception domain's own attention/salience step" |
| parity `STRAT-261` | `verified`, P2 | verifies the attention-focus read by a test that calls it directly, while stating its only pipeline caller has zero call sites |
| registry `perception` | `orphan` / `contradicted`, 2026-09-20 | thing #1 is dead |

The contract's stated flow — gate -> `world_signals` -> Perception Update -> downstream consumers — does not exist: the gate's real
consumer is tactical targeting, there is no signal producer, and there are no consumers. The Bible describes a different system that
does run. So the gap is a *reconciliation* between two authoritative descriptions, not a missing first declaration. A fourth thing
carries the same word: a stat, `perception: int = 5` (`src/core/state.py:557,572`), not investigated here.

**Precedence not applied.** The project rule that the Mechanics Bible wins would mechanically make thing #2 canonical and #1 removable.
That rule settles legacy-vs-Bible ambiguity; this is a Bible-vs-domain-contract split, and applying it would silently make the design
decision. It is recorded as a decision, not resolved by rule.

**What the declaration would have to say** (five questions, none answered here):
1. What is "the entity's perception" — the radius view (#2), the budgeted `PerceptionModel` (#1), or a declared layering of the gate (#3) under one of them?
2. What consumes it? Today strategy consumes the raw radius query, tactics consume the gate, and nothing consumes `PerceptionModel`.
3. Where does it sit in the tick pipeline, and in what order relative to the gate?
4. What happens to the non-canonical pieces — remove, repurpose, or explicitly scope apart with a registry note?
5. Which document is authoritative (Bible §5 or the contract), and which of `STRAT-238` / `STRAT-261` / the registry `perception` entry change with it?

**What a decider should know:** choosing #1 means building three things, not one — instantiating the phase in the pipeline, a producer
of `world_signals`, and at least one consumer of the model — plus a determinism and state-hash review (whether `PerceptionModel` is in
the hash surface was not checked). Choosing #2 means removing code, the contract, `STRAT-261`'s subject and the registry entry, with
nothing else reading them. A "coexist" answer has to give #1 a job that #2 does not do. **No option is chosen here; the decision needs
the user or the roadmap owner.**

## Test Summary
(none yet)

## Files Changed
(none yet)

## Completion Summary
(none yet)

**Verdict as of 2026-09-30: `UNDECLARED` (confirmed)** — but two authoritative declarations exist and conflict (Bible §5 vs the perception contract); reconciliation needs a human decision, not made here. See Implementation Notes. Still `OPEN`.

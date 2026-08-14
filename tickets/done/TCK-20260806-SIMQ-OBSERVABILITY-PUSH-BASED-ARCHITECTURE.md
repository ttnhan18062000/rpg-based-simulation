---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE
phase: done
date: 2026-08-06
tags: [observability, engine, simulation-quality, performance]
---

# TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE

## Title
Investigate replacing post-tick snapshot-diff event extraction with push-based emission at the
authoritative apply layer

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
A 2026-08-06 investigation (parent: `TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY`)
traced how simulation events actually get produced and found the entire observability pipeline —
not just combat — is built on **post-tick snapshot diffing**, not trigger-point emission:

- `src/engine/kernel.py:909`: `EventExtractor.extract(prior_state, self._state, update, obs_mode)`
  is called **once per tick** and is the **sole source of nearly every event type** in the corpus
  (`quest_event`, `diplomatic_transition`, `gold_sink_fired`, `resource_harvested`,
  `trade_executed`, `combat_damage`, `xp_granted`, etc.). Direct grep of `gold_sink.py`,
  `quests.py`, `faction_decision.py` found **zero direct event-push calls** in any of them — none
  of these systems emit their own events; everything is reconstructed after the fact by diffing
  `prior_state.entities` against `current_state.entities` (scoped to `update.entity_updates.keys()`
  where available, `event_extractor.py:85-87`).
- A real, thread-safe, bounded, non-blocking delivery queue already exists
  (`src/observability/queue.py`, `BoundedObservabilityQueue.push()`) — but it sits **downstream**
  of event creation; it delivers already-constructed envelopes, it does not decide what an envelope
  should contain. Nothing feeds it directly from a mutation call site today.
- This diffing approach has two confirmed costs: (1) **scaling** — cost is proportional to (dirty
  entities × fields the extractor knows to diff) every tick, not to actual event volume; a richer
  observability surface means more diff logic re-run every tick regardless of whether anything
  happened; (2) **honesty** — causal attribution depends on the extractor correctly reading
  secondary fields on typed update records (e.g. `CombatUpdate.attacker_id`, `.outcome_kind`), and
  a confirmed real bug (`TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX`) shows
  what happens when the extractor doesn't check the right field: hazard drain got double-classified
  as combat for months of corpus history.

The user's stated position: push-based (emitting events at or near the actual mutation, not via
post-hoc diffing) is architecturally correct, and — if engineered correctly — need not cost more
performance than the current approach. This ticket investigates that position properly rather than
defaulting to the status quo, while taking the real coupling risks seriously.

## Key finding already established during scoping — do not re-derive

**The natural push point is the authoritative apply layer, not domain code.** Domain systems
(`combat.py`, `world_dynamics.py`, `gold_sink.py`, `quests.py`) already return richly-typed,
already-tagged update records (`CombatUpdate.outcome_kind` ∈ `{SURVIVE, DEFEAT, KILL, REJECTED}`,
`ResourceTransferIntent.source_kind` ∈ `{NODE, GROUND_ITEM, CORPSE, CRAFTING, SHOP_BUY, SHOP_SELL}`,
etc. — confirmed via `grep -rn "outcome_kind" src/`, every real mutation site already populates
these honestly). `ApplyPath.apply_generation()` (`src/engine/apply.py:179+`) already walks every
`StateUpdate`/`entity_updates`/etc. exactly once to mutate `AuthoritativeState` — this is the
single centralized point where every typed, already-causally-tagged update is already being
visited. Emitting events **from within this apply pass**, keyed off the update records' own
already-correct tags, would:
- Be genuinely trigger-point-adjacent (same tick, same pass, not a separate post-hoc diff), which
  is what the user is asking for.
- Require **zero new imports into domain code** — `combat.py`/`world_dynamics.py`/etc. never need
  to import `src/observability/`, respecting `combat_engagement_contract.md`'s "domains must not
  import from other domain packages" constraint (this constraint is domain-to-domain, but the
  spirit — domains stay unaware of observability — is worth preserving for the same reasons).
  Stay centralized in one layer (the apply/pipeline layer), avoiding the "N call sites to keep
  consistent" risk of literal per-domain push calls.
- Plausibly **reduce** total work rather than add it — no separate full diff scan needed; event
  candidates fall out of the same walk that's already mutating state.

**Concrete shape, not just "centralize it":** a small registry of shaper functions keyed by typed
update-record kind (`CombatUpdate` → combat shaper, `ResourceTransferIntent` → economy shaper,
etc.), all invoked from the single point inside `ApplyPath.apply_generation()` where each update is
already being walked — each shaper owns both "does this update deserve an event" and "how is it
formatted," uniformly, the same two decisions `event_extractor.py` makes today, just triggered by
walking already-tagged updates instead of diffing raw state after the fact. This is not a novel
pattern for this codebase — `QualityHub.SCORER_REGISTRY` (`{event_type: [Scorer(weights)]}`) is the
same shape (small central registry, one clean function per domain, uniform dispatch) already
proven out for SimQ's own scoring layer. A bug in one shaper stays exactly as centralized and
fixable as today's single-file `event_extractor.py` bug — this is a different trigger point, not a
loss of the "one place to fix it" property.

This is a real candidate design, not just a compromise — but it is **not yet validated** against
the project's harder constraints (below). That validation is this ticket's job.

## Scope
1. **Read the authoritative constraints first** (Context Scan): `docs/engine/kernel.md` (6-phase
   loop), `docs/engine/authoritative_pipeline.md` (32-phase sequence),
   `docs/engine/authoritative_mutation_pipeline_contract.md`, `quality_scoring_contract.md` §3.1
   ("Zero Simulation Impact") and §3.2 (Overhead Budget), `docs/core/state.md` (immutability law).
2. **Determinism risk**: `SimulationEvent.event_id` uses `uuid.uuid4().hex`
   (`src/observability/events.py:56`) and `timestamp: float = Field(default_factory=time.time)` —
   both already non-deterministic today, regardless of push vs. diff. Confirm whether this matters
   (event IDs/timestamps are presumably not part of the replay-determinism contract, only
   `AuthoritativeState` is) — do not assume, verify against `tests/unit/kernel/
   test_replay_determinism.py` and `tests/certification/`.
3. **"Zero Simulation Impact" compatibility**: determine whether emitting inside
   `ApplyPath.apply_generation()` can be proven not to affect simulation outcomes — e.g. via a
   strict try/except-and-drop wrapper around emission, or by keeping emission strictly
   read-of-already-computed-update / never influencing what gets applied. Check how
   `tests/perf/test_simq_isolation_overhead.py` currently measures overhead and whether that
   measurement point/methodology would still work if emission moves into the apply layer.
4. **Coverage audit + shaper-registry design**: for the ~10 event-producing domains currently
   covered by `EventExtractor.extract()`, determine which already have a sufficiently-tagged typed
   update record (candidates for a shaper in the registry design sketched above, mirroring
   `QualityHub.SCORER_REGISTRY`'s shape) vs. which don't (would still need diff-based inference, or
   new tagging work) — do not assume 100% coverage is trivial. Produce a per-domain table, not a
   single yes/no.
5. **Volume/mode control**: `event_extractor.py` has an explicit "volumization rule" (skip routine
   damage in `LIGHT`/`LONG_RUN` mode unless lethal). An apply-layer emission design needs an
   equivalent filtering mechanism — sketch how mode-awareness would work without re-introducing a
   diff step.
6. **Migration risk**: this touches the tick's hottest path. Sketch (do not implement) a rollout
   plan — e.g., run apply-layer emission in `SHADOW` mode alongside the existing extractor,
   compare event streams for a representative run set, before ever removing the diff-based path.
7. Produce a concrete recommendation: build it, and how; or don't, and why; with the coupling,
   performance, determinism, and coverage questions above answered with evidence, not assumption.

## Out of Scope
- Implementing the redesign itself — this ticket is investigation-and-recommendation only, given
  the size and hot-path sensitivity of the change. A follow-up ticket (or ticket set) implements
  whatever this one recommends.
- `TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX`'s narrow bug fix — that lands
  independently of this ticket's outcome, since it fixes a bug in the *current* diffing approach
  regardless of whether that approach is eventually replaced.
- Any change to `AuthoritativeState`, the mutation pipeline's actual mutation logic, or replay
  determinism guarantees themselves.

## Acceptance Criteria
- [ ] Determinism question (event_id/timestamp non-determinism) answered with evidence from the
      actual replay-determinism test suite, not assumption
- [ ] "Zero Simulation Impact" compatibility assessed concretely (not just asserted possible)
- [ ] Coverage audit completed: which domains' existing typed update records are
      apply-layer-emission-ready today vs. which need tagging work first
- [ ] A volume/mode-control sketch exists for the apply-layer design
- [ ] A migration/rollout sketch exists (shadow-mode comparison before cutover)
- [ ] A concrete recommendation is produced: build (with a scoped follow-up ticket's shape sketched)
      or don't (with the blocking reason stated plainly)

## Related Tickets
- TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY (parent — this ticket generalizes one of
  its findings into the full architecture question)
- TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX (sibling, narrow fix, independent
  of this ticket's outcome)

## Related Docs
- `docs/engine/kernel.md`, `docs/engine/authoritative_pipeline.md`,
  `docs/engine/authoritative_mutation_pipeline_contract.md`
- `docs/simulation_quality/quality_scoring_contract.md` §3 (Performance Contract, incl. §3.1 Zero
  Simulation Impact, §3.2 Overhead Budget)
- `docs/core/state.md` (immutability law)
- `docs/simulation/domains/combat_engagement_contract.md` (domain-isolation constraint, cited as
  the spirit to preserve even though it's domain-to-domain, not domain-to-observability)
- `docs/performance/simq_isolation_overhead.md` (existing overhead measurement)

## Related Stored Artifacts
None yet — will be created at
`staging_artifacts/TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE/` during implementation.

## Related Code Areas
- `src/engine/kernel.py` (`_phase_observability`, the current call site)
- `src/engine/apply.py` (`ApplyPath.apply_generation` — candidate new emission point)
- `src/observability/event_extractor.py` (current diff-based mechanism, for comparison)
- `src/observability/queue.py` (`BoundedObservabilityQueue` — reusable regardless of outcome)
- `src/observability/events.py` (`SimulationEvent`, `ObservabilityEventEnvelope`)
- `src/core/updates.py` (`CombatUpdate.outcome_kind`, and other typed update records' existing
  causal tags)
- `tests/perf/test_simq_isolation_overhead.py`, `tests/unit/kernel/test_replay_determinism.py`,
  `tests/certification/`

## Assumptions / Open Questions
- Whether `event_id`/`timestamp` non-determinism already matters to any existing guarantee is
  explicitly unverified — Scope item 2 must confirm, not assume, before this ticket can conclude.
- Whether every event-producing domain's update records carry sufficient tagging for apply-layer
  emission, or some still need new tagging work, is unknown until Scope item 4's audit runs.

## Implementation Notes
All 6 Scope items resolved with direct evidence, not assumption. Determinism: grepped
`tests/certification/` and read `test_replay_determinism.py` directly — zero references to
observability event types, contract scoped entirely to `AuthoritativeState`. Zero Simulation
Impact: re-read `quality_scoring_contract.md` §3.1 carefully and confirmed via `kernel.py:909`/953
that emission already runs synchronously inside the tick today — §3.1 protects scoring
(`QualityHub.on_envelope()`, off-thread via the drain worker), not emission, so this was never a
real constraint on the proposed design. Performance: found `test_simq_isolation_overhead.py` and
its companion doc already measure and regression-guard the exact cost category this migration
would touch, with the "disabled" baseline already including today's diffing cost — no new tooling
needed. Coverage: read `event_extractor.py`'s actual detection code for 4 domains directly (not
inferred) — COMBAT/ECONOMY/FACTION already read typed update records (`CombatUpdate.outcome_kind`,
`ResourceTransferIntent.source_kind`, `update.faction_updates` respectively — the FACTION code
already proves the target pattern works today, it's just not used for anything else yet);
PROGRESSION's quest detection is genuine diff-only (`entity.strategic.projects` compared against
`prior_ent`'s snapshot, no typed record). Filed Phase 1 as its own implementation ticket scoped
exactly to the 3 already-ready domains, deliberately not filing Phase 2 yet since the quest/
demographic/XP audit wasn't exhaustive enough to scope it precisely.

## Test Summary
No production code changed by this ticket (investigation + doc + ticket-filing only). Verification:
`python3 tools/validate_frontmatter.py` passed on all 6 touched/created files on the first attempt
(applied the correct staging-artifact schema from the start this time, based on the prior ticket's
gate failure in this same session). `run_static_precheck('...', 'standard', None)` returned all
PASS on the first run. `make knowledge-index-update` ran successfully.

## Files Changed
- `docs/audits/D20_simq_quality_status_review.md` — added Finding 11
- `staging_artifacts/TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE/` — investigation.md,
  plan.md, test_plan.md
- `tickets/todos/simq-pillar-lifecycle-depth/TCK-20260806-SIMQ-OBSERVABILITY-PUSH-EMISSION-PHASE1-COMBAT-ECONOMY-FACTION.md` (new)
- `tickets/todos/simq-pillar-lifecycle-depth/TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE.md` — blocking dependency updated to reference Phase 1 instead of this (now-done) investigation
- `tickets/todos/simq-pillar-lifecycle-depth/SEQUENCE.md` — rewritten for the full 8-ticket state

## Completion Summary
Investigated whether the diff-based observability pattern found in the parent ticket should be
replaced with push-based emission at the authoritative apply layer, per the user's explicit
position that this was architecturally correct if engineered properly. Conclusion: yes, and all
three originally-feared blockers (determinism, "Zero Simulation Impact," performance
measurability) turned out to already be non-issues on direct inspection — not because the risks
were unreasonable to raise, but because this codebase's existing constraints and tooling already
accommodate the design. The real constraint is coverage, not risk: 3 of 4 checked domains
(COMBAT/ECONOMY/FACTION) already read typed, causally-tagged update records and need zero new
instrumentation; PROGRESSION's quest detection does not and needs a real instrumentation
investment first. Recommended and filed a phased migration — Phase 1 scoped exactly to the
already-ready domains, via a shaper registry mirroring `QualityHub.SCORER_REGISTRY`'s proven shape,
rolled out behind the existing `FeatureMode.SHADOW` mechanism before any cutover. Phase 2 (quest/
demographic/XP domains) deliberately left unscoped pending Phase 1's own findings.

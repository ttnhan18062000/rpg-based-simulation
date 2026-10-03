---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE
artifact_type: investigation
tags: [observability, engine, simulation-quality, performance]
---

# investigation.md — TCK-20260806-SIMQ-OBSERVABILITY-PUSH-BASED-ARCHITECTURE

## Summary

**Should we: yes. Can we: yes, but as a phased/hybrid migration, not a clean full cutover.** Every
hard constraint checked (determinism, "Zero Simulation Impact", performance measurability) turned
out to already be compatible or a non-issue. The one real constraint is that not all domains are
equally ready — some already read typed, causally-tagged update records today (no new
instrumentation needed), others are genuinely diff-only and would need new typed records added
before they could emit at the apply layer.

## Findings

### 1. Determinism risk — resolved, no issue

`SimulationEvent.event_id` (`uuid.uuid4().hex`) and `timestamp` (`time.time()`) are both already
non-deterministic today, regardless of push vs. diff. Checked what the actual replay-determinism
contract covers: `tests/unit/kernel/test_replay_determinism.py::test_transaction_trace_determinism`
asserts only on `kernel._state.transaction_trace` (part of `AuthoritativeState`). Grepped
`tests/certification/` for any reference to `SimulationEvent`/`event_id`/`simulation_events.jsonl`
— **zero hits**. The determinism contract is scoped entirely to `AuthoritativeState`; observability
events are provably outside it, today, under either design. Moving emission earlier in the tick
(apply-layer instead of post-tick diff) does not change this — the observation layer was never part
of what determinism checks.

### 2. "Zero Simulation Impact" (§3.1) — does not apply to emission, only to scoring

Re-read `quality_scoring_contract.md` §3.1 carefully: it guarantees the simulation never blocks for
*quality scoring* — `QualityHub.on_envelope()` runs off the `BoundedObservabilityQueue` drain
worker thread (INPROCESS) or a separate consumer process (BROKER), never inside
`kernel.tick_once()`. **This says nothing about event production/emission itself.** Confirmed by
reading `kernel.py:909`: `EventExtractor.extract()` and `event_recorder.record()` (kernel.py:953)
are *already* called synchronously, inline, inside the tick, today — the same place apply-layer
emission would live. §3.1 has never protected emission from being synchronous; it protects scoring
from being synchronous. **Apply-layer emission is not a new violation of anything — it's the same
category of work the tick already does, just relocated and (per Finding 4) likely cheaper.**

### 3. Performance measurability — a mature, reusable harness already exists

`docs/performance/simq_isolation_overhead.md` / `tests/perf/test_simq_isolation_overhead.py`
already measure and regression-guard the full engine-process cost of observability + scoring
(`BenchHarness.run_benchmark()`, `cpu_time_total_delta_s`, locked thresholds: inprocess <25%,
broker <30% overhead vs. a "disabled" baseline). Critically, the "disabled" baseline **already
includes today's diff-based `EventExtractor` running in full** (only `QualityHub`'s `quality_fn`
callback is skipped) — so this harness already isolates exactly the kind of cost apply-layer
emission would change. No new tooling is needed to validate a migration's performance; the existing
harness and regression-guard convention (`perf_baseline_policy.md` §3's band-tolerance rule) apply
directly.

### 4. Coverage audit — 3 of 4 checked domains already read typed, tagged update records

Checked what each domain's event detection actually reads from, not just whether events fire:

| Domain | Current detection mechanism | Push-ready today? |
|---|---|---|
| COMBAT | `CombatUpdate.outcome_kind` (`SURVIVE`/`DEFEAT`/`KILL`/`REJECTED`/`HAZARD`/`SUCCESS`) + `attacker_id`, already tagged by `combat.py`/`world_dynamics.py` at every mutation site | **Yes** — already reads a typed record, just needs relocating from post-tick diff to apply-time read (and the `outcome_kind` filter bug fix from `TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX`) |
| ECONOMY | `ResourceTransferIntent.source_kind` (`NODE`/`GROUND_ITEM`/`CORPSE`/`CRAFTING`/`SHOP_BUY`/`SHOP_SELL`/`QUEST`/gold-sink kinds) | **Yes** — same pattern, already typed and tagged |
| FACTION | Iterates `update.faction_updates` (`FactionUpdate.diplomatic_relations_set`) directly — **not diffed at all**, already reads the typed update record today | **Yes, already effectively push-shaped** — `event_extractor.py`'s own `diplomatic_transition` code (lines 961-984) proves this pattern already works in this exact file |
| PROGRESSION (quest) | `entity.strategic.projects[qid].status` compared against `prior_ent`'s snapshot — genuine before/after **state diffing**, no typed "project status changed" update record exists | **No** — would need new instrumentation (a typed update record for quest/project status transitions) before this domain could move off diffing |

Not exhaustively audited beyond these four (demographic birth/mortality and raw XP/level detection
also read as diff-based on a quick pass, same category as quest) — a full per-domain table across
all ~10 is Scope work for whichever ticket implements this, not fully re-derived here, but the
pattern is clear enough to conclude on: **most of the domains this session actually cared about
(combat, economy, faction) are already push-ready with zero new tagging work; at least one
(progression/quest) is not.**

### 5. Volume/mode control — solvable at the shaper level, no architecture change needed

`event_extractor.py`'s volumization rule ("skip routine damage inside `LIGHT`/`LONG_RUN` mode
unless lethal") is just a conditional inside the existing combat-damage branch. In a shaper-registry
design, each shaper receives the same `ObservabilityMode` context a diff-based branch would, and
applies the same kind of check before constructing an event. No new mechanism is needed — this is a
per-shaper concern, not a systemic one.

### 6. Migration risk — real, but bounded by the existing SHADOW feature-mode pattern

`FeatureMode.SHADOW` ("Feature runs but output is discarded — parallel shadow execution") already
exists as a first-class concept in this codebase (`feature_flags.py`) and is exactly the right tool
for de-risking this: run apply-layer emission in parallel with the existing diff-based extractor,
compare the two event streams for a representative run set, without cutting anything over, before
ever removing the diff path. This is not a new pattern to invent — it already has a name and
precedent in this codebase's own flag system.

## Recommendation

**Build it, as a phased migration, not a rewrite:**

1. **Phase 1** (small, low-risk): move COMBAT, ECONOMY, and FACTION event shaping from
   post-tick diffing to apply-layer emission (reading the same typed update records they already
   read, just earlier and inline) via a small shaper registry inside `ApplyPath.apply_generation()`
   mirroring `QualityHub.SCORER_REGISTRY`'s shape. Run in `SHADOW` mode first, compare event streams
   against the existing diff-based extractor across the calibration corpus, cut over once matched.
   This alone converts the 3 domains with the most active investigation history this session (and
   fixes the `outcome_kind` bug as a side effect of the relocation, though
   `TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX` should still land first/
   independently since it's needed regardless of this migration's timeline).
2. **Phase 2** (larger, needs new instrumentation): add a typed update record for quest/project
   status transitions (and audit demographic/XP domains the same way), then migrate PROGRESSION's
   quest detection off diffing too.
3. Do not attempt a single all-domains cutover — the coverage audit shows the domains are
   genuinely at different readiness levels, and forcing progression's quest detection to migrate
   before its typed-record gap is closed would just recreate the honesty problem this investigation
   started from, in a new place.
4. Reuse `test_simq_isolation_overhead.py`'s existing harness and `perf_baseline_policy.md`'s
   band-tolerance convention to validate each phase — no new performance tooling needed.

None of the three "hard constraint" risks originally flagged in this ticket's Scope (determinism,
Zero Simulation Impact, performance measurability) turned out to be real blockers — all three
resolved to "already compatible" or "already has the right tooling" on inspection. The actual
constraint is coverage, not architecture risk.

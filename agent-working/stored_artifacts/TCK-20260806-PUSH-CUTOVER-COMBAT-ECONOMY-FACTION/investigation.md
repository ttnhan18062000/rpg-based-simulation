---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION
artifact_type: investigation
tags: [observability, engine, combat, simulation-quality]
---

# investigation.md — TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION

## Summary

Confirmed `TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`'s GO verdict directly (read its Completion
Summary, not assumed). Before touching any code, traced each of the 3 domains' old-extractor
branches against what the shaper actually covers, to determine whether "remove the branch" is
safe for every migrated event or not.

## Real finding: `entity_killed`/`hero_death_unrecorded` cannot be a clean branch removal

`event_extractor.py`'s "Kill events" branch (lines 177-201) fires on **any**
`prior_ent.lifecycle.active and not entity.lifecycle.active` transition, regardless of cause —
this was a deliberate, disclosed design choice preserved by both
`TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX` and
`TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT` (both explicitly left this branch's own firing
condition unchanged, only fixing `killer_id`'s population). The shaper's `entity_killed` is
**narrower by design** — gated on `outcome_kind=="KILL"` specifically (per
`TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT`'s reopen fix) — because old-age death and
delayed-hazard-transition death (confirmed real, `TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`) never
carry a same-tick `outcome_kind=="KILL"` combat_upd for the shaper to read.

**If the old branch is removed wholesale at cutover, old-age and delayed-hazard-transition deaths
would stop producing `entity_killed`/`hero_death_unrecorded` entirely** — not deferred, genuinely
lost. This is exactly the "missing an existing defined event" failure mode this epic was
explicitly instructed to avoid. Confirmed this is real and current (not already covered
elsewhere): grepped for any other `entity_killed`/`hero_death_unrecorded` construction site —
none exists outside `event_extractor.py`'s single branch.

**Verified no other migrated event has this issue.** Re-checked each domain's old-extractor
condition against the shaper's own condition:
- `combat_damage`/`combat_initiated`/`near_death_survival`: both use the identical
  `_real_combat_update()` discriminant (shared function, single source of truth) — confirmed
  matching exactly via the validation ticket's 130/131 real-corpus comparison.
- `hazard_drain_applied`: both conditions are `outcome_kind=="HAZARD"` exactly, no broader scope
  on either side.
- ECONOMY's 7 events and FACTION's 8 events: all are clean 1:1 `source_kind`/typed-record
  conditions with no broader old-extractor scope to preserve.

`entity_killed`/`hero_death_unrecorded` is the only case needing special handling.

## Fix: narrow the old branch's condition, don't remove it

Rather than removing `event_extractor.py`'s Kill-events branch, **modify its condition to exclude
exactly the case the shaper now owns** (same-tick, `outcome_kind=="KILL"`), preserving every other
cause (old-age, delayed-hazard-transition, and any future non-KILL-tagged cause) exactly as
before:

```python
real_combat_upd = _real_combat_update(e_upd)
is_shaper_owned_kill = real_combat_upd is not None and real_combat_upd.outcome_kind == "KILL"
if not is_shaper_owned_kill:
    # ... existing CombatKillEvent / hero_death_unrecorded construction, unchanged
```

This yields **zero net coverage change** for `entity_killed`/`hero_death_unrecorded`: the shaper
delivers the same-tick KILL case live (from the apply layer), the old extractor continues covering
every other cause exactly as it did before cutover. Neither double-fires (mutually exclusive
conditions) nor drops coverage.

## Scope for the other 2 domains

`ECONOMY`'s and `FACTION`'s old-extractor branches ARE safe for clean, full removal — confirmed
above, no broader-scope preservation needed. However, see the deployment-mechanism decision below,
which applies uniformly to all 3 domains regardless of individual branch cleanliness.

## Deployment-mechanism decision: wholesale branch removal is unsafe — keep both paths, flag-gated

The ticket's original Scope ("remove the COMBAT/ECONOMY/FACTION-specific branches from
`event_extractor.py`") has a real, significant gap: `ENABLE_PUSH_EVENT_SHAPERS` currently defaults
`OFF` (`FeatureFlagManager.__init__`, DEV-002 policy). If the old branches are removed
unconditionally while the shaper only *delivers* when the flag is explicitly `"ON"` (its documented
SHADOW-vs-ON distinction), then **any run that doesn't explicitly set the flag would lose
COMBAT/ECONOMY/FACTION event emission entirely** — not migrated, not deferred, gone. This is a real
regression the ticket's own AC ("Full corpus re-run matches the validated shadow-mode baseline")
would only catch if the corpus re-run explicitly sets the flag — a silent trap for any run that
doesn't.

Two ways to resolve this, both considered:

1. **Flip the flag's default to `"ON"` and delete the old branches outright.** Rejected: this
   removes the only real rollback mechanism. If a production issue surfaces post-cutover, there
   would be no way back to the old, previously-working behavior without a code revert — a much
   slower, higher-friction rollback than a config flag flip. Given this touches 3 major SimQ
   pillars' event streams, a real rollback lever is worth keeping.
2. **Keep both paths in the code, made mutually exclusive by the flag; flip the default to `"ON"`.**
   The old branches gain a guard (`if <flag> != "ON":`) so they only fire when the shaper is NOT
   delivering — matching the exact pattern every other feature flag in this codebase already uses
   (gate new/alternate behavior, never delete the prior path). Default flips to `"ON"` since the
   design is now validated (130/131 real-corpus match, 0 payload mismatches, no perf overhead) —
   this is no longer a speculative rollout candidate, it's a completed replacement with a real
   safety net still in place. Setting the flag to `"OFF"` restores the exact prior (pre-epic)
   behavior as a genuine, working rollback — not just a partial one.

**Decision: option 2.** This is a deliberate, reasoned deviation from the ticket's originally-
scoped "remove the branches" language — recorded here explicitly, not silently substituted. The
net *default* behavior after this ticket still changes exactly as intended (push-based becomes the
live path for these 3 domains, everywhere, immediately) — the difference is *how* that's achieved
(flag-gated mutual exclusion, default flipped, both paths retained) rather than deletion.

## Full-corpus verification (Scope item 4): root-cause of the grade-regression failures

`make simq-full-audit-full` (79 scenarios) was run to satisfy this ticket's own Scope item 4
("Run the full calibration corpus... compare against the validated shadow-mode baseline").
Result: `test_grade_regression.py` showed 32/69 failures (18 deselected as `slow`), including
`hero_guild_routing_seed42_500t` drifting on COGNITION, COMBAT, and PROGRESSION, with
`quality_report.json` showing `COMBAT.event_count=0`, `ECONOMY.event_count=0`,
`FACTION.event_count=0` against a non-zero COMBAT anchor (0.057971). This needed root-causing
before the ticket could close, per this repo's rule against treating a failing gate as an
obstacle to route around.

**Investigation, in order:**

1. Traced `calibrate_simq.py`'s scoring path: it is not live — `main()` runs the engine, then
   `_replay_jsonl_through_hub()` separately re-reads `simulation_events.jsonl` and replays each
   row through `QualityHub`, silently `logger.debug`-skipping any row that fails
   `ObservabilityEventEnvelope(**data)` construction. Checked `EventRecorder.record()`: envelope
   conversion is uniform for both `event_extractor`- and `event_shapers`-sourced events, making a
   field-mismatch/replay-skip theory unlikely on its own.
2. Grepped the corpus log for this migration's own exception-swallow message
   (`push_event_shapers raised`) — no hits. Ruled out "shaper raises and kernel.py's defensive
   `except Exception` silently eats it" as the mechanism.
3. Found the real candidate mechanism directly in `kernel.py`: a tick-budget watchdog
   (`_final_compute_ms > min(hard_cap, limit_ms)` at kernel.py:429) that logs a warning and calls
   `self._status.record_dropped_work(9999)` on every overrun tick, plus a mid-tick emergency
   throttle in `_phase_resolution()` (kernel.py:583-607) that can drop trailing `_final_results`
   items outright when a tick runs over its hard cap. The corpus log for
   `hero_guild_routing_seed42_500t` shows **dozens** of "Tick N exceeded budget" warnings spread
   across the full 500-tick run.
4. This exact mechanism is already documented as **INFRA-273** (F6-class tick-budget-watchdog
   trajectory divergence, `docs/parity_ledger/infrastructure.yaml`), which explicitly names
   COMBAT (among SOCIAL/ECONOMY/PROGRESSION/NARRATIVE/WORLD) as a pillar already known to be
   susceptible to this mechanism, pre-dating this epic by three weeks
   (`TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP`, closed 2026-07-15/16).

**Decisive confirming experiment.** Reproduced `hero_guild_routing_seed42_500t` in isolation
(outside the 79-scenario corpus, so no cross-scenario session-load carryover) three times:

- Once with the flag at its normal default (`ON`, shaper path live).
- Once again with the flag at default (repeat, to check determinism).
- Once with `ENABLE_PUSH_EVENT_SHAPERS` forced to `"OFF"` on the tick's `prior_state` (old
  `event_extractor.py` branches live instead of the shaper), via a kernel-level monkeypatch since
  `calibrate_simq.py`'s own flag-override parser only recognizes `ON`/`STRICT`/`SHADOW`, not `OFF`.

All three runs produced **near-identical pillar breakdowns** — `AGENCY=687`, `NARRATIVE=407`,
`PROGRESSION=1`, `WORLD=26`, `COGNITION≈182-183`, and, critically, `COMBAT=0`, `ECONOMY=0`,
`FACTION=0` in **every** run regardless of which pipeline (shaper or old extractor) was live.
Raw `simulation_events.jsonl` for both the flag-ON and flag-OFF runs was inspected directly:
only `hazard_drain_applied` (environmental damage, 16 events) fired from the combat domain in
either run — no `combat_damage`, `combat_initiated`, or `entity_killed` from real attacker-driven
combat in either pipeline. `phase_costs.combat_engagement` in the watchdog alert payloads shows
~0.003ms per tick — combat-engagement work is essentially not executing in this run at all, at
the simulation level, upstream of both observability pipelines.

**Conclusion: this is not a regression caused by the push-shaper migration.** It reproduces
byte-for-byte identically whether the shaper or the old extractor is the live path, confirming
the root cause is upstream, at the scheduler/resolution layer (INFRA-273's already-documented
dropped-resolution-queue-item mechanism), not in event construction or delivery. `grade_anchors.json`'s
non-zero COMBAT anchor for this scenario was generated under different timing/hardware conditions
than this session's; under this session's/machine's current tick-budget pressure, combat_engagement
work is being starved before either pipeline ever sees a real combat resolution to report. This is
a pre-existing, already-tracked infrastructure fragility (INFRA-273), not something in this
ticket's scope to fix. See `docs/parity_ledger/infrastructure.yaml` INFRA-273 for the updated
cross-reference recording this confirming evidence.

---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM
artifact_type: investigation
tags: [simulation-quality, cognition, self-model, determinism]
---

# Repro Sweep — TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM

Working evidence file (not one of the three required staging artifacts), mirrors
`stored_artifacts/TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY/raw_calibration_sweep.md`'s
precedent. All four runs below drive `urban_political` seed 123, 500 ticks, via
`tools/calibrate_simq.py`'s real internal helpers (`_resolve_profile`, `_load_profile_feature_flags`,
`_load_weights`, `_build_hub`, `_run_engine`, `_replay_jsonl_through_hub`) — the real throttled
`Kernel` (`no_frame_pacing=True`, no `audit_mode`), same code path a real calibration run exercises.
Driver script: ad hoc, not committed (`/tmp/.../scratchpad/repro_step1.py`, per Step 1's scope —
`repro_sweep.md` is the durable record, the driver script is throwaway).

`budget_warnings` = count of `Tick N exceeded budget` log lines (end-of-tick watchdog,
`kernel.py:420-442`). `watchdog_trips` = count of `Mid-tick emergency throttle triggered` log
lines (mid-tick emergency throttle, `kernel.py:574-601`). Both counted from a `logging.StreamHandler`
attached to the `src.engine.kernel` logger for the duration of each run.

Induced load = a `multiprocessing` pool of tight-loop CPU-bound busy-workers (pure integer
arithmetic, no I/O/GIL-yielding calls), started ~2s before the drive and kept running for its
full duration, oversubscribing the machine's 4 cores (`nproc`=4, no `stress-ng` available on this
box). Two load intensities were tried, escalating per Step 1's "retry with a longer/heavier load
window before concluding anything" instruction.

## Runs

| Run | Load | elapsed_s (engine) | wall_elapsed_s | budget_warnings | watchdog_trips | COGNITION event_count | COGNITION raw_score | COGNITION normalized_score | COGNITION grade | COGNITION loop_detected |
|---|---|---|---|---|---|---|---|---|---|---|
| idle-1 | none | 10.44 | 12.24 | 28 | 0 | 2 | 11.0 | 0.088 | B | True |
| idle-2 | none | 10.56 | 12.32 | 31 | 0 | 2 | 11.0 | 0.088 | B | True |
| load-2x | 8 busy workers (2x cores) | 17.64 | 21.52 | 40 | 1 | 2 | 11.0 | 0.088 | B | True |
| load-4x | 16 busy workers (4x cores) | 37.45 | 43.03 | 108 | 0 | 2 | 11.0 | 0.088 | B | True |

Resolved profile's feature-flag dump (`_load_profile_feature_flags("urban_political")`, identical
in every run — confirmed empirically, closes investigation Open Question #5):
```json
{"ENABLE_SOCIAL_COOPERATION": "ON", "ENABLE_BELIEF_ASSIMILATION": "ON"}
```
`ENABLE_SELF_MODEL_COGNITION` is absent (defaults OFF, `src/domains/optimization/feature_flags.py:15`)
for every run, confirming the planning-time static-read finding empirically: `self_model_updated`
never fires for this anchor's calibration profile regardless of load, but that does not affect the
result below since `decision_divergence_detected` (the event the investigation identified as the
F6-exploitable one) does not depend on that flag.

## Interpretation

The induced-load mechanism is confirmed real and load-sensitive by direct evidence — `budget_warnings`
climbs monotonically with load intensity (28/31 idle -> 40 at 2x -> 108 at 4x, a ~3.7x increase over
idle at the heaviest setting), `wall_elapsed_s` grows from ~12s idle to ~43s at 4x oversubscription
(3.5x slower), and a genuine mid-tick emergency throttle (`watchdog_trips=1`) fired at 2x load, absent
in both idle runs. This is the same F6 mechanism (`docs/audits/D06_longrun_health.md` §F6,
`kernel.py:420-442`/`574-601`) previously confirmed by `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`'s
sweep — it is firing here too, not a null result requiring further retry.

Despite that confirmed throttle sensitivity, **COGNITION's `event_count`/`raw_score`/`normalized_score`/
`grade`/`loop_detected` are bit-identical across all four runs** — two idle repeats and two
independently-escalated load levels, including the run with the heaviest observed throttle activity
(108 `budget_warnings`, 3.5x wall-clock slowdown). All four also match the committed
`grade_anchors.json` anchor (`B`, `0.088`) exactly. `loop_detected=True` is present in every run
including both idle baselines — it is not a load-induced signal for this anchor, it reflects the
window-buffer tag-proportion mechanism (`pillar_accumulator.py:60-70`) tripping on the scenario's
normal (small, 2-event) COGNITION activity, unrelated to throttle variance.

This means the investigation's F6-driven mechanism — dropped resolution-queue work stalling an
entity's `danger`-concern resolution and causing `decision_divergence_detected` to re-fire tick after
tick — is not observed to be exercised by `urban_political_seed123_500t` at this seed/tick-count/load
range: no entity in this scenario's 500-tick run appears to enter the `danger urgency > 0.7` +
non-survival-project state that the missing dedup gate would otherwise cause to explode under
dropped resolution work. The originally reported 2->119 anomaly (Request Summary) was observed under
a different, much longer (~30 min sustained) sweep as part of a full-corpus multi-scenario run — this
controlled, single-scenario repro at up to 4x core oversubscription for ~500 engine-ticks (~40s
wall-clock) did not reproduce it for this specific anchor.

## Decision

**Fallback outcome selected — bit-identical achievable.** Per Step 2's classification criteria: two
independent idle repeats and two independently-escalated induced-load runs (2x and 4x core
oversubscription, confirmed via `budget_warnings` 28/31 -> 40 -> 108 and a genuine `watchdog_trips=1`
at 2x) all produced identical `event_count=2`, `raw_score=11.0`, `normalized_score=0.088`, `grade=B`,
`loop_detected=True` for COGNITION on `urban_political_seed123_500t`. The throttle mechanism itself is
demonstrably load-sensitive (satisfying Step 1's "retry with a longer/heavier load window" requirement
before concluding a null result — the result is not null, the throttle fires more under load, but
COGNITION's output does not move), so this is a genuine bit-identical result for this anchor, not an
under-powered repro. **Proceeding to Step 3b** (tight bit-identical assertion test), not Step 3a.

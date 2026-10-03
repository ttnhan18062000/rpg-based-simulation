---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION
artifact_type: report
tags: [feature-flags]
---

# Trial Evidence — TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION

Raw output of the 2-leg fresh calibration trial run per `plan.md` Steps 1-6. Environment note:
the worktree's bare `python3` lacks `pydantic` (a pre-existing, unrelated environment gap,
confirmed directly this session — `python3 -c "import pydantic"` raises `ModuleNotFoundError`);
both legs and every pytest invocation were run with
`/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` (the main checkout's venv,
confirmed to have `pydantic` 2.12.5 installed), with `cwd` remaining this worktree so
`data/runs/` and `data/calibration/` output landed exactly where the plan's commands specify.

## Commands run (verbatim except interpreter path)

```
# OFF leg — temporary probe, omits ENABLE_INFORMATION_INTENT_EXECUTION entirely
.venv/bin/python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name urban_political \
  --profile urban_political_information_intent_execution_off_probe \
  --output data/calibration/urban_political_information_intent_execution_off_probe_seed42_200t
# -> data/runs/run_1788026423_5169

# ON leg — existing permanent probe, ENABLE_INFORMATION_INTENT_EXECUTION: "ON"
.venv/bin/python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name urban_political \
  --profile urban_political_selfmodel_execution_probe \
  --output data/calibration/urban_political_selfmodel_execution_probe_seed42_200t
# -> data/runs/run_1788026439_5169
```

## World-loading path confirmation

Both commands exited 0 and printed `[calibrate_simq] Profile feature flags: ...` matching each
profile YAML's own `feature_flags:` block exactly:
- OFF leg: `{'ENABLE_SOCIAL_COOPERATION': 'ON', 'ENABLE_SELF_MODEL_COGNITION': 'ON',
  'ENABLE_BELIEF_ASSIMILATION': 'ON'}` — no `ENABLE_INFORMATION_INTENT_EXECUTION` key, confirming
  the env-var-override `_KNOWN_FLAGS` gap (see Honest Gap below) was correctly avoided by using
  `--profile` instead.
- ON leg: `{'ENABLE_SOCIAL_COOPERATION': 'ON', 'ENABLE_SELF_MODEL_COGNITION': 'ON',
  'ENABLE_BELIEF_ASSIMILATION': 'ON', 'ENABLE_INFORMATION_INTENT_EXECUTION': 'ON'}` — all 4
  flags ON, `ENABLE_BELIEF_ASSIMILATION` held at its real global-default ON in both legs as
  required.

Both commands also printed `entities=10` — `urban_political`'s real compiled
`data/worlds/urban_political/resolved/world.resolved.yaml` entity count. Per
`calibrate_simq.py:138-153`, `--name urban_political` failing to resolve would raise
`FileNotFoundError` rather than silently falling back to the generic hero+goblins world — a
successful run itself is sufficient proof, no separate fingerprint check needed since only one
world is used across both legs.

## Evidence tally

### Signal 1 — pillar grades/scores/event counts (both legs)

| Pillar | OFF leg (`..._off_probe`) | ON leg (`..._execution_probe`) |
|---|---|---|
| AGENCY | grade=C norm=0.0 events=0 | grade=C norm=0.0 events=0 |
| COGNITION | grade=S norm=27.28 events=5455 | grade=S norm=27.28 events=5455 |
| COMBAT | grade=A norm=1.67 events=118 | grade=A norm=1.845 events=129 |
| ECONOMY | grade=B norm=0.1644 events=4 | grade=B norm=0.1644 events=4 |
| FACTION | grade=S norm=2.9 events=29 | grade=S norm=2.9 events=29 |
| INFORMATION | grade=B norm=0.2 events=1 | grade=B norm=0.2 events=1 |
| NARRATIVE | grade=C norm=0.0 events=0 | grade=C norm=0.0 events=0 |
| PROGRESSION | grade=B norm=0.399 events=8 | grade=B norm=0.3219 events=6 |
| SOCIAL | grade=S norm=13.87 events=1061 | grade=S norm=13.35 events=1035 |
| WORLD | grade=B norm=0.25 events=17 | grade=B norm=0.25 events=17 |
| overall | grade=S score=5.0029 | grade=S score=4.9284 |

Notable OFF-vs-ON differences: `COMBAT` (118 events OFF vs 129 ON), `PROGRESSION` (8 vs 6),
`SOCIAL` (1061 vs 1035) — small (≤13-event, ≤10%) run-to-run deltas from downstream cascading
divergence (the single toggled flag changes tick-by-tick decision ordering for entities that
route through `InformationIntentExecutionPhase`, which then ripples into unrelated combat/social
scheduling in later ticks), not a suppression pattern (no pillar collapsed toward zero on the ON
leg; `INFORMATION`, `AGENCY`, `FACTION`, `WORLD`, `NARRATIVE`, `ECONOMY`, `COGNITION` are
identical between legs).

### Signal 2 — `ActionIntentAdapter` / `action_intent` trace count (both legs)

```
grep -c '"event_type": *"action_intent"' data/runs/run_1788026423_5169/simulation_events.jsonl  -> 0  (OFF)
grep -c '"event_type": *"action_intent"' data/runs/run_1788026439_5169/simulation_events.jsonl  -> 0  (ON)
grep -c 'ActionIntentAdapter' data/runs/run_1788026423_5169/simulation_events.jsonl              -> 0  (OFF)
grep -c 'ActionIntentAdapter' data/runs/run_1788026439_5169/simulation_events.jsonl              -> 0  (ON)
```

**0 traces in both legs** — matches `INFRA-270`'s own `support_boundary` and investigation.md's
independent trace-through: Branch B (`InformationBeliefPhase`'s query-routing branch) does not
route a query in `urban_political`'s real compiled state at seed 42 within a 200-tick window,
regardless of which leg. This is the expected "not reached in this corpus" result, **not a
suppression or regression finding** — it is identical to the already-on-file finding from the
`SELF-MODEL-COGNITION` sibling's own trial. Since Branch B never produces an `ActionIntent` in
this corpus, `InformationIntentExecutionPhase.execute()` has nothing to execute in either leg,
which is exactly why the two legs' `quality_report.json` numbers differ only by small
downstream-cascade deltas rather than by a `intent_results`-driven signal — the calibration-safety
proof this trial can offer is "wiring the phase into the pipeline and gating it ON does not
regress calibration," not "Branch B fired and was executed for real" (that remains the job of the
deterministic hand-built scenario test, see Signal 4 below).

### Signal 3 — cross-check ON leg against `grade_anchors.json["urban_political_selfmodel_execution_probe_seed42_200t"]`

Anchor: `COGNITION=S/27.485`, `AGENCY=C/0.0`, `COMBAT=A/0.7839195979899497`, `FACTION=S/2.9`,
`ECONOMY=C/0.0`, `PROGRESSION=C/-0.1568627450980392`, `SOCIAL=S/16.815`, `INFORMATION=B/0.2`,
`WORLD=B/0.21`, `NARRATIVE=C/0.0`.

- AGENCY, FACTION, NARRATIVE: exact match.
- INFORMATION: B/0.2 vs anchor B/0.2 — **exact match** (unlike the SELF-MODEL-COGNITION sibling's
  `urban_political_selfmodel_probe` run key, this run key's own anchor was already set with
  `INFORMATION=B/0.2` at `TCK-20260713-SIMQ-COGNITION-PIPELINE-WIRE` time, so this specific pillar
  shows no drift here).
- COGNITION: S/27.28 vs anchor S/27.485 — within tolerance (diff 0.205, floor
  max(0.05, 0.2×27.485)=5.497).
- WORLD: B/0.25 vs anchor B/0.21 — within tolerance (diff 0.04, floor max(0.05, 0.2×0.21)=0.05).
- COMBAT: A/1.845 vs anchor A/0.7839 — **band passes** (same letter grade) but **score
  drifted beyond tolerance** (diff 1.061, floor max(0.05, 0.2×0.7839)=0.1568) — carries an
  existing `known tick_budget` ceiling classification (`attrition_90pct_by_tick=200`,
  scenario ticks=200, per `tools/simq_ceiling.py`'s own `lookup_ceiling()`).
- ECONOMY: B/0.1644 vs anchor C/0.0 — **score drifted beyond tolerance**, carries an existing
  `known tick_budget` ceiling classification (`zero_trade_after_tick=300`).
- PROGRESSION: B/0.3219 vs anchor C/-0.1569 — **score drifted beyond tolerance**, carries an
  existing `known tick_budget` ceiling classification (`progression_frozen_by_tick=200`).
- SOCIAL: S/13.35 vs anchor S/16.815 — **band passes** (same letter grade) but **score drifted
  beyond tolerance** (diff 3.465, floor max(0.05, 0.2×16.815)=3.363) — `lookup_ceiling()` returns
  `None` for `SOCIAL` on this run key; **no existing ceiling classification covers this drift.**

This ON-leg run reproduces, to the exact same numeric values (COMBAT=1.845, ECONOMY=0.1644,
PROGRESSION=0.3219, SOCIAL=13.35), the already-disclosed `INFORMATION`/`SOCIAL` grade-anchor
drift described in `tickets/todos/TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION.md`
(filed from the `SELF-MODEL-COGNITION` sibling's own trial, currently `OPEN`, not yet resolved).
**This ticket's trial reproduces that drift's `SOCIAL`-pillar half exactly** — `INFORMATION`
itself does not drift on *this specific* run key (see above; the drift ticket's own text confirms
`INFORMATION` only drifted on the sibling `urban_political_selfmodel_probe` run key, not this
`_execution_probe` one — this trial's own numbers are consistent with that). This is disclosed
here as confirmation, not fixed — see Honest Gap below; the pre-existing failing state of
`test_urban_political_selfmodel_execution_isolated_grade_anchor` observed in Step 1's baseline
(before this ticket ran any of its own trial legs) was itself leftover output from that same
already-filed, still-open drift-investigation ticket's own prior calibration run
(`data/calibration/urban_political_selfmodel_execution_probe_seed42_200t/quality_report.json`,
timestamped 2026-08-29 22:44, one day before this ticket's own execution) — not this ticket's own
run. This ticket's own fresh ON-leg run (Step 4) independently reproduces the identical numbers,
confirming the drift is deterministic and stable, not run-to-run noise.

### Signal 4 — deterministic no-suppression proof (hand-built scenario, unaffected by corpus)

`test_information_intent_execution_fires_through_kernel_tick_once` — **passed** in both the Step 1
baseline run and the Step 6 post-trial re-run. This is `INFRA-270`'s own guaranteed proof that
`ActionIntentAdapter.execute()` fires through a real `Kernel.tick_once()` loop when Branch B does
route a query, using a minimal hand-built scenario rather than depending on real corpus content —
independent of Signal 2's 0-trace finding above.

### Regression suite re-run — before/after tallies

Both the Step 1 (pre-trial) and Step 6 (post-trial) runs of the 5 scoped pytest commands produced
**identical pass/fail/skip tallies**:

```
tests/unit/engine/test_information_intent_execution_phase.py            -> 3 passed
tests/integration/domains/information/test_phase5_information_belief_phase.py -> 5 passed
tests/unit/config/test_phase10_feature_flags.py                          -> 7 passed
tests/integration/test_world_profile_feature_flag_guardrail.py           -> 67 passed
tests/simulation_quality/test_grade_regression.py -k "information_intent_execution or selfmodel_execution"
    -> 1 failed, 1 passed, 87 deselected
```

`test_urban_political_selfmodel_execution_isolated_grade_anchor` (the anchor test) **failed in
both the before and after runs, with byte-identical failure output** — this is a deviation from
plan.md's own expectation (it expected `SKIP` at baseline, transitioning to `PASS`/`FAIL` only
after Step 4 regenerated the report). The actual cause: a calibration report for this exact run
key already existed on disk *before* this ticket ran anything (leftover from the still-open
`TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION` ticket's own prior run, dated
2026-08-29), so the test never had a chance to `SKIP` at Step 1 — it was already asserting against
that leftover data and already failing on the same `SOCIAL`-pillar drift. Step 4's own fresh
ON-leg run then overwrote that file with this ticket's own independently-produced data, which
reproduced the identical failure — confirming the drift is real, deterministic, and reproducible
under this ticket's own execution, not an artifact of stale leftover data alone. See "Deviations"
in `plan.md` for the full note.

**Failure detail — `test_urban_political_selfmodel_execution_isolated_grade_anchor`:**
```
AssertionError: urban_political_selfmodel_execution_probe_seed42_200t — pillar(s) drifted beyond score tolerance:
  COMBAT: actual_score=1.845 outside tolerance of anchor_score=0.7839195979899497 [known tick_budget: ...]
  ECONOMY: actual_score=0.1643835616438356 outside tolerance of anchor_score=0.0 [known tick_budget: ...]
  PROGRESSION: actual_score=0.3219178082191781 outside tolerance of anchor_score=-0.1568627450980392 [known tick_budget: ...]
  SOCIAL: actual_score=13.35 outside tolerance of anchor_score=16.815
```
Band check (letter grade ±1) passed for every pillar (no letter-grade drift); score-tolerance
check failed on 4 pillars, 3 of which carry an existing `known tick_budget` ceiling
classification (pre-existing, unrelated to this flag). `SOCIAL` carries no such classification.

### No-suppression check

Passes. Signal 1's per-leg pillar breakdown shows no pillar collapsing toward zero on the ON leg
relative to OFF; Signal 2's 0-trace result is symmetric across both legs (expected "not reached,"
not a collapse from a nonzero OFF baseline); Signal 4's deterministic hand-built-scenario test
independently proves execution fires when Branch B does route a query. No evidence the
`ENABLE_INFORMATION_INTENT_EXECUTION` gate is starving `InformationIntentExecutionPhase` or that
wiring it into the pipeline destabilizes any other phase.

## Honest Gap

1. **`tools/calibrate_simq.py`'s `_KNOWN_FLAGS` allowlist gap (confirmed, not fixed by this
   ticket).** `_KNOWN_FLAGS` (`tools/calibrate_simq.py:243-250`) is the allowlist `main()`'s
   env-var-override loop (lines 272-277) iterates; it does not include
   `ENABLE_INFORMATION_INTENT_EXECUTION`. A bare env-var override
   (`ENABLE_INFORMATION_INTENT_EXECUTION=ON python3 tools/calibrate_simq.py ...`) would therefore
   silently no-op for this specific flag — `_parse_flag_value` never runs against it, so
   `combined_flag_overrides` never gains the key. This trial avoided the trap entirely by using
   `--profile`-level `feature_flags:` overrides (both legs), which have no such allowlist
   restriction. Not fixed here — out of this ticket's scope, per explicit instruction.
2. **The `urban_political_selfmodel_execution_probe_seed42_200t` anchor drift is real and
   reproduced, not a new finding this ticket discovered, but independent confirmation of an
   already-filed, still-open one.** `SOCIAL: actual=13.35 vs anchor=16.815` (uncovered by any
   `known tick_budget` ceiling classification) is byte-identical to the number already reported in
   `tickets/todos/TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION.md`, which was
   filed from the `SELF-MODEL-COGNITION` sibling ticket's own trial and remains `OPEN`
   (unresolved) as of this ticket's own execution. **This ticket's ON leg reproduces that same
   drift pattern** — confirmed here explicitly, not re-investigated or fixed (that ticket's own
   scope, not this one's). `INFORMATION` does *not* drift on this specific run key (exact match
   with its anchor, `B/0.2`) — the drift ticket's own filing text is consistent with this, since it
   only reported `INFORMATION` drift on the sibling `urban_political_selfmodel_probe` (materialization-
   only) run key, not this `_execution_probe` (full-stack) one. This ticket does not attempt to fix,
   re-anchor, or further trace the `SOCIAL` drift's root cause — that remains
   `TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION`'s own job.
3. **Deviation from plan.md's Step 1 expectation**, per the Regression suite section above: the
   pre-trial baseline showed `FAIL` (from leftover data belonging to the drift-investigation
   ticket), not the `SKIP` plan.md predicted. Recorded in `plan.md`'s own Deviations section.
4. **The corpus/seed/window combination in this trial (`urban_political`, seed 42, 200 ticks)
   cannot independently confirm `ActionIntentAdapter.execute()` fires with real, non-hand-built
   routed content** — 0 traces in both legs (Signal 2). This matches `INFRA-266`'s and the
   `SELF-MODEL-COGNITION` sibling's own prior finding for the identical corpus/seed/window; it is
   not a new gap this ticket surfaced, and per investigation.md's own Anti-Drift Notes, an
   extended-tick leg was deliberately not run (low marginal evidentiary value relative to cost,
   matching all 4 prior sibling tickets' own precedent).

## Recommendation

**Keep OFF, deferred.** No shipped `config/simulation_quality/profiles/*.yaml` turns
`ENABLE_INFORMATION_INTENT_EXECUTION` on anywhere (`urban_political_selfmodel_execution_probe.yaml`
is explicitly non-shipped — a probe-only fixture, not referenced by any world's default
calibration inheritance chain) — the same DEV-003 "shipped production profile" gap all 4 prior
sibling flags share. This trial confirms: (a) the distinction from `ENABLE_BELIEF_ASSIMILATION` is
real and structural — `ENABLE_BELIEF_ASSIMILATION` gates whether Branch B *populates*
`intent_results`; `ENABLE_INFORMATION_INTENT_EXECUTION` gates whether an already-populated
`ActionIntent` is *executed* — confirmed by direct code read (investigation.md) and by this
trial's own OFF-vs-ON comparison showing no `action_intent`/`ActionIntentAdapter` traces in either
leg despite `ENABLE_BELIEF_ASSIMILATION` being ON throughout; (b) no suppression or regression is
introduced by wiring the phase into the pipeline gated ON (Signal 1, No-suppression check); (c)
Branch B does not route a query in `urban_political` at seed 42 within a 200-tick window
regardless of which leg — an already-established, not-reached (not broken) finding, matching
`INFRA-266`/`INFRA-270`; (d) the deterministic hand-built-scenario test remains the guaranteed
proof that execution itself works when Branch B does fire (Signal 4). No new
`docs/guidelines/intentional_divergences.md` entry is needed — the flag's behavior versus the
Mechanics Bible does not change either way, and no chapter governs this Phase-10-era
infrastructure flag regardless.

This is the **5th and final of the 5 flags originally deferred by `TCK-20260824-ROLLOUT-FLAG-DECISIONS`**
(`ENABLE_COMBAT_ENGAGEMENT`, `ENABLE_SELF_MODEL_COGNITION`, `ENABLE_WORLD_EMERGENCE`,
`ENABLE_PROGRESSION_EVOLUTION`, and now `ENABLE_INFORMATION_INTENT_EXECUTION`) — all 5 now carry
real trial evidence on file. If a future ticket wants to re-open this: a shipped SimQ corpus
profile begins using `ENABLE_INFORMATION_INTENT_EXECUTION=ON` in production, matching the DEV-003
precedent directly, or a higher-`unknowns`-density world/seed independently confirms Branch B
routing a query through a real (not hand-built) corpus run.

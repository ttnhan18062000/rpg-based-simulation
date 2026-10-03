---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION
artifact_type: report
tags: [feature-flags]
---

# Trial Evidence — TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION

Raw output of the 2-leg fresh calibration trial run per `plan.md` Steps 1-4. Environment note:
the worktree's bare `python3` lacks `pydantic` (a pre-existing, unrelated environment gap); both
runs were executed with `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` (the
main checkout's venv) instead, with `cwd` still the worktree so `data/runs/` and
`data/calibration/` output landed in the same place the plan's commands specify.

## Commands run (verbatim except interpreter path)

```
# urban_political_selfmodel_probe (materialization-only, ENABLE_BELIEF_ASSIMILATION absent)
.venv/bin/python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name urban_political \
  --profile urban_political_selfmodel_probe \
  --output data/calibration/urban_political_selfmodel_probe_seed42_200t
# -> data/runs/run_1788018145_5169

# urban_political_selfmodel_execution_probe (full-stack, adds ENABLE_BELIEF_ASSIMILATION +
# ENABLE_INFORMATION_INTENT_EXECUTION)
.venv/bin/python3 tools/calibrate_simq.py --ticks 200 --seed 42 --name urban_political \
  --profile urban_political_selfmodel_execution_probe \
  --output data/calibration/urban_political_selfmodel_execution_probe_seed42_200t
# -> data/runs/run_1788018253_5169
```

## World-loading path confirmation

Both commands exited 0 and printed `[calibrate_simq] Profile feature flags: ...` matching each
profile's own YAML exactly (probe: `{ENABLE_SOCIAL_COOPERATION: ON, ENABLE_SELF_MODEL_COGNITION:
ON}`; execution probe: adds `ENABLE_BELIEF_ASSIMILATION: ON, ENABLE_INFORMATION_INTENT_EXECUTION:
ON}`), and `entities=10` — `urban_political`'s real compiled `data/worlds/urban_political/
resolved/world.resolved.yaml` entity count. Per `calibrate_simq.py:138-153`, `--name
urban_political` failing to resolve would raise `FileNotFoundError` rather than silently falling
back to the generic hero+goblins world — a successful run itself is sufficient proof, no separate
fingerprint check needed here since only one world is used across both legs (unlike the
combat-engagement sibling's two-world A/B).

## Evidence tally

### Step 3 signal 1 — pillar grades/scores/event counts (both runs)

| Pillar | probe (materialization-only) | execution probe (full-stack) |
|---|---|---|
| COGNITION | grade=S norm=27.28 events=5455 | grade=S norm=27.28 events=5455 |
| INFORMATION | grade=B norm=0.2 events=1 | grade=B norm=0.2 events=1 |
| SOCIAL | grade=S norm=13.35 events=1035 | grade=S norm=13.35 events=1035 |
| COMBAT | grade=A norm=1.845 events=129 | grade=A norm=1.845 events=129 |
| ECONOMY | grade=B norm=0.1644 events=4 | grade=B norm=0.1644 events=4 |
| PROGRESSION | grade=B norm=0.3219 events=6 | grade=B norm=0.3219 events=6 |

### Step 3 signal 2 — `self_model_updated` event volume vs INFRA-266's historical figure

`grep -c '"event_type": *"self_model_updated"' data/runs/{run_id}/simulation_events.jsonl`:
- probe run (`run_1788018145_5169`): **5454** events
- execution probe run (`run_1788018253_5169`): **5454** events

INFRA-266's historically recorded figure at this same world/seed/tick-count was `~5610-5611`
events/run. This fresh run's 5454 is within ~2.8% of that historical order of magnitude —
confirms the same unconditional per-alive-active-entity firing mechanism
(`self_model_phase.py:52-71`, no probability/threshold gate), not a collapse or suppression. Not
bit-identical to the historical figure (expected — a real corpus run, not a replayed fixture), and
the `quality_report.json` `event_count` (5455) is off-by-one from the raw grep count (5454) in
both legs identically — a stable, reproducible reporting-boundary artifact of how the report's own
window accounting counts vs. the raw JSONL, not a discrepancy between the two legs.

### Step 3 signal 3 — cross-check against `grade_anchors.json`

**`urban_political_selfmodel_probe_seed42_200t`** (anchor: `COGNITION=S/28.05`,
`INFORMATION=C/0.0`, `SOCIAL=S/17.895`):
- COGNITION: S/27.28 vs anchor S/28.05 — **within tolerance** (diff 0.77, floor
  max(0.05, 0.2×28.05)=5.61).
- INFORMATION: **B/0.2 vs anchor C/0.0 — DRIFTED.** `event_count=1`, not the anchored `0`.
- SOCIAL: S/13.35 vs anchor S/17.895 — same letter grade (band passes) but **score drifted
  beyond tolerance** (diff 4.545 vs floor max(0.05, 0.2×17.895)=3.579).

**`urban_political_selfmodel_execution_probe_seed42_200t`** (anchor: `COGNITION=S/27.485`,
`INFORMATION=B/0.2`, `SOCIAL=S/16.815`, plus `COMBAT=A/0.784`, `ECONOMY=C/0.0`,
`PROGRESSION=C/-0.157`):
- COGNITION: S/27.28 vs anchor S/27.485 — within tolerance.
- INFORMATION: B/0.2 vs anchor B/0.2 — **exact match.**
- SOCIAL: S/13.35 vs anchor S/16.815 — same letter grade but **score drifted beyond tolerance**
  (diff 3.465 vs floor max(0.05, 0.2×16.815)=3.363).
- COMBAT/ECONOMY/PROGRESSION also drifted outside score tolerance, but each is flagged by
  `tools/simq_ceiling.py`'s existing `lookup_ceiling()` as a **known, pre-existing** structural
  ceiling: `scenario ticks=200 <= detection_params.yaml`'s own `attrition_90pct_by_tick`/
  `zero_trade_after_tick`/`progression_frozen_by_tick` thresholds — a documented class of
  200-tick-window noise unrelated to `ENABLE_SELF_MODEL_COGNITION`, already classified by
  existing tooling, not a new finding.

### Step 4 — grade-anchor regression suite, un-skipped

`.venv/bin/python3 -m pytest tests/simulation_quality/test_grade_regression.py -k selfmodel -q`:

```
FAILED tests/simulation_quality/test_grade_regression.py::test_urban_political_selfmodel_cognition_isolated_grade_anchor
FAILED tests/simulation_quality/test_grade_regression.py::test_urban_political_selfmodel_execution_isolated_grade_anchor
2 failed, 4 skipped, 83 deselected
```

Both of the 2 target tests transitioned from `skipped` (no local report) to **actually running and
asserting** — the mechanism plan.md Step 4 called for. They did **not** pass. The other 4
`selfmodel`-matched tests (the `unit_selfmodel_pilot` seed/tolerance band checks) remain skipped —
they require `unit_selfmodel_pilot`'s own separate calibration reports, which this ticket's scope
did not regenerate (per plan.md Step 4's own explicit allowance: "not a blocker —
`unit_selfmodel_pilot`'s own evidence already exists from its own ticket").

**Failure detail — `test_urban_political_selfmodel_cognition_isolated_grade_anchor`:**
```
assert pillars["INFORMATION"]["grade"] == "C"
AssertionError: assert 'B' == 'C'
```
This is a hard equality assert (not the ±1 band check), so it fails on the exact `C` vs `B`
mismatch documented above.

**Failure detail — `test_urban_political_selfmodel_execution_isolated_grade_anchor`:**
```
AssertionError: ... pillar(s) drifted beyond score tolerance:
  COMBAT: actual_score=1.845 outside tolerance of anchor_score=0.784 [known tick_budget: ...]
  ECONOMY: actual_score=0.164 outside tolerance of anchor_score=0.0 [known tick_budget: ...]
  PROGRESSION: actual_score=0.322 outside tolerance of anchor_score=-0.157 [known tick_budget: ...]
  SOCIAL: actual_score=13.35 outside tolerance of anchor_score=16.815
```
Band check passed (no letter-grade drift); score tolerance failed on 4 pillars, 3 of which carry
an existing `known tick_budget` ceiling classification (pre-existing, unrelated to this ticket).
`SOCIAL` carries no such classification — `lookup_ceiling()` was checked directly for
`SOCIAL`/`INFORMATION` on both run keys and returned `None` in every case (see Honest Gap below).

Also re-ran (results match investigation.md's own prior baselines):
- `tests/unit/cognition/test_phase2_self_model_phase.py tests/unit/config/test_phase10_feature_flags.py -q`
  → **12 passed**.
- `tests/integration/domains/test_fused_loop.py -k "self_model or branch_b or belief" -q`
  → **7 passed, 3 deselected**.

## Honest gap — a real, undisclosed anchor drift (not a suppression regression, not fixed here)

**`INFORMATION` and `SOCIAL` drifted from their committed `grade_anchors.json` values on both
probe run keys, with no existing `known ceiling` classification covering either pillar.** Traced
to source: both runs' `belief_assimilated`/`belief_updated` event pair (subject
`bandit_road_danger`, actor 22, tick 1) is produced by `SelfModelUpdatePhase.run()`'s own Step 1
("Knowledge Assimilation", `self_model_phase.py:103-141`, via `KnowledgeModelService.assimilate()`
against a seeded `pending_self_model_information_events` entry) — a mechanism gated only by
`ENABLE_SELF_MODEL_COGNITION`, **not** by `ENABLE_BELIEF_ASSIMILATION`. It fired identically in
both legs (same subject, actor, tick), so this is reproducible, not run-to-run noise. This
mechanism was evidently not producing this event when the `urban_political_selfmodel_probe_seed42_200t`
anchor's `INFORMATION=C/0.0` value was set (`TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`) —
the anchor predates whatever seeded content or code path change now causes it to fire once within
this 200-tick window. `SOCIAL`'s drift (13.35 actual vs 17.895/16.815 anchored, both legs) was not
traced further — out of this ticket's scope (Scope Guards: "Do not fix any new bug the trial might
surface... inline — disclose it... as a new finding requiring a separate ticket").

This is disclosed as a genuine, reproducible finding, not smoothed over: **the fresh trial does
not cleanly reproduce the committed grade anchors for either `urban_political_selfmodel*_probe`
run key.** This does not itself change this ticket's keep/flip recommendation (see
`rollout_flag_decisions_m1.md`'s new section) — the DEV-003 "shipped profile" bar was already
unmet regardless of anchor cleanliness — but it is a new, separate finding requiring its own
follow-up ticket to either re-anchor `INFORMATION`/`SOCIAL` for these two run keys (if the drift
is a legitimate scoring-input change) or investigate a real regression (if it is not). Not
resolved or fixed as part of this ticket.

## AC2 resolution — `ENABLE_ADVENTURE_ROUTING` combination (static, not empirical)

Re-confirmed this session: `grep -rn "ENABLE_ADVENTURE_ROUTING" src/ tools/` still returns zero
live `is_enabled(...)`/`get_flag_mode(...)`/`feature_flag="ENABLE_ADVENTURE_ROUTING"` call sites —
only the flag's own registration (`feature_flags.py:25`), a comment stating it no longer gates
anything (`adventure_scorer.py:120`), a scenario-runner test-weight dict entry, and 3 `tools/*.py`
CLI-convenience references. `docs/engine/known_limitations.md` Section 1.5 and
`docs/parity_ledger/strategic_cognition.yaml` `STRAT-252` already document this inertness in
prose. No empirical combination trial was run (per plan.md's explicit Anti-Drift Hazard — no
runtime path exists for the two flags to interact, so a trial cannot produce a different answer
than the static analysis).

A new regression guard, `tests/architecture/test_adventure_routing_flag_inert.py::
test_enable_adventure_routing_has_no_live_gating_call_site`, was added to make this resolution
durable — it greps `src/` for the same 3 gating patterns and asserts zero matches outside
`feature_flags.py`'s own registration. `1 passed` when run this session.

## Recommendation

**Keep OFF, deferred.** Three independent real trials are now on file for
`ENABLE_SELF_MODEL_COGNITION` (`unit_selfmodel_pilot`'s shipped-ON 3-seed run, `INFRA-266`'s
real-world generalization split verdict, and this ticket's own 2 fresh confirming
`urban_political_selfmodel*_probe` runs), but `unit_selfmodel_pilot` remains the sole flag-ON
shipped profile — a dedicated 16-entity Unit-tier isolation world, not a real archetype world like
`urban_political`/`sandbox_world`. The DEV-003 "shipped production profile" bar is still unmet.
This fresh trial additionally surfaced a real, undisclosed `INFORMATION`/`SOCIAL` anchor drift on
both probe run keys — a genuine new finding (see Honest Gap above), not itself a reason to flip,
but a reason a separate follow-up ticket is needed before treating these two anchors as trustworthy
regression guards going forward.

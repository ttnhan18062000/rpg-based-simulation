---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT
artifact_type: investigation
tags: [simulation-quality, calibration, corpus, economy, progression]
---

# Investigation — TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT

## Current Behavior

### Fresh calibration re-verification (both named run_keys, current HEAD)

`tools/calibrate_simq.py --ticks 500 --seed 456 --name hero_guild_routing`, run 6 times this
session (5 clean, 1 with a DEBUG log handler attached — see Risks #2):

```
=== Quality Report: hero_guild_routing_seed456_500t ===
  ticks=500 events=104 elapsed=7.65s profile=hero_guild_routing window_size=200 loop_threshold=0.7
  overall_grade=B overall_score=0.0017

  Pillar breakdown:
    AGENCY                grade=C  norm=+0.0000  events=0
    COGNITION             grade=C  norm=+0.0000  events=0
    COMBAT                grade=C  norm=+0.0000  events=0
    ECONOMY               grade=C  norm=+0.0000  events=0
    FACTION               grade=C  norm=+0.0000  events=0
    INFORMATION           grade=C  norm=+0.0000  events=0
    NARRATIVE             grade=C  norm=+0.0000  events=0
    PROGRESSION           grade=C  norm=-0.3025  events=11
    SOCIAL                grade=C  norm=+0.0000  events=0
    WORLD                 grade=B  norm=+0.3200  events=57
```

ECONOMY (`0 events / 0.0`) and PROGRESSION (`11 events / -0.30252100840336...`, raw `-108.0`) were
**bit-identical across all 5 clean trials** (trials 1, 3, 4, 5, 6 — the debug-instrumented trial 2
alone showed 12 events/-0.2837, traced to the debug handler's own I/O overhead perturbing the
wall-clock watchdog throttle, not a second natural state — see Risks #2). This matches the ticket's
cited actual values exactly: ECONOMY `0.0` vs. anchor `B/0.10972568578553615`; PROGRESSION
`-0.3025210084033613` vs. anchor `D/-0.6212534059945504`. **Confirmed accurate at current HEAD, not
stale** — this is a genuinely deterministic drift, not an artifact of the earlier snapshot.

`tools/calibrate_simq.py --ticks 500 --seed 456 --name simq_routing_test`, run 6 times this session
(5 clean, 1 debug-instrumented):

```
=== Quality Report: simq_routing_test_seed456_500t ===
  ticks=500 events=131 elapsed=7.55s profile=simq_routing_test window_size=200 loop_threshold=0.7
  overall_grade=C overall_score=-0.0033

  Pillar breakdown:
    AGENCY                grade=C  norm=+0.0000  events=0
    COGNITION             grade=C  norm=+0.0000  events=0
    COMBAT                grade=B  norm=+0.0727  events=6
    ECONOMY               grade=B  norm=+0.0952  events=4
    FACTION               grade=C  norm=+0.0000  events=0
    INFORMATION           grade=C  norm=+0.0000  events=0
    NARRATIVE             grade=C  norm=+0.0000  events=0
    PROGRESSION           grade=C  norm=-0.2359  events=25
    SOCIAL                grade=C  norm=+0.0000  events=0
    WORLD                 grade=B  norm=+0.0350  events=11
```

COMBAT (`6 events / 0.07272727272727272`, deterministic across all 6 trials) and ECONOMY
(`4 events / 0.09523809523809523`, deterministic across all 6 trials) matched the ticket's citations
exactly (`actual=0.0727...` for COMBAT). **PROGRESSION showed real run-to-run non-determinism across
6 independent process invocations, same seed/code**: `21 events/-0.15483870967741936` (trials 1, 5)
vs. `25 events/-0.2359249329758713` (trials 2[debug], 3, 4, 6) — a genuine bimodal split, not a
single stable value. The ticket's cited actual (`-0.15483870967741936`) is one of the two observed
natural states, not the more frequently-observed one (2/5 clean trials vs. 3/5). See Finding 2 below.

Ran the ticket's own specified regression command against these fresh reports:

```
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k \
  "hero_guild_routing_seed456_500t or simq_routing_test_seed456_500t"
```

Result: **2 failed** (both parametrizations of `test_grade_within_anchor_band`), zero `band_failures`
on either run_key (confirming the ticket's framing — this is purely a score-tolerance issue, not a
letter-band crossing). Full `score_failures` list per run_key (verbatim from the fresh pytest run,
`_format_score_failures`'s `[known ...]` annotations included where `simq_ceiling.lookup_ceiling()`
already classifies the pillar):

**`hero_guild_routing_seed456_500t` — 4 pillars flagged:**
```
COMBAT: actual_score=0.0 outside tolerance of anchor_score=-0.0967741935483871 [known flag_gated: ...]
ECONOMY: actual_score=0.0 outside tolerance of anchor_score=0.10972568578553615
PROGRESSION: actual_score=-0.3025210084033613 outside tolerance of anchor_score=-0.6212534059945504
WORLD: actual_score=0.32 outside tolerance of anchor_score=0.115 [known tick_budget: scenario ticks=500 <= detection_params.yaml's zero_emergence_by_tick=500; ...]
```

**`simq_routing_test_seed456_500t` — 2 pillars flagged:**
```
COMBAT: actual_score=0.07272727272727272 outside tolerance of anchor_score=0.0 [known flag_gated: ...]
PROGRESSION: actual_score=-0.2359249329758713 outside tolerance of anchor_score=-0.6927374301675978
```

**This is a real, previously-unknown finding beyond the ticket's own framing**: `hero_guild_routing_
seed456_500t` also has a WORLD-pillar score-tolerance failure (`0.32` vs. anchor `0.115`), but it is
already fully "known" — `tools/simq_ceiling.py`'s computed `tick_budget` classifier (not a
`score_ceilings.json` fixture entry; it's derived live from `config/simulation_quality/
detection_params.yaml`'s `zero_emergence_by_tick=500` vs. this run_key's own `ticks=500` in
`corpus_registry.yaml`) already explains it structurally: at exactly the gate threshold, the
`loop_sustained_window`/emergence-dormancy rule is inherently unreliable. **No action needed on
WORLD** — it is not part of this ticket's named scope and is already correctly disclosed by the
automated ceiling mechanism, not a silent gap.

Both run_keys' COMBAT failures are likewise already `[known flag_gated]` — confirmed accurate
(`FLAG_GATED_PILLAR_CEILINGS["COMBAT"]`, `tools/simq_ceiling.py:64-76`: `ENABLE_COMBAT_ENGAGEMENT`
corpus-wide OFF per `TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY`). This confirms the
ticket's spot-check request: `simq_routing_test_seed456_500t`'s COMBAT drift remains correctly
explained by the existing flag-gated ceiling classification, unchanged.

**Net: exactly 3 (run_key, pillar) pairs are genuinely unexplained** — `hero_guild_routing_
seed456_500t`/ECONOMY, `hero_guild_routing_seed456_500t`/PROGRESSION, `simq_routing_test_
seed456_500t`/PROGRESSION. These are the ticket's own named scope, confirmed complete: no additional
undisclosed drift exists on either run_key beyond what the ticket already named.

### Finding 1 — root cause: tier-5 goal-arbitration dominance by `COMBAT_ENGAGE`/`REGION_STABILIZATION` starves `HARVESTING`, which drives both ECONOMY and PROGRESSION's capability-growth signal

A DEBUG-level trace of `StrategicIntelligenceSystem`'s own tier-5 goal-selection log
(`intelligence.py:1478-1481`, `"[Tick N] Entity E strategic goal selection: chosen=..., rejected=..."`)
was captured for both run_keys via a fresh, isolated instrumented run (500 ticks each, same seed,
current HEAD; script written to
`/tmp/.../scratchpad/run_debug_trace.py`, attaching a `logging.FileHandler` at `DEBUG` to the
`src.systems.strategic_systems.intelligence` logger before calling `tools.calibrate_simq.main()`
directly — no source file touched).

**`hero_guild_routing_seed456_500t`, 371 total goal-selection decisions across the run:**
```
144 region_stabilization
135 combat_engage
 57 resolve_blocker
  5 town_return
  1 harvesting          <-- HARVESTING wins tier-5 arbitration exactly once in 371 evaluations
 29 chosen=None (no candidate cleared the 20.0 utility floor)
```

**`simq_routing_test_seed456_500t`, 335 total goal-selection decisions:**
```
158 region_stabilization
 86 resolve_blocker
 65 combat_engage
  4 recover
  3 town_return
  1 harvesting          <-- same signature: 1/335
```

Sample raw trace lines (`hero_guild_routing`, ticks 7/13):
```
[Tick 7] Entity 13 strategic goal selection: chosen=combat_engage (73.5), rejected=harvesting:23.4, social:11.2, ...
[Tick 13] Entity 7 strategic goal selection: chosen=combat_engage (93.5), rejected=harvesting:30.2, social:11.2, ...
```
`harvesting`'s own rejected-candidate utility peaks around 15-30 and is typically 1-5 — it is very
rarely the top-rejected candidate and never wins when `combat_engage`/`region_stabilization` are
active, which (per the tally above) is on ~75% of all evaluated ticks combined.

**Direct read of the three competing scorers confirms this is a formula-level, not a bug-level,
cause**:
- `HarvestScorer.score()` (`src/ai/goals/scorers.py:6-34`): `utility = 50.0 / dist` (Manhattan
  distance to the nearest resource node, floor 1.0) — inherently distance-decayed, only near its
  peak (~50) when the entity is standing right next to a resource node. Observed values in the trace
  (1-30) are consistent with entities rarely being positioned near a node while busy with
  combat/stabilization.
- `CombatEngageScorer.score()` (`scorers.py:101-132`): `utility = 40.0 + bravery*40.0 +
  stamina_ratio*20.0` when a hostile is in range — not distance-decayed, structurally floors at 40
  and commonly reaches 70-140+.
- `RegionStabilizationGoalScorer.score()` (`src/ai/goals/region_stabilization_scorer.py:61`):
  `utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX` where
  `raw_score = urgency * 2.9` (`docs/guidelines/intentional_divergences.md` §2.43) — observed flat
  `100.0` in the trace, i.e. `urgency` is at/near its own ceiling on effectively every tick region
  danger is present, by design (§2.43 is an `Enforced` divergence, not a bug).

**This is the same causal *family* as the sibling ticket's Problem B finding
(`TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE`'s Deviations §2 / filed follow-up
`TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5`)**: entities in both
`hero_guild_routing_seed456_500t` and `simq_routing_test_seed456_500t` spend the overwhelming
majority of ticks on `COMBAT_ENGAGE`/`REGION_STABILIZATION`, structurally starving every other
tier-5 `GoalKind` — that ticket found this for `ADVENTURE_ROUTE` (capped at `_ADVENTURE_ROUTE_SCORE_
MAX=2.9`, normalized to ~20-26, confirmed in its own DEBUG trace); this investigation independently
confirms the identical starvation pattern for `HARVESTING` (via a distance-decayed formula, not an
explicit scale cap — a mechanistically distinct GoalKind and a different specific formula, but the
same downstream effect and the same two dominant competitors). **It is not the ADVENTURE_ROUTE
finding itself** (this ticket's two drifted run_keys' AGENCY fields are unrelated — already
recalibrated to `C/0.0` by the parent ticket and confirmed unaffected here) — it is a related,
independently-confirmed instance of the same broader tier-5-arbitration-dominance phenomenon,
affecting a different `GoalKind` and therefore a different set of pillars (ECONOMY directly;
PROGRESSION indirectly, via `capability_growth_stalled`, see below).

**PROGRESSION's specific mechanism, confirmed via `data/calibration/{run_key}/quality_report.json`'s
`worst_events`**: for `hero_guild_routing_seed456_500t`, all 11 PROGRESSION events are
`capability_growth_stalled` (`delta=-10.0` each), reason `"entity's level/skills/gear/gold all flat
for the stall window"`, plus an `xp_plateau` loop flag. For `simq_routing_test_seed456_500t`
(25-event state), 17 of 25 events are the same `capability_growth_stalled` penalty. `gear`/`gold`
growth is driven by harvesting/crafting/trading (ECONOMY's own event set) and quest completion —
since `HARVESTING` essentially never wins tier-5 arbitration (1/371, 1/335), gear/gold never grow,
and the small amount of combat-driven XP that does occur (`combat_engage` wins 135/371 and 65/335
ticks respectively) is not enough by itself to avoid the stall/plateau detection. **PROGRESSION's
drift is a direct downstream consequence of the same ECONOMY-starving mechanism, not an independent
cause.**

### Finding 2 — `simq_routing_test_seed456_500t`/PROGRESSION additionally exhibits genuine
`watchdog_variance`-class run-to-run jitter on top of the Finding-1 suppression

6 independent process invocations of `tools/calibrate_simq.py --ticks 500 --seed 456 --name
simq_routing_test` this session (same seed, same code, no edits between runs) produced a
**reproducible bimodal split**, not a single stable value:

| Trial | events | raw_score | normalized_score | Notes |
|---|---|---|---|---|
| 1 | 21 | -54.0 | -0.15483870967741936 | clean |
| 2 | 25 | -86.0 | -0.19642857142857142 (approx) | DEBUG-instrumented (file I/O overhead) |
| 3 | 25 | -88.0 | -0.2359249329758713 | clean |
| 4 | 25 | -88.0 | -0.2359249329758713 | clean, byte-identical to trial 3 |
| 5 | 21 | -54.0 | -0.15483870967741936 | clean, byte-identical to trial 1 |
| 6 | 25 | -88.0 | -0.2359249329758713 | clean, byte-identical to trials 3/4 |

Among the 5 clean (non-instrumented) trials: 2/5 landed on the `21-event/-0.1548` state, 3/5 landed
on the `25-event/-0.2359` state. `COMBAT`, `ECONOMY`, and every other pillar stayed byte-identical
across all 6 trials — the jitter is localized to PROGRESSION specifically, on this run_key. This is
the identical signature to the already-documented `score_ceilings.json` `watchdog_variance` entries
for `simq_routing_test_seed42_500t`/PROGRESSION and `simq_routing_test_seed123_500t`/PROGRESSION
(real run-to-run non-determinism from `kernel.py`'s wall-clock tick-budget throttle, D06 F6,
intermittently dropping a different number of events run-to-run) — **not a code defect, and not
explained by Finding 1 alone** (Finding 1 explains why PROGRESSION's baseline is suppressed at all;
Finding 2 explains why the exact suppressed value itself varies run-to-run). No corresponding
variance was found for `hero_guild_routing_seed456_500t`'s ECONOMY or PROGRESSION — those were
bit-identical across 5/5 clean trials (the one differing trial was the debug-instrumented one, whose
own timing perturbation is the most likely explanation, not a second natural state for that
run_key — see Risks #2).

**Answering the ticket's three-way disjunction directly**:
- `hero_guild_routing_seed456_500t` ECONOMY/PROGRESSION: **Finding 1 only** (deterministic tier-5
  starvation, same causal family as the sibling's ADVENTURE_ROUTE finding but a distinct GoalKind).
  Not `watchdog_variance` — no jitter observed across 5 clean trials.
- `simq_routing_test_seed456_500t` PROGRESSION: **both Finding 1 (why it's suppressed) and Finding 2
  (why the suppressed value itself jitters)** — genuinely qualifies for a `watchdog_variance`
  ceiling annotation on top of a point-recalibration, matching the `TCK-20260810-SIMQ-FAST-TIER-
  DRIFT-AND-RELIABILITY-GAP` precedent exactly.
- Not "something else" in either case — no third, unrelated mechanism was found.

## Mechanics / Engine Constraints

- `docs/guidelines/intentional_divergences.md` §2.41 "Adventure-Route Defer-Reason Observability
  Gap" (Broadened-disclosure addendum, 2026-08-13) — documents the identical tier-5-competition-scale
  phenomenon for `ADVENTURE_ROUTE` specifically. This investigation's Finding 1 is a related,
  independently-confirmed instance for a different `GoalKind` (`HARVESTING`) — see Docs Requiring
  Update.
- `docs/guidelines/intentional_divergences.md` §2.43 "Regional-Danger Stabilization No Longer
  Unconditionally Wins the Project Slot" (`TCK-20260811-REGION-STABILIZATION-GOAL-SCORER`) — the
  `Enforced` divergence that introduced `REGION_STABILIZATION` as a live, competing tier-5
  `GoalKind` for the first time (previously zero production callers). Its `raw_score = urgency * 2.9`
  formula, observed flat at its own ceiling in this session's trace, is one of the two structurally
  dominant competitors identified in Finding 1. This entry documents the mechanism's introduction
  correctly; it does not document (and is not the right place to document) its downstream
  starvation effect on `HARVESTING`/ECONOMY/PROGRESSION — that belongs alongside §2.41's own
  broadened disclosure of the same starvation *class* for `ADVENTURE_ROUTE`.
- `docs/mechanics/03_economic_laws.md` and `docs/mechanics/01_entity_anatomy.md` (XP/progression
  chapter) are not contradicted by this finding — the harvesting/XP *formulas* themselves are
  unchanged and correct; only the *frequency* with which the harvesting goal is ever selected has
  collapsed, a strategic-cognition-layer effect, not an economic- or progression-law violation.
- Strategic/Tactical Rule (CLAUDE.md) — not violated; this is a legitimate strategic
  goal-arbitration outcome (tactical execution correctly reflects whatever the strategic layer
  selects), not a case of tactical goal-stacking substituting for strategic direction.

## Docs Requiring Update

- `tests/simulation_quality/fixtures/grade_anchors.json`: `hero_guild_routing_seed456_500t`'s
  ECONOMY (`B/0.10972568578553615` → `C/0.0`) and PROGRESSION (`D/-0.6212534059945504` →
  `C/-0.3025210084033613`) fields, plus `simq_routing_test_seed456_500t`'s PROGRESSION field
  (`D/-0.6927374301675978` → a representative current value — Plan must pick between the two
  observed natural states, `C/-0.15483870967741936` (2/5 clean draws) or `C/-0.2359249329758713`
  (3/5 clean draws); this investigation recommends the more frequently-observed `-0.2359249329758713`
  but flags this as a real open call, not pre-decided — see Risks #1). Not a docs/ path but the
  primary durable-truth artifact this ticket recalibrates.
- `tests/simulation_quality/fixtures/score_ceilings.json`: needs a new `watchdog_variance` entry for
  `("simq_routing_test_seed456_500t", "PROGRESSION")`, matching the existing `simq_routing_test_
  seed42_500t`/PROGRESSION and `simq_routing_test_seed123_500t`/PROGRESSION entries' shape exactly
  (`reason` citing the 21-vs-25-event bimodal split confirmed via 6 independent re-runs this session,
  `evidence` citing this ticket's own re-runs, `since_ticket` this ticket's ID). No corresponding
  entry is needed for `hero_guild_routing_seed456_500t` (deterministic, no jitter observed).
- `docs/guidelines/intentional_divergences.md`: §2.41 should get a further dated addendum (or a
  cross-reference note) disclosing that the same tier-5-starvation phenomenon it already documents
  for `ADVENTURE_ROUTE` also suppresses `HARVESTING` on these same two run_keys, with downstream
  effects on ECONOMY (directly) and PROGRESSION (via `capability_growth_stalled`) — citing this
  ticket's DEBUG-trace evidence (1/371 and 1/335 win rates) and cross-referencing the existing
  follow-up ticket `TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5` as the natural
  place a future code-level fix (if one is ever undertaken) would need to consider `HARVESTING`
  alongside `ADVENTURE_ROUTE`, since both lose to the identical two competitors for the identical
  structural reason. This is a disclosure obligation (CLAUDE.md "no material gap left unstated" /
  Authoritative Mechanics Rule's Divergence clause), not a code-fix commitment.
- `docs/simulation_quality/eval_matrix_results.md`: both the `simq_routing_test` (500t table,
  ~line 374-396) and `hero_guild_routing` (500t table, ~line 1451-1462) subsections' existing tables
  state stale ECONOMY/PROGRESSION values for seed456 (the `simq_routing_test` historical table shows
  `PROGRESSION | C | C | C | norm ≈ -0.06, event_count=1, all 3 seeds` — no longer accurate for
  seed456 at `-0.2359`/`25 events`; the `hero_guild_routing` table shows `PROGRESSION | B | B | B |
  stable` — no longer accurate for seed456 at `C`/`-0.3025`). A dated NOTE block in each subsection
  (matching this doc's own established pattern, e.g. the 2026-08-13 COGNITION/AGENCY NOTE blocks
  already present) recording this ticket's fresh measurements and root cause is needed — do not
  silently rewrite the historical tables themselves.

## Parity Ledger Overlap

- No `docs/parity_ledger/*.yaml` entry makes a specific numeric-grade claim for either run_key's
  ECONOMY or PROGRESSION pillar that this finding contradicts. `docs/parity_ledger/town_resource.yaml`
  and `docs/parity_ledger/progression.yaml` were checked (`search_docs`/`graphify query` plus direct
  grep for `hero_guild_routing`/`simq_routing_test`) — no matching entries. `docs/parity_ledger/
  strategic_cognition.yaml` (STRAT-255, the `REGION_STABILIZATION` scorer entry) and
  `docs/parity_ledger/infrastructure.yaml` (INFRA-237) both already carry addenda about the tier-5
  competition-dominance phenomenon in general (from the sibling AGENCY ticket and
  `ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE`), but neither makes a per-pillar ECONOMY/PROGRESSION
  claim — no edit to either is required by this ticket. No P0 parity entry is implicated, so no
  `test_path`-passing requirement is triggered.
- `docs/parity_ledger/strategic_cognition.yaml` STRAT-185/186/187 (`3d992dd0` interruption-bypass
  generalization) and the seed123 COGNITION/AGENCY commit cluster: confirmed **not** the cause here
  — this investigation's root cause (tier-5 goal-competition dominance) is a distinct, independently
  confirmed mechanism from that commit cluster's own cause (§2.40).

## Prior Work

- `stored_artifacts/TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT/` (investigation.md
  Risk #3, plan.md Step 9b/Deviations) — the ticket that first flagged both of this ticket's findings
  as out-of-named-scope discoveries, deferring them here. Confirmed both anchor citations
  (`hero_guild_routing_seed456_500t` ECONOMY/PROGRESSION, `simq_routing_test_seed456_500t`
  PROGRESSION) match this investigation's own fresh re-verification exactly.
- `tickets/done/TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE.md` +
  `stored_artifacts/TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE/plan.md` (Deviations §2)
  — the direct precedent for this investigation's root-cause methodology (DEBUG-trace of tier-5
  goal-selection). Its filed follow-up, `TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-
  TIER5` (OPEN), tracks the `ADVENTURE_ROUTE` half of this same broader phenomenon; this
  investigation independently confirms an analogous `HARVESTING` half exists, affecting different
  pillars.
- `stored_artifacts/TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP/` — established the
  `watchdog_variance` ceiling mechanism and its evidentiary bar (multiple independent same-seed
  re-runs showing real event-count variance). Finding 2's 6-trial bimodal-split evidence directly
  follows this same evidentiary pattern.
- `tools/simq_ceiling.py` (`TCK-20260808-SIMQ-SCORE-CEILING-PROVENANCE`) — the `flag_gated`/
  `tick_budget` computed-ceiling mechanism that already, correctly explains both run_keys' COMBAT
  failures and `hero_guild_routing_seed456_500t`'s newly-observed WORLD failure without requiring
  any fixture edit.

## Risks and Open Questions

1. **Exact recalibration value for `simq_routing_test_seed456_500t`/PROGRESSION is a real, undecided
   choice, not resolved here.** Two natural states were observed (`-0.15483870967741936`, 2/5 clean
   draws; `-0.2359249329758713`, 3/5 clean draws). Point-editing to either value leaves the *other*
   state's future draws still failing score tolerance by ~0.081 (exceeds the default `max(0.05,
   20%*|anchor|)` floor regardless of which is chosen) — this is precisely why a `watchdog_variance`
   ceiling annotation is also needed (Finding 2), not a substitute for picking a value. Plan should
   decide the exact anchor value; this investigation recommends the more-frequently-observed
   `-0.2359249329758713` but does not pre-decide it.
2. **Adding a `SCORE_TOLERANCE_OVERRIDES` entry for `("simq_routing_test_seed456_500t",
   "PROGRESSION")` would break `test_score_tolerance_override_table_scoped_to_named_pillars`**
   (`tests/simulation_quality/test_grade_regression.py:686-706`), which asserts the override table
   contains **exactly** its current 5 entries. The existing `watchdog_variance` precedent for
   `simq_routing_test_seed42_500t`/`_seed123_500t` PROGRESSION does **not** have a matching
   `SCORE_TOLERANCE_OVERRIDES` entry either — confirming the established pattern is: `score_ceilings.
   json` documents *why* an occasional score-tolerance failure is expected/understood, it does not
   widen the tolerance itself. Plan/Implement must not add a `SCORE_TOLERANCE_OVERRIDES` entry as
   part of this ticket (would require also updating that anti-drift guard test, a larger and
   differently-scoped change than a fixture point-edit).
3. **This ticket's own AC wording ("shows 0 unexplained failures") does not mean the scoped pytest
   command will exit 0.** Confirmed directly this session: even after recalibrating all 3 named
   (run_key, pillar) pairs, `hero_guild_routing_seed456_500t` will still show COMBAT (`[known flag_
   gated]`) and WORLD (`[known tick_budget]`) score-tolerance failures in the same test's output —
   both pre-existing, both already correctly annotated by the automated ceiling classifiers, neither
   part of this ticket's scope to silence. `simq_routing_test_seed456_500t` will likewise still show
   COMBAT (`[known flag_gated]`) and, on roughly 2/5 future draws, PROGRESSION itself (`[known
   watchdog_variance]`, once the new ceiling entry exists) — this is the correct, intended
   end-state, not a leftover gap. Test_plan.md's verification section must state this explicitly so
   Implement/Verify do not mistake a still-red pytest run for an incomplete fix.
4. **DEBUG-instrumented calibration runs are not a reliable "clean HEAD" measurement.** One of this
   session's 6 trials per run_key had a `logging.FileHandler` attached to capture the tier-5
   goal-selection trace; that trial's own numbers diverged slightly from the other 5 clean trials on
   `hero_guild_routing_seed456_500t` (12 vs. 11 events) and landed on the "25-event" state for
   `simq_routing_test_seed456_500t` — plausibly because the added per-tick file I/O perturbed
   wall-clock watchdog-throttle timing. Any future re-verification should use clean (non-instrumented)
   `tools/calibrate_simq.py` invocations for the final committed numbers, not a debug-trace run's own
   output.
5. **No code-level bug was found or is being proposed.** Both findings are downstream consequences
   of already-shipped, already-reviewed strategic-cognition behavior (§2.40/§2.41/§2.42/§2.43's
   GoalScorer-wrapper migrations) interacting with these two worlds' specific danger/hostile density.
   Per the ticket's Out of Scope, no change to `src/domains/adventure/`,
   `src/systems/strategic_systems/intelligence.py`, `src/ai/goals/`, or any other production code is
   proposed here. If a future ticket does decide to revisit the tier-5 utility-scale/competition
   design (as `TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5` already proposes for
   `ADVENTURE_ROUTE`), this investigation's Finding 1 is evidence that `HARVESTING`'s distance-decay
   formula should be considered in the same pass, since it is starved by the identical two
   competitors for a structurally analogous reason — but that is a candidate follow-up, not this
   ticket's or this investigation's decision to make.

## Anti-Drift Hazards

- **Do not touch `hero_guild_routing_seed456_500t`'s or `simq_routing_test_seed456_500t`'s COMBAT or
  WORLD fields in `grade_anchors.json`** — both are already correctly, automatically explained by
  `tools/simq_ceiling.py`'s computed `flag_gated`/`tick_budget` classifiers; editing the anchor would
  not change the pytest outcome (the classifier is independent of the anchor value) and would be
  scope creep beyond this ticket's own named 3 (run_key, pillar) pairs.
- **Do not add a `SCORE_TOLERANCE_OVERRIDES` entry** for either run_key/pillar (Risk #2) — would
  require also updating `test_score_tolerance_override_table_scoped_to_named_pillars`'s exact-5-entry
  assertion, a materially larger and differently-scoped change than this ticket's own Related Code
  Areas (`grade_anchors.json`, `score_ceilings.json` only).
- **Do not delete or overwrite the existing `simq_routing_test_seed42_500t`/`_seed123_500t`
  `watchdog_variance` entries** — the new entry for `simq_routing_test_seed456_500t`/PROGRESSION is
  additive, a sibling entry, not a replacement.
- **Do not touch AGENCY or COGNITION on either run_key** — both already correctly sit at `C/0.0`
  from the parent ticket's own recalibration; this ticket's findings are unrelated to and do not
  reopen that recalibration.
- **Do not fix `src/ai/goals/scorers.py`'s `HarvestScorer` distance-decay formula, `src/ai/goals/
  region_stabilization_scorer.py`, or `src/systems/strategic_systems/intelligence.py`'s tier-5 loop**
  — explicitly out of scope per the ticket; this is a recalibration-and-disclose ticket, and any
  code-level rebalancing is a candidate for `TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-
  TIER5` or a new, separately-scoped follow-up, not this ticket.
- **Do not run `tools/calibrate_simq.py` with a DEBUG log handler attached and commit its output as
  the "official" recalibration numbers** — Risk #4's own perturbation finding means only clean,
  non-instrumented runs should feed the final `grade_anchors.json`/`score_ceilings.json` values.

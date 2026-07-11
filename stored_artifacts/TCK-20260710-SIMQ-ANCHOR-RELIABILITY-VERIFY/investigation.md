---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY
artifact_type: investigation
tags: [simulation-quality, calibration, determinism, corpus]
---

# Investigation — TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY

## Current Behavior

### The 18 `SLOW_ANCHOR_KEYS` and the invocation each requires

`tests/simulation_quality/test_grade_regression.py:106-131` defines `SLOW_ANCHOR_KEYS`, consumed by
`test_grade_within_anchor_band_long_run` (`test_grade_regression.py:219-248`, `@pytest.mark.slow`).
For each key it loads `data/calibration/{run_key}/quality_report.json`
(`_load_calibration_report`, line 159) and `pytest.skip`s if the file is absent — it never invokes
the engine itself. `data/calibration/` is gitignored (confirmed via `git check-ignore`), so this
directory is machine-local and ephemeral; **7 of the 18 keys currently have no report on disk in
this environment** (`unit_selfmodel_pilot_seed42_1000t`, `hero_guild_routing_seed42_1000t`,
`simq_routing_test_seed42_1000t`, `unit_faction_tension_seed42_{1000,2000}t`,
`urban_political_seed42_2000t`, `generated_frontier_3_42_seed42_1000t`); the other 11 are present
from a prior session. This means the test currently silently skips those 7 rather than failing —
re-running calibration is not optional busywork, it is required just to make the existing slow
suite exercise those keys at all in a fresh environment/CI.

Each key name follows `{world}_seed{N}_{ticks}t` and maps directly to `tools/calibrate_simq.py`'s
CLI (`--ticks`, `--seed`, `--name`, `--profile`, args at lines 286-299). `--profile` defaults to
`--name` if `config/simulation_quality/profiles/{name}.yaml` exists, else `"default"`
(`_resolve_profile`, lines 32-41). Confirmed profile file presence via `ls
config/simulation_quality/profiles/`: all 8 worlds have a matching profile file **except**
`unit_faction_tension`, which falls back to `"default"`.

Full key → invocation map (profile omitted = defaults to `--name`, i.e. its own profile file):

| Key | `--name` | `--seed` | `--ticks` | `--profile` |
|---|---|---|---|---|
| `dungeon_crawl_seed42_1000t` | dungeon_crawl | 42 | 1000 | dungeon_crawl |
| `sandbox_world_seed42_1000t` | sandbox_world | 42 | 1000 | sandbox_world |
| `dungeon_crawl_seed123_1000t` | dungeon_crawl | 123 | 1000 | dungeon_crawl |
| `dungeon_crawl_seed456_1000t` | dungeon_crawl | 456 | 1000 | dungeon_crawl |
| `urban_political_seed42_1000t` | urban_political | 42 | 1000 | urban_political |
| `urban_political_seed123_1000t` | urban_political | 123 | 1000 | urban_political |
| `urban_political_seed456_1000t` | urban_political | 456 | 1000 | urban_political |
| `dungeon_crawl_seed42_2000t` | dungeon_crawl | 42 | 2000 | dungeon_crawl |
| `dungeon_crawl_seed123_2000t` | dungeon_crawl | 123 | 2000 | dungeon_crawl |
| `dungeon_crawl_seed456_2000t` | dungeon_crawl | 456 | 2000 | dungeon_crawl |
| `sandbox_world_seed42_2000t` | sandbox_world | 42 | 2000 | sandbox_world |
| `unit_selfmodel_pilot_seed42_1000t` | unit_selfmodel_pilot | 42 | 1000 | unit_selfmodel_pilot |
| `hero_guild_routing_seed42_1000t` | hero_guild_routing | 42 | 1000 | hero_guild_routing |
| `simq_routing_test_seed42_1000t` | simq_routing_test | 42 | 1000 | simq_routing_test |
| `unit_faction_tension_seed42_1000t` | unit_faction_tension | 42 | 1000 | **default** (no profile file) |
| `unit_faction_tension_seed42_2000t` | unit_faction_tension | 42 | 2000 | **default** |
| `urban_political_seed42_2000t` | urban_political | 42 | 2000 | urban_political |
| `generated_frontier_3_42_seed42_1000t` | generated_frontier_3_42 | 42 | 1000 | generated_frontier_3_42 |

Example invocation: `python3 tools/calibrate_simq.py --ticks 1000 --seed 42 --name
generated_frontier_3_42` (profile auto-resolves to `generated_frontier_3_42`; omit `--profile`
unless overriding). `--output` may be used to redirect a given trial's report to a non-canonical
path (e.g. `data/calibration/{run_key}_trial2/`) to avoid clobbering the prior trial before
comparison — see Anti-Drift Hazards.

### Tolerance-guard pattern to reuse for "unstable" keys

`tests/unit/worldassembly/test_corpus_diversity.py::test_generated_frontier_3_42_extended_population_stability`
(lines 289-374) is the one existing precedent: drives the real (non-`audit_mode`) `Kernel` for 3
independent same-seed trials to 1000 ticks, hard-asserts the standard 60%-of-starting floor
per-trial through tick 800 (where the investigation found reproducibility held), then asserts a
relaxed **mean-across-trials** floor at ticks 900/1000 plus a hard no-full-extinction check, with
thresholds set below the worst pre-fix per-checkpoint observation. This is a population-checkpoint
guard, not a grade guard — this ticket's "unstable" conversions need an analogous pattern applied
to **per-pillar grade** stability instead (e.g., assert the pillar grade across N calibration trials
never falls outside the existing `GRADE_ORDER` ±1 band from the anchor, rather than asserting a
single-run point value). No existing test does this for grades; the Plan phase must design the
exact shape (e.g., a new `test_grade_stability_multi_trial` helper or an extension of
`test_grade_within_anchor_band_long_run` itself).

### `make evaluate-full` does not exercise `SLOW_ANCHOR_KEYS` — a gap in the ticket's own AC wording

`Makefile:295-296`: `evaluate-full` re-runs `tools/evaluate_simq.py` with no flags, and its own
Makefile comment says "Re-run engine for all **fast (≤500t)** scenarios." `SLOW_ANCHOR_KEYS` is
never touched by `evaluate-full`. The actual slow-tier regression command is `make
simq-full-audit-slow` (`Makefile:312-313`: `pytest tests/simulation_quality/test_grade_regression.py
-q`, i.e. no `-m "not slow"` filter, so it runs both fast and slow tests) or directly `pytest
tests/simulation_quality/test_grade_regression.py -m slow`. The ticket's AC item "`make
evaluate-full` (or the equivalent scoped regression sweep) reports 0 regressions" is only
satisfiable for this ticket's actual scope via the "equivalent scoped regression sweep" branch —
running bare `make evaluate-full` alone would give false confidence, since it silently never
touches any of the 18 keys under test here. Flagged for the Plan phase test-command selection.

## Mechanics / Engine Constraints

- `docs/engine/kernel.md` §"Emergency Throttling" (lines 66-70): "If a tick exceeds 2x its average
  duration or the hard cap in `RuntimeProfile`, the Kernel will: 1. Signal the Governor to
  transition to DEGRADED mode. 2. Drop remaining work items in the current resolution queue. 3. Log
  a warning." This is the documented, intentional mechanism this ticket measures the blast radius
  of — confirmed still present, unmodified, at `src/engine/kernel.py:420-442` (end-of-tick
  watchdog) and `src/engine/kernel.py:574-601` (mid-tick emergency throttle, `elapsed =
  (time.perf_counter_ns() - self._start_perf_ts) / 1e6` measured against real wall-clock, gated
  `not self._audit_mode`).
- `docs/engine/kernel.md` §"State Hashing in Phase 7" (lines 100-126): DEGRADED mode emits
  `TICK_END.hash = "SKIPPED"` (no canonical SHA-256 proof); only the lightweight MD5 fingerprint
  runs, and it excludes several state domains. This is why hash-based determinism checks cannot
  catch the F6 divergence — it is a DEGRADED-mode gap by design, not a bug.
- `docs/engine/performance_contract.md` §7 "Adaptive Phase Budget Governor" (lines 65-76): the
  broader `PhaseBudgetGovernor` mechanism the tick-budget watchdog belongs to — granular sub-phase
  budgets under system pressure, a corpus-wide, intentional performance-scaling contract.
- `docs/mechanics/05_world_evolution.md` "Hazard Impacts" governs the (unrelated, already-fixed)
  `moon_cave`/`arcane_circle` hazard-kind content bug documented in the F6-discovery investigation
  — not implicated in this ticket's own scope, cited only because the anchors this ticket re-verifies
  were captured post-fix.
- No mechanics-bible or engine-contract text is being changed by this ticket; `src/engine/kernel.py`
  is explicitly out of scope (ticket AC: "zero diff lines").

## Parity Ledger Overlap

- `docs/parity_ledger/world_dynamics.yaml::WORLD-029` (P0, `verified`) and `::WORLD-060` (P0,
  `verified`) — "Calamity aura and regional hazards apply local debuffs/drain" / "Regional hazards
  drain HP/Readiness based on intensity." Both entries' `test_path` already lists
  `test_generated_frontier_3_42_extended_population_stability` from the prior ticket. **No status
  change expected** from this ticket (measurement-only, per its own AC) — but if the Implement phase
  adds new multi-trial tolerance-guard tests to `test_corpus_diversity.py` for additional worlds
  (beyond `generated_frontier_3_42`), consider whether those entries' `test_path` lists should be
  extended for traceability, since they are the P0 entries governing the hazard-drain mechanism the
  throttle-driven population variance interacts with.
- `docs/parity_ledger/infrastructure.yaml::INFRA-258` (P1, `verified`) — the kernel tick-alignment
  fix documenting `GovernorModeChanged` firing naturally (63-73 occurrences) through real
  `Kernel.tick_once()` loops in `dungeon_crawl`/`sandbox_world` 2000t baselines. Directly adjacent
  context (confirms `DEGRADED`-mode transitions are expected, already-verified behavior in exactly
  the long-run scenarios this ticket re-verifies) but **not** expected to require a status change.
- No P0 parity entry governs test-determinism guarantees for `Kernel.tick_once()` under sustained
  load specifically (flagged as a pre-existing documentation gap by the F6-discovery investigation,
  not something this ticket should originate a fix for).
- Per the ticket's own AC: "No `docs/parity_ledger/` entry requires a status change, since no scored
  behavior changes as a result of this ticket." This investigation found no evidence to contradict
  that — confirmed no parity entry currently asserts single-run grade-anchor reliability as a
  claim this ticket would falsify.

## Prior Work

- `stored_artifacts/TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE/investigation.md`
  (read in full) — the source of F6 and the exact re-run methodology (Method section: same-seed,
  same-code, same-machine, back-to-back instrumented drives) and Root cause 1/2/3 analysis this
  ticket scales to grade-stability across all 18 keys. Its own Risk 1 explicitly anticipated this
  exact follow-up question ("whether other long-run calibration tiers... are silently exposed to
  the same run-to-run variance... out of this ticket's scope... flagged so a future audit does not
  have to rediscover the mechanism from scratch") and its Risk 4 gave the fork the Plan phase here
  must resolve: fix content only and accept a wider/averaged tolerance, vs. running under
  `audit_mode=True` (which structurally disables both throttle paths and would measure a materially
  different, unrealistically optimistic scenario — explicitly **not** a valid substitute for this
  ticket's purpose of measuring the throttled, real-world-representative anchor reliability).
- `stored_artifacts/TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS/investigation.md` — established most
  of the non-`generated_frontier_3_42`/non-`dungeon_crawl`/non-`urban_political`/non-`sandbox_world`
  `SLOW_ANCHOR_KEYS` entries (`unit_selfmodel_pilot`, `hero_guild_routing`, `simq_routing_test`,
  `unit_faction_tension`×2, `urban_political_seed42_2000t`). Confirms the same
  `data/calibration/{name}_seed{seed}_{ticks}t/quality_report.json` mechanism and that each anchor
  to date has been a **single** calibration run — consistent with this ticket's premise.
- `stored_artifacts/TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS/investigation.md` —
  established `generated_frontier_3_42_seed42_1000t`'s original anchor (this world's first-ever
  1000t data point), later re-verified unchanged post-hazard-fix by the F6-discovery ticket. Its own
  open question ("exact seed/tick grid for the long-run tier... left to the Plan phase") is the same
  class of judgment call this ticket's Plan phase inherits for the tolerance-guard conversion design.
- `docs/simulation_quality/eval_matrix_results.md` already documents extensive per-world,
  per-pillar grade tables and drift attributions for most of these 18 keys (content-driven drift,
  not throttle-driven) — this ticket adds a **new, distinct** reliability-status field ("was this
  grade re-verified stable across repeated runs of the same content/seed") that the existing
  document does not yet carry for any key.

## Risks and Open Questions

### Timing measurement and sweep feasibility (required by the ticket's own Assumptions section)

Ran one real, representative calibration invocation:
`python3 tools/calibrate_simq.py --ticks 1000 --seed 42 --name generated_frontier_3_42`
(44 entities — the anchor whose instability triggered the F6 discovery). Result:

- Engine tick-loop only (`elapsed` printed by the script, `_run_engine`'s
  `time.perf_counter()` delta around the `tick_once()` loop): **30.46s**
- Total wall-clock for the full invocation (`/usr/bin/time -v`, includes Python startup, world
  compile, JSONL event replay through `QualityHub`, report write): **33.22s**, 99% CPU, no swap,
  125MB peak RSS.
- Grade output matched the committed `grade_anchors.json` anchor **exactly** on all 10 pillars
  (COGNITION B, AGENCY C, COMBAT B, FACTION A, ECONOMY B, PROGRESSION B, SOCIAL C, INFORMATION B,
  WORLD B, NARRATIVE A) — i.e. this key's first informal re-run trial is already evidence toward
  "stable," though the ticket requires 2-3 formal trials before classifying.

**Extrapolation.** The 8 worlds in the corpus range from 16-18 entities (`sandbox_world`,
`unit_selfmodel_pilot`, `unit_faction_tension`) to 30-44 entities (`dungeon_crawl`,
`urban_political`, `hero_guild_routing`, `simq_routing_test`, `generated_frontier_3_42`). Using the
measured ~33s/1000t as representative of the 30-44-entity tier and scaling down proportionally
(~entity count, consistent with D06's own per-tick compute figures: 9-15ms/tick at 15-18 entities)
for the smaller worlds gives roughly ~15s/1000t for the small tier:

| Tier | Keys (count) | Approx. cost/run |
|---|---|---|
| Large (30-44 entities), 1000t | `dungeon_crawl`×3, `urban_political`×3, `hero_guild_routing`, `simq_routing_test`, `generated_frontier_3_42` (9 keys) | ~30s each → ~270s |
| Large, 2000t | `dungeon_crawl`×3, `urban_political`×1 (4 keys) | ~60s each → ~240s |
| Small (16-18 entities), 1000t | `sandbox_world`, `unit_selfmodel_pilot`, `unit_faction_tension` (3 keys) | ~15s each → ~45s |
| Small, 2000t | `sandbox_world`, `unit_faction_tension` (2 keys) | ~30s each → ~60s |

One full pass through all 18 keys ≈ **615s (~10.3 min)**. At 2 re-runs/key: **~1230s (~20.5 min)**.
At 3 re-runs/key: **~1845s (~30.75 min)**. Even applying a generous 2x safety margin for
system-load variance (the exact phenomenon under test) and per-run report-parsing/documentation
overhead, the full 18-key × 2-3-rerun sweep is **~25-60 minutes of wall-clock compute** —
comfortably feasible within a single implementation session. **No reduced/staged subset is
required on feasibility grounds.** This extrapolation is based on one measured data point
(`generated_frontier_3_42`, 44 entities) scaled by entity count for the other worlds, not a
per-world measurement — actual per-world costs may vary ±30-50% depending on event density (which
affects JSONL replay time, a smaller fraction of total cost than the tick loop itself, per the
measured 30.46s-engine vs. 33.22s-total split). The Plan phase should still budget real time for
report inspection and `eval_matrix_results.md` documentation on top of raw compute, and can lean
toward 3 re-runs (not 2) per key given the headroom this measurement reveals, for stronger
statistical confidence per key at negligible added cost.

### Design fork inherited from the F6-discovery investigation, not yet resolved

The prior investigation's Risk 1 (option (a) vs (b)) is directly inherited here at 18x the scale:
whether "stable" classification should be judged by re-running the real throttled `Kernel` (as
`test_generated_frontier_3_42_extended_population_stability` does) or would ever be tempted toward
`audit_mode=True` for a cleaner signal. This ticket's own Scope section already answers this
implicitly by requiring re-runs "via `tools/calibrate_simq.py`" (which always drives the real,
throttled `Kernel` — `_run_engine` at `tools/calibrate_simq.py:154-254` never sets `audit_mode`) —
flagged here only to confirm the Plan phase should not silently drift toward `audit_mode` as a
shortcut for any key, since that would measure a different, non-representative scenario.

### Whether any key's instability has a non-throttle root cause

Per the ticket's own Assumptions: if a re-run reveals grade instability NOT consistent with the F6
mechanism (e.g., genuine RNG/content non-determinism), that must be escalated as a separate,
more serious finding — not silently absorbed into a tolerance guard. This investigation found no
evidence of such a case in the single confirmatory run performed, but the full 2-3-trial sweep for
all 18 keys has not yet been executed (that is Implement-phase work, not Investigate-phase work per
this ticket's own scope) — this is an explicit open question the Plan phase should not assume
resolved.

### `grade_anchors.json` schema has no slot for tolerance ranges

Confirmed by direct inspection: every entry is `{PILLAR: single_grade_string}`. The ticket's own
Assumptions section already flags this as a "plan-revision trigger, not something to route around
silently" if the Implement step finds the schema can't cleanly represent a tolerance range — this
investigation confirms the schema constraint is real (no range/list-valued fields exist anywhere in
the fixture) but takes no position on resolution; that is squarely a Plan-phase decision. The
precedent (`test_generated_frontier_3_42_extended_population_stability`) does **not** modify
`grade_anchors.json` at all — it lives entirely as a separate multi-trial test in
`test_corpus_diversity.py` with its own hardcoded floors, which is consistent with the ticket's
stated expectation.

## Anti-Drift Hazards

- **Do not touch `src/engine/kernel.py`** — confirmed unmodified by this investigation; the ticket's
  own AC requires zero diff lines there. The watchdog (`kernel.py:420-442`) and mid-tick throttle
  (`kernel.py:574-601`) are the object under measurement, not a target for change.
- **Do not silently overwrite the canonical `data/calibration/{run_key}/quality_report.json` on the
  first of 2-3 trials and lose the ability to compare trials.** `tools/calibrate_simq.py --output`
  supports redirecting a given run to a distinct directory; the Implement phase should use distinct
  output paths per trial (e.g. `{run_key}_trial1`, `{run_key}_trial2`, `{run_key}_trial3`) and only
  the final canonical write should land at `data/calibration/{run_key}/quality_report.json` — or all
  trial outputs should be captured before any get overwritten, since `data/calibration/` is
  gitignored and per-trial data will not survive into the ticket's own commit regardless (only
  `grade_anchors.json` and `eval_matrix_results.md` are committed artifacts).
- **`data/calibration/` is gitignored — nothing written there persists across sessions or into the
  final commit.** The evidence this ticket's AC requires ("grades observed per trial, not just a
  conclusion") must be transcribed into `eval_matrix_results.md` at implementation time; do not
  assume the raw JSON reports themselves serve as the durable evidence trail.
- **Do not silently substitute `make evaluate-full` for the slow-tier sweep** — it only re-runs
  ≤500t fast anchors and will report "0 regressions" without ever touching any of the 18 keys this
  ticket is about. Use `pytest tests/simulation_quality/test_grade_regression.py -m slow` (or `make
  simq-full-audit-slow`, which runs the full file unfiltered) as the actual scoped verification.
- **Do not expand scope to fix the `moon_cave`/`bandit_road` hazard-kind content gaps** (Root causes
  1/2 in the F6-discovery investigation) — those are explicitly out of scope here (P2-O/P2-Q,
  separate backlog items) and already fixed for `moon_cave` specifically; re-touching that content
  is not this ticket's job even if a re-run surfaces it again.
- **Do not widen the ±1-letter `GRADE_ORDER` band tolerance itself** (`_within_band`,
  `test_grade_regression.py:140-148`) as a shortcut to make an unstable key look stable — the
  ticket's own Assumptions section is explicit that "stable" means re-runs never *require* widening
  that existing tolerance, not that the tolerance itself gets changed.
- **Do not add `generated_frontier_3_42` (or any other key's world) to any `test_corpus_diversity.py`
  world list that assumes a prior fix has landed** (e.g. `HAZARD_KIND_MATCH_WORLDS`,
  `POPULATION_STABILITY_WORLDS`) as a side effect of this ticket unless the underlying condition
  that list encodes is actually true — those lists are already correctly populated by prior tickets
  and are not this ticket's concern.

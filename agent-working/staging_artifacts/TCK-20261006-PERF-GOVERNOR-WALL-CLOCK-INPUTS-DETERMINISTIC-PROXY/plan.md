---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY
date: 2026-10-06
tags: [performance, determinism, engine, testing]
---

# Plan (design): TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY

Design only. Nothing here is implemented and no `src/` or `tests/` file was edited. Evidence is in `investigation.md`. The code waits
for the full no-touch window. perf-planner reviews this; the owner decides the questions in section 3.

## 1. The shape of the fix

Both governors keep their logic. What changes is where their cost inputs come from, chosen by a **signal contract**:

- **LIVE** (default; today's behaviour, bit for bit): cost inputs are measured milliseconds.
- **CANONICAL**: cost inputs are **modelled reference-milliseconds** computed from deterministic counts. No `perf_counter_ns`, no `psutil`,
  no thread timing is read to build them.

Mechanics, so that Live stays identical and old tests keep working:
- `PressureSignals` (`src/core/governance.py`) gains `tick_cost`, `tick_budget` and `phase_cost: Dict[str, float]`, all optional.
  A property returns `tick_cost` if set, else `tick_compute_ms` (and the budget falls back to `profile.max_tick_budget_ms`, phase cost to
  `phase_costs_ms`). Tests that build `PressureSignals(tick_compute_ms=...)` therefore need no edit.
- The governors compare `cost >= budget * ratio` in the same expression form they use now, so Live float behaviour does not move.
- A new module `src/engine/signal_source.py` owns signal construction: `LiveSignalSource` (today's code moved out of `kernel.py`) and
  `CanonicalSignalSource`. The kernel calls one of them from `_phase_init` and `_record_runtime_signals`.
- `ResourceGovernor._get_indicated_mode(profile, signals)` keeps its name and signature. Four tests override it (see section 5).

## 2. A proxy for each input

The unit is the **reference-millisecond**: the modelled cost, in ms, of a tick on the reference host class. Weights are constants in code,
versioned (`WORK_MODEL_V1`), and the version is recorded in the run manifest next to the contract. Changing a weight is a new version,
like a hash scheme. So the existing profile thresholds (`max_tick_budget_ms`, the 1.5 / 1.0 / 0.7 / 0.8 ratios, the 15 / 10 ms phase
floors, 0.5 / 0.3 phase fractions) keep their meaning and **no new threshold field is needed**: a Canonical run behaves as if on the
reference host. The cost is that Canonical models overload and does not measure it (a trade-off PERF-D1 already accepts).

| Input | Canonical proxy | Where counted | Why stable across sequential, thread and process executors |
|---|---|---|---|
| `tick_compute_ms` | `tick_cost = w_e*entities_active + w_m*movement_candidates + w_l*leads` (starting point from the probe: 1.10, 4.79, 7.80; to be re-fit, section 6 step 1) | in the kernel thread after `refine` and before `_phase_advancement` (`_current_update` is cleared at advancement), from `self._state`, the sorted `_final_results` and `refined_update.metric_counters` | counts are taken from canonically sorted results and from the single-threaded `refine`, never from workers. Worker-side values (peak active threads, chunk timing) are not used. The executor-parity tests (`tests/unit/kernel/test_executor_parity.py`, `test_worker_equivalence.py`) already assert the results are executor-independent, and a new test asserts the units are |
| `phase_costs_ms["locomotion"]` | `locomotion_cost = w_m2 * movement_candidates` (probe r = 0.93, R^2 = 0.79) | same place; counter `movement_candidates` already exists (`metric_counters`) | same |
| `phase_costs_ms["final_integrity"]` | **undecided**: no counter tried explains it (r <= 0.54). First implementation step measures dirty-set size inside `refine`. **Fallback:** if no counter reaches R^2 >= 0.6, Canonical drops rule 2 of `PhaseBudgetGovernor` (`phase_governor.py:127-135`) and the divergence is recorded | measure in `refine` | n/a until chosen |
| `worker_utilization`, `queue_utilization` | `queue = min(1, ceil(batch_items / 50) / max_queue_depth)`, `worker = 0` if `max_worker_count == 0` else `min(1, batch_items / (max_worker_count * 50))`; 50 is the existing thread chunk cap in `worker_manager.py` | batch size from `_current_work_items` | batch size is a property of the scheduled work, identical for every executor; no pool state is read |
| `memory_estimate_mb` | **not an input under Canonical** | n/a | RSS is a host property. PERF-D1's proxy list names work units, queue depth against a fixed ceiling and work debt, not memory. A modelled footprint would need a calibration this design cannot do |
| `replay_backlog_kb` | **not an input under Canonical** | n/a | replay is non-authoritative (architecture Law 2) and the backlog depends on a flush thread and the disk. Modelling a disk would be fiction. Recovery already ignores it (`governor.py:146-152`) |
| `work_debt_total` | removed by retire step 2; unchanged until then (always 0) | n/a | deterministic |
| warm-up cap (ticks <= 5, `kernel.py:545-546`) | not applied under Canonical | n/a | it exists to hide cold-start timing noise; modelled costs have none |

**Cost is demand, not work done (feedback loop).** Under Canonical the cost is computed from **pre-policy** counts: quantities that exist before
the mode's scan policy, cadence and budgets act. Examples: active entities, leads, and entities that have a movement objective, all read from
`AuthoritativeState`. It is **not** computed from post-policy counts such as `len(_final_results)` (cadence gating shrinks it) or the number
of movement candidates a throttled scan produced (`EXACT_DIRTY` shrinks it). Reason: if cost were work done, DEGRADED would lower its own cost
input, the lowered cost would trigger recovery, recovery would restore the work and raise cost again, and the mode would thrash
(deterministically, but still). With demand-based cost the mode does not feed back into its own input; state evolution still can, which is
ordinary dynamics. **Recommendation: pre-policy demand.** Consequence for the probe: it ran in `NORMAL` throughout, where movement candidates
equal the full-scan demand, so its correlations still hold; step 1 must re-fit with the state-derived "entities with a movement objective"
in place of the post-policy counter, and `locomotion_cost` uses that variable.

Hysteresis, dwell, confidence window and the rolling average (`RuntimeStatus.record_signals`) stay as they are; the average is taken over
`tick_cost`. They are deterministic given deterministic inputs.

**PERF-D6 link.** The keys the governor reads, `"locomotion"` and `"final_integrity"` (`phase_governor.py:112,127`), are **cost buckets** inside
`AuthoritativeApplyPipeline.refine` (`pipeline.py:300`, `:466`): groups of several `run_phase()` calls (`locomotion` is `action_routing`,
`position_swaps` and `movement_routing`). They are not catalog phase names, so the phase catalog PERF-D6 describes (one typed entry per
`run_phase()` call) does not yet say which bucket a phase belongs to. Recommendation: when the catalog lands, each entry carries a `cost_bucket`,
and the work-unit definition for a bucket is declared once, on the catalog, next to the bucket, not scattered in the kernel; `phase_cost` is
keyed by bucket name, and `PhaseBudgetGovernor` takes its two bucket names from the catalog instead of string literals. Until the catalog
exists, the bucket names stay literals and `work_units.py` holds the two definitions. Nothing here blocks on the catalog.

What Canonical cannot protect: a Canonical run has no memory or replay-backlog guard. A host out of RAM is a Live concern (section 4).

## 3. OWNER QUESTION: how is the contract chosen, and what happens to `audit_mode`?

Today `audit_mode` zeroes every pressure input (`kernel.py:530-541`), so deterministic runs never degrade (investigation section 2).
PERF-D1 asks for a Canonical contract where pressure is a deterministic proxy. The question is what a run uses by default and what
`audit_mode` becomes.

**Option 1: add a contract, leave `audit_mode` alone (recommended).** `RuntimeProfile` gains `signal_contract: LIVE | CANONICAL`
(default `LIVE`; part of the configuration and of the manifest). `audit_mode` keeps both of its meanings (extra consistency checks and
pressure off) and wins when set. CANONICAL is used by tests and scenarios that need deterministic degradation: the hash-equality test #379
removed, SimQ overload calibration, and deterministic coverage of degraded-mode gameplay.
- Cost: low. No existing run changes. Two deterministic paths coexist (zeroed and modelled).
- Gain: deterministic degradation becomes testable, nothing else moves, and certification and the pinned hash baselines are untouched.
- Open point: the live server stays on LIVE, so a normal non-audit server run is still host-dependent until the Live half ships.

**Option 2: Canonical replaces the zeroing under `audit_mode`.** `audit_mode` keeps its checks and takes modelled signals instead of zeros.
All four harnesses and 25 test files then run the governors.
- Cost: medium to high. Any audit run whose modelled load crosses a threshold now changes mode, and so changes its hashes. The pinned
  baselines (`tests/regression/baseline_5k.json` and others) may move and need review. Calibration becomes urgent.
- Gain: one deterministic path, and certification covers degradation.

**Option 3: Canonical is the default for every run; Live is an explicit opt-in.** `audit_mode` becomes checks only.
- Cost: highest. Every non-audit run changes behaviour, and the live server loses real-load protection (no memory or backlog guard, no
  response to a slow host) until the Live half with a control trace exists. That contradicts PERF-D1's reason for keeping Live.
- Gain: every run is reproducible by default.

**Recommendation: Option 1 now.** It delivers the proof the ticket asks for with no blast radius. Revisit Option 2 once the calibration
data from Option 1 exists and the owner has seen which pinned baselines would move. Do Option 3 only after the Live trace is built.

Two smaller questions for the owner:
- **Q-A. Memory and replay backlog excluded under Canonical (section 2).** Agree? Recommended: yes, as PERF-D1's own proxy list implies.
- **Q-B. Canonical thresholds keep their millisecond meaning, as "reference host" milliseconds, instead of new work-unit fields.**
  Agree? Recommended: yes; it avoids new profile fields and keeps every existing profile valid. The reference host class and the weights'
  provenance are recorded in the manifest.

**Owner decision 2026-10-06:** Option 1 (`signal_contract` on `RuntimeProfile`, default `LIVE`, `audit_mode` unchanged); Q-A yes (memory and
replay backlog are not inputs under Canonical); Q-B yes (thresholds keep their millisecond meaning, as reference-host milliseconds); the Live half
is `TCK-20261006-PERF-LIVE-CONTROL-TRACE`. Recorded by perf-planner in `performance_optimization_decisions.md` (PERF-D1, "Update 2026-10-06").

Precedence under Option 1: `audit_mode` set -> zeroed signals (today). Else `signal_contract == CANONICAL` -> modelled. Else live.
A kernel flag may not override the profile's contract, so a run's contract is always readable from its profile.

## 4. The Live half: a follow-up ticket, not this one

A separate ticket, `TCK-20261006-PERF-LIVE-CONTROL-TRACE` (filed by perf-planner, owner-approved 2026-10-06). Reasons:
- Different deliverable: a versioned, bounded control-trace format (mode transitions with tick, from, to; the emitted phase budgets;
  the kernel's report-only overrun records), a writer in `ReplayManager`, and a Canonical-mode replay that consumes the trace and
  reproduces the hashes (PERF-D1 "Verification": a trace-replay test).
- Different risk: schema, storage and replay-format versioning; it touches `replay_manager.py`, the manifest and the replay reader.
- Independent: the proxies do not need it, and it does not need the proxies. Its prerequisite is only this ticket's `signal_contract` field.
- It owns what the Canonical path deliberately drops: a memory and backlog guard that is allowed because its decisions are recorded.
Until it exists, a LIVE run keeps the `verification_level = REDUCED` label (INFRA-363) when it leaves `NORMAL`.

## 5. What happens to tests that drive a mode through time or a seam

(Assumes Option 1; the default stays LIVE, so none of the seams changes.)
- `test_milestone_b_closure` (tick-keyed fake clock): unchanged. It is the Live regression test. Add a Canonical twin that drives the
  mode by injecting counts, not time.
- `test_camp_raid_targeting` (`_DegradedGovernor`), `test_tick_budget_report_only` (`_NormalOnlyGovernor`), `test_catalog_entity_spawn_wiring`
  (`_PinnedNormalGovernor`): unchanged, as long as `_get_indicated_mode(profile, signals)` keeps its name and signature. That is a design constraint.
- `test_work_debt_stays_empty_in_production`: unchanged by this ticket (Live, real time). Retire step 2 changes it for its own reasons.
- Tests constructing `PressureSignals(tick_compute_ms=...)` (resource governor contract, anti-thrashing, phase-budget governor, signal truth,
  governance isolation): unchanged, by the optional-fields design in section 1.
- `test_resilience_recovery` (patches `ResourceGovernor.evaluate`): unchanged.
- `test_long_run_stability` and `test_cert_long_run_stability` (CI skips): with a Canonical profile they could run reliably; re-evaluating the
  skips stays with `test-architecture-reviewer` (AC 9 of #379).
- If a later step ever makes CANONICAL the default for tests (Option 2), `tests/integration/campaigns/test_catalog_entity_spawn_wiring.py` (#367) must set
  `signal_contract=LIVE` explicitly: its pinned `NORMAL` stream needs K > 0 perceived hostiles. The same applies to any other governor-pinned test that
  relies on the default.
- New tests are listed in `test_plan.md`.

## 6. Order of the eventual work and size of the change

Steps (each is a commit):
1. **Calibration, no behaviour change.** Re-run the probe on a real matrix (idle, movement, resource, strategic, combat; 3 sizes; thread and
   process executors; two hosts), read the dirty-set size inside `refine`, fit and freeze `WORK_MODEL_V1`, and decide the `final_integrity`
   fallback. Output: a stored artifact with the fit and its error per family. Acceptance: pooled R^2 >= 0.85 and per-family actual-to-predicted
   within 0.5 to 2.0 (the probe got 0.87 and 0.48 to 1.30), or the model is revised.
   **Preconditions (rpg-planner review of PR #384, accepted):**
   - Both performance defects in the RPG-core bench are merged first: `TCK-20261006-COOPERATION-PENDING-OFFER-SCAN-IS-QUADRATIC-PER-TICK`
     (the quadratic found by #172, about 11 s per tick at 5,000 entities) and `TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP`
     (about 3.3 s per tick). Fallback if they are not merged: exclude the `cooperation` and `combat_engagement` cost buckets from the fit and say so
     in the stored artifact.
   - The calibration artifact records the RPG-core base commit it was measured on.
   - Re-fit, or at least re-check the error band, after the salience fix, Lane B's spawn-faction batch and symmetric attack legality
     (CONFLICT-03) land, because they change population and movement demand.
2. `signal_source.py`, `work_units.py`, `PressureSignals` optional fields, `RuntimeProfile.signal_contract`; Live source is a code move. This step touches `src/engine/pipeline.py` only if step 1 found a `final_integrity` counter that has to be produced inside `refine`. `pipeline.py` is one of the four core files, so it is inside the full no-touch window anyway; the other files in this table are lifted or in the same window.
   Step 2 rebases on the salience fix: it edits the same kernel signal-building region (`_phase_init`, about lines 530-560), and salience goes first by
   agreement. Re-measure `kernel.py` headroom after the salience fix lands, and do not work on the two in parallel.
3. Canonical source and the governor reading `tick_cost`; the proof tests (`test_plan.md`).
4. Docs, parity ledger, divergence entry, `wall_clock_inventory` regeneration.

Estimated size (lines; kernel.py is the constraint: 1,396 lines against a module-length ceiling of 1,419, so 23 lines of headroom):

| File | Today | Change | Net |
|---|---|---|---|
| `src/engine/kernel.py` | 1,396 | the two signal-building blocks (`_phase_init` 530-560, `_record_runtime_signals` 788-803, about 45 lines) become two calls, plus 4 lines to take the units after `refine` | about -35 to -20 |
| `src/engine/signal_source.py` (new) | - | Live source (moved code) and Canonical source | +170 |
| `src/engine/work_units.py` (new) | - | weights table, version constant, unit functions; imports neither `time` nor `psutil` | +110 |
| `src/engine/governor.py` | 155 | read `tick_cost` / `tick_budget` | +/- 15 |
| `src/engine/phase_governor.py` | 150 | read `phase_cost`, drop the warm-up and absolute floors rule under Canonical only if the calibration says so | +/- 20 |
| `src/core/governance.py` | 70 | three optional fields and the fallback property | +10 |
| `src/engine/runtime_status.py` | 106 | rolling average over `tick_cost` | +4 |
| `src/config/profiles.py` | 173 | `signal_contract`, enum | +14 |
| `src/engine/pipeline.py` | (gated file) | a unit counter for the `final_integrity` bucket, only if step 1 finds one | +0 to +10 |
| manifest writer (find in step 2) | - | record contract and `WORK_MODEL_V1` | +6 |
| tests | - | new files about +350; edits to at most 2 existing tests | +350 |

Code-health risk: kernel.py shrinks, so its ratchet improves; the new modules are small and single-purpose. The one watch point is
`phase_governor.evaluate` cognitive complexity if both contracts share it; keep the contract difference in the signal source, not in
the governor's branches.

## 7. Risks and what this design does not decide
- **Feedback and thrash.** Even with demand-based cost (section 2), the mode changes scan policy and budgets, which change how state evolves, which changes demand. A scenario near a threshold could oscillate. The dwell time, confidence window and recovery watermark bound it, and `test_plan.md` section 9 tests the bound; if a scenario still thrashes, the fix is in the thresholds or the watermark, not in the proxy.
- The probe's per-family error (up to a factor of 2.7) may partly come from the quadratic cooperation defect, which grows faster than entity count; the
  re-fit in step 1 happens after that defect is fixed, so the real error band may be smaller.
- The reference-millisecond model is an approximation (per-family error up to a factor of 2.7 in the probe). It models overload; it does not measure it.
- `final_integrity` may have no good proxy; the fallback is an owner-visible divergence.
- Option 1 leaves the live server reproducible only under `audit_mode`. The Live half closes that.
- Section 6 step 1 needs more than this VM: the 60 to 4,260 ms ticks seen here are a host property.
- Gate: no `src/` edit until the full no-touch window opens or a new partial lift names `kernel.py` (AC 2); this ticket stays INPROGRESS.

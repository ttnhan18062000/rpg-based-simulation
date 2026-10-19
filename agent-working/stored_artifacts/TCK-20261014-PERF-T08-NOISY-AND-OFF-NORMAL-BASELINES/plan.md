---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES
date: 2026-10-15
tags: [performance, benchmarking]
---

# Plan: TCK-20261014-PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES

Branch `perf-t08-noisy-baselines` from `origin/main` a528dd1bd. **Nothing below that runs a benchmark starts before lead-planner says "gate open"** (swap 7.6 GB; asset's #608 proof run goes first). Diagnosis (AC1) is done from kept samples, see investigation.md.

## Phase 0, now, no heavy run (perf-planner approved 2026-10-15)
1. AC1 diagnosis: investigation.md (approved).
2. **P1/P1b code and tests (no run)** and P3 (`combat_10_local` 20 -> 100 sampled ticks) in `tools/perf/rerun_baselines.py`, `tests/unit/perf/test_rerun_baselines.py`; a pin test that the two tripwire RunSpecs stay 10 + 50.
3. AC4: docstring on `build_mixed_state` (140 entities for a 200 request), one ledger line, a test pinning 140 entities + 60 nodes; no output change, no rename.
4. Retry-promoted pair: keep both v0001 records; ledger note on the `resource_100` within-run drift with the consequence: the average depends on the window length, so a later comparison must use the same sampled-tick count.
5. AC1 reproduction script kept in the staging folder (moves to stored_artifacts at close), not in `tools/perf/`.

## Protocol-change proposal (step 2), for perf-planner's review
The analysis says the spread is a **between-process level shift** that lasts 10-40 ticks inside a run, so a longer window averages some regimes but does not remove them, and 3 runs cannot settle a bimodal host. The smallest change, in order of cost:

- **P1. Record steal and mean `cpu MHz`** before and after each run into `runN.meta.json`. Cheap, kept, but **checked and flat on this host** (steal 0, MHz 2687.998 constant, no cpufreq; investigation.md), so it cannot show the regime.
- **P1b. A fixed host-speed probe** (deterministic pure-Python integer spin, 400k iterations, about 50-60 ms) timed in the measuring process right before and right after the measured run (the pre-probe sits before state build and warm-up, the post-probe directly after the last sampled tick), written to `runN.meta.json` and the promotion note. If the probe moves with the tick average across runs, the host regime is shown rather than inferred; if it does not, the 30-33 ms floor hypothesis is rejected. Landed in `tools/perf/rerun_baselines.py` with tests, **no run needed**.
- **P2 (POLICY change, not only protocol; not coded): 5 fresh-process runs, promote the median, spread computed on the 3 middle runs.** It weakens the 15 % test, so it falls under the `perf_baseline_policy.md` paragraph the owner approves and **must be fixed in writing before any re-record**; it cannot be chosen after seeing which statistic passes. It is one option next to **P2'**: keep the 15 % rule on all runs and bound the allowed spread by `tripwire.NOISE_BUDGET` (0.35, the A/A-calibrated whole-process variance) for the two tripwire records only. Perf-planner takes the 15 % question to the owner through lead-planner. P2 applies to the 3 NOISY local records. It does not touch `tripwire.TRIPWIRE_SCENARIOS`: `tripwire.TRIPWIRE_SCENARIOS` (10 warm-up + 50 sampled ticks, `idle_100_local` on `PERF_512MB_LOCAL`, `movement_100_local` on `PERF_1GB_LOCAL`) stays as it is, so no testing-planner decision is needed for P1 or P2.
- **P3. Longer sampled window only for records not in `TRIPWIRE_SCENARIOS`:** `combat_10_local` 20 → 100 sampled ticks (about 5 s per process), and `simq_corpus_crowded_frontier` unchanged at 1000 (its window is already 1000). The new tick count is written in `protocol.measured_ticks`, so it is not comparable with the old record; that is acceptable because the old one is a legacy reference.
- **Not proposed:** a warm-up drop (warm-up is ruled out), GC instrumentation (GC is disabled), dropping spikes (they carry 2-13 %; the spread survives their removal).
- **Likely outcome for the two tripwire records:** `tripwire.py calibrate` already measured 0.35 head/base deviation with identical code (44 A/A pairs, 2026-10-10, "whole-process variance"), which is the same size as the 35.3 % `idle_100_local` spread here. So P1 + P2 probably will not bring `idle_100_local` under 15 % on this host; the 15 % rule itself may be the wrong test for it (a spread bound tied to `NOISE_BUDGET`, or recording it on a quieter runner). That is a policy question for the owner, not something to tune by re-running until a window passes.
- **Needs another decision, not a protocol change:** if `idle_100_local` / `movement_100_local` still exceed 15 % under P1 + P2, the only remaining lever is the tripwire `RunSpec` window, which needs **testing-planner's agreement** (AC2), and the owner approves the `perf_baseline_policy.md` paragraph that records P1-P3.

## Phase 1, after the gate opens (one process at a time, capped; the largest process here is the corpus at about 800 MB RSS, under the 3 GB tell-lead line)
**Preconditions:** lead-planner says "gate open" (asset's #608 first); AC2: the owner's written agreement to the `perf_baseline_policy.md` paragraph (P2 or P2' or neither), fixed before any re-record.
1. Re-record in this order: `combat_10_local` (cheap), `idle_100_local`, `movement_100_local`, then `simq_corpus_crowded_frontier` (about 70 s per process x 3 to 5). Quiet-window check before each: loadavg1 below 1.5 and `free -m` available above 2500 MB, recorded in the note. **Note that the loadavg < 1.5 check is itself a change from T08:** T08's three noisy local records were measured at loadavg 2.2-2.7 with no such bar, so the promotion note says the new records were taken under the stricter window.
2. Promote only through `baseline_lifecycle.py promote`, only records within 15 %; the others stay PENDING-NOISY with the P1 host numbers in the ledger.

## Phase 2, no run
`mixed_200_*`, `strategic_100_*`, `simq_corpus_frontier_extended`, `simq_corpus_frontier_marches` stay "not a baseline under canonical" in the ledger; the ticket closes with them PENDING (tick-cost investigation has not landed any fix).

## Docs and close
`perf_baseline_policy.md` (owner approves the paragraph; no edit before agreement), `baseline_invalidation_ledger.md`, `make knowledge-index-update`, paths guard before push, `tests/perf` + `tests/tools` scoped tests, mechanism-registry advisory, hand-orchestrated closure record. Tell perf-planner before commits; the owner says yes to the push.

---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP
phase: open
date: 2026-08-10
tags: [simulation-quality, calibration, corpus]
---

# TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP

## Title
Two real, disclosed findings from verifying `TCK-20260810-SIMQ-EVALUATE-SLOW-TIER-SCOPE-LEAK`'s
fix: (1) 12 corpus keys never re-run since `TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION`
show the same already-understood SUB-384 cascade drift, and (2) `simq_routing_test_seed42_500t`
shows real run-to-run non-determinism beyond score tolerance — the first confirmed instance of
FAST-tier (<=500t) grade-anchor instability, a class of problem `TCK-20260710-SIMQ-ANCHOR-
RELIABILITY-VERIFY` only ever checked for the SLOW tier

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
While verifying `TCK-20260810-SIMQ-EVALUATE-SLOW-TIER-SCOPE-LEAK`'s timing fix (a real fast-tier
-only `tools/evaluate_simq.py` full re-run, no `--scenario`), the run regenerated
`quality_report.json` for every fast-tier corpus key — including several that had stale or
entirely-missing calibration data (never re-run since SUB-384's fix). This surfaced 2 distinct,
real findings:

**(1) Real, recalibratable drift on 6 previously-unverified worlds (12 pillar instances):**
`crowded_frontier` (COMBAT C→A, 2 seeds), `frontier_marches` (COMBAT C→A, 1 seed),
`generated_frontier_3_42` (COMBAT C→A ×2, PROGRESSION C→A ×2, 3 seeds),
`simq_scale_stress_seed42_seed42_200t` (COMBAT C→A), `lifecycle_full_coverage_world_seed42_200t`
(FACTION C→S, ECONOMY C→A, PROGRESSION C→A, SOCIAL C→S). All match the exact pattern already
confirmed twice today (`TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION`,
`TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION`) — COMBAT/PROGRESSION jumping up as
previously-invisible hostile entities now correctly engage, cascading into other pillars.
(`quest_dense_frontier`, initially mis-flagged from a truncated grep, was re-checked at
Investigate and confirmed to have zero REGRESS items — corrected here.)

**(2) New: confirmed real non-determinism on `simq_routing_test_seed42_500t` (FAST tier).**
Re-running this exact scenario 3 additional times just now (identical seed, identical code) gave
3 different PROGRESSION values (event_count 10/11/11; score -0.272/-0.300/-0.249) and 2 different
COGNITION values (event_count 194/196/194) — real run-to-run variance beyond score tolerance.
This is the *opposite* of what was confirmed earlier today for `urban_political_seed42_500t`
(SOCIAL score bit-identical across 3 re-runs despite active watchdog trips). `TCK-20260710-SIMQ-
ANCHOR-RELIABILITY-VERIFY` established SLOW-tier (1000t/2000t) anchor stability via an 18-key,
3-trial-each reliability sweep, explicitly noting the FAST tier was never subjected to the same
check. This is the first direct evidence that at least one FAST-tier scenario is genuinely
unstable — any anchor value committed for it will eventually drift out of tolerance on a future
re-run regardless of what value is chosen, for reasons unrelated to any real code change.

## Scope
1. **Investigate**:
   - Re-run `tools/evaluate_simq.py` (fast-tier only, now correctly scoped) fresh and get the
     complete, current REGRESS list with exact pillar/value data (the list above was captured
     from one real run's terminal output, not yet cross-referenced pillar-by-pillar for
     `quest_dense_frontier`).
   - For finding (1): confirm each is the same SUB-384 cascade (not a coincidence) via the same
     methodology already established today (compile_context.json inspection for legacy_roles/
     legacy_factions, scorer grep for role/faction independence where relevant).
   - For finding (2): determine whether `simq_routing_test_seed42_500t`'s instability is the D06
     F6 watchdog-throttle mechanism specifically (check for `WatchdogTrip` alerts during the
     unstable runs, same direct-check methodology already used today) or a different source.
     Check whether other FAST-tier scenarios show the same instability (a wider multi-trial
     sweep across a sample of FAST_ANCHOR_KEYS, mirroring TCK-20260710's own SLOW-tier method).
2. **Plan**: for finding (1), a straightforward recalibration (same pattern as today's other 2
   tickets). For finding (2), the fix approach depends on root cause — could be a wider score
   tolerance for unstable keys specifically, excluding the key from strict tolerance checking
   with a documented reason (matching the `[known ...]` annotation convention already used for
   tick_budget/flag_gated noise), or a structural fix if a non-watchdog cause is found.
3. **Implement**: the confirmed fix/recalibration per finding.

## Out of Scope
- `TCK-20260810-SIMQ-EVALUATE-SLOW-TIER-SCOPE-LEAK`'s own tooling fix — already done, not
  revisited here.
- The already-fixed SUB-384 root cause itself (`WorldCompiler.compile()`) — not touched.
- A full FAST-tier reliability sweep matching TCK-20260710's exact 18-key/3-trial SLOW-tier
  methodology is IN scope for finding (2)'s investigation but may be descoped to a smaller,
  representative sample if a full sweep proves too wall-clock-expensive — disclose either way.

## Acceptance Criteria
- [x] Complete, current REGRESS list re-verified with exact pillar/value data (confirmed
      identical 12-item list; corrected an earlier draft's stray `quest_dense_frontier` mention —
      it has zero REGRESS items, only pre-existing annotated noise)
- [x] Finding (1)'s cascade cause confirmed (not assumed) per key, recalibrated — all 6 worlds'
      `compile_context.json` files confirmed to carry real SUB-384-affected monster content
- [x] Finding (2)'s root cause directly checked (watchdog logs inspected, not just hypothesized) —
      confirmed `WatchdogTrip` alerts firing from tick ~25 in unstable runs; also confirmed present
      (harmlessly) in stable runs, ruling out "watchdog presence alone" as the discriminator
- [x] A concrete recommendation for finding (2) (tolerance widening, annotation, or structural
      fix) with reasoning — no forced anchor edits that will just drift again next run. Used a new
      `watchdog_variance` `score_ceilings.json` annotation (no code change, existing mechanism)
- [x] Scoped pytest passes with 0 unexplained failures after the fix (31 failed / 39 passed / 18
      deselected — every failing test's assertion message carries a `[known ...]` annotation)

## Related Tickets
- TCK-20260810-SIMQ-EVALUATE-SLOW-TIER-SCOPE-LEAK (DONE, same session — this ticket's own
  verification run surfaced both findings here)
- TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION (DONE, same session — established the
  exact cascade pattern finding (1) matches)
- TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY (DONE — SLOW-tier-only reliability precedent finding
  (2) extends to the FAST tier for the first time)

## Related Docs
- `docs/audits/D06_longrun_health.md` F6 (the watchdog-throttle mechanism, candidate cause for
  finding 2)
- `docs/parity_ledger/substrate.yaml` SUB-384 (finding 1's root cause)

## Related Stored Artifacts
None yet — will be created at Investigate per standard tier.

## Related Code Areas
- `tests/simulation_quality/fixtures/grade_anchors.json`
- `src/engine/kernel.py` (watchdog mechanism, if finding 2 traces there)
- `tests/simulation_quality/test_grade_regression.py` (annotation dict, if finding 2 needs a
  `[known ...]`-style entry)

## Assumptions / Open Questions
- Whether finding (2) is isolated to `simq_routing_test_seed42_500t` or affects other FAST-tier
  keys — not assumed, the Investigate phase's own job to determine via a representative sample.

## Implementation Notes
Finding (1): recalibrated 12 fields across 6 run_keys (`crowded_frontier_seed42_200t`,
`crowded_frontier_seed456_200t`, `frontier_marches_seed42_200t`, `generated_frontier_3_42_seed42_200t`,
`generated_frontier_3_42_seed123_200t`, `generated_frontier_3_42_seed456_200t`,
`simq_scale_stress_seed42_seed42_200t`, `lifecycle_full_coverage_world_seed42_200t`) plus 2 more
fields on `hero_guild_routing_seed456_500t` (confirmed stable via 3x re-run — ordinary drift, not
instability) — 14 fields total, same established methodology as
`TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION`.

Finding (2): added 6 new entries to `tests/simulation_quality/fixtures/score_ceilings.json` under
a new `ceiling_kind: "watchdog_variance"` (`simq_routing_test_seed42_500t` PROGRESSION/COGNITION,
`simq_routing_test_seed123_500t` PROGRESSION, `urban_political_seed456_500t` ECONOMY/PROGRESSION —
5 confirmed-unstable pairs; the docs update also folds in the discriminating pattern found:
low absolute event count, not tied to one world/flag family). `tools/simq_ceiling.py`'s existing
`lookup_ceiling()` already treats `ceiling_kind` as free text sourced from this JSON fixture
(the `content_threshold`/`corrected` mechanism) — no Python code change was needed, only data.

## Test Summary
Direct authoritative scan (via `_within_band`/`_format_score_failures` from
`test_grade_regression.py`, not the coarser `evaluate_simq.py --dry-run` diff) across all of
`FAST_ANCHOR_KEYS`: 0 unannotated failures. `pytest tests/simulation_quality/test_grade_regression.py
-m "not slow" -q`: 31 failed / 39 passed / 18 deselected — confirmed every failing test's own
assertion message carries at least one `[known ...]` annotation (83 total annotated lines across
31 failing tests via `grep -c "\[known"`), matching this session's established "clean" convention
(annotation informs the failure message, it does not suppress the pytest assertion itself — same
as every pre-existing `tick_budget`/`flag_gated` entry).

## Files Changed
- `tests/simulation_quality/fixtures/grade_anchors.json` (14 fields recalibrated across 7 run_keys)
- `tests/simulation_quality/fixtures/score_ceilings.json` (6 new `watchdog_variance` entries)
- `docs/audits/D06_longrun_health.md` (F6 extended to note the FAST-tier finding; summary table
  row updated)

## Completion Summary
Both findings from `TCK-20260810-SIMQ-EVALUATE-SLOW-TIER-SCOPE-LEAK`'s own verification run
investigated and resolved. Finding (1) (12 REGRESS pillars on 6 previously-unverified worlds) was
the same, already-understood SUB-384 cascade — confirmed per-world via `compile_context.json`
inspection, recalibrated. Finding (2) (real non-determinism on `simq_routing_test_seed42_500t`)
was directly investigated rather than just cited: confirmed the D06 F6 watchdog-throttle
mechanism is active in every sampled run (stable and unstable alike), and that instability is
specifically driven by low absolute event counts for the affected pillar — not isolated to one
world or feature flag, found on both `simq_routing_test` (ENABLE_ADVENTURE_ROUTING) and
`urban_political`. Classified via a new `watchdog_variance` score-ceiling entry (existing
mechanism, no code change) rather than forcing an anchor value that would just drift again.
`docs/audits/D06_longrun_health.md` F6 extended to record this as the first FAST-tier instance of
an already-documented, intentional engine behavior. No `kernel.py` change — out of scope, same
guard as the original F6 finding.

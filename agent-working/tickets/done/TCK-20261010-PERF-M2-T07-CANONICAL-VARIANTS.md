---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261010-PERF-M2-T07-CANONICAL-VARIANTS
phase: done
date: 2026-10-10
tags: [performance, determinism, benchmarking]
---

# TCK-20261010-PERF-M2-T07-CANONICAL-VARIANTS

## Title
PERF-M2-T07: Canonical variants of the PERF_* profiles

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Give each PERF_* profile in src/perf/profiles.py a canonical variant with signal_contract = CANONICAL. baseline_invalidation_ledger.md §5 lists this as a prerequisite: every timing baseline must be captured under CANONICAL, and until a canonical variant exists a rerun is LIVE and must pass the all-NORMAL check. Default profiles stay unchanged. This lands after T02b, or is merged with it, because both touch the same file.

Source concern IDs: C2.

## Scope
- Add a canonical variant for each of the 8 original PERF_PROFILES entries in src/perf/profiles.py, built with model_copy(update={'signal_contract': SignalContract.CANONICAL}) because RuntimeProfile is frozen
- Put the variants in a separate map (e.g. PERF_CANONICAL_PROFILES) or behind a helper, so existing consumers that iterate PERF_PROFILES/PERF_MATRIX see no change
- Decide and document whether variant names carry a _CANONICAL suffix
- Add tests under tests/unit/perf/ covering the variants, the unchanged defaults and signal_source_for() routing

## Out of Scope
- Changing the RuntimeProfile.signal_contract default (stays LIVE, src/config/profiles.py)
- Recording contract.determinism in benchmark identities (PERF-M2-T02b/T08)
- Rerunning any baseline (PERF-M2-T08)
- Removing the hard-coded CLASS_A (PERF-M2-T02b)
- Any edit outside src/perf/profiles.py and tests/unit/perf/

## Acceptance Criteria
- [x] For every key K among the original 8 PERF_PROFILES entries (PERF_512MB_LOCAL ... PERF_4GB_CONC), a canonical variant exists and its .signal_contract is SignalContract.CANONICAL
- [x] Each canonical variant's model_dump() differs from its default counterpart only in signal_contract (and name, if renamed). ram, workers, tick budget, cadence and hardware_class are equal.
- [x] Every original PERF_PROFILES[K].signal_contract is still SignalContract.LIVE, and PERF_MATRIX maps only to the original LIVE profile names
- [x] signal_source_for(canonical_variant) in src/engine/signal_source.py returns the CanonicalSignalSource instance, and signal_source_for(default_profile) returns the live source
- [x] tests/unit/engine/test_signal_contract_foundation.py::test_signal_contract_defaults_to_live and tests/perf/test_profiler_integrity.py still pass

## Related Tickets
- TCK-20261006-PERF-LIVE-CONTROL-TRACE
- TCK-20261009-EPIC-SESSION-LEAD-PLANNER
- TCK-20260513-PERF-PROFILES-TUNING

## Related Docs
- docs/performance/baseline_invalidation_ledger.md
- docs/architecture/performance_optimization_decisions.md
- docs/plans/design_enhancement/performance_optimization/performance_m2_performance_contract_epic.md
- docs/performance/benchmark_identity_schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/perf/profiles.py
- src/config/profiles.py
- src/engine/signal_source.py
- src/engine/kernel.py
- tools/bench_corpus_world.py
- tools/perf/run_perf_baseline.py
- tools/perf/run_benchmarks.py
- tools/release/verify_production_profiles.py

## Assumptions / Open Questions
- Lift boundary (roadmap RPG-core gate item 8, owner 2026-10-09): `src/` edits are limited to `src/perf/bench_harness.py`, `src/perf/profiles.py`, `src/perf/long_run_harness.py`, new `src/perf/benchmark_record.py`, `src/observability/reporting/baseline_comparator.py` and `sweep_report.py`. Any other `src/` path listed under Related Code Areas is read-only here; editing it needs a new owner lift.
- Depends on PERF-M2-T02b landing first (same file, make_perf_profile CLASS_A removal), or is merged with it
- The OD-8 owner lift for src/perf/profiles.py is confirmed before implementing
- If variants keep the LIVE profile name, baseline files that record only the profile name cannot tell the contract apart. The identity's contract.determinism field (T02b/T08) is relied on, or a suffix is used.
- WORK_MODEL_V1 excludes combat_engagement, so combat-heavy canonical runs produce V1-labelled results (a T08 concern)

## Implementation Notes
- Landed in the same batch as T02b, after it, in `src/perf/profiles.py`: `CANONICAL_SUFFIX`, `canonical_variant(profile)` (a `model_copy` changing only `name` and `signal_contract`) and `PERF_CANONICAL_PROFILES`, keyed by the original name.
- **Naming decision (the ticket asks for it to be documented): variants carry the `_CANONICAL` suffix.** A baseline that records only the profile name could not tell the contracts apart otherwise. The map is separate from `PERF_PROFILES`, so `PERF_PROFILES` and `PERF_MATRIX` iterate exactly as before.
- The ticket and its acceptance criterion name `signal_source_for()`; the function is `select_signal_source(profile, audit_mode)` in `src/engine/signal_source.py`. The routing test uses the real name.
- A canonical variant's name is not a key of `PERF_PROFILES`, so code that maps a result's profile name back through `PERF_PROFILES` will not find it. No such consumer is touched here; `PERF-M2-T08` will meet it when it writes canonical results.

## Test Summary
- `tests/unit/perf/test_perf_profiles_canonical.py` (new): 8 variants exist and are CANONICAL, differ from their default only in `name` and `signal_contract`, defaults stay LIVE, `PERF_MATRIX` maps only to originals, routing through `select_signal_source`, source profile not mutated.
- `tests/unit/engine/test_signal_contract_foundation.py` and `tests/perf/test_profiler_integrity.py` pass. Run with the T02b set: 152 passed.

## Files Changed
- `src/perf/profiles.py` (shared with T02b), `tests/unit/perf/test_perf_profiles_canonical.py`.

## Completion Summary
Each of the eight `PERF_*` profiles has a canonical variant (`PERF_CANONICAL_PROFILES`, name suffix `_CANONICAL`); defaults, `PERF_MATRIX` and the `RuntimeProfile.signal_contract` default are unchanged. No baseline was rerun (T08).

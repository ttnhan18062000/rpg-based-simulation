---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA
phase: open
date: 2026-10-03
tags: [performance, benchmarking, schema, documentation]
---

# TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA

## Title
PERF-M2-T02 design draft: versioned benchmark identity and result schema, from an inventory of every result format that exists today (provisional; documents only)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`PERF-M2-T02` (`performance_m2_performance_contract_epic.md`) is the schema that T03 (tripwire), T04 (capacity run), and T05 (baseline lifecycle) all depend on. Its inputs exist: T01 is done (`docs/performance/performance_clause_inventory.md`), PERF-D2 is approved, and PERF-D4 is applied, which names the identity fields every result carries (PERF-D2 runtime identity, PERF-D1 contract, `RuntimeMode` sequence, processed-work count). The stack survey (`performance_stack_survey.md`, benchmark harness row) says "survey and design may start now".

The RPG-core entry gate still holds. On 2026-10-03 the owner approved this ticket as a deliberate exception to the roadmap's "everything else in M1-M6 waits for the entry gate": a design document only, labeled provisional, to be re-validated after M1 and after the gate lifts. It takes no measurement and changes no code.

## Scope
Deliverable: `docs/performance/benchmark_identity_schema.md` (frontmatter `status: active`, `authority: P2`, `layer: performance`). The first lines after the title must state that the document is a provisional design draft under the RPG-core entry gate, and that no part of it is implemented or binding until T03/T04/T05 adopt it.

1. **Inventory of current result formats.** Enumerate every format the repository writes or reads today for a benchmark, baseline, or profile result. Cover at least: `tests/perf/baselines/*.json` and the reader in `tests/perf/test_perf_regression_baseline.py`; the corpus baseline (`tests/tools/test_corpus_perf_baseline.py` and its data); `tools/perf/perf_baseline.py`, `run_perf_baseline.py`, `run_benchmarks.py`, `perf_report.py`, `perf_ci.py`, `check_perf_regression.py`; the profiling toolkit artifacts (`profile_diff.py`, `flag_attribution.py`, `_profiling_common.py`); `src/perf/regression_gate.py`'s `PerfBaseline`/`PerfResult` (no consumer, per `perf_baseline_policy.md` §3); `assert_perf_threshold` call sites (`tests/tools/perf_assertions.py`). Find any others by reading these modules' imports and writers; don't assume the list is complete. For each one, give its path, writer, reader, fields, and which identity fields it records or lacks. Read code only; run nothing that produces a measurement
2. **Coverage matrix.** Rows: the M2 epic's "Required contract dimensions" list plus the PERF-D4 point 6 fields. Columns: the formats from item 1. Cells: recorded / partial / absent, with the field name
3. **Proposed schema.** One versioned record (`schema_version`) with two parts:
   - an **identity** block: scenario and checkpoint identity, workload cardinality, engine, content/rules, config, RNG, and schema versions, PERF-D2 runtime identity and DET-PORT tier, PERF-D1 contract, executor/backend and worker count, observer level, gate tier/projection (tripwire, capacity run, comparative per `performance_contract.md`)
   - a **result** block: measurement protocol (warmup, measured ticks, repetitions), raw samples or a pointer to them, latency distribution, throughput, CPU/wall time, memory high-water, `RuntimeMode` sequence, processed/dropped/coalesced work, replay/hash validity, outcome (`PASS`/`REGRESSION`/`INCONCLUSIVE`/`NOT_APPLICABLE`) with reason
   
   Give each field a type, a required/optional status, and a source (which existing code can provide it today, or "not yet available", with the milestone that provides it). Express the schema as a JSON Schema draft embedded in the document; do not add a schema file elsewhere
4. **Comparability rule.** Define which identity differences make two results incomparable (→ `INCONCLUSIVE`, never a silent pass) and which are recorded but do not block comparison. State how a `schema_version` change is handled
5. **Tool mapping.** Show how the record maps onto the survey's chosen tools (`pytest-benchmark` JSON for the PR lane, `pyperf` for controlled runs, instruction-count measurement for the tripwire): which fields each tool already emits, and which this repository adds as extra metadata. Use the tools' documented output formats; cite the documentation version. Do not install anything or add dependencies
6. **Migration.** For each current format from item 1: map it into the schema, mark it retired (no consumer), or keep it outside the schema with a reason. Existing `tests/perf/baselines/` files remain tripwire references, per PERF-D4
7. **Open questions** for perf-planner and the owner, including anything M1 may change (the M2 epic's entry condition "M1 identifies every correction that changes benchmark identity" is not met; list the identity fields M1 candidates could affect)
8. Link the new document from `performance_m2_performance_contract_epic.md` (T02 row) and from `docs/engine/performance_contract.md` only if that file already has a pending-schema pointer for T02. If it does not, add nothing to the P1 file and report it. Then `make knowledge-index-update`

## Out of Scope
- Any edit under `src/`, `tests/`, `tools/`, or `.github/`, and any new dependency
- Running a benchmark, a baseline, a profile, or any command that produces a performance number
- Implementing T03/T04/T05, or choosing thresholds, sample sizes, or runners
- Changing any P1 document's normative text (only the optional pointer in Scope item 8)
- The hosted benchmark-tracking decision (open with the owner)

## Acceptance Criteria
- [ ] `docs/performance/benchmark_identity_schema.md` exists, passes frontmatter validation, and states its provisional status under the entry gate in its opening lines
- [ ] The inventory covers every format named in Scope item 1 plus any found by following imports, each with writer, reader, and fields cited by path
- [ ] The coverage matrix has a cell for every required dimension × format
- [ ] Every schema field has a type, a required/optional status, and a source or "not yet available" with a milestone
- [ ] The comparability rule maps every identity field to blocking or recorded-only
- [ ] The tool mapping cites the `pytest-benchmark` and `pyperf` output documentation with versions
- [ ] Open questions include the M1-dependent identity fields
- [ ] `tests/docs` and `tests/static` pass
- [ ] `git diff` touches only `docs/performance/benchmark_identity_schema.md`, the M2 epic doc's T02 row, at most one pointer line in `docs/engine/performance_contract.md`, `agent-working/`, `docs/REGISTRY.yaml`, and the knowledge index files

## Related Tickets
- TCK-20261003-PERF-M2-CLAUSE-INVENTORY (PERF-M2-T01)
- TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT (applied PERF-D2/D4)
- TCK-20261003-PERF-PROFILING-TOOLKIT (profile artifact format)
- TCK-20260919-PERF-SCENARIO-METROPOLIS-SPAWN-COLLISION (a scenario identity must not map to `build_metropolis_state()` until fixed; note it in the scenario-identity field)

## Related Docs
- `docs/plans/design_enhancement/performance_optimization/performance_m2_performance_contract_epic.md`
- `docs/plans/design_enhancement/performance_optimization/performance_stack_survey.md` (benchmark harness and CI regression rows)
- `docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md` (RPG-core stability entry gate)
- `docs/architecture/performance_optimization_decisions.md` (PERF-D1, D2, D4)
- `docs/engine/performance_contract.md`, `docs/engine/deterministic_execution.md`
- `docs/performance/performance_clause_inventory.md`, `docs/performance/perf_baseline_policy.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261003-PERF-M2-CLAUSE-INVENTORY/`

## Related Code Areas
Read only: `tools/perf/`, `tests/perf/`, `tests/tools/perf_assertions.py`, `src/perf/regression_gate.py`, `src/observability/performance/`

## Assumptions / Open Questions
- Owner exception (2026-10-03): this M2 design work runs before the entry gate lifts, as a provisional document. It cannot be promoted to a contract until the gate lifts and M1 has reported its identity-changing corrections.
- If the inventory shows a current format that already claims capacity, record it as a finding for perf-planner; do not correct it here.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary


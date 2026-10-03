---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA
date: 2026-10-03
tags: [performance, documentation]
---

# Plan: TCK-20261003-PERF-M2-T02-BENCHMARK-IDENTITY-SCHEMA

## Summary
One new document, `docs/performance/benchmark_identity_schema.md`, provisional under the RPG-core entry gate. No `src/`, `tests/`, `tools/`, or `.github/` edit; no measurement.

## Steps
1. Inventory current result formats from code (read-only subagent report, then spot-checked by path).
2. Build the coverage matrix: M2 epic "Required contract dimensions" plus PERF-D4 point 6 fields, against each format.
3. Draft the schema (identity block, result block) as embedded JSON Schema draft 2020-12, one table of field, type, required, source or milestone.
4. Write the comparability rule: every identity field is blocking or recorded-only; schema_version change handling.
5. Tool mapping against `pytest-benchmark` 5.3.0 and `pyperf` documented output; instruction-count tripwire fields are repository metadata.
6. Migration table per format; open questions including M1-dependent identity fields.
7. Link from the M2 epic T02 row; add the draft pointer to the existing pending-schema sentence in `performance_contract.md` (it exists, line 51); `make knowledge-index-update`; run `tests/docs`, `tests/static`.

## Scope guards
No thresholds, sample sizes, or runners are chosen. The scenario-identity field notes the metropolis spawn-collision ticket. Formats that claim capacity are recorded as findings for perf-planner, not corrected.

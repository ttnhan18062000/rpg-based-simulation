---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261028-PARITY-INFRA-430-431-PERF-SCHEMA-DRIFT
phase: open
date: 2026-10-28
tags: [benchmarking]
---

# TCK-20261028-PARITY-INFRA-430-431-PERF-SCHEMA-DRIFT

## Title
Parity ledger INFRA-430 and INFRA-431 state the perf benchmark schema version and the legacy-tripwire list as they were, not as the code holds them now (#626)

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Issue #626 is a finding from perf-planner, relayed by lead-planner. `docs/parity_ledger/` is rpg's path.
The issue's own numbers are stale: the code moved again after it was filed. On origin/main fdfc5f9fd:
- `src/perf/benchmark_record.py:59` `SCHEMA_VERSION = "1.4"`. The steps were all MINOR and additive:
  1.1 `identity.runner`, 1.2 the after-collect `result.memory_mb` keys, 1.3 the `working_set_*` keys,
  1.4 the optional `outcome.check`.
- `tools/perf/baseline_lifecycle.py:54` `LEGACY_TRIPWIRE_REFERENCES` holds 6 files: mixed_200_concurrent,
  mixed_200_local, simq_corpus_frontier_extended, simq_corpus_frontier_marches, strategic_100_concurrent,
  strategic_100_local.
- `docs/parity_ledger/infrastructure.yaml` INFRA-430 says "schema 1.0", and INFRA-431 says "the 15 pre-schema files".

U4 batch. Scope OK'd by rpg-planner (u24) on 2026-10-28, relayed by lead-planner-u24 and then lead-planner. The owner's dispatch go is logged on #715 issuecomment-6474978097, item 1.

## Scope
1. At write time, read the current `SCHEMA_VERSION` and `LEGACY_TRIPWIRE_REFERENCES` from the code, and state both values and the commit sha in the ticket.
2. Rewrite the INFRA-430 text: the current schema version, the additive MINOR history, and the rule that only a MAJOR mismatch is INCONCLUSIVE.
3. Rewrite the INFRA-431 text: the current LEGACY_TRIPWIRE_REFERENCES count instead of "15".
4. Re-check `v2_evidence` and `test_path` for both entries against the code, and confirm both test_paths pass.
5. Write through `parity_ledger_writer.py` only, and check `git diff --stat` shows only these two rows.

## Out of Scope
- `docs/performance/benchmark_identity_schema.md`. It is perf's doc. Its stale "1.2" at lines 9 and 159 was reported to perf-planner, which fixed it in ecea69d1f on its own branch.
- The coming 1.5 bump (TCK-20261025-PERF-RECORD-IDENTITY-PINS-INSTALLED-RUNTIME-DEPENDENCIES). perf-planner has INFRA-430 in that ticket's sweep (fd038c870), and its edit needs an rpg OK in that PR.
- infrastructure.yaml's general paydown, which the owner assigned to testing on 2026-10-10.

## Acceptance Criteria
1. INFRA-430 and INFRA-431 state the values the code holds at the PR head, with the sha recorded in the ticket.
2. status stays `verified`; v2_evidence and test_path are checked, and the test_paths pass.
3. Only those two rows change in infrastructure.yaml.
4. `python3 -m codebase.gates.parity_ledger_schema check` passes, with no rule rising.
5. Proof: the gate check plus the cited tests, with no sim run (rpg-planner, 2026-10-28).

## Related Tickets
- TCK-20261028-PARITY-PAYDOWN-WORLD-DYNAMICS (same U4 PR)
- TCK-20261025-PERF-RECORD-IDENTITY-PINS-INSTALLED-RUNTIME-DEPENDENCIES (perf; the next version bump)

## Related Docs
- docs/parity_ledger/infrastructure.yaml, docs/performance/benchmark_identity_schema.md, docs/performance/perf_baseline_policy.md

## Related Stored Artifacts

## Related Code Areas
- src/perf/benchmark_record.py, tools/perf/baseline_lifecycle.py, tests/unit/perf/test_benchmark_record.py, tests/unit/perf/test_baseline_lifecycle.py

## Assumptions / Open Questions
- If perf's 1.5 PR merges before U4, write 1.5, and say so in the ticket.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

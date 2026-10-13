---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261010-PERF-M2-T05B-KNOWN-DEBT-LEDGER
date: 2026-10-12
tags: [performance, benchmarking, testing]
---

# Plan: TCK-20261010-PERF-M2-T05B-KNOWN-DEBT-LEDGER

- Declare perf's own `RegistrySpec` (`PERF_DEBT_SPEC`, top key `known_debt`, required fields = the shared six, optional `expected_signature` and `note`, `strict_fields=True`) in `tools/perf/known_debt.py`. No change to `tools/test_architecture/`.
- Decision (the ticket left it open: regex, scenario+phase key or clause id): `expected_signature` is `<STATE>:<check>`, a closed vocabulary. STATE is a non-pass `OutcomeState`; check is a `compare()` check name. Chosen because it is what the gate can actually produce and a typo cannot silently never match; a regex or a phase key would need data `compare()` does not expose.
- `match` is an fnmatch pattern on the scenario id. The ledger ships empty: no lane has an owned red yet, and inventing a row would assert an outcome nobody measured.

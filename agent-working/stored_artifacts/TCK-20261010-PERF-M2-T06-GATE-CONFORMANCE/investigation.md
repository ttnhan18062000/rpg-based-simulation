---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261010-PERF-M2-T06-GATE-CONFORMANCE
date: 2026-10-24
tags: [performance, documentation, certification]
---

# Investigation: TCK-20261010-PERF-M2-T06-GATE-CONFORMANCE

- Call sites: `tools/perf/perf_threshold_inventory.build_report` finds the helper calls by AST. The ticket text says 56 (clause inventory section 5.2); the count is re-taken when the map is written.
- Clause IDs: the clause inventory (`docs/performance/performance_clause_inventory.md` section 3) defines PC-, CC-, BP-, OA-, OI-, RG- and RP- rows; section 4 lists the live checks that enforce no documented clause, which is most of the absolute ceilings.
- `Outcome` is `(state, reason)`. `compare()` runs six checks in order (schema, each_side, blocking_fields, hash_scheme, mode_sequences, latency). `tools/perf/known_debt.py` already declares the closed vocabulary `CHECKS` and the `<STATE>:<check>` signature format but nothing matches an outcome against it yet.
- Serialization: `BenchmarkRecord.to_dict` is generic over dataclass fields and `from_dict` ignores unknown keys, so an optional field is backward-compatible on read; a MINOR schema bump records it.
- `certification_contract.md` already holds the earlier-name notes (landed in #306); only a read-only guard is needed.

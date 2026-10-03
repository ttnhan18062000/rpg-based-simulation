---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT
date: 2026-10-03
tags: [performance, determinism, documentation]
---

# Test Plan: TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT

No code changes, so no new tests. Verification:

- `python3 tools/validate_frontmatter.py <file>` on every edited document: OK.
- `pytest tests/docs tests/static -m "not slow"`: 121 passed, 2 skipped, 1 xfailed. `pytest tests/architecture tests/parity tests/tools/test_perf_tag_test_scoper_wiring.py tests/tools/test_test_scope_coverage_static.py` and the contract text pin `tests/perf/test_perf_regression_baseline.py::test_performance_contract_lists_runtimemode_scoped_claim`: 150 passed.
- Parity ledger: the edited `infrastructure.yaml` loads; schema errors equal `HEAD`'s 330 (pre-existing).
- Inventory-versus-edited-text check (AC4), done by reading while editing, not by a script: each row of `performance_clause_inventory.md` §3 with a destination was located in the edited text: STAY and CERT rows (PC-01..03, 05, 06, 11, 15..17; CC-01..14) are unchanged or only renamed (CC-05, CC-06, CC-10); CAPRUN/TRIP/CAP rows (PC-04, 07, 08, 09, 10, 13; BP-02, 03, 09..13, 15, 17) are in `performance_contract.md` §3.2, §3.3, §5, §5.1; HW rows (BP-04..06, RP-02, RP-03) point to `certification_contract.md` §3 (`perf_baseline_policy.md` and `runtime_profiles.md`); DEL rows (PC-14, BP-01, 07, 14, 16) are removed or rewritten (§5, baseline policy §1-§2); FLAG rows (PC-12, BP-08, OA-11) are the comparative kind (§3.3, §4.2) and the governor rule outside the contract (§5.2). The three performance documents agree on warmup/sample minimums (100/1000, capacity run), the class definition (certification §3), and the targets (contract §5.1).
- Literal phase count: `grep -rnE "39[ -]phases?" AGENTS.md CLAUDE.md docs/engine/authoritative_pipeline.md docs/engine/README.md tools/agent_orchestration_codex_adapter/generator.py` finds nothing.

## Proof Plan

- Level: documentation review plus existing doc and static tests.
- Proof kind: grep-based consistency checks and the existing frontmatter and doc tests.
- Oracle source: the owner-approved decision records and the generated inventories.
- Expected effect: no edited document describes an approved-but-unbuilt mechanism as existing; counts and classes agree across documents.
- Selected commands: as listed above.

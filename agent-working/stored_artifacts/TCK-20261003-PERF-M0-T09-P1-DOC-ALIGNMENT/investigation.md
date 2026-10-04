---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT
date: 2026-10-03
tags: [performance, determinism, documentation]
---

# Investigation: TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT

Findings made while applying the edits (the evidence itself is in the inventories under `docs/performance/`):

- Two tests pin "39": `tests/agent_orchestration_codex_adapter/test_agents_md_generation.py:14,18`; the generator note hard-codes it. Reported to perf-planner; moved to TCK-20261003-PERF-PHASE-COUNT-PINNED-TEXT.
- `docs/architecture/performance_optimization.md`: the ADR's decisions 1, 2 and 4 could not be found in current code (no `model_copy(deep=False)`, no `Grid` bytearray class, no `find_frontier_target`; the entity type is the `EntityState` dataclass). The status line that said they "remain valid and were separately implemented" was replaced with "not verified as current".
- `docs/testing/regression_policy.md` and `docs/engine/architecture.md` cited the baseline policy's removed thresholds, `UnacceptableRegressionError` and class table; both updated.
- `docs/parity_ledger/infrastructure.yaml` has 330 schema errors at `HEAD` and the same 330 after the edit (pre-existing: for example `test_path: null` on a `verified` entry). INFRA-223 was the only entry citing changed text.
- Not edited (historical or out of list): `docs/architecture/kernel_concurrency_design_philosophy.md:235` and `docs/guidelines/tag_taxonomy.md:68` cite the policy's old sections as dated records; `.claude/agents/test-scoper.md` cites policy §3 (outside this ticket's paths); render/art and aseprite plans and brainstorm docs keep their "39-phase" text (other tracks).
- `CLAUDE.md` row for `performance_contract.md` still says "Hardware classes (A/B/C) and scaling limits", which is stale after PERF-D4; left alone because the owner approved only the phase-count edit.

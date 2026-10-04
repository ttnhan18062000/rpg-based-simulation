---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261003-PERF-PHASE-COUNT-PINNED-TEXT
date: 2026-10-03
tags: [performance, documentation]
---

# Test Plan: TCK-20261003-PERF-PHASE-COUNT-PINNED-TEXT

- `pytest tests/agent_orchestration_codex_adapter`: 30 passed with the rewritten tests.
- Mutation proof (each reverted afterwards, `git diff` shows only the intended edits):
  1. `39-phase` reintroduced into the `AGENTS.md` pipeline note: `test_agents_md_states_authoritative_pipeline_without_a_phase_count` FAILED (match `39-phase`).
  2. `## The 39 Phases of Refinement` reintroduced in `authoritative_pipeline.md`: `test_agents_md_pipeline_note_matches_live_engine_doc` FAILED (match `39 Phases`).
  3. The words "refinement phase" removed from `authoritative_pipeline.md`: the same test FAILED (unit no longer defined).
- `pytest tests/docs tests/static -m "not slow"`: 121 passed, 2 skipped, 1 xfailed.

## Proof Plan

- Level: unit.
- Proof kind: mutation proof of a documentation-invariant test.
- Oracle source: the PERF-D6 rule that prose states no literal refinement-phase count and defines the unit.
- Expected effect: the tests fail when a literal count or an undefined unit is reintroduced.
- Selected commands: `pytest tests/agent_orchestration_codex_adapter -p no:cacheprovider`.

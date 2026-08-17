---
status: historical
layer: engine
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260817-STANDARD-AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT
tags: [ai, engine, bug]
---

# Test Plan — TCK-20260817-STANDARD-AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT

## Normal flow
- `pytest tests/agent_orchestration_codex_adapter/ -q` — all tests in the affected package pass,
  including the originally-failing `test_agents_md_pipeline_note_matches_live_engine_doc` and the
  newly-renamed `test_agents_md_states_authoritative_37_phase_pipeline`.

## Regression check
- Full re-verification that `AGENTS.md` and `.agents/skills/*` are genuinely regenerated (not
  hand-edited) via `render_codex_guidance()`, matching the file's own "do not hand-edit —
  regenerate instead" header.
- Grep sweep (`grep -rln "32-phase\|32 phases\|31 phases\|31-phase"`) confirming every remaining
  hit after the fix is a legitimately frozen historical file
  (`tickets/done/`, `stored_artifacts/`, `docs/archive/`, `docs/plans/archive/`, `docs/audits/`),
  not a currently-active document.

## Edge case
- The 6 newly-added phase-table rows (`faction_awareness`, `diplomatic_transitions`,
  `military_conflict`, `gold_sink`, `guild_visit`, `paid_information`) are verified against real
  `run_phase(...)` call sites in `src/engine/pipeline.py`, not assumed from memory — each row's
  citation ID is pulled directly from the surrounding code comment.

## Failure mode covered
- The "fix half the drift, leave the other half" failure mode this investigation specifically
  guards against: a bare string-swap in `generator.py` alone (32→31, matching the doc's
  then-current-but-still-wrong count) would have made the originally-failing test pass while
  leaving `authoritative_pipeline.md`'s own table incomplete — the actual substance this repo's
  Authoritative Mechanics Rule cares about. Both are fixed together.

## Results
- `pytest tests/agent_orchestration_codex_adapter/ -q`: 27 passed.

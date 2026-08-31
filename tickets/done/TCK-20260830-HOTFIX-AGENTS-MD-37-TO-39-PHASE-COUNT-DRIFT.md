---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260830-HOTFIX-AGENTS-MD-37-TO-39-PHASE-COUNT-DRIFT
phase: open
date: 2026-08-30
tags: [architecture]
---

# TCK-20260830-HOTFIX-AGENTS-MD-37-TO-39-PHASE-COUNT-DRIFT

## Title
Update `AGENTS.md`/Generator's Hardcoded "37-phase" Pipeline Count to 39

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
CI job "Agent orchestration / codex / replay" failed on PR #90 after merging `origin/main` into
`m1-quick-wins`:
`tests/agent_orchestration_codex_adapter/test_agents_md_generation.py::test_agents_md_pipeline_note_matches_live_engine_doc`
asserted `"37 phases"` is in `docs/engine/authoritative_pipeline.md`, but that file now reads
`"...refined through these 39 phases"` — real pipeline phases were added since the last time this
count was synced (this exact drift class already has its own precedent ticket family,
`TCK-20260817-STANDARD-AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT` et al., for the 17→37 transition).

## Scope
- `tools/agent_orchestration_codex_adapter/generator.py`'s hardcoded `_AUTHORITATIVE_PIPELINE_NOTE`
  string updated "37-phase"/"37 phases" → "39-phase"/"39 phases".
- `AGENTS.md` regenerated from the updated generator (single-line diff, matches the note text
  only — verified via `git diff --stat`).
- `tests/agent_orchestration_codex_adapter/test_agents_md_generation.py`: renamed
  `test_agents_md_states_authoritative_37_phase_pipeline` →
  `..._39_phase_pipeline`, updated both hardcoded assertions to "39-phase"/"39 phases".

## Out of Scope
Per this session's own investigation, many other live docs/skills still reference the stale
"37-phase" figure (`CLAUDE.md`, `.claude/skills/*`, `.agents/skills/*`,
`docs/engine/README.md`, `docs/plans/design_enhancement/*`) — none of these are covered by any
test assertion (verified: `grep -rln "37-phase\|37 phase" tests/` returns nothing after this
ticket's fix), so leaving them stale is not a CI hard-error, just doc staleness. Filed separately
as `TCK-20260830-STALE-37-PHASE-REFERENCES-SWEEP` rather than fixed here, to keep this hotfix
minimal and CI-unblocking.

## Acceptance Criteria
- `tests/agent_orchestration_codex_adapter/test_agents_md_generation.py` passes (all 3 tests).
- `AGENTS.md`'s diff is a single line (the pipeline-note text), not a broader regeneration
  artifact.

## Related Tickets
- TCK-20260817-STANDARD-AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT (precedent for this exact drift class)
- TCK-20260830-STALE-37-PHASE-REFERENCES-SWEEP (broader doc/skill sweep, filed separately)

## Related Code Areas
- tools/agent_orchestration_codex_adapter/generator.py
- AGENTS.md
- tests/agent_orchestration_codex_adapter/test_agents_md_generation.py

## Assumptions / Open Questions
None.

## Implementation Notes
Implemented and verified: `tests/agent_orchestration_codex_adapter/test_agents_md_generation.py`
3/3 pass. `AGENTS.md` diff confirmed single-line via `git diff --stat AGENTS.md` (1 changed line).

## Test Summary
tests/agent_orchestration_codex_adapter/test_agents_md_generation.py: 3 passed.

## Files Changed
tools/agent_orchestration_codex_adapter/generator.py, AGENTS.md,
tests/agent_orchestration_codex_adapter/test_agents_md_generation.py

## Completion Summary
(pending Parity/Verify/Finalize)

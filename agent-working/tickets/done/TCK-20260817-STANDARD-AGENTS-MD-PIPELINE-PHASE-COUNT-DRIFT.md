---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260817-STANDARD-AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT
phase: done
date: 2026-08-17
tags: [ai, engine, bug]
---

# TCK-20260817-STANDARD-AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT

## Title
Fix `AGENTS.md`'s stale "32-phase" pipeline claim by correcting `docs/engine/authoritative_pipeline.md`'s
own phase table (37 real phases, not 31) and propagating the fix everywhere it's cited

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Real CI failure on the "API / tools / logging" job (run
https://github.com/ttnhan18062000/rpg-based-simulation/actions/runs/32000421496):
`tests/agent_orchestration_codex_adapter/test_agents_md_generation.py::test_agents_md_pipeline_note_matches_live_engine_doc`
failed — the generated `AGENTS.md` claims a "32-phase" pipeline; the live
`docs/engine/authoritative_pipeline.md` said "31 Phases".

Investigation found this is not a simple 32-vs-31 typo: `docs/engine/authoritative_pipeline.md`'s
own 31-row table was itself stale against `src/engine/pipeline.py::refine()`, which has 37 real
`run_phase(...)` call sites. Six phases (`faction_awareness`, `diplomatic_transitions`,
`military_conflict`, `gold_sink`, `guild_visit`, `paid_information`) were missing from the table
entirely, added to `pipeline.py` in commits that never updated this doc. Neither "31" nor "32" was
ever the true count. A bare string-swap in `generator.py` (matching the number to the doc's
then-still-wrong count) would have made the failing test pass while leaving the underlying doc
incomplete — exactly the kind of gate-vs-substance shortcut this repo's rules forbid.

## Scope
- `docs/engine/authoritative_pipeline.md`: rebuild the phase table with all 37 real phases in
  their real, verified order, with real citations for the 6 previously-missing rows.
- `tools/agent_orchestration_codex_adapter/generator.py`: `_AUTHORITATIVE_PIPELINE_NOTE` "32" → "37".
- Regenerate `AGENTS.md` + `.agents/skills/*` via `render_codex_guidance()` (never hand-edited).
- `CLAUDE.md:258`: "32-phase" → "37-phase".
- 5 living `.claude/skills/*.md` files citing the phase count as current fact, including
  recomputing 3 files' specific numbered phase-# table rows against the corrected table.
- `tests/agent_orchestration_codex_adapter/test_agents_md_generation.py`: a second test in the
  same file (`test_agents_md_states_authoritative_32_phase_pipeline`) was not in the original
  failing set (both sides of its comparison were stale-but-matching) but would break once
  `AGENTS.md` is regenerated correctly — updated and renamed in the same change.

## Out of Scope
- `docs/ai/agents_dir_disposition.md`'s "32-phase" citation — a frozen factual snapshot inside a
  disposition-table analysis of a different archived file, not a live ongoing claim.
- Any `tickets/done/`, `stored_artifacts/`, `docs/archive/`, `docs/plans/archive/`, or
  `docs/audits/` file citing the old count — legitimately frozen historical records.
- Any change to `src/engine/pipeline.py` — the 37-phase reality is correct production behavior;
  only documentation was stale.
- Any other ticket in this batch.

## Acceptance Criteria
- [ ] `docs/engine/authoritative_pipeline.md`'s phase table matches `src/engine/pipeline.py::refine()`'s
      real 37 `run_phase(...)` call sites exactly, in order.
- [ ] `test_agents_md_pipeline_note_matches_live_engine_doc` passes.
- [ ] `AGENTS.md`/`.agents/skills/*` are regenerated (not hand-edited) and internally consistent.
- [ ] No currently-active document still cites "32-phase"/"31-phase" as current fact.

## Related Tickets
None — standalone, pre-existing, unrelated to recent session work.

## Related Docs
- `docs/engine/authoritative_pipeline.md` (fixed)
- `CLAUDE.md` (fixed)

## Related Stored Artifacts
`stored_artifacts/TCK-20260817-STANDARD-AGENTS-MD-PIPELINE-PHASE-COUNT-DRIFT/`

## Related Code Areas
- `tools/agent_orchestration_codex_adapter/generator.py`
- `docs/engine/authoritative_pipeline.md`
- `.claude/skills/{debugging-strategies,cognition-strategy,python-performance-optimization,combat-mechanics,systems-economy}/SKILL.md`

## Assumptions / Open Questions
None — the 6 missing phases and their real order were verified directly against
`src/engine/pipeline.py`'s source, not assumed.

## Implementation Notes
Rebuilt `docs/engine/authoritative_pipeline.md`'s phase table from a direct `run_phase(...)`
call-site count (37, verified via grep + manual cross-check), inserting the 6 missing phases at
their real source-code positions with citations pulled from surrounding code comments. Updated
`generator.py`'s hardcoded note, regenerated `AGENTS.md`/`.agents/skills/*` via
`render_codex_guidance(repo_root, repo_root)` (this also brought two unrelated, pre-existing stale
`.agents/skills/` companion copies — `brainstorming`, `implement-ticket` — back in sync with their
`.claude/skills/` source; not touched by hand, purely a side effect of running the regenerator for
the first time in a while). Updated `CLAUDE.md` and 5 living skill docs, recomputing specific
phase-number table cells in 3 of them against the corrected 37-phase order. Fixed a second,
previously-passing-by-coincidence test in the same file that would have broken once `AGENTS.md`
was correctly regenerated.

## Test Summary
- `pytest tests/agent_orchestration_codex_adapter/ -q`: 27 passed.

## Files Changed
- `docs/engine/authoritative_pipeline.md`
- `tools/agent_orchestration_codex_adapter/generator.py`
- `AGENTS.md`, `.agents/skills/*/SKILL.md` (regenerated)
- `CLAUDE.md`
- `.claude/skills/debugging-strategies/SKILL.md`
- `.claude/skills/cognition-strategy/SKILL.md`
- `.claude/skills/python-performance-optimization/SKILL.md`
- `.claude/skills/combat-mechanics/SKILL.md`
- `.claude/skills/systems-economy/SKILL.md`
- `tests/agent_orchestration_codex_adapter/test_agents_md_generation.py`

## Completion Summary
Fixed the real underlying drift: `docs/engine/authoritative_pipeline.md`'s phase table was
incomplete (missing 6 phases), not merely off-by-one. Corrected the authoritative doc first, then
propagated the corrected count through the generator, the generated `AGENTS.md`, and every
currently-active document citing it — leaving nothing half-fixed.

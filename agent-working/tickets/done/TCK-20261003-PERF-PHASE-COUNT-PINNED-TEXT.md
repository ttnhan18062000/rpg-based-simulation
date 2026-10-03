---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261003-PERF-PHASE-COUNT-PINNED-TEXT
phase: done
date: 2026-10-03
tags: [performance, documentation]
---

# TCK-20261003-PERF-PHASE-COUNT-PINNED-TEXT

## Title
Remove the literal refinement-phase count from the AGENTS.md generator note and the pipeline contract, and re-point the tests that pin "39" at the PERF-D6 invariant

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
PERF-D6 (owner-approved 2026-10-03) says prose never states a refinement-phase count as a literal number, because the count changes with every RPG-core phase. The `run_phase()` count is 44 today and the contract says 39. `TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT` items 6 and 7 remove the literal, but perf-implementer stopped and reported that two tests pin it:
- `tests/agent_orchestration_codex_adapter/test_agents_md_generation.py:11-18` asserts `"39-phase"` is in `AGENTS.md` and `"39 phases"` is in `docs/engine/authoritative_pipeline.md`
- `tools/agent_orchestration_codex_adapter/generator.py:13` hard-codes the note `_AUTHORITATIVE_PIPELINE_NOTE` ("the 39-phase authoritative mutation pipeline ... refined through these 39 phases")

The tests guard two real things: `AGENTS.md` must not carry the stale "17-phase" figure, and the `AGENTS.md` note must agree with the live engine contract. Under PERF-D6, "agree" no longer means "both say 39"; it means neither states a literal count and both name the same counted unit. This ticket changes the generator note and re-points the tests at that invariant. T09 is docs-only, so this work does not belong there.

## Scope
- `tools/agent_orchestration_codex_adapter/generator.py`: reword `_AUTHORITATIVE_PIPELINE_NOTE` without a number. Keep its meaning: the Singular Bottleneck Law, the `StateUpdate` route, the link to `docs/engine/authoritative_pipeline.md`. Use the PERF-D6 unit wording, for example "refined through the authoritative mutation pipeline's refinement phases (one per `run_phase()` call in `AuthoritativeApplyPipeline.refine`) defined in ...". Regenerate `AGENTS.md` with the generator
- `docs/engine/authoritative_pipeline.md`: remove the literal "39" from the heading and prose (the part of T09 item 6 that is pinned). Coordinate with T09 so the file is edited once
- `tests/agent_orchestration_codex_adapter/test_agents_md_generation.py`: replace the two "39" assertions with assertions that keep their purpose:
  - `AGENTS.md` contains neither "17-phase" nor "17 phase" (kept) and links `docs/engine/authoritative_pipeline.md` (kept)
  - neither `AGENTS.md`'s pipeline note nor `authoritative_pipeline.md` states a literal refinement-phase count (a regex such as `\b\d+[- ]phases?\b` over the note and the pipeline document's prose, with any allowed kernel-phase mention handled explicitly)
  - `authoritative_pipeline.md` defines the counted unit "refinement phase"
  Rename the test function from `..._39_phase_pipeline` to match
- The remaining "39-phase" mentions in documents outside T09's list: `docs/engine/README.md:14` and `docs/plans/agent_infrastructure/session_layer_working_process.md:762`. Reword them without a number
- Leave the render-and-art plans, `aseprite-mcp-pixel-art/README.md`, and `docs/brainstorm/` untouched. List them in the Completion Summary as remaining mentions owned by other tracks (render/asset planning) or by unregistered brainstorm material

## Out of Scope
- Any change to `src/`, to the pipeline, or to the phase catalog (`PERF-M3-T01`)
- Generating the count from code into any document (the catalog does not exist yet)
- Other generator behavior, or the other tests in that file
- Documents owned by the render/asset track

## Acceptance Criteria
- [x] `AGENTS.md` equals the generator's output, and contains no literal refinement-phase count and no "17-phase"
- [x] `authoritative_pipeline.md` states no literal refinement-phase count and defines "refinement phase"
- [x] The rewritten tests pass, and they fail if someone reintroduces "39-phase" (or any literal count) into the note or the contract; mutation proof recorded in the test plan
- [x] `tests/agent_orchestration_codex_adapter/` and `tests/static` pass
- [x] `git diff` touches only the generator file, `AGENTS.md`, the test file, the three named documents, `docs/REGISTRY.yaml`, `agent-working/tickets/`, `agent-working/stored_artifacts/`, `agent-working/agent-monitoring/`

## Related Tickets
- TCK-20261003-PERF-M0-T09-P1-DOC-ALIGNMENT (sibling; owns the rest of items 6 and 7)
- TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT (evidence for the 44 count and the counted units)

## Related Docs
- `docs/architecture/performance_optimization_decisions.md` (PERF-D6, C-02, F-07)
- `docs/performance/phase_inventory.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT/`

## Related Code Areas
- `tools/agent_orchestration_codex_adapter/generator.py`, `tests/agent_orchestration_codex_adapter/test_agents_md_generation.py`

## Assumptions / Open Questions
- This is a deliberate exception to the batch's docs/tools-only rule, approved by perf-planner on 2026-10-03. The tests change because the approved decision changes the fact they pin, not to make a gate pass; their guarding purpose is kept and re-expressed
- Implement together with or right after T09 items 6 and 7, in the same PR, so `CLAUDE.md`, `AGENTS.md`, and the contract never disagree on `main`
- perf-planner reviews before commit

## Implementation Notes
- Generator note reworded without a count; `AGENTS.md` regenerated (pre-change generator output equalled `AGENTS.md`, so the diff is the note line only).
- `authoritative_pipeline.md` heading and prose de-numbered (the table's row numbers are row indexes, not a count); `docs/engine/README.md` and `session_layer_working_process.md` reworded; the `CLAUDE.md` Engine Contracts row reworded with the user's explicit approval.
- Tests re-pointed at the PERF-D6 invariant; mutation proof recorded in the stored test plan.
- Remaining "39-phase" mentions left to other tracks: `docs/plans/render-and-art/`, `docs/plans/render_and_art_program_roadmap.md`, `docs/plans/live_map_rendering_and_surface_integration_milestone_plan.md`, `docs/plans/aseprite-mcp-pixel-art/README.md`, and several `docs/brainstorm/` files.

## Test Summary
- `tests/agent_orchestration_codex_adapter`: 30 passed. Mutation proof: three reintroductions each failed the intended test. `tests/docs` + `tests/static`: 121 passed.

## Files Changed
- tools/agent_orchestration_codex_adapter/generator.py; AGENTS.md; CLAUDE.md (one table row)
- tests/agent_orchestration_codex_adapter/test_agents_md_generation.py
- docs/engine/authoritative_pipeline.md, docs/engine/README.md, docs/plans/agent_infrastructure/session_layer_working_process.md

## Completion Summary
No literal refinement-phase count remains in the generator note, `AGENTS.md`, `CLAUDE.md`, `authoritative_pipeline.md` or `docs/engine/README.md`. The tests keep their purpose (no stale figure, the note agrees with the contract) and now fail on a literal count or an undefined unit. Remaining mentions in render/art, aseprite and brainstorm documents belong to other tracks.

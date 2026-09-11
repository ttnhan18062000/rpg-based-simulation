---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-VISUAL-AGENT-REVIEW
phase: done
date: 2026-08-21
tags: [visualization, simulation-quality, determinism, world]
---

# TCK-20260821-VISUAL-AGENT-REVIEW

## Title
Tiered agent-review pipeline for visual-quality escalation

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Build a tiered agent-review pipeline: Tier 0 (pure data, zero image, deterministic hard/soft/scoring-rule path, primary/default) -> Tier 1 (compact JSON digest) -> Tier 2 (actual image, fetched only on escalation, annotated/gridlined by default for citable coordinates).

## Scope
- Implement the Tier 0 -> Tier 1 -> Tier 2 escalation pipeline per PROPOSAL.md §4c-§4h's proven mechanism (Tier 0/1 already shown bit-identical SHA256; annotated-vs-plain distinction already tested)
- Decide new .claude/agents/world-render-reviewer.md subagent vs folding into an existing agent (simulation-analyst.md is the closest structural template; world-debugger.md ruled out as a different job)
- Define the exact Tier 1 digest JSON schema and the exact escalation threshold (both explicitly open, decide jointly with the grade-scorer ticket at Plan-phase time)
- Ensure the annotated/gridlined PNG variant (not plain) is fetched on escalation, giving citable tile-coordinate ranges
- Follow simulation-analyst.md's contract output shape: one-line summary, findings table with severity + evidence/coordinates, recommended next steps

## Out of Scope
- Any change to the renderer itself or to the Tier 0 scoring system's internals beyond consuming their output
- CI-gating this pipeline — report-only, on-demand, never CI-gated

## Acceptance Criteria
- [x] When Tier 0 does not flag an anomaly, the pipeline completes with a Tier 1 digest only and zero image is ever fetched via Read
- [x] When Tier 0 flags an anomaly, the ANNOTATED/gridlined PNG variant (not plain) is fetched, and the resulting verdict cites tile-coordinate ranges traceable to that image
- [x] The Tier 1 digest is deterministic — byte/field-identical across repeated runs of the same state
- [x] Agent-review output follows simulation-analyst.md's contract shape: one-line summary, findings table with severity + evidence/coordinates, recommended next steps
- [x] A golden-hash regression test (tests/unit/, regression marker) covers the Tier 0/1 determinism claim

## Related Tickets
- TCK-20260821-WORLD-RENDER-CORE
- TCK-20260821-VISUAL-GRADE-SCORER
- TCK-20260820-EPIC-WORLD-RENDERING-CORE

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- experiments/spatial_rendering/PROPOSAL.md
- .claude/agents/simulation-analyst.md
- .claude/agents/world-debugger.md

## Assumptions / Open Questions
- Whether this becomes a new .claude/agents/world-render-reviewer.md subagent or folds into an existing agent is a genuine unresolved tradeoff, decided during this ticket's own Plan phase
- Exact Tier 1 digest JSON schema and exact escalation threshold are explicitly open, likely decided jointly with the grade-scorer ticket
- simulation-quality: this pipeline consumes the SimQ-sibling Tier 0 scoring system, tagged for topical adjacency rather than SimQ-subsystem membership

## Implementation Notes

Implemented all 9 steps of `staging_artifacts/TCK-20260821-VISUAL-AGENT-REVIEW/plan.md` as written, no architectural deviations:

- **Step 1**: `src/rendering/render_annotated.py` ports `render_annotated()`, the `DIGITS` 3x5 bitmap font, and `draw_text()` from `experiments/spatial_rendering/prototype/render_annotated.py` near-verbatim, importing `terrain_color`/`DEFAULT_TERRAIN_COLOR` from `src.rendering.render` and `write_png` from `src.rendering.png_writer` instead of the prototype's `sys.path`-bootstrapped local imports. No `__main__` CLI block.
- **Steps 3-5**: `src/rendering/review_pipeline.py` adds `should_escalate` (single call site for the D/F cutoff), the frozen `Tier1Digest` dataclass + `digest_to_json` (`sort_keys=True`), and `run_tier0_tier1_pipeline`, which composes `connectivity.py`/`density.py`/`shape.py`/`grading.py` and calls `render_annotated(...)` only inside the `if escalate:` branch — the sole call site. `flagged_shape_components` is explicitly `sorted(..., key=lambda d: (d["terrain_type"], d["bbox"]))` per Decision 5 (the Review-caught determinism fix), since `connected_components`'s internal `set` iteration order is not a documented contract.
- **Step 7**: `.claude/agents/world-render-reviewer.md` is a new subagent, structurally modeled on `simulation-analyst.md` (Data Sources / Review Dimensions / Severity Classification / Output), with zero Mechanics Bible citations and the prompt-compliance instruction to read the Tier 1 digest first and only `Read` the annotated image when `escalate` is `True`.
- **Step 8**: Re-ran `grep -n "^- id: INFRA-3" docs/parity_ledger/infrastructure.yaml | tail` before appending — confirmed `INFRA-374` was still the last entry, so `INFRA-375` was free, exactly as plan.md predicted. Appended verbatim.
- **Step 9**: Ran `git status`/`git diff` on `docs/engine/contracts/regression_and_verification.md` before editing — confirmed no concurrent session had touched it since plan-write time. Extended §1 Captured Artifacts (item 4) and §4 Determinism Check with the two targeted additions per plan.md.

One test-construction issue found and fixed during implementation (not a plan deviation, an implementation detail): the first draft of `test_annotated_renderer_produces_valid_png_and_matches_plain_terrain_palette` sampled a terrain pixel at grid position (0,0), which coincides with the fixture's "dead" entity (`TEST_DEAD`, `combat.alive=False`) — `render_annotated()` (like the prototype it was ported from) draws every `lifecycle.active` entity in one color regardless of `combat.alive`, so that pixel was entity-colored, not terrain-colored, and the test failed. Fixed by sampling tile (3,0) instead, which has no entity overlap. Also added the actual `@pytest.mark.regression` marker (present in `pyproject.toml` but, on inspection, not actually applied to the sibling `test_render_core.py::test_render_golden_hash_...` test it mirrors) to both new golden-hash tests, since AC #5 and the ticket's own verify command (`pytest ... -m regression`) require it to be genuinely selectable by that marker.

## Test Summary

All three required commands pass:
- `PYTHONPATH=. pytest tests/unit/rendering/ tests/architecture/test_rendering_zero_new_dependency_guard.py -v -m "not slow"` — 94 passed (all pre-existing rendering-sibling tests plus all new tests for this ticket; zero regressions in `render.py`/`incremental.py`/the four sibling metric modules/`grading.py`).
- `PYTHONPATH=. pytest tests/unit/rendering/ -m regression -v` — 2 passed (`test_annotated_renderer_golden_hash_bit_identical_across_three_independent_runs`, `test_tier1_digest_golden_hash_field_identical_across_three_independent_runs`).
- `PYTHONPATH=. pytest tests/docs/test_doc_integrity.py -q -m "not slow"` — 10 passed, 1 skipped (frontmatter/schema check on the parity ledger and docs additions).

## Files Changed

- `src/rendering/render_annotated.py` (new)
- `src/rendering/review_pipeline.py` (new)
- `tests/unit/rendering/test_render_annotated.py` (new)
- `tests/unit/rendering/test_review_pipeline.py` (new)
- `.claude/agents/world-render-reviewer.md` (new)
- `docs/parity_ledger/infrastructure.yaml` (appended `INFRA-375`)
- `docs/engine/contracts/regression_and_verification.md` (extended §1 and §4)
- `docs/ai/agents.md` (Document-Update phase: added the new `world-render-reviewer` subagent roster entry, a real gap this ticket's own Investigate phase didn't flag since it's the batch's first ticket introducing a new `.claude/agents/*.md` file)
- `tickets/inprogress/TCK-20260821-VISUAL-AGENT-REVIEW.md` (this file — status/AC/notes updated)

Not modified by this run (already existed from prior Investigate/Plan phases, read-only reference during Implement): `staging_artifacts/TCK-20260821-VISUAL-AGENT-REVIEW/investigation.md`, `staging_artifacts/TCK-20260821-VISUAL-AGENT-REVIEW/plan.md`, `staging_artifacts/TCK-20260821-VISUAL-AGENT-REVIEW/test_plan.md`.

## Completion Summary

Implemented the Tier 0 (pure data) -> Tier 1 (JSON digest) -> Tier 2 (annotated image, escalation-only) agent-review pipeline: `src/rendering/render_annotated.py` (gridlined/coordinate-labeled renderer, stdlib-only, reusing `render.py`'s palette) and `src/rendering/review_pipeline.py` (`should_escalate`, `Tier1Digest`/`digest_to_json`, `run_tier0_tier1_pipeline`), plus the new `.claude/agents/world-render-reviewer.md` subagent. The annotated PNG is written to disk only when `should_escalate(...)` is `True`, making "zero image exists to read in the non-escalating case" a structural property, not just an agent-prompt convention. All 5 acceptance criteria are satisfied and covered by new tests, the parity ledger entry `INFRA-375` was added, and `docs/engine/contracts/regression_and_verification.md` was extended with the annotated-render artifact note and the Tier 1 digest determinism paragraph. No change to `render.py`, `incremental.py`, or any `src.simulation_quality` code.

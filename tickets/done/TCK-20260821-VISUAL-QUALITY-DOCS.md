---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260821-VISUAL-QUALITY-DOCS
phase: open
date: 2026-08-21
tags: [documentation, visualization, simulation-quality]
---

# TCK-20260821-VISUAL-QUALITY-DOCS

## Title
Documentation deliverables for the visual-quality system

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Two docs deliverables mirroring SimQ's precedent exactly: a new docs/visual_quality/ subfolder (naming TBD) mirroring docs/simulation_quality/'s shape (scoring contract, current-state doc, calibration/audit-workflow doc), and a new docs/audits/ periodic dimension entry — confirmed next number D26 at investigation time (D25 claimed same-day by an unrelated ticket) — mirroring D20_simq_integration.md's relationship to docs/simulation_quality/.

## Scope
- Create docs/visual_quality/ subfolder with files mirroring quality_scoring_contract.md, current_state.md, and audit_workflow.md's shapes/headers/frontmatter
- Create docs/audits/D26_<slug>.md following D20_simq_integration.md's Dimension Profile table + Related dimensions + Findings Summary format
- Re-verify D26 is still the correct next available number at actual implementation time (already re-confirmed twice during proposal/investigation, but this is a shared, actively-changing repo)
- Decide whether to also fix docs/audits/audit_dimensions.md's already-stale master index (missing D19/D21-D25) or follow the stale precedent
- Use only registry-allowlisted layer/tags (rendering/visualization already registered 2026-08-20)

## Out of Scope
- Documenting speculative/undesigned behavior — this ticket documents the grade-scorer ticket's REAL implemented contract, so it must be sequenced after that ticket (and, per epic ordering, after the calibration and agent-review tickets too)
- Adding docs/visual_quality/ to tests/docs/test_doc_path_existence.py's currently-scoped coverage (worth deciding, not required by this ticket)

## Acceptance Criteria
- [x] docs/visual_quality/ subfolder exists with >=3 files mirroring quality_scoring_contract.md/current_state.md/audit_workflow.md's shapes, each passing tools/validate_frontmatter.py
- [x] docs/audits/D26_<slug>.md is created following D20's Dimension Profile table format, with D26 re-confirmed as the correct next number at implementation time (not just trusted from prior investigation)
- [x] All new docs use only registry-allowlisted layer/tags
- [x] docs/REGISTRY.yaml regeneration at ticket close correctly picks up the new docs

## Related Tickets
- TCK-20260821-VISUAL-GRADE-SCORER
- TCK-20260821-VISUAL-QUALITY-CALIBRATION
- TCK-20260821-VISUAL-AGENT-REVIEW
- TCK-20260820-EPIC-WORLD-RENDERING-CORE

## Related Docs
- docs/simulation_quality/quality_scoring_contract.md
- docs/simulation_quality/current_state.md
- docs/simulation_quality/audit_workflow.md
- docs/audits/D20_simq_integration.md
- docs/audits/audit_dimensions.md
- docs/plans/world_rendering/idea_world_render_validation.md
- docs/plans/world_rendering/idea_world_rendering_core.md
- docs/plans/world_rendering_core_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
None.

## Assumptions / Open Questions
- D26 was independently re-verified twice already (proposal + investigation) but must be checked again at actual implementation time since this is a shared, actively-changing repo
- Whether D26 should also repair audit_dimensions.md's stale master index or follow the existing stale precedent is an open question, not resolved here
- docs/visual_quality/ naming is explicitly TBD
- simulation-quality: this ticket documents a SimQ-sibling system (not a SimQ-subsystem change itself), tagged for topical adjacency since it mirrors SimQ's own doc precedent

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260821-VISUAL-QUALITY-DOCS/plan.md`'s 7 steps,
no deviations.

- **Step 1** — re-ran `ls docs/audits/D*.md | sort -V` myself at implementation time (2026-08-23).
  D25 (`D25_engine_docs_drift.md`) confirmed still the max; D26 confirmed free.
- **Step 2** — created `docs/visual_quality/scoring_contract.md`: 7 numbered sections (Purpose &
  Scope, Architectural Position, The Four Metric Families, Grade Model, Escalation Pipeline,
  Testing Contract, Non-Goals). All three numeric anchors (density CV `0.6478017242079448` /
  `0.6782405727873148`, TVD `0.23161981243456373`, grade ladder `S=2.0/A=0.5/B=0.0/C=-0.5/D=-1.0`)
  copied verbatim from plan.md/investigation.md, cross-checked against
  `config/rendering/grade_thresholds.toml` and `src/rendering/density.py`/`variants.py` docstrings
  during writing — not recomputed.
- **Step 3** — created `docs/visual_quality/current_state.md`: single `## 2026-08-23 —` dated
  entry. States plainly that the metric/grading mechanism is real and finished, while the
  `grade_thresholds.toml` healthy-band *values* remain illustrative — quoting the config file's own
  "Illustrative values only, NOT calibrated" comment verbatim, and stating that no
  `config/rendering/calibration_report_*.json` exists on disk and `compute_trail_activity` has zero
  calibration evidence. No sentence implies the threshold values themselves are calibrated.
- **Step 4** — created `docs/visual_quality/audit_workflow.md`: 5 sections documenting only the two
  real entry points (`tools/calibrate_rendering.py run`/`aggregate`, and dispatching
  `world-render-reviewer` over a `Tier1Digest` from `run_tier0_tier1_pipeline`). Explicitly states
  no formal `/visual-quality-audit` workflow file exists, unlike SimQ's real `simq-audit.js`.
- **Step 5** — created `docs/audits/D26_visual_quality_integration.md`: Dimension Profile table (7
  rows), Related dimensions table (D20/D10/D17), Findings Summary table (F1/F2/F3). Impact=3/5 and
  Interest=3/5 are my own judgment calls made after reading `docs/audits/audit_dimensions.md:52-71`'s
  rubric (Impact: "moderate contribution... absence noticeable but manageable" fits, since the
  rendering system is an explicitly non-authoritative, read-only QA layer, not a prerequisite for a
  core simulation system; Interest: "useful, standard engineering concern" fits, since the Tier
  0/1/2 escalation pattern is sensible but mirrors an existing SimQ precedent rather than being
  novel). Priority computed as 3+3=6, not independently chosen. F3 discloses
  `audit_dimensions.md`'s staleness (missing D19/D21-D25, pre-existing D20 duplicate) without
  fixing it, per plan.md Decision 3.
- **Step 6** — ran `make docs-registry` (exit 0). Regenerated `docs/REGISTRY.yaml` contains exactly
  4 new entries matching `docs/visual_quality/\|docs/audits/D26_`
  (`grep -c` = 4). `git diff docs/REGISTRY.yaml` shows only the routine `# Generated:` timestamp
  line changed plus the 4 new entries added — no pre-existing entry was dropped or altered. Cross-
  checked `layer_registry.py list` (`world` present) and `tag_registry.py list`
  (`rendering`/`visualization`/`simulation-quality`/`documentation` all present, all pre-registered
  2026-07-06/2026-08-20, none newly registered by this ticket).
- **Step 7** — ran all three scoped pytest commands from test_plan.md using `.venv/bin/python3 -m
  pytest` (bare `python3` lacks `pydantic` in this sandbox, a known local-environment gap unrelated
  to this ticket's changes — `tools/validate_frontmatter.py` and `tools/generate_registry.py`
  themselves don't need it and ran fine under bare `python3`). All three commands passed; see Test
  Summary below.

No deviations from plan.md — no "Deviations" section added to plan.md, since none was needed.

## Test Summary

All three scoped pytest commands from `test_plan.md`, run via `.venv/bin/python3 -m pytest`:

1. `pytest tests/docs/ -m "not slow and not extra_slow"` → **45 passed, 1 skipped, 1 xfailed**.
   The 1 xfailed is `tests/docs/test_doc_path_existence.py`'s pre-existing, unchanged `strict=True`
   xfail (its `SCOPE_DIRS` does not include `docs/visual_quality/` or `docs/audits/`, so it could
   not regress from this ticket's changes either way). `tests/docs/test_doc_integrity.py` stayed
   green, confirming this ticket's changes didn't disturb the fixed-manifest doc-integrity checks.
2. `pytest tests/unit/rendering/ tests/architecture/test_rendering_zero_new_dependency_guard.py
   tests/tools/test_calibrate_rendering.py -m "not slow and not extra_slow"` → **105 passed**. The
   rendering system this ticket documents is confirmed still green.
3. `pytest tests/tools/test_validate_frontmatter.py tests/tools/test_generate_registry.py
   tests/tools/test_layer_registry.py tests/tools/test_tag_registry.py -m "not slow and not
   extra_slow"` → **184 passed**. The frontmatter/registry tooling this ticket's Steps 2-6 depend
   on is confirmed unaffected.

Also ran, non-pytest, per-file: `python3 tools/validate_frontmatter.py <path>` for each of the 4
new files individually (the script only accepts one path argument at a time) — all 4 exited 0
("OK: 1 file(s) checked — no violations").

## Files Changed

- `docs/visual_quality/scoring_contract.md` (new)
- `docs/visual_quality/current_state.md` (new)
- `docs/visual_quality/audit_workflow.md` (new)
- `docs/audits/D26_visual_quality_integration.md` (new)
- `docs/plans/world_rendering/idea_world_render_validation.md` (Document-Update phase: a real
  gap found and fixed — every one of the 8 prior sibling tickets deferred this doc's update
  specifically to this final ticket, but this ticket's own Investigate/Plan phases never
  addressed it. Flipped `status: idea -> historical`, `maturity: idea -> shipped`, and added a
  new dated blockquote pointing to the real `docs/visual_quality/scoring_contract.md`,
  `current_state.md`, `audit_workflow.md`, and `docs/audits/D26_visual_quality_integration.md`
  as the authoritative replacement. No body content rewritten; not moved to
  `docs/plans/archive/` per `docs/architecture/doc_updater_agent.md`'s rule that archival is a
  separate, whole-epic human decision, not a per-ticket action.)
- `docs/REGISTRY.yaml` (regenerated via `make docs-registry`, not hand-edited — re-run after
  the idea-doc edit above so its registry entry reflects the corrected `status`)
- `tickets/inprogress/TCK-20260821-VISUAL-QUALITY-DOCS.md` (this file — Status, Acceptance
  Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary)
- `staging_artifacts/TCK-20260821-VISUAL-QUALITY-DOCS/investigation.md` (pre-existing, created in
  this run's own Investigate phase before Implement started — not modified further by Implement)
- `staging_artifacts/TCK-20260821-VISUAL-QUALITY-DOCS/plan.md` (pre-existing, created in this run's
  own Plan phase before Implement started — not modified further by Implement)
- `staging_artifacts/TCK-20260821-VISUAL-QUALITY-DOCS/test_plan.md` (pre-existing, created in this
  run's own Plan phase before Implement started — not modified further by Implement)

## Completion Summary

Implemented the final, 9th ticket of the world-rendering-core batch: four new documentation files
describing the shipped, real visual-quality (rendering QA) system. Created
`docs/visual_quality/scoring_contract.md` (the four metric families, grade model, escalation
pipeline), `docs/visual_quality/current_state.md` (stating the metric/grading mechanism is complete
and tested, while the healthy-band threshold *values* in `config/rendering/grade_thresholds.toml`
remain illustrative/uncalibrated — the load-bearing anti-drift fact this ticket exists to record),
`docs/visual_quality/audit_workflow.md` (the two real entry points: `tools/calibrate_rendering.py`
and dispatching `world-render-reviewer` over a `Tier1Digest`), and
`docs/audits/D26_visual_quality_integration.md` (the first audit-dimension entry for this system,
following D20's format, disclosing but not repairing `audit_dimensions.md`'s pre-existing
staleness). During Document-Update, a real gap the ticket's own Investigate/Plan phases missed
was found and fixed: `docs/plans/world_rendering/idea_world_render_validation.md` — the idea
doc every one of the 8 prior sibling tickets deferred updating specifically to this final
ticket — was flipped `status: idea -> historical`, `maturity: idea -> shipped`, with a new
blockquote pointing readers to the four real docs above as the authoritative replacement (body
content left untouched; not moved to `docs/plans/archive/`, per project convention that archival
is a separate, whole-epic decision). All five files pass `tools/validate_frontmatter.py`;
`docs/REGISTRY.yaml` was regenerated a second time, after this fix, and picks up all changes with
no unrelated entries dropped. All scope guards were respected — no edits to
`audit_dimensions.md`, `grade_thresholds.toml`, any `src/rendering/*.py`
file, `tools/calibrate_rendering.py`, `docs/simulation_quality/*.md`, `docs/audits/D20_*.md`, or
`test_doc_path_existence.py`'s `SCOPE_DIRS`; no new parity-ledger entry; no numeric anchor was
rounded or recomputed; no sentence claims the threshold values are calibrated.

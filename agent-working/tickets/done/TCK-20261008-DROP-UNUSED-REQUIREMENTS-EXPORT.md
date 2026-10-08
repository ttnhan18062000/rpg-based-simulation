---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT
phase: done
date: 2026-10-08
tags: [architecture, delivery]
---

# TCK-20261008-DROP-UNUSED-REQUIREMENTS-EXPORT

## Title
Delete the unused requirements.txt export and repoint what pinned it

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`requirements.txt` is a `uv export` that no installer consumes: every CI job runs `uv sync --locked`. uv recommends against keeping both a `uv.lock` and a `requirements.txt` (brief section 1 and 2). Filed from `docs/plans/codebase_health/repo_root_layout_ticket_brief.md` by codebase-planner (owner-approved 2026-10-08), sequence in `SEQUENCE.md`. Order: after A1 (independent; ordered after it only to keep one PR's edits to `test.yml` readable).

## Scope
- Delete `requirements.txt`
- Remove it from the PERF/MIG path regexes in `.github/workflows/test.yml` (make sure `pyproject.toml` and `uv.lock` are in them) and the pin in `tests/static/test_ci_narrow_path_filtered_jobs.py`
- Keep the intent of `tests/static/test_ci_requirements_no_ml_stack.py` (the ML stack never reaches CI installs) by asserting it on the default dependency groups of `pyproject.toml` / `uv.lock`; fix its stale `pip install -r` comment
- Update the export comments in `pyproject.toml` and the human docs that say to use `requirements.txt` (`agent_working_environment.md`, `migration_ci_lanes.md`, `performance_profiling.md`)

## Out of Scope
- `requirements-knowledge.txt` (proposed to agent-working in the batch A handoff, not ticketed)
- Any file under `src/`
- Tests that pin CI or the Makefile may be edited under owner decision 8.11, with a notice to testing in the batch PR's handoff

## Acceptance Criteria
- [x] No live reference to `requirements.txt` outside history (done tickets, stored artifacts, monitoring data)
- [x] `tests/static` and `tests/tools` pass
- [x] `make knowledge-index-update` is run, or its skip is noted
- [x] `git diff --stat` lists no path under `src/`
- [x] The testing notice (owner decision 8.11) is in the batch PR's handoff

## Related Tickets
- TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK
- TCK-20261008-NOJEKYLL-TO-DOCS-SITE-STATIC
- TCK-20261008-OPS-FILES-INTO-DOCKER-DIR
- TCK-20261008-DROP-MAKE-BAT
- TCK-20261008-GRAPH-HTML-JS-DEPS-BESIDE-TOOL
- TCK-20261008-REPO-ROOT-ALLOWLIST-GUARD

## Related Docs
- docs/plans/codebase_health/repo_root_layout_ticket_brief.md
- docs/guidelines/repo_tooling_layout.md

## Related Stored Artifacts
None.

## Related Code Areas
- requirements.txt
- .github/workflows/test.yml
- tests/static/
- pyproject.toml
- docs/guidelines/

## Assumptions / Open Questions
- Evidence and the owner's decisions are in the brief (sections 1 to 5); no open question beyond what the brief lists.

## Implementation Notes
- Deleted `requirements.txt`. Consumers found beyond the brief's list and repointed: `tools/test_architecture/scenario_lane_paths.py` (the scenario-lane path regex) and its test `tests/unit/tools/test_scenario_lane_paths.py` (the `requirements.txt` trigger case now uses `uv.lock`, which stays in the regex), `tests/static/test_ci_step_summary_reporting.py` (read `requirements.txt` for banned entries; now reads `pyproject.toml`), `tests/tools/test_evidence_cache_identity_contract.py` (candidate list), `tests/tools/test_delivery_ci_triage_classifier.py` (inline sample workflow text), and comments in `config/rendering/grade_thresholds.toml`, `tests/codebase/test_code_health_impact.py`, `tests/tools/test_knowledge_search.py`, `requirements-knowledge.txt`.
- `.github/workflows/test.yml`: `requirements\.txt$` removed from `PERF_RE` and `MIG_RE`; `pyproject.toml` and `uv.lock` were already in both. `test_ci_narrow_path_filtered_jobs.py` no longer expects `requirements.txt` to match.
- `tests/static/test_ci_requirements_no_ml_stack.py` keeps its intent: `torch`, `sentence-transformers`, `sqlite-vec`, `rank-bm25` must not reach the default install. It now walks `uv.lock` from the roots a plain `uv sync` installs (project dependencies plus `[tool.uv] default-groups`) and asserts none of the four is in the closure; the stale `pip install -r` comment is gone. (They are in `uv.lock` behind the `knowledge` / `search-mcp` extras, so asserting on the whole lock would be wrong.)
- Docs: `agent_working_environment.md` (the pip-install row now shows an on-demand `uv export ... | uv pip install -r -`; first-time setup, "Changing a dependency" and the 3.13 venv bootstrap no longer mention the export), `performance_profiling.md`, `migration_ci_lanes.md`, `cache_migration_plan.md`, and `pyproject.toml` comments.
- Impact for agent-working: `.venv-knowledge` and other worktrees used `pip install -r requirements.txt`. The guide now gives the on-demand export command; this is raised in the batch A handoff to agent-working.
- Left as history (not edited): `docs/plans/**`, `docs/archive/**`, `experiments/**`, `docs/ai/monitoring_writer_decision.md`, `docs/parity_ledger/infrastructure.yaml`, `agent-working/handover-transit/**`, and open `todos/` tickets owned by others (`embedding-latent-cognition/*`; also the in-progress `TCK-20261008-PERF-LANE-PATH-GATE-MISSES-SIMULATION-SRC-DIRS` mentions `requirements.txt` as a trigger and edits the same `test.yml` regex region, so its owner may need to rebase).

## Test Summary
- `tests/static` and `tests/unit/tools/test_scenario_lane_paths.py`: 140 passed.
- 42 test files referencing the touched files (`tests/tools`, `tests/unit/tools`, `tests/codebase`, `tests/architecture`, `tests/docs`): all pass with the known local 60 s budget failure `tests/codebase/test_codebase_health_snapshot.py::test_make_target_runs_successfully_end_to_end` deselected (identical on clean main; tracked by `TCK-20261005-CODE-HEALTH-MAKE-TARGET-TESTS-LOCAL-TIMEOUT`).
- A full `tests/tools` run was stopped at `test_entity_lifecycle_score.py::TestRealIntegration::...800t...` hitting the 60 s test limit, unrelated to this change; the scoped set above replaces it.
- `make knowledge-index-update` was not run: it is killed by its timeout under the 2 GB cap on this machine (twice already).

## Files Changed
- deleted: `requirements.txt`
- `.github/workflows/test.yml`, `tools/test_architecture/scenario_lane_paths.py`, `pyproject.toml`, `requirements-knowledge.txt`, `config/rendering/grade_thresholds.toml`
- tests: `tests/static/test_ci_requirements_no_ml_stack.py` (rewritten), `tests/static/test_ci_narrow_path_filtered_jobs.py`, `tests/static/test_ci_step_summary_reporting.py`, `tests/unit/tools/test_scenario_lane_paths.py`, `tests/tools/test_evidence_cache_identity_contract.py`, `tests/tools/test_delivery_ci_triage_classifier.py`, `tests/tools/test_knowledge_search.py`, `tests/codebase/test_code_health_impact.py`
- docs: `docs/guidelines/agent_working_environment.md`, `docs/guides/performance_profiling.md`, `docs/testing/migration_ci_lanes.md`, `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md`

## Completion Summary
`requirements.txt` is gone and nothing live reads it; the ML-stack guard now checks the lock's default install closure. All acceptance criteria met except the knowledge index refresh, which was skipped and noted (it times out under the cap). The remaining mentions are in history and other owners' open tickets (listed above).

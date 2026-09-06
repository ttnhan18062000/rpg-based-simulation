---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION
phase: done
date: 2026-09-04
tags: [ai, agent-monitoring, data-quality, documentation]
---

# TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION

## Title
Classify retention treatment for repo artifact classes outside monitoring shards

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
The already-shipped TCK-20260902/903-MONITORING-* epics cover only runs/events/tools.jsonl, leaving stored_artifacts/, tickets/done/, working_log.csv, graphify-out/, and knowledge-index/ unclassified for retention. This ticket classifies every artifact class using the 4-category taxonomy (Ephemeral/Run-scoped/Ticket-scoped/Long-lived-Institutional) in a committed doc. The source concern posed graphify-out/ and knowledge-index/ as 2 open questions to resolve with evidence or explicitly defer — investigation found both are in fact resolvable now with concrete evidence already on hand (gitignore lines, zero CI references, zero tracked files, existing documentation and rebuild automation for each), so this ticket resolves them directly rather than leaving them open.

## Scope
- Create a new committed doc with a retention-classification table covering all 8 artifact classes: agent-monitoring/data/, stored_artifacts/, tickets/done/, retro/RETRO-*.md, working_log.csv, graphify-out/, knowledge-index/, .claude/current_run — each row assigned a category from the 4-way taxonomy plus a recommended treatment
- Resolve the graphify-out/ question with cited evidence (.gitignore lines 260-261, zero .github/workflows/*.yml references, zero git-tracked files, tests/tools/test_code_health_impact.py's documentation, prior TCK-20260818-HOTFIX-GRAPHIFY-CLI-TEST-MISSING-INDEX-SKIP finding) and a resolved recommendation
- Resolve the knowledge-index/ question with cited evidence (.gitignore line 264, Makefile:331's 'developer env only — not CI' comment, docs/guidelines/agent_working_environment.md's existing table, tools/hooks/post-commit-reindex.sh) and a resolved recommendation
- Decide the new doc's location/filename during Plan (e.g. docs/observability/ or docs/guidelines/) — not specified in the source material
- Reference this batch's TCK-20260904-WORKING-LOG-CSV-PARSER by ID for working_log.csv's row rather than duplicating or blocking on it

## Out of Scope
- Actually implementing the working_log.csv parser/cleanup fix — tracked separately
- M3's ownership/lifecycle documentation deliverable — separate milestone with its own ticket, do not conflate despite sharing a References/Out-of-Scope boundary in the source epic doc
- Rewriting docs/guidelines/agent_working_environment.md's existing table to add a missing graphify-out/ row unless the implementer chooses to do so in this ticket; if deferred, must be flagged explicitly as a named follow-up rather than silently left

## Acceptance Criteria
- [x] New committed doc contains a retention-classification table covering all 8 artifact classes (agent-monitoring/data/, stored_artifacts/, tickets/done/, retro/RETRO-*.md, working_log.csv, graphify-out/, knowledge-index/, .claude/current_run), each with a category from the 4-way taxonomy and a recommended treatment
- [x] graphify-out/ row cites concrete evidence (gitignore line, zero CI references, zero tracked files) and a resolved recommendation
- [x] knowledge-index/ row cites concrete evidence (gitignore line, Makefile comment, existing rebuild automation) and a resolved recommendation
- [x] If either question is left unresolved instead of resolved, the doc names a specific follow-up owner/role and trigger (N/A — both questions are resolved directly in this ticket, not left open; verified by test asserting absence of "open question" phrasing)

## Related Tickets
- TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC
- TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC
- TCK-20260818-HOTFIX-GRAPHIFY-CLI-TEST-MISSING-INDEX-SKIP
- TCK-20260816-HOTFIX-KGMCP-LOCAL-DATA-BOOTSTRAP-DOCS

## Related Docs
- docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md
- docs/guidelines/agent_working_environment.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md
- docs/guidelines/agent_working_environment.md
- .gitignore
- Makefile
- tools/hooks/post-commit-reindex.sh
- tests/tools/test_code_health_impact.py
- tickets/done/agent-monitoring-weekly-sharding/TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC.md
- tickets/done/agent-monitoring-unified-weekly-data/TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC.md
- tickets/done/TCK-20260818-HOTFIX-GRAPHIFY-CLI-TEST-MISSING-INDEX-SKIP.md

## Assumptions / Open Questions
- The new doc's exact location/filename is undecided and must be chosen during Plan
- working_log.csv's row should reference TCK-20260904-WORKING-LOG-CSV-PARSER by ID rather than duplicate or gate on it, since this ticket is itself gated on nothing
- M3 (ownership/lifecycle doc) is a separate milestone that shares a References/Out-of-Scope boundary with this ticket in the source epic doc — must not be conflated

## Implementation Notes
Implemented exactly per `staging_artifacts/TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION/plan.md`, all 5 steps, no deviations:

1. Created `docs/guidelines/artifact_retention_classification.md` with the exact frontmatter (`status: active`, `layer: guidelines`, `authority: P1`, `audience: agent`, tags `[ai, agent-monitoring, data-quality, documentation]`) and body content the plan specified verbatim: the 4-category taxonomy (Ephemeral / Run-scoped / Ticket-scoped / Long-lived / Institutional), the 8-row retention-classification table, and the `graphify-out/`/`knowledge-index/` resolution sections with concrete evidence citations.
2. Created `tests/docs/test_artifact_retention_classification_doc.py` with the 3 test functions the plan specified, following `tests/docs/test_redaction_retention_policy_doc.py`'s static-assertion pattern (read as text via `Path.read_text()`, assert literal substrings, never import/execute the doc).
3. Edited `docs/guidelines/agent_working_environment.md`: dropped the `(Knowledge Gateway MCP)` parenthetical from the "Other Local, Gitignored Caches" header, rewrote the intro paragraph from "one of three"/all-MCP framing to "one of four" with the `graphify` code-graph index called out as the non-MCP fourth cache, and added the new `graphify-out/graph.json` table row after the existing `retrieval_cache.db` row. No other part of the file touched.
4. Edited `docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md`: appended "— SHIPPED" to the M2 heading, inserted the shipped-note paragraph pointing to this ticket and the new doc, updated the M2 acceptance-signal bullet to "met" with the concrete doc reference, and added a References bullet for the new doc. M1 and M3 sections left byte-identical.
5. Ran the full verification pass: the 3 new tests pass; `tests/docs/test_redaction_retention_policy_doc.py` still passes unmodified (7/7); `python3 tools/validate_frontmatter.py` reports zero violations on the new doc; the broader scoped pytest run (`tests/docs/`, frontmatter/tag/layer/registry/code-health-impact test files) passed after regenerating `docs/REGISTRY.yaml` via `make knowledge-index-update && make docs-registry` (the new doc's addition was the only drift, expected and now resolved); manual re-verification confirmed every cited `.gitignore`/`Makefile`/`test_code_health_impact.py` line and the working_log.csv parser ticket's still-open status all match the live repo.

No architectural issues encountered — this is pure documentation, no `src/`/`tools/` behavior changes, no new tag/layer registrations (all four tags and the `guidelines` layer were already registered).

## Test Summary
- `pytest tests/docs/test_artifact_retention_classification_doc.py -v` — 3/3 passed (new tests).
- `pytest tests/docs/test_redaction_retention_policy_doc.py -v` — 7/7 passed, unmodified (regression guard).
- `python3 tools/validate_frontmatter.py docs/guidelines/artifact_retention_classification.md` — OK, zero violations.
- `pytest tests/docs/ tests/tools/test_validate_frontmatter.py tests/tools/test_tag_registry.py tests/tools/test_layer_registry.py tests/tools/test_generate_registry.py tests/tools/test_registry_query.py tests/tools/test_code_health_impact.py -v` — 272 passed, 1 skipped (graphify-CLI-dependent, expected), 1 xfailed, after regenerating `docs/REGISTRY.yaml` (the one initial failure, `test_check_flag_detects_no_drift_against_real_registry`, was expected drift from the new doc's addition, resolved by `make knowledge-index-update && make docs-registry`).
- Manual citation re-verification: confirmed `.gitignore:260-261` (`graphify-out/*`, `src/graphify-out/`) and `.gitignore:264` (`knowledge-index/`); confirmed `Makefile:331` `# developer env only — not CI` immediately precedes the `knowledge-index:` target; confirmed `tests/tools/test_code_health_impact.py`'s `_requires_graphify` skip marker and comment unmodified; confirmed zero `git ls-files graphify-out/` results and zero `grep -rn "graphify-out" .github/workflows/` hits; confirmed `tickets/todos/ai-first-hardening-h1-h2-followon/TCK-20260904-WORKING-LOG-CSV-PARSER.md` still exists outside `tickets/done/` (so the new doc's "not yet implemented" phrasing remains accurate).

## Files Changed
- `docs/guidelines/artifact_retention_classification.md` (new)
- `tests/docs/test_artifact_retention_classification_doc.py` (new)
- `docs/guidelines/agent_working_environment.md` (edited — Other Local, Gitignored Caches section)
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md` (edited — M2 section)
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/bucket_c_future_options.md` (edited by Document-Update phase — added an "Update:" note resolving a stale "still open" cross-reference to the graphify-out/knowledge-index git-tracking question, now that M2 has resolved both)
- `docs/REGISTRY.yaml` (regenerated)
- `staging_artifacts/TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION/investigation.md` (created during this run's Investigate phase)
- `staging_artifacts/TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION/plan.md` (created/revised during this run's Plan phase, through 2 architecture-review fix cycles)
- `staging_artifacts/TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION/test_plan.md` (created during this run's Investigate phase)
- `tickets/inprogress/TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION.md` (this file)
- `agent-monitoring/data/2026-W36/tools.jsonl` (auto-updated by monitoring hooks)

## Completion Summary
Created `docs/guidelines/artifact_retention_classification.md`, a committed doc classifying all 8 remaining repo artifact classes (outside the already-shipped agent-monitoring weekly shards) against a 4-category retention taxonomy (Ephemeral / Run-scoped / Ticket-scoped / Long-lived-Institutional), resolving both the `graphify-out/` and `knowledge-index/` open questions from the source epic with concrete evidence citations rather than deferring them. Added a matching doc-structure test file (3 tests, all passing), added the previously-missing `graphify-out/graph.json` row to `agent_working_environment.md`'s local-cache table with corrected "one of four" framing, and marked M2 of `telemetry_retention_epic.md` as shipped with a cross-reference to this ticket and the new doc. Pure documentation change — no runtime behavior changed, no new tag/layer registrations.

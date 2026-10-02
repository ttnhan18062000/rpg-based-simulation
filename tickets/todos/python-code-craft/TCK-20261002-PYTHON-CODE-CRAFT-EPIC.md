---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261002-PYTHON-CODE-CRAFT-EPIC
phase: open
date: 2026-10-02
tags: [planning, tracking]
---

# TCK-20261002-PYTHON-CODE-CRAFT-EPIC

## Title
Epic: Python Code Craft Foundation (tracks M1 to M3)

## Status
OPEN

## Tier
epic

## Type
chore

## Priority
P1

## Request Summary
A scope-only epic-tier ticket that tracks the three foundation milestones of the Python code craft roadmap (M1 code standard document, M2 uv as the single dependency source, M3 measure and baseline) as its children and cites the binding plan, docs/plans/codebase_health/python_code_craft_roadmap.md (rev 2, approved 2026-10-02). It implements nothing itself and closes when M1, M2 and M3 are done. It carries the constraints that apply to every child: no file under src/ is modified (no autofix, no reformat, no inline suppression comments such as # noqa or # type: ignore; existing violations are held in an external baseline), no simulation behaviour change, no tests/ change beyond tests for the new tooling, governing files and the agent-working domain are not edited, new tooling goes in a tools/code_health/ subpackage, and existing work is reused per roadmap Section 4. This matters because many sessions are working in src/ and the owner has frozen it for this plan.

## Scope
- Create the epic ticket with '## Tier' = epic, citing docs/plans/codebase_health/python_code_craft_roadmap.md (rev 2, approved 2026-10-02) as the binding plan under Related Docs
- List the child tickets under Related Tickets: M1 TCK-20261002-PYTHON-CODE-STANDARD-DOC; M2 TCK-20261002-UV-DECLARE-AND-LOCK and TCK-20261002-UV-FIRST-CI-JOB; M3 TCK-20261002-CODE-HEALTH-TOOL-CONFIG, TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY and TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS
- State the dependency order: M3 tickets depend on M2 (uv) for installing the tools; UV-FIRST-CI-JOB depends on UV-DECLARE-AND-LOCK; the snapshot ticket comes last in M3
- Record the shared constraints every child must carry: git diff --stat shows no src/ path; no autofix, reformat or inline suppression comments; no simulation behaviour change; tests/ changes limited to tests for new tooling; CLAUDE.md, .claude/settings.json, hooks, .claude/agents/, .claude/workflows/ and .claude/skills/ not edited; new tooling in tools/code_health/ per docs/guidelines/repo_tooling_layout.md; reuse rules from roadmap Section 4
- State the closing condition as 'all M1, M2 and M3 child tickets are in tickets/done/'

### Child tickets and dependency order

| Milestone | Child ticket | Depends on |
|---|---|---|
| M1 | TCK-20261002-PYTHON-CODE-STANDARD-DOC | none |
| M2 | TCK-20261002-UV-DECLARE-AND-LOCK | none |
| M2 | TCK-20261002-UV-FIRST-CI-JOB | TCK-20261002-UV-DECLARE-AND-LOCK |
| M2 | TCK-20261002-UV-REMAINING-CI-JOBS | TCK-20261002-UV-FIRST-CI-JOB closed with a green PR run (added by hand 2026-10-02 after the owner decision below) |
| M3 | TCK-20261002-CODE-HEALTH-TOOL-CONFIG | M2 (uv installs the tools) |
| M3 | TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY | M2 (uv installs the tools) |
| M3 | TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS | M2; last in M3 |

### Shared constraints every child must carry

- `git diff --stat` shows no `src/` path.
- No autofix, no reformat, no inline suppression comments (such as `# noqa` or `# type: ignore`); existing violations are held in an external baseline.
- No simulation behaviour change.
- `tests/` changes are limited to tests for the new tooling, **with one exception by owner decision 2026-10-02 (roadmap decision 8.11):** the existing tests that pin CI and the Makefile (`tests/static/test_ci_step_summary_reporting.py`, `tests/tools/test_dashboard_makefile_targets.py` and any sibling that pins an install line) may be edited by the uv tickets, changing only what they pin. Where a child ticket still says "no edit to any existing test file", this exception applies to the uv CI tickets only.
- `CLAUDE.md`, `.claude/settings.json`, hooks, `.claude/agents/`, `.claude/workflows/` and `.claude/skills/` are not edited.
- New tooling goes in `tools/code_health/` per docs/guidelines/repo_tooling_layout.md.
- Existing work is reused per the reuse rules in roadmap Section 4.

### Closing condition

All M1, M2 and M3 child tickets are in tickets/done/.

## Out of Scope
- Roadmap milestone M4: CI gates, mypy blocking, prek (the mypy gate stays as pinned by INFRA-TYPE-001 and tests/static/test_typecheck_gate_configured.py)
- Roadmap milestone M5: package registry, ast-grep, import-linter
- Roadmap milestone M6: agent integration
- Roadmap milestone M7: refactor lane
- Any direct implementation: the epic changes no file under src/, tests/, tools/, .claude/ or CLAUDE.md
- A tools/ tidy ticket, a new dead-code detector, or re-filing TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS (roadmap Section 4)
- Renaming the worktree from rpg-code-craft to codebase (roadmap Section 5.1 follow-up)

## Acceptance Criteria
- [ ] The epic ticket has '## Tier' = epic, cites docs/plans/codebase_health/python_code_craft_roadmap.md (rev 2, approved 2026-10-02) under Related Docs, and lists every M1, M2 and M3 child ticket ID under Related Tickets; python3 tools/validate_frontmatter.py and tools/ticket_field_values.py accept it
- [ ] The epic's Out of Scope section names roadmap milestones M4 (CI gates, mypy blocking, prek), M5 (package registry, ast-grep, import-linter), M6 (agent integration) and M7 (refactor lane), and no child ticket in tickets/todos/python-code-craft/ delivers any of them
- [ ] The epic's own commits change no file outside tickets/ (plus the auto-generated docs/REGISTRY.yaml and agent-monitoring/ shards): git diff --stat against the branch point shows no src/, tests/, tools/, .claude/ or CLAUDE.md path
- [ ] Each child ticket listed by the epic carries an acceptance criterion that git diff --stat shows no src/ path, and a statement that CLAUDE.md, .claude/settings.json, hooks, .claude/agents/, .claude/workflows/ and .claude/skills/ are not edited
- [ ] The epic's closing condition is stated as 'all M1, M2 and M3 child tickets are in tickets/done/', and at close these deliverables exist: docs/guidelines/python_code_standard.md, a refreshed uv.lock with at least one CI job on uv sync, and tools/code_health/ plus registries/code_health_exceptions.jsonl
- [ ] docs/plans/codebase_health/python_code_craft_roadmap.md and python_code_craft_foundation_ticket_brief.md are tracked in git (committed with or before the epic ticket), so the cited binding plan resolves

## Related Tickets
Children (M1):
- TCK-20261002-PYTHON-CODE-STANDARD-DOC

Children (M2):
- TCK-20261002-UV-DECLARE-AND-LOCK
- TCK-20261002-UV-FIRST-CI-JOB
- TCK-20261002-UV-REMAINING-CI-JOBS

Children (M3):
- TCK-20261002-CODE-HEALTH-TOOL-CONFIG
- TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY
- TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS

Related (not children):
- TCK-20260817-CODEBASE-HEALTH-OBSERVATORY-TOOLING-EPIC
- TCK-20260817-ARCHITECTURE-BOUNDARY-HARDENING-EPIC
- TCK-20260623-TYPE-CHECKER
- TCK-20260702-CI-REQUIREMENTS-SPLIT
- TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS
- TCK-20260929-RETIRE-SCRIPTS-DIR
- TCK-20260925-STATIC-CHECK-HARDCODED-VENV-INTERPRETER-PATH
- TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md (rev 2, approved 2026-10-02; the binding plan)
- docs/plans/codebase_health/python_code_craft_foundation_ticket_brief.md
- docs/guidelines/repo_tooling_layout.md
- docs/guidelines/subsystem_ownership_lifecycle.md
- docs/guidelines/agent_working_environment.md
- docs/guidelines/design_patterns.md
- docs/parity_ledger/infrastructure.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_foundation_ticket_brief.md
- docs/guidelines/repo_tooling_layout.md
- docs/plans/plans_tracking.md
- tools/ticket_field_values.py
- tools/codebase_health_snapshot.py
- pyproject.toml
- uv.lock
- .github/workflows/test.yml
- Makefile

## Assumptions / Open Questions
- Layer: no 'codebase' or 'infrastructure' layer exists in registries/layer_registry.jsonl; the roadmap and brief use layer: architecture, so the epic and children use an existing registered layer rather than registering a new append-only one unless the owner decides otherwise
- No code-health tag is registered; registering one is append-only and is left to the owner, so only already-registered tags are used
- M2 and M3 are split into two and three tickets respectively, as the brief anticipated; epic closure is all-or-nothing (roadmap Section 5.6), so all children must close (seven, after the addition below)
- Migration of the remaining CI jobs to uv was first left out, blocked on an owner decision about tests that pin those jobs verbatim. The owner allowed those test edits on 2026-10-02, so it is now the child TCK-20261002-UV-REMAINING-CI-JOBS, written by hand after the scoping run
- Roadmap Section 5.1 says only the implementer seat runs git; who commits these tickets follows that convention
- Search tooling was degraded during investigation (graphify graph and local knowledge index absent); no duplicate was found via search_docs, REGISTRY.yaml, working_log.csv and the open-ticket scanner
- Tag fit: `planning` is registered for plan/roadmap-tracking doc artifacts and `tracking` for index/tracking docs; both are used here for an epic ticket that tracks a roadmap and its child tickets, a near but not exact fit
- Post-merge step (from `TCK-20261002-PYTHON-CODE-STANDARD-DOC`): after this branch merges, run `make knowledge-index-update` in the main checkout. It was not run in the `rpg-code-craft` worktree, which has no `knowledge-index/`; the served index lives in the main checkout.

## Implementation Notes

### Shared test fixtures and patterns

## Test Summary

## Files Changed

## Completion Summary

---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY
phase: open
date: 2026-10-02
tags: []
---

# TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY

## Title
M3b: Code-health adapters, ratchet command and exceptions registry

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Freeze the existing codebase's craft debt in a baseline, with no src/ edits, so that only new or worsened violations fail. The author wants tools/code_health/ adapters that normalise each tool's JSON output, plus one ratchet command that fails only when a violation is new or worse than its baseline row, matching by file and symbol rather than line number so moved code does not resurface as new; registries/code_health_exceptions.jsonl with a CLI and validator modelled on tools/capability_envelope_baseline.py, seeded from a full scan with reviewed: false, where, unlike the tag and layer registries, rows are deleted when debt is paid; a make code-health entry point; and tests for the adapters, the ratchet and the registry validator. The duplication check must not re-file the pairs in TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS. The shared constraints apply: no src/ edits, no autofix or reformat or inline suppression comments, no simulation behaviour change, tests/ changes limited to tests for the new tooling, no edits to governing files or the agent-working domain.

## Scope
- Add one adapter per adopted tool under tools/code_health/ that normalises the tool's JSON output to a record with file, symbol (or null), tool, rule and value
- Define and document the match key for symbol-less findings (ruff rules without a symbol, jscpd clone pairs across two files) so matching never depends on line number
- Add the ratchet command: fail only on a violation with no baseline row or a measured value above its row's ceiling; report without failing rows whose violation has disappeared or improved
- Create registries/code_health_exceptions.jsonl with the roadmap Section 6.3 row fields (file, symbol, tool, rule, measured value or count, ceiling, added_date, reviewed, retiring ticket), seeded from a full scan with reviewed: false
- Add the registry CLI and validator modelled on tools/capability_envelope_baseline.py for CLI shape and the reviewed field, with row deletion supported
- State how complexipy is handled: its own native baseline file with the registry recording only its existence and size (roadmap Section 6.3), or an adapter
- Add a 'make code-health' target that runs every adopted tool plus the ratchet, in .PHONY
- Add tests for the adapters (from captured real-output fixtures), the ratchet and the registry validator
- Add a parity ledger entry in docs/parity_ledger/infrastructure.yaml and an ownership row in docs/guidelines/subsystem_ownership_lifecycle.md for the new registry and ratchet

## Out of Scope
- Wiring the ratchet into CI, prek hooks or any pipeline phase (M4; roadmap Sections 5.3, 7, 8.3)
- Tool configuration and the line-count script (TCK-20261002-CODE-HEALTH-TOOL-CONFIG)
- Snapshot metrics and the first snapshot (TCK-20261002-CODE-HEALTH-SNAPSHOT-METRICS)
- Paying down any baseline row: no src/ file is fixed, reformatted or annotated
- Creating tickets or new registry findings for the four class pairs in TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS
- Changing tools/capability_envelope_baseline.py or its registry
- Any file under src/, existing tests, CLAUDE.md, .claude/settings.json, hooks, .claude/agents/, .claude/workflows/, .claude/skills/

## Acceptance Criteria
- [ ] tools/code_health/ has one adapter per adopted tool; each adapter test feeds a captured JSON fixture of that tool's real output and asserts a normalised record with at least file, symbol (or null), tool, rule, value
- [ ] The ratchet command exits 0 when run against a baseline seeded from the same scan, exits non-zero when a fixture adds a violation with no baseline row, exits non-zero when a fixture raises a measured value above its row's ceiling, and exits 0 when the same (file, symbol, tool, rule) violation only changes line number
- [ ] The ratchet reports, and does not fail on, a baseline row whose violation has disappeared or improved; the registry CLI supports deleting a row and a test covers the delete
- [ ] registries/code_health_exceptions.jsonl exists, every seeded row has reviewed: false, and the validator rejects a row with a missing required field, a duplicate (file, symbol, tool, rule) key, or a file path that does not exist; a separate test covers each of the three rejections
- [ ] The match key for symbol-less findings and for jscpd clone pairs is documented in the ticket and the registry docstring, and a test shows a symbol-less finding that moves lines within its file is not reported as new
- [ ] 'make code-health' runs every adopted tool plus the ratchet and exits 0 on the seeded baseline; the target is in .PHONY
- [ ] The duplication output and its baseline rows create no ticket and no new finding for the four class pairs named in TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS beyond a link to that ticket
- [ ] docs/parity_ledger/infrastructure.yaml has an entry for the code-health registry and ratchet with a test_path pointing at the new tests, and docs/guidelines/subsystem_ownership_lifecycle.md has a 5-cell row for it; pytest tests/docs/test_subsystem_ownership_lifecycle_doc.py passes unmodified
- [ ] All new modules use package imports ('from tools.code_health...') with no sys.path.insert, and pytest tests/tools/test_tools_orphan_check.py passes
- [ ] 'git diff --stat <base>...HEAD' lists no path under src/, the count of '# noqa' / '# type: ignore' lines under src/ is unchanged (23 at investigation time), tests/ changes are confined to new test files for tools/code_health/, and no path under .claude/ and not CLAUDE.md appears
- [ ] No change to .github/workflows/test.yml: the ratchet is not run in CI

## Related Tickets
- TCK-20261002-PYTHON-CODE-CRAFT-EPIC
- TCK-20261002-CODE-HEALTH-TOOL-CONFIG
- TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS
- TCK-20260904-CAPABILITY-ENVELOPE-BASELINE
- TCK-20260915-RATCHET-CONFLATES-HISTORICAL-DEBT-WITH-LIVE-REGRESSION
- TCK-20260929-TOOLS-ORPHAN-FILE-CHECK
- TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS
- TCK-20260819-STANDARD-CODE-HEALTH-IMPACT-COMMAND

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_foundation_ticket_brief.md
- docs/guidelines/repo_tooling_layout.md
- docs/parity_ledger/infrastructure.yaml
- docs/guidelines/subsystem_ownership_lifecycle.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/capability_envelope_baseline.py
- registries/capability_envelope_registry.jsonl
- tools/gate_checks/tools_orphan_check.py
- tools/audit_unreachable_code.py
- tools/code_health_impact.py
- Makefile
- pyproject.toml
- docs/parity_ledger/infrastructure.yaml
- docs/guidelines/subsystem_ownership_lifecycle.md
- docs/guidelines/repo_tooling_layout.md
- tickets/todos/TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS.md

## Assumptions / Open Questions
- Depends on TCK-20261002-CODE-HEALTH-TOOL-CONFIG for the adopted tool list; an adapter is written only for tools that ticket kept
- 'Modelled on tools/capability_envelope_baseline.py' covers CLI shape and the reviewed field only: that tool is append-only and audit-only, while this registry deletes rows and backs a failing ratchet
- File-and-symbol matching is underspecified for hard cases (ruff gives no symbol for most rules, jscpd reports cross-file clone pairs, the worst offender is a 2,093-line function nested in create_v2_app); a per-file per-rule count with a ceiling is the suggested key for symbol-less findings, to be confirmed in the plan. A function renamed or moved across files will still surface as new
- Baseline size may exceed a thousand rows if ruff D rules are included, which invites merge conflicts across concurrent worktrees; per-file counts would reduce this and the granularity is an open design choice
- Other sessions are editing src/, so the seeded baseline will drift before M4; prior ratchets here were removed or made report-only after conflating historical debt with live regressions, which is why this one stays out of CI
- complexipy handling (native baseline file versus adapter) conflicts between roadmap Section 6.3 and the request's 'adapter per tool'; the roadmap is the binding plan, so the native baseline is the default unless the owner says otherwise
- The ownership row must use one of the three roles hardcoded in tests/docs/test_subsystem_ownership_lifecycle_doc.py, since that test cannot be edited
- 'make code-health' and tools/code_health/ are close in name to the existing codebase-health-* targets and tools/code_health_impact.py; the names come from the brief and are kept, with a Makefile comment to tell them apart
- Layer `testing` was inferred at ticket creation (code-quality check tooling, a ratchet and its tests); no registered layer names static-analysis tooling specifically, so confirm or change it if the epic's other children settle on a different one

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

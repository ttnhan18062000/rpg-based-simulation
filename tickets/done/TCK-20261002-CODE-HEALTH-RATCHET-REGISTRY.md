---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY
phase: done
date: 2026-10-02
tags: []
---

# TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY

## Title
M3b: Code-health adapters, ratchet command and exceptions registry

## Status
DONE

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
- [x] tools/code_health/ has one adapter per adopted tool; each adapter test feeds a captured JSON fixture of that tool's real output and asserts a normalised record with at least file, symbol (or null), tool, rule, value
- [x] The ratchet command exits 0 when run against a baseline seeded from the same scan, exits non-zero when a fixture adds a violation with no baseline row, exits non-zero when a fixture raises a measured value above its row's ceiling, and exits 0 when the same (file, symbol, tool, rule) violation only changes line number
- [x] The ratchet reports, and does not fail on, a baseline row whose violation has disappeared or improved; the registry CLI supports deleting a row and a test covers the delete
- [x] registries/code_health_exceptions.jsonl exists, every seeded row has reviewed: false, and the validator rejects a row with a missing required field, a duplicate (file, symbol, tool, rule) key, or a file path that does not exist; a separate test covers each of the three rejections
- [x] The match key for symbol-less findings and for jscpd clone pairs is documented in the ticket and the registry docstring, and a test shows a symbol-less finding that moves lines within its file is not reported as new
- [x] 'make code-health' runs every adopted tool plus the ratchet and exits 0 on the seeded baseline; the target is in .PHONY
- [x] The duplication output and its baseline rows create no ticket and no new finding for the four class pairs named in TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS beyond a link to that ticket
- [x] docs/parity_ledger/infrastructure.yaml has an entry for the code-health registry and ratchet with a test_path pointing at the new tests, and docs/guidelines/subsystem_ownership_lifecycle.md has a 5-cell row for it; pytest tests/docs/test_subsystem_ownership_lifecycle_doc.py passes unmodified
- [x] All new modules use package imports ('from tools.code_health...') with no sys.path.insert, and pytest tests/tools/test_tools_orphan_check.py passes
- [x] 'git diff --stat <base>...HEAD' lists no path under src/, the count of '# noqa' / '# type: ignore' lines under src/ is unchanged (23 at investigation time), tests/ changes are confined to new test files for tools/code_health/, and no path under .claude/ and not CLAUDE.md appears
- [x] No change to .github/workflows/test.yml: the ratchet is not run in CI

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
- stored_artifacts/TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY/plan.md
- stored_artifacts/TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY/investigation.md
- stored_artifacts/TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY/test_plan.md

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
Hand-orchestrated by the `codebase-implementer` session in worktree `rpg-code-craft`, branch `python-code-craft`.

**Done first, from the planner's review of `TCK-20261002-CODE-HEALTH-TOOL-CONFIG`:** ruff's `select` had dropped the default pyflakes set, hiding 1,043 existing findings (F401, F821, F841, F541, F811), so a new undefined name would have been invisible. `F` and `E9` are now selected as a correctness group, with rule X1 in the standard, before the registry was seeded. Total ruff findings are now 6,472.

**Modules** (`tools/code_health/`, package imports only, no `sys.path`): `findings.py` (the `Finding` record and key), `adapters.py` (one pure adapter per tool), `registry.py` (rows, validator, seed, delete, tighten), `ratchet.py` (compare, report), `scan.py` (run the tools, read their JSON), `__main__.py` (CLI: `check`, `scan`, `seed`, `validate`, `list`, `delete`, `tighten`). `line_count.py` gained `report_to_dict` and a `relative_to` option.

**Match key** `(file, symbol, tool, rule)`, never a line number:
- ruff: `(file, null, "ruff", code)`, value = number of findings of that rule in the file. Ruff gives no symbol, so one file and one rule is the unit.
- complexipy: `(file, "Class.method", "complexipy", "cognitive-complexity")`, value = complexity, only over the limit in `[tool.complexipy]`.
- line_count: `(file, symbol or null, "line_count", "function-length" | "class-length" | "module-length")`, value = lines; only functions over the fail limit and classes or modules over their limit.
- jscpd: `(lower path, "dup:" + higher path, "jscpd", "duplicate-block")`, value = total duplicated lines for that file pair.
A repeated key in one file (property getter and setter, overloads) takes the larger value for complexipy and line_count and the sum for ruff and jscpd; tested. A function renamed or moved shows as new, and its old row as gone.

**Ratchet:** no row is NEW (fails); value above the row's ceiling is WORSE (fails); below the ceiling is IMPROVED and a row with no finding is GONE (both reported, never failing). A violation that only changes line is unchanged. Frozen debt and live regressions are separate lists in the report. A source file deleted by another change is a "gone" row, not an invalid registry (the validator still rejects a nonexistent path when run as `validate`).

**Registry:** `registries/code_health_exceptions.jsonl`, seeded from a full scan: 3,617 rows (ruff 2,892; complexipy 384; line_count 283; jscpd 58), 730 KB, every row `reviewed: false`, ceiling equal to the measured value, sorted by key so concurrent edits merge. Rows are deleted when debt is paid (`delete`, `tighten`); `tighten` lowers ceilings and removes gone rows and never loosens. The ruff rows are per file and per rule (not per function) to keep the file this size; the cost is that fixing one violation and adding another of the same rule in the same file in one change is not caught.

**complexipy is handled by an adapter, not its native snapshot.** Roadmap 6.3 allowed either; the request and the first acceptance criterion say one adapter per adopted tool; the adapter gives one ratchet, one registry and symbol keys straight from complexipy's JSON. This departs from the roadmap's default and is open to reversal: drop `adapt_complexipy` and record the snapshot file in the registry instead.

**Same-name pairs:** none of the 58 duplication rows touches the seven files in `TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS`. A duplication row that did would carry that ticket's id in `retiring_ticket` and nothing else; no ticket or other finding is created, and no other tool's row on those files is linked. Tested.

**Makefile:** `make code-health` runs `python3 -m tools.code_health check` (scan, then ratchet) and is in `.PHONY`, with a comment telling it apart from the `codebase-health-*` targets. It exits 0 on the seeded baseline in about 4 seconds. It is not run in CI, and `.github/workflows/test.yml` is unchanged by this ticket.

**Docs and ledger:** parity ledger entry `INFRA-419` (written through `tools/parity_ledger_writer.py`; a dry-run re-dump of the shard was byte-identical, so no reformat diff); ownership row for the registry and ratchet using `Documentation Governance Maintainer`; the standard's command table and a registry paragraph.

**Known limits:** a ruff or complexipy version bump changes findings and needs `seed --force`; jscpd runs through `npx` with unpinned transitive dependencies, so it must not become a blocking gate before it has a lockfile (noted in the epic); the baseline will drift as other sessions edit `src/`, which `tighten` and `delete` absorb for improvements and `check` reports for regressions.

**Not done:** `make knowledge-index-update` (worktree has no `knowledge-index/`; post-merge step is in the epic).

## Test Summary
- New: `tests/tools/test_code_health_adapters.py` (11) and `tests/tools/test_code_health_ratchet_registry.py` (34), with real captured tool output in `tests/fixtures/code_health/` (ruff 0.16.10, complexipy 8.0.1, jscpd 5.4.0, line_count over a sample package; the only edit to the real output is a placeholder for ruff's absolute capture directory). They cover: one adapter per tool; seeded scan passes; a new violation fails; a value above the ceiling fails; a line move passes; a symbol-less ruff finding that moves lines is not new; improved and gone rows are reported without failing; delete and tighten; the three validator rejections, each in its own test, plus wrong types, bad JSON and a missing clone-pair partner; seed refuses without `--force`; repeated keys; the same-name-pairs link; the Makefile target and `.PHONY`; the jscpd pin and complexity limit read from the Makefile and `pyproject.toml`; no `sys.path` in the package.
- No test reads the live registry or live `src/`, so another session editing `src/` cannot break them.
- `pytest` over the new tests, `tests/static/`, the Makefile and CI-coverage pins, `tests/tools/test_tools_orphan_check.py`, `tests/tools/test_search_mcp.py`, `tests/architecture/test_docker_compose_dependency_hygiene.py`, the knowledge-extra test and `tests/docs/`: 263 passed, 2 skipped, 1 xfailed. `pytest tests/tools -k parity`: 177 passed.
- Real run: `python3 -m tools.code_health seed` then `make code-health`: exit 0, 3,617 unchanged. `validate`: valid.
- `ruff check tools/code_health` clean; mypy clean (with `--explicit-package-bases`). Orphan check: every new module `LIVE`.
- `# noqa` / `# type: ignore` under `src/`: 23 before and after. This ticket's diff has no path under `src/`, `.claude/`, `.github/` or `CLAUDE.md`, and modifies no existing test file.
- Not run: the wider test suite.

## Files Changed
- tools/code_health/{findings,adapters,registry,ratchet,scan,__main__}.py (new); tools/code_health/line_count.py
- registries/code_health_exceptions.jsonl (new, seeded)
- tests/tools/test_code_health_adapters.py, tests/tools/test_code_health_ratchet_registry.py, tests/fixtures/code_health/ (new)
- pyproject.toml (ruff `F` and `E9`), Makefile (`code-health`)
- docs/parity_ledger/infrastructure.yaml (INFRA-419), docs/guidelines/subsystem_ownership_lifecycle.md, docs/guidelines/python_code_standard.md
- docs/REGISTRY.yaml (regenerated); stored_artifacts/TCK-20261002-CODE-HEALTH-RATCHET-REGISTRY/

## Completion Summary
A registry of 3,617 grandfathered violations is seeded from a full scan of `src/`, and `make code-health` fails only on a violation that is new or above its row, matching by file and symbol and never by line. Nothing in `src/` was touched and nothing runs it in CI yet.

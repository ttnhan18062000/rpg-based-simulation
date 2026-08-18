---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP
artifact_type: test_plan
tags: [testing, process-improvement, mcp]
---

# Test Plan: TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP

## New Tests — `tests/tools/test_test_scope_coverage_static.py`

**`expected_test_dirs_for` (pure mapping, 8 tests):**
- Flat `tools/*.py` → `tests/tools/`
- Hyphenated `tools/agent-monitoring/` → `tests/tools/`
- `tools/gate_checks/` → `tests/tools/`
- `tools/agent_codex_<x>/` → same-name `tests/agent_codex_<x>/` mirror
- `src/<subsystem>/` → `tests/unit/<subsystem>/`
- Unrecognized `src/` subsystem → `None` (not a guessed path)
- `docs/`/`tickets/` paths → `None`
- Unmapped `tools/` subpath → `None` (not a silent `tests/tools/` fallback — surfaces gaps in
  the map itself instead of masking them)

**`check_test_scope_coverage` (aggregator, 7 tests):**
- Direct reproduction of the real incident's exact shape (files_changed + pytest_command pattern
  matching the real ticket) → `FAIL` on `tests/tools/`
- Genuinely-covered bare directory → `PASS`
- Only individually-named files inside the directory (not the bare directory) → `FAIL` — this is
  the critical trap case; a naive substring check would wrongly `PASS` here (caught and fixed
  during implementation, see investigation.md)
- Multiple files mapping to the same directory → reported once, not duplicated
- Unmapped files → no results (not a false PASS or FAIL)
- Empty `pytest_command` → `FAIL` for every mapped file
- Mixed `src/` + `tools/` changes → each directory checked independently

## Regression Coverage

- Full `tests/tools/` suite (128+ files) run after implementation — not just the new test file —
  since this ticket's own diff is itself a `tools/`-tree change and must not repeat the gap it
  fixes.
- `tests/tools/test_perf_tag_test_scoper_wiring.py` specifically re-run: it does raw-source-text
  parsing against `implement-ticket.js` and is exactly the kind of pre-existing test that could
  break from a Test-phase JS edit without living anywhere near the new code.
- `node --check .claude/workflows/implement-ticket.js` — syntax validity of the edited JS file
  (not real Node-executed, but confirms no malformed template-literal/escaping introduced).
- End-to-end wiring reproduction: the exact `python3 -c "..."` invocation as it appears in
  `implement-ticket.js`, run by hand against the real incident's file/command shape, confirming
  the JSON output the orchestrator would actually parse.

## Out of Scope for Testing

- No test exercises the full `implement-ticket.js` workflow end-to-end (it's not a real
  Node-executed program in this environment) — coverage is via direct invocation of the
  `python3 -c "..."` command the workflow embeds, plus static source-text assertions matching
  this repo's existing convention for `.claude/workflows/*.js` (see
  `test_document_update_phase_wiring.py`, `test_perf_tag_test_scoper_wiring.py`).

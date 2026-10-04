---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-AST-GREP-SARIF-AND-SNAPSHOT
artifact_type: plan
tags: [architecture, delivery]
---

# Plan — TCK-20261004-AST-GREP-SARIF-AND-SNAPSHOT

## Approach
**SARIF (`codebase/gates/sarif_feedback.py`)**
- `_tool_sarif` also runs `ast-grep scan --config codebase/rules/sgconfig.yml <files> --format sarif` (binary found by `scan._find("ast-grep")`; the binary is never `sg`). A missing binary or a non-0/1 exit raises `SarifError`, which `run()` already turns into exit 2 + summary line + warning, so it is never a silent pass. Verified locally: `--format sarif` exits 0 with findings, URIs are repo-relative.
- New `filter_ast_grep(run, rows, resolver, root)`: ast-grep SARIF carries a line but no enclosing symbol, and the registry key is `(file, symbol, "ast_grep", rule id)` with value = count of findings of that rule in that symbol. So the filter groups results by that key and drops a group whose count is at or below its row's ceiling, and keeps a group whole when over the ceiling or without a row, exactly as ruff groups are kept (the summary text already explains whole groups).
- Symbol resolution reuses `adapters`' span logic through one new public helper `adapters.symbol_resolver(root) -> Callable[[file, line], symbol]` (a thin public wrapper over the private `_symbol_spans`/`_enclosing_symbol`; `adapt_ast_grep` is refactored to call it, behaviour identical, its tests unchanged). No cross-module import of a `_private` name (rule N3).
- Summary line gains an `ast-grep` clause; the `kept` count and annotation include it. The result runs list gains a third run.

**Snapshot (`codebase/health/scan.py`, `metrics.py`)**
- `ast_grep` joins `OFFLINE_TOOLS` (a local binary, no network) and the stale comment about it goes.
- Three new keys in `CRAFT_METRIC_KEYS`/`CRAFT_LABELS` (live keys): `craft_ast_grep_private_name_imports` (N3), `craft_ast_grep_version_marker_names` (N4), `craft_ast_grep_silent_excepts` (E3), each the sum of finding counts for its rule id. No combined craft number.
- Existing 14 dimensions: a test computes them before and after on one fixture and asserts identical values.
- **The brief assumed the history schema takes new keys additively. It does not:** `build_snapshot_record` requires `set(craft) == CRAFT_METRIC_KEYS` exactly, and the history-schema doc says any key change is a paired change that bumps `SNAPSHOT_SCHEMA_VERSION`. So: bump 2 -> 3, add a version-3 row and the three field rows to `docs/agent-monitoring/codebase_health_history_schema.md`, and update the codebase tests that pin `== 2`. Existing history lines are never rewritten; the scorecard already tolerates a craft key missing from an older record ("no trend data yet"). The history file itself is not touched by this ticket.

## Steps
1. `adapters.symbol_resolver` + refactor `adapt_ast_grep` (tests first).
2. `filter_ast_grep`, `_tool_sarif`, `_summary`, `run()` wiring.
3. `scan.OFFLINE_TOOLS`, metrics keys, labels, schema version 3, schema doc.
4. Tests (see test_plan.md).
5. `docs/guidelines/python_code_standard.md` untouched; update `codebase/README.md` or the SARIF module docstring (it says ruff and complexipy only).

## Scope guards
No `src/`; no threshold, tool version or registry row change; ast-grep stays advisory (flip ticket owns blocking); no new rules; the history file is not rewritten; CI workflow file not edited (the SARIF job already installs the `lint` group that holds `ast-grep-cli`).

## Acceptance-criteria map
New finding reported, grandfathered omitted: step 2. Missing binary exit 2 + warning: step 2. Three dimensions, existing values identical: step 3. No threshold/version/row change: guard, checked by diff. No src diff.

## Open choices (defaults taken)
- Metric key names above; rule id to key mapping is fixed in one dict.
- Version bump 2 -> 3 (required by the repo's own rule, deviates from the brief's "additive" wording).

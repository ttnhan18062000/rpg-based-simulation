---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-AST-GREP-RULE-PACK-ADVISORY
artifact_type: plan
tags: [architecture, planning]
---

# Plan — TCK-20261004-AST-GREP-RULE-PACK-ADVISORY

## Prototype findings (scratch, uncommitted; ast-grep 0.45.3 via `uvx --from ast-grep-cli`)
- N3 (`import_from_statement` with an imported name matching `^_[^_]`): 11 findings in `src/` (ai 4, engine 3, observability 3, domains 1).
- N4 (`function_definition` / `class_definition` whose name matches `^V2|V2$|_v2(_|$)|_new$`): 7 findings. The standard's trailing `2` is left out: `vec2`/`utf2`-style names would be false positives, and the standard's own examples are `V2`, `_v2`, `_new`.
- E3 (`except_clause` whose block is exactly `pass`): 115 findings (a rough grep gave 107). One scan of `src/` takes 0.25 s.
- T3 (`dict[str, Any]` in public function signatures): a signature-only rule still matches 185 places and cannot tell a typed-model candidate from a legitimate JSON passthrough (API presenters, payload builders); the broad form also hits local variable annotations. **Decision: T3 stays a reviewer rule; the ticket records why** (the brief allows this).

## Design
1. **Dependency:** `ast-grep-cli==0.45.3` in the `lint` group of `pyproject.toml`; `uv lock` refresh. If `uv lock` also bumps other pins, stop and report (M4 soak: ruff and complexipy versions must not change).
2. **Rules:** `codebase/rules/sgconfig.yml` (`ruleDirs: [rules]`, `testConfigs: [{testDir: rule-tests}]`), `codebase/rules/rules/{n3-private-name-import,n4-version-marker-name,e3-silent-except}.yml`, each message states the fix; `codebase/rules/rule-tests/<id>-test.yml` with valid and invalid snippets (including the false-positive guards: dunder names for N3, `vec2` for N4, `except: pass` with a logged body for E3). `tests/codebase/test_ast_grep_rules.py` runs `ast-grep test --config codebase/rules/sgconfig.yml --skip-snapshot-tests` through the interpreter's environment; it skips with a message only when the binary is missing, never silently passes.
3. **Adapter** (`codebase/health/adapters.py::adapt_ast_grep`): pure function of ast-grep's `--json=stream` records (file, ruleId, range). The enclosing symbol is computed from the file with the stdlib `ast` (`Class.method` qualified like the other adapters; `None` at module level), so the key is `(file, symbol, "ast_grep", <rule id>)`, value = number of findings of that rule in that symbol, never a line. `TOOL_AST_GREP = "ast_grep"` in `findings.py`; docs the key there.
4. **Scan:** `scan.py` gains `_scan_ast_grep` (binary found beside the interpreter like complexipy, then PATH; exit codes 0 and 1 allowed; output `ast_grep.json`), `"ast_grep"` in `ALL_TOOLS` and `OFFLINE_TOOLS`, and the `collect_findings` branch. A missing binary raises `ToolUnavailableError` (exit 2, never a clean pass).
5. **Seeding without touching other tools' rows:** `python3 -m codebase.health seed --tool ast_grep [--from DIR]` seeds only that tool's findings and keeps every other row verbatim (and keeps `reviewed`/`added_date` for ast_grep keys that persist). Test: after the seed, the rows of ruff, complexipy, jscpd and line_count are byte-identical to before. The committed registry diff is then ast_grep rows only (about 130 rows), shown in the closing notes.
6. **Reporting:** `make code-health` and the advisory `code-health` job already run `check`, so ast_grep joins the ratchet summary with no workflow edit; the job's step is advisory and its summary lists new/worse rows of every tool. SARIF changed-line feedback (`codebase/gates/sarif_feedback.py`) builds ruff and complexipy SARIF only; adding a tool needs a structural change, so it is **noted as a follow-up, not done**.
7. **Blocking interplay:** the flip ticket (`TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING`) already excludes `ast_grep` (planning commit). This ticket verifies the key it names matches `TOOL_AST_GREP` (`ast_grep`) and files `TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING` (BLOCKED; dates written at the merge: soak start = merge date, end = start + 14 days).
8. **Docs:** standard rules N3, N4, E3 Enforcement cells name `ast-grep n3-private-name-import` etc. (T3 unchanged); `codebase/README.md` row for `rules/`; `codebase/health/findings.py` docstring; roadmap Section 6 note that T3 stays reviewer-only (one sentence).
9. **Also in this ticket's first commit (planner nit on ticket 4):** the import-linter record and outbox Message 9 now say the `kernel.py` imports are function-local (done).

## Scope guards
No `src/` path; ruff and complexipy pins and thresholds untouched; no existing registry row changed; nothing blocking; `.claude/` untouched.

## Amendments during implementation (2026-10-04)
- `ast_grep` is in `ALL_TOOLS` but NOT in `OFFLINE_TOOLS`: the codebase-health snapshot would otherwise gain a tool and change its metrics; snapshot inclusion is a follow-up. A test pins the split.
- N3 counts imported NAMES (one finding per `_private` name), not statements: ast-grep's `field:` only checks the first of several same-named children, so the rule matches the `dotted_name` after the `import` keyword. Seeded: 13 N3 rows (23 findings), 7 N4, 91 E3 (120 findings) = 111 rows, all under tool `ast_grep`; the diff to `code_health_exceptions.jsonl` is +111 lines, 0 deleted, the other 3,617 rows verbatim.
- Planner conditions: (1) the staged hook runs ruff only and never looks for `ast-grep`; ast_grep rows in the registry are ignored there (test); a missing binary raises `ToolUnavailableError` naming `ast-grep` in scan/check, so `make code-health` and the advisory job's could-not-run path report it. (2) N4's Enforcement cell says a trailing digit is left to the reviewer; `_new` is matched only at the end of a name. (3) The binary is looked up as `ast-grep` (test asserts the lookup name). Module-level findings use the symbol `<module>`.

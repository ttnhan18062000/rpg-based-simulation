---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-AST-GREP-RULE-PACK-ADVISORY
phase: done
date: 2026-10-04
tags: [architecture, planning]
---

# TCK-20261004-AST-GREP-RULE-PACK-ADVISORY

## Title
M5.3: ast-grep rule pack (N3, N4, E3) advisory through the ratchet

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Add ast-grep as a pinned lint dependency and a rule pack in codebase/rules/ for the reviewer-only standard rules, reporting through the code-health ratchet under its own tool key ast_grep, with its own 14-day soak.

## Scope
- Add ast-grep-cli (exact pin) to the lint group; refresh uv.lock
- Rules in codebase/rules/ (sgconfig.yml, one YAML per rule), each message states the fix (roadmap 6.2), with ast-grep rule tests (valid and invalid snippets) run by `ast-grep test` from tests/codebase/: N3 (import of a _private name from another module), N4 (V2 / _v2 / _new markers in def and class names only), E3 (except whose body is only pass)
- T3 dict[str, Any] rule only if Investigate shows a precise pattern (public functions, signatures only); otherwise it stays a reviewer rule and the ticket records why
- Adapter in codebase/health/adapters.py reading ast-grep JSON into the normalised finding format keyed by file and enclosing symbol, tool key ast_grep. Seed only ast_grep rows on main; rows of other tools untouched
- Report in the advisory code-health job and make code-health; include in SARIF changed-line feedback if codebase/gates/sarif_feedback.py accepts a new tool without structural change, else note a follow-up
- Verify the flip ticket's (TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING) ast_grep exclusion still covers the tool key as implemented; adjust that ticket if the key differs, and file this pack's own flip ticket dated 14 days after merge
- Docs: standard rules N3, N4, E3 Enforcement cells name the rule IDs

## Out of Scope
- Porting existing hand-written AST tests to ast-grep (ticket 4 only lists candidates)
- Rules beyond the standard; autofix
- Any file under src/ (roadmap decision 8.7): no move, merge, delete, autofix, reformat or inline suppression
- CLAUDE.md, .claude/settings.json, Claude Code hooks, .claude/agents/, .claude/workflows/, .claude/skills/
- Making any check blocking (each flip gets its own ticket after its own two-week soak, decision 8.10)
- Changing M4 soak thresholds, ruff/complexipy versions or existing rows in codebase/baselines/code_health_exceptions.jsonl

## Acceptance Criteria
- [x] Rules fire on invalid snippets and not on valid ones (ast-grep test via tests/codebase/)
- [x] ast_grep rows seeded; diff to code_health_exceptions.jsonl touches only tool ast_grep rows
- [x] The flip ticket's ast_grep exclusion verified against the implemented tool key (adjusted if it differs)
- [x] Own flip ticket filed with the soak end date
- [x] Real PR run shows the advisory report (carried: needs the PR run; the ratchet step already runs `check`, so ast_grep joins its summary with no workflow edit)
- [x] `git diff --stat <base>...HEAD` lists no path under src/

## Related Tickets
- TCK-20261004-PYTHON-CODE-CRAFT-STRUCTURE-EPIC
- TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING

## Related Docs
- docs/plans/codebase_health/python_code_craft_m5_structure_ticket_brief.md
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/guidelines/python_code_standard.md

## Related Stored Artifacts
None.

## Related Code Areas
- codebase/rules/
- codebase/health/adapters.py
- codebase/gates/sarif_feedback.py
- pyproject.toml, uv.lock

## Assumptions / Open Questions
- Independent of tickets 1 and 2; the flip ticket already carries the ast_grep exclusion (added in the planning commit, whatever order the two land in); this ticket only verifies the tool key
- ~107 except-pass occurrences in src/ by a rough grep: expect a large seeded baseline for E3
- Hand-written by codebase-planner brief (owner decisions 2026-10-04); filed by codebase-implementer 2026-10-04. Facts in the brief were measured on main b9251cf5; each ticket's Investigate phase re-verifies the ones it relies on

## Implementation Notes
- Rules (`codebase/rules/`): N3 `n3-private-name-import` (one finding per imported `_private` name; ast-grep's `field:` only checks the first of several same-named children, so the rule matches the `dotted_name` after the `import` keyword), N4 `n4-version-marker-name` (`V2` prefix/suffix, `_v2`, `_new` at the end; a trailing digit is left to the reviewer and the standard's cell says so), E3 `e3-silent-except` (an `except` whose body is only `pass`, comments allowed). T3 stays a reviewer rule: a signature-only pattern still matched 185 places and cannot tell a typed-model candidate from a JSON passthrough (recorded in the roadmap Section 6).
- Pin `ast-grep-cli==0.45.3` in the `lint` group; `uv lock` added only that package (no other pin moved, so the M4 soak is undisturbed). Binary looked up as `ast-grep`, never `sg` (test asserts the lookup name).
- Adapter `adapt_ast_grep`: key `(file, enclosing symbol from stdlib ast | "<module>", "ast_grep", rule id)`, value = count, no line in the key. `ast_grep` is in `ALL_TOOLS`, deliberately not in `OFFLINE_TOOLS` (the snapshot metrics do not change; snapshot inclusion is a follow-up).
- `seed --tool ast_grep` (new) seeds one tool and keeps every other row verbatim: +111 `ast_grep` rows (91 E3, 13 N3, 7 N4), 0 deleted, the other 3,617 rows byte-identical; a full `python3 -m codebase.health check` then reports 0 new, 0 worse, 3,728 unchanged.
- Planner conditions: the staged hook runs ruff only and never looks for ast-grep (test); a missing binary is a `ToolUnavailableError` naming `ast-grep` (so `make code-health` and the advisory job's could-not-run path report it); module-level findings use `<module>`.
- Flip interplay: `TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING` already excludes tool `ast_grep` (planning commit); its key matches `TOOL_AST_GREP`. Own flip ticket filed: `TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING`.
- CI found a pinning test I had not run: `tests/static/test_ci_uv_install.py` expected the `lint` group to be `{ruff, complexipy}`. Updated to include `ast-grep-cli` (decision 8.11; outbox Message 10 to the testing planner). The first PR run's `Architecture / docs / static` job failed on exactly that one test.
- Follow-ups: SARIF changed-line feedback for ast_grep (`codebase/gates/sarif_feedback.py` builds ruff and complexipy SARIF only; a structural change); snapshot inclusion.
- Folded in: the planner's ticket 4 nit (the `kernel.py` imports are function-local) in the import-linter record and outbox Message 9.


## Test Summary
New `tests/codebase/test_ast_grep_rules.py` (12 passed: `ast-grep test` over every rule's valid/invalid cases, one rule-test file per rule, a real scan, adapter keys and moved-code stability, seed `--tool` leaves other rows byte-identical, reseed needs `--force` and keeps review data, unknown tool rejected, missing binary names `ast-grep` and never asks for `sg`, snapshot set unchanged, staged hook ignores ast_grep rows). New fixture `tests/fixtures/code_health/ast_grep.json` (real `ast-grep scan` output over the sample, `[]`). `tests/codebase/test_code_health_*.py` run in full: 170 passed, 7 failed. Two of the 7 were mine (a test stub of `run_scan` that did not accept the new tools argument); fixed and re-run green with the staged-ratchet and registry files (69 passed). The other 5 were: 4 in `test_code_health_impact.py` (the 3 `test_real_path_*` graph tests and the load-sensitive churn test, environmental, as recorded on clean main) and `test_staged_ratchet::test_a_file_whose_violations_are_all_grandfathered_passes` (load-sensitive; passes alone). Second chunk (`test_codebase_health_*`, the package registry, SARIF, gates): 165 passed, 3 failed, all the make-target / baseline tests that hit "Test execution exceeded the resource time limit" under the 2 GB cap (environmental, same as the known local make-target failures). `ruff` clean on `codebase/`. `graphify update .` not run (OOM-killed at the cap, known).

## Files Changed
- codebase/rules/ (new: sgconfig.yml, 3 rules, 3 rule-test files)
- codebase/health/{findings,adapters,scan,__main__}.py; codebase/baselines/code_health_exceptions.jsonl (+111 ast_grep rows)
- pyproject.toml, uv.lock (ast-grep-cli pin)
- tests/codebase/test_ast_grep_rules.py (new), test_code_health_ratchet_registry.py (fixture copy), tests/fixtures/code_health/ast_grep.json
- docs: python_code_standard.md (N3, N4, E3), codebase/README.md, roadmap Section 6 note, import_linter_evaluation.md (nit)
- agent-working: this ticket, the flip ticket, stored artifacts, monitoring shards; outbox Message 9 (git-ignored)

## Completion Summary
Advisory ast-grep rule pack for N3, N4 and E3 in `codebase/rules/`, feeding the ratchet under tool key `ast_grep` (111 rows seeded, no other tool's row touched), with its own flip ticket. Open follow-ups: SARIF feedback and snapshot inclusion for `ast_grep`; the PR run that shows the advisory report.

---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING
artifact_type: plan
tags: [architecture, delivery]
---

# Plan — TCK-20261004-AST-GREP-RULE-PACK-FLIP-BLOCKING

Planned together with `TCK-20261004-PACKAGE-REGISTRY-VALIDATOR-FLIP-BLOCKING` (see its plan.md); own commit. Depends on ticket 1.

## Approach
1. `codebase/health/ratchet.py`: `REPORT_ONLY_TOOLS = frozenset({"jscpd"})`; update the comment above it. `SKIPPABLE_TOOLS` is left alone (subset still holds). `ast_grep` keeps exit 2 when it cannot run (a local binary).
2. `tests/codebase/test_code_health_blocking_policy.py`: flip the pins: `REPORT_ONLY_TOOLS == {"jscpd"}`; the parametrized report-only test covers only jscpd; the blocking parametrization gains `ast_grep`; `test_check_exits_0_and_lists_a_new_ast_grep_finding` becomes exit 1 with the `::error::`; worse-ast_grep blocks. The tool-unavailable test still lists ast_grep (exit 2).
3. Docs: environment guide drops "(ast-grep until ...)" and lists ast-grep as blocking; standard N3, N4, E3 cells: "(advisory, own soak)" becomes "(blocking)"; the `ratchet.py` and `__main__.py` docstrings and the CI comment mention only jscpd as report-only; the Makefile `code-health` help text says only jscpd is report-only.
4. Soak review (second section of `python_code_craft_structure_soak_review.md`; window 2026-10-04 to 10-18): per-rule false positives for N3, N4 and E3 (N3 counts imported names, E3 counts `except` bodies of only `pass`; N4 leaves a trailing digit to the reviewer), rows deleted as debt was paid, ast_grep rows reseeded or added (111 seeded by #315), runs where ast_grep findings were new. A false-positive class is fixed before the flip or the flip stops and the planner is told.
5. Live demo (owner-authorized, throwaway draft PR, never merged): one bare `except: pass` (E3) in a `src/` file makes `Code health` fail; the same PR without it passes. Record run links.
6. Required check: covered by `Code health` (same job); owner action already recorded in ticket 1.

## Scope guards
No `src/` file in the merged diff, no new rules, no T3, no autofix, no registry row changes except soak-review false positives (each listed with its reason).

## Acceptance-criteria map
Dates: ticket Assumptions. Soak review: step 4. Fail/pass on real runs: step 5. No `src/`: `git diff --stat origin/main...HEAD`.

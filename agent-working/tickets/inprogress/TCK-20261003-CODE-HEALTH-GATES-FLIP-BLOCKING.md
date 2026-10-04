---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING
phase: open
date: 2026-10-03
tags: [delivery]
---

# TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING

## Title
M4f: After the two-week soak, make the code-health ratchet, SARIF step and mypy baseline block new violations

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Decision 8.5/8.10: advisory for a two-week soak, then blocking for new violations only. Owner decision 2026-10-03: mypy flips together with the ratchet; jscpd stays report-only. BLOCKED until the soak end date, which TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB records here.

## Scope
- Soak review first (`docs/plans/codebase_health/python_code_craft_gates_soak_review.md`; window 2026-10-03 to 2026-10-17, drafted now, finalized after the window): runs, exit-1 and exit-2 runs, each new or worse finding and its disposition, reseeds and mypy-baseline syncs, reviewed-row count, and the deferred SARIF live proof (PR #291, `ruff` check run at `65731e0c9` "4 new alerts", success at `c659d67a7`)
- Precondition: `main` ratchet-clean and mypy-gate-clean at the flip commit; re-run now and right before merge. Clean on `origin/main` 053f459e4 (2026-10-04)
- Ratchet: a named `REPORT_ONLY_TOOLS = frozenset({"jscpd", "ast_grep"})` in `codebase/health/ratchet.py`; `check` exits 1 only for new/worse findings of other tools; report-only findings stay in the report and summary, labelled report-only. A separate `SKIPPABLE_TOOLS = frozenset({"jscpd"})` (network/npx dependency, `SKIPPABLE_TOOLS <= REPORT_ONLY_TOOLS`): if jscpd cannot run it is skipped as "not measured" (never "gone"), with a summary line and a warning annotation; exit 2 stays for every other tool and for registry errors (planner decision 2026-10-04)
- Tighten the 6 improved rows and delete the 4 gone rows on the branch base; the check then reports 0 improved, 0 gone
- CI: remove `continue-on-error` from the `Code health ratchet` step, the `mypy` step and the `code-health` job (default: remove the job-level backstop; a broken setup must not read as a pass for a required check); `Package registry` keeps its step-level one until its own flip; rename the jobs "Code health" and "Type check"; rewrite the CI comments; the SARIF job is untouched except its comment ("advisory permanently, decision 8.19")
- Remove `|| true` from the `make typecheck-py` recipe and fix the `##` help text of `typecheck-py` and `code-health`
- Update INFRA-TYPE-001 text and `v2_evidence`, the environment guide section, the standard's Enforcement cells and the tests that pin advisory status
- Live demos (owner-authorized pushes only, throwaway draft PRs, never merged): (a) one new ruff violation and one new mypy error in a `src/` file fail `Code health` and `Type check`; (b) a no-`src/` change passes both
- Ask the owner to mark `Code health` and `Type check` required in the `main` ruleset (owner action; record date and who)

## Out of Scope
- Any file under src/
- Gating jscpd or line-count beyond what the ratchet already does (jscpd report-only)
- Raising strictness or tightening ceilings

## Acceptance Criteria
- [ ] Soak review written with dates, counts and dispositions
- [ ] The ratchet and mypy gates fail a PR that introduces a new violation and pass one that does not (demonstrated on real PR runs)
- [ ] Owner confirmed the required-check setting
- [ ] Green PR run link recorded
- [ ] `git diff --stat <base>...HEAD` lists no path under src/

## Related Tickets
- TCK-20261004-AST-GREP-RULE-PACK-ADVISORY
- TCK-20261004-PACKAGE-REGISTRY-VALIDATOR
- TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC
- TCK-20261003-CODE-HEALTH-RESEED-AND-ADVISORY-CI-JOB
- TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK
- TCK-20261003-MYPY-BASELINE-ADVISORY

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_m4_gates_ticket_brief.md
- docs/parity_ledger/infrastructure.yaml (INFRA-TYPE-001)

## Related Stored Artifacts
None.

## Related Code Areas
- .github/workflows/test.yml
- tests/codebase/test_typecheck_gate_configured.py

## Assumptions / Open Questions
- **Explicit step (done in `TCK-20261003-CODEBASE-DOMAIN-ROOT-MOVE`, the next codebase batch): the real soak start (the merge date of PR #305) and end (start + 14 days) are written into this ticket, the epic and roadmap Section 7.**
- Soak start: 2026-10-03 (PR #305, the PR that carries the advisory CI job, merged 2026-10-03T16:47:13Z). Soak end: 2026-10-17 (start + 14 days)
- Blocking gates affect every domain that edits src/; announce the date to other planners before flipping

## Implementation Notes
- Policy in code (`codebase/health/ratchet.py`): `REPORT_ONLY_TOOLS = {jscpd, ast_grep}` and a separate `SKIPPABLE_TOOLS = {jscpd}`, pinned `SKIPPABLE_TOOLS <= REPORT_ONLY_TOOLS`. `RatchetResult.failed` keeps its meaning (edit hook and staged ratchet); `blocking_failed` is what `check` exits 1 on.
- **Decision (planner, 2026-10-04): jscpd is exempt from exit 2.** `scan.run_scan(..., skippable=)` returns the tools that could not run; `check` skips them ("not measured", never "gone": their rows are left out of the comparison), writes a summary line and a `::warning::`, and exits 0/1 from the other tools. Reason: with the step blocking, an npm registry or `npx --yes` failure would fail a required check for a tool that is report-only by decision 16. Exit 2 stays for ruff, complexipy, line_count, ast_grep and any registry error. `check --from DIR`, `seed` and `tighten` never skip, so a partial scan can never delete jscpd rows or reseed from one.
- Annotations on `check` and `mypy_gate` changed from `::warning::` to `::error::` (they now fail a required check); the skip note stays a `::warning::`.
- CI: no `continue-on-error` on the `code-health` job, the `Code health ratchet` step or the `mypy` step (a broken setup must not read as a pass for a required check). **Kept on purpose:** the "Paths this PR changed" step (it truncates `/tmp/changed.txt` first and a failed diff only changes summary ordering) and `Package registry` (until its own flip). Jobs renamed `Code health` and `Type check`. The workflow has no path filter and neither job has an `if:`, so a required check cannot hang in "expected".
- Registry: `tighten --yes` after reading the list: 6 rows lowered, 4 deleted (see the soak review); `check` then reports `0 improved, 0 gone`.
- Precondition measured 2026-10-04 on `origin/main` 053f459e4: `check` exit 0 and `mypy_gate` exit 0. To be repeated right before merge.
- The mypy gate first reached `main` in PR #313 (2026-10-04T04:59Z), so its window ends 2026-10-18T04:59Z; the merge is on or after 2026-10-18 05:00Z.

## Test Summary

## Files Changed

## Completion Summary

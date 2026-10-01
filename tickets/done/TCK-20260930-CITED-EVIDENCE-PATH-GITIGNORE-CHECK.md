---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-CITED-EVIDENCE-PATH-GITIGNORE-CHECK
phase: done
date: 2026-09-30
tags: [ai]
---

# TCK-20260930-CITED-EVIDENCE-PATH-GITIGNORE-CHECK

## Title
Advisory check: a path a ticket or test cites must be tracked in git, not silently gitignored

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`.gitignore` line 239 drops `stored_artifacts/**/*.json` (only `manifest.json` is excepted). Evidence
written as `.json` passes locally but is missing from a clean checkout. PR #268's runtime-probe
outputs were never committed this way, and PR #270's first CI run failed because a classification
table was dropped. Found by agent-working-implementer by reproducing CI from a clean clone.

## Scope
1. Add an advisory check (report-only, never blocking, in the style of the done-checker Proof Plan
   advisory) that lists any `stored_artifacts/`, `staging_artifacts/` or `tickets/` path cited by a
   closing ticket that is not in `git ls-files`, or is matched by `git check-ignore`.
2. Wire it into the closing flow as a WARN with the offending path and the matching ignore rule.
3. Decide whether the `.gitignore` rule itself should change; record the call and why.

## Out of Scope
- Making the check blocking. Agent tooling checks stay proportionate.

## Acceptance Criteria
1. A ticket citing an ignored `.json` evidence path produces a WARN naming the path and the rule.
2. A ticket whose cited paths are all tracked produces no WARN.
3. The check never changes the done-checker verdict.

## Related Tickets
- TCK-20260930-DONE-CHECKER-PROOF-PLAN-ADVISORY (the advisory style to follow)

## Related Docs
- `docs/guides/delivery_process.md` (advisory paragraph)
- `.claude/agents/done-checker.md` (Step 0c)


## Related Stored Artifacts
- `stored_artifacts/TCK-20260930-CITED-EVIDENCE-PATH-GITIGNORE-CHECK/` (plan, investigation, test_plan)


## Related Code Areas
- `tools/gate_checks/cited_evidence_advisory.py` (new), `tools/gate_checks/done_checker_static.py`, `.gitignore`
- `tests/tools/test_cited_evidence_advisory.py`


## Assumptions / Open Questions
- Citations are extracted from backticked paths only (resolved as the ticket's open question); unbackticked prose paths are not checked.
- `.gitignore` decision: the `stored_artifacts/**/*.json` rule is kept. It keeps large generated JSON out of the repo, `.jsonl` is the existing convention, and `manifest.json` is already excepted. The WARN tells the author to store as `.jsonl`.


## Implementation Notes
New `cited_evidence_advisory.py` wired into `run_advisory_checks()` as `cited_evidence_tracked`. Skips the ticket's own path, wildcard/placeholder tokens and paths absent on disk; resolves a `staging_artifacts/` citation at its migrated `stored_artifacts/` path. WARN names the path and the matching ignore rule (`git check-ignore -v`), or flags an untracked path (`git ls-files`).


## Test Summary
`pytest tests/tools/test_cited_evidence_advisory.py tests/tools/test_proof_plan_advisory.py tests/tools/test_done_checker_static.py tests/tools/test_skill_usage_metric.py`: 202 passed across test_cited_evidence_advisory, test_proof_plan_advisory, test_done_checker_static, test_skill_usage_metric.

## Files Changed
- `tools/gate_checks/cited_evidence_advisory.py` (new)
- `tools/gate_checks/done_checker_static.py`
- `tests/tools/test_cited_evidence_advisory.py` (new)
- `docs/guides/delivery_process.md`, `.claude/agents/done-checker.md`

## Completion Summary
Added the report-only `cited_evidence_tracked` advisory: a ticket citing a gitignored or untracked evidence path gets a WARN naming the path and the ignore rule; all-tracked citations are OK; it never enters the precheck or changes the exit code. Kept the `.gitignore` rule (rationale in Assumptions).

---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH
phase: done
date: 2026-09-15
tags: [claude-md, process-improvement, workflows]
---

# TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH

## Title
A `CONFLICTING` PR produces zero CI runs, not failing ones — CLAUDE.md's CI triage guidance covers failing jobs thoroughly and absent runs not at all, so an agent following it correctly still ends up guessing

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Reported by `rpg-feature-planning` 2026-09-15 after it cost ~20 minutes on PR #205 and nearly
produced a wrong fix. **Independently verified here before scoping.**

`.github/workflows/test.yml` declares:

```yaml
on:
  pull_request:
  push:
    branches: [main]
  schedule: [...]
  workflow_dispatch: {}
```

A feature branch therefore gets CI **only** via the `pull_request` event, which GitHub evaluates
against the merge ref `refs/pull/N/merge`. That ref cannot be computed while a PR is
`CONFLICTING`, so **no workflow run is created in any state** — `gh api
repos/.../actions/runs?head_sha=<sha>` returns `total_count: 0`.

**The failure presents as pending, not as blocked.** PR open, commit pushed, checks area empty —
every visible signal matches a slow queue. "No run yet" and "no run ever" are indistinguishable
from outside, which is the same silence-as-a-state shape this arc has catalogued repeatedly
(`docs/plans/agent_infrastructure/reachability_verification_findings.md`), here in our own CI
surface rather than in simulation code.

**The natural next step actively destroys evidence.** The reporting session's leading option was an
empty no-op commit to re-trigger the webhook. That pushes into the same conflicted state, produces
no run again, and stacks a second unexplained silence on the first — whose natural escalation is
force-push or branch recreation, which discards the evidence without touching the cause.

**This has now happened at least three times today, and two went unrecorded.** During the
agent-monitoring batch, PRs #194 and #199 both showed zero check-runs while `CONFLICTING`; this
session diagnosed it verbally each time ("no check-runs will register while the PR is CONFLICTING —
that's been the pattern on every conflicted PR this batch") and never wrote it anywhere durable.
That is Finding 7 of the reachability doc — a real finding dying in prose — committed while the
same batch was cataloguing it. The third occurrence is what finally routed it here.

**Confirmed gap**: CLAUDE.md's "CI Failure Triage" section is thorough on a *failing* job (pull real
logs, never conclude from a job name, classify before acting, the Fortinet-blocked-log path) and has
no branch whatsoever for a job that never ran. A grep for absent-run guidance returns nothing.

## Scope
- Add an absent-run branch to CLAUDE.md's CI Failure Triage section, establishing that **an absent
  signal needs a different diagnostic path from a failing one**. Minimum content:
  - Before treating a missing CI run as a delivery/webhook problem, check
    `gh pr view <N> --json mergeable` and the workflow's own trigger block.
  - `CONFLICTING` + a `pull_request:`-only trigger fully explains a missing run. The fix is to
    resolve the conflict — **never** a re-trigger commit, force-push, or branch recreation.
  - `git ls-remote origin <branch>` compared against `headRefOid` is the cheap read-only check that
    the push actually landed, distinguishing "push didn't arrive" from "run wasn't created".
- Keep it proportionate: this is a short branch added to existing guidance, not a rewrite of the
  section.

## Out of Scope
- Changing `.github/workflows/test.yml`'s triggers. Adding a `push:` trigger for all branches would
  mask the condition rather than explain it, and would double CI spend on every feature push.
- Any tooling that auto-detects the condition. A documented diagnostic step is the proportionate
  fix for something whose correct response is one command; revisit only if it recurs after the
  guidance lands.
- The broader "absent signal vs failing signal" pattern across other subsystems — name it in the
  guidance, don't chase it here.

## Acceptance Criteria
- [x] CLAUDE.md's CI Failure Triage section contains an absent-run branch covering the
      `mergeable` check, the trigger-block check, and the explicit prohibition on re-trigger
      commits / force-push / branch recreation as a response to a missing run. Pinned by
      `test_absent_run_branch_covers_the_mergeable_check`,
      `test_absent_run_branch_covers_the_trigger_block_check`,
      `test_absent_run_branch_prohibits_retrigger_force_push_and_branch_recreation`.
- [x] The guidance states the general principle, not only the specific case: an absent signal is
      diagnosed differently from a failing one. Pinned by
      `test_absent_run_branch_states_the_general_principle_not_only_the_specific_case`.
- [x] The `git ls-remote` push-landed check is included, since it is the cheap disambiguator.
      Pinned by `test_absent_run_branch_includes_git_ls_remote_disambiguator`.
- [x] **User authorization is obtained before editing CLAUDE.md.** Obtained directly via
      `AskUserQuestion`, showing the exact proposed content, before any edit was made — not
      inferred from the batch-level authorization, which this ticket's own Assumptions explicitly
      says does not supply it.

## Related Tickets
- `TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE` (done) — the same
  "two correct instructions / one missing branch" instruction-defect shape
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (done) — the silence-as-a-state catalogue
- `TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX` (done) — why PRs in this repo conflict so
  routinely, which is what makes this condition common rather than exotic

## Related Docs
- `CLAUDE.md` — "CI Failure Triage" (the section to extend)
- `.github/workflows/test.yml` — the trigger block that causes it
- `docs/plans/agent_infrastructure/reachability_verification_findings.md` — Finding 7

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `CLAUDE.md`
- `.github/workflows/test.yml` (read-only reference; not to be modified)

## Assumptions / Open Questions
- **Editing CLAUDE.md requires explicit user authorization.** It has been withheld all batch as a
  standing rule, and a peer's report of a process gap does not supply it. The implementer must have
  the user confirm directly before touching that file. Resolved: obtained directly via
  `AskUserQuestion`, showing the exact proposed content, before any edit.
- The reporting session notes the repo's own merge drivers resolved #205's conflict cleanly once
  attempted — so the conflict was never hard, only invisible. Worth reflecting in the wording: the
  fix is usually trivial once the cause is known, which is precisely why the diagnostic step is
  worth documenting. Reflected in the added text ("The fix is usually trivial once the cause is
  known" framing carried via "nothing else needs investigating" and the emphasis that the fix is
  simply resolving the conflict, not a complex diagnostic).

## Implementation Notes
See `staging_artifacts/TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH/investigation.md` for the
full verification of the core technical claim.

Independently verified before touching anything: read `.github/workflows/test.yml`'s own trigger
block directly, confirming exactly what the ticket states — `pull_request:` has no branch filter,
but `push:` is restricted to `branches: [main]`, so a feature branch's own commits get CI only via
`pull_request`, evaluated against `refs/pull/N/merge` — a ref GitHub cannot compute while
`CONFLICTING`. This is standard GitHub Actions platform behavior, not something specific to this
repo needing its own empirical reproduction.

Added a new item 1 to CLAUDE.md's "CI Failure Triage" numbered list (renumbering the existing 4
items to 2-5, a mechanical shift, not a rewrite — verified no other file asserts on this section's
exact numbering before renumbering), covering exactly the 3 required pieces plus the general
principle: the `mergeable`/trigger-block check, the explicit prohibition on
re-trigger/force-push/branch-recreation (each explained as actively destroying the evidence that
would show the real cause, not just an unhelpful response), and the `git ls-remote` vs
`headRefOid` push-landed disambiguator. Kept proportionate per the ticket's own instruction — a
short branch added to existing guidance, not a rewrite (diff: 8 insertions, 4 deletions, all from
the mechanical renumbering).

Added a new test file rather than relying on manual review, pinning each Acceptance Criterion as a
real, reproducible content check against CLAUDE.md itself.

## Test Summary
- `tests/docs/test_ci_triage_absent_run_branch.py` (new, 8 tests): section presence; the
  `mergeable`/trigger-block content; the re-trigger/force-push/branch-recreation prohibition; the
  `git ls-remote`/`headRefOid` disambiguator; the general principle stated (not only the specific
  case); the absent-run branch appears before the failing-job branch (you cannot triage logs for a
  run that never existed); the numbered list stays consistently 1-5 after insertion.
- Full `tests/docs/` suite re-run: 67 passed, 1 skipped, 1 xfailed (both pre-existing, unaffected).
- The 5 `tests/tools/` files that reference "CLAUDE.md" in prose/docstrings (found via grep before
  editing, to rule out any exact-numbering dependency) re-run clean: 176 passed.

## Files Changed
- `CLAUDE.md` — new absent-run branch added to "CI Failure Triage" (item 1; existing items 1-4
  renumbered to 2-5).
- `tests/docs/test_ci_triage_absent_run_branch.py` (new) — 8 tests pinning the AC content.

## Completion Summary
Verified the core technical claim independently (read `.github/workflows/test.yml`'s own trigger
block) before scoping anything, confirming a `CONFLICTING` PR with a `pull_request:`-only trigger
produces zero CI runs, not failing or pending ones — standard GitHub Actions platform behavior.
Obtained direct user authorization for the CLAUDE.md edit via `AskUserQuestion`, showing the exact
proposed content, before making any change — the batch-level "yes" that authorized picking up this
ticket did not itself supply this authorization, per the ticket's own explicit Assumptions note.
Added a short, proportionate absent-run branch to CLAUDE.md's existing CI Failure Triage section
covering all 3 required pieces (mergeable/trigger-block check, the prohibition on
re-trigger/force-push/branch-recreation, the `git ls-remote` disambiguator) plus the general
principle the AC also requires. Pinned every AC item with a real content test rather than trusting
the prose was written as intended.

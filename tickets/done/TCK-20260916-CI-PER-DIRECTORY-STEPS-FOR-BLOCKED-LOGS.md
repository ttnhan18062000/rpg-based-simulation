---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260916-CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS
phase: done
date: 2026-09-16
tags: [testing, process-improvement, claude-md]
---

# TCK-20260916-CI-PER-DIRECTORY-STEPS-FOR-BLOCKED-LOGS

## Title
Combined CI jobs are undiagnosable when raw logs are network-blocked — split them into per-directory steps with `if: always()` so the failing directory names itself

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Routed in by `rpg-feature-planning` 2026-09-16 as a proven technique, after it solved an otherwise
undiagnosable failure.

**The problem.** `Unit · infra / observability` runs **17 test paths in a single `Run` step**
(~2,700 tests). When it fails and raw logs are unreachable, nothing identifies which directory —
let alone which test — failed. Log fetching is blocked by a Fortinet filter in this environment
(cert subject `O=Fortinet, CN=Fortiguard SDNS Blocked Page`) and the block is **per-job-blob-shard
and unpredictable**: three distinct shard hosts were blocked on 2026-09-15/16, and a partial
full-run fetch once returned six unrelated jobs' logs while silently omitting exactly the two
failing ones. Check-run annotations give only `Process completed with exit code 1`.

**The technique.** Step-level conclusions remain readable via
`gh api repos/:owner/:repo/actions/jobs/{id} --jq '.steps[]'` even when logs are blocked. Splitting
one opaque `Run` step into one step per test directory makes the failing directory name itself, with
no log access required. Repeating one level deeper reaches the file.

**Verified twice in this repo on 2026-09-16**, not taken on report:
- On the `deploy` job, step conclusions alone localised the failure to step 6 `Configure Pages`
  (with `Build` green and later steps skipped) — which led directly to the real cause, GitHub Pages
  not being enabled, with no log ever read.
- On `API / tools / logging`, step conclusions showed the failure at step 5 (`Run`) with all
  infrastructure steps green, ruling out a setup/install problem immediately.

**`if: always()` is load-bearing.** Without it the first failing step short-circuits the rest, and
the skipped steps actively mislead — a reader can take "skipped" for "passed". The workflow already
uses `if: always()` in **10** places, so this extends an existing convention rather than introducing
one.

**Cost is near zero**: steps within a job share checkout and `pip install`. No extra runner, no
extra setup.

## Scope
- Split the `unit-infra` job's single `Run` step into one step per test path (or per sensible
  grouping), each with `if: always()`, preserving the existing markers and `--junit-xml` output.
- **Verify on one job before any repo-wide rollout** — a per-directory split changes pytest
  invocation boundaries, so anything relying on cross-directory collection or session-scoped
  fixtures could behave differently. Compare pass/fail/skip/deselect counts before and after.
- If the single-job trial is clean, apply the same shape to the other combined jobs.
- **Document the diagnostic in CLAUDE.md's CI Failure Triage section**: step conclusions are
  readable when logs are not, and a *partial* log fetch is not evidence that log fetching works —
  it can silently omit exactly the failing job. **This part requires the user's direct
  authorization before editing CLAUDE.md** (see Assumptions).

## Out of Scope
- Fixing the network block. It is environmental and not ours to change.
- Changing which tests run, their markers, or their grouping semantics beyond step boundaries.
- The `deploy` and `Slow regression` lanes' own failures — separately ticketed and deferred.

## Acceptance Criteria
- [ ] `unit-infra`'s steps name their own directories, and a deliberately-failing test in one
      directory produces a step list that identifies that directory without any log access.
- [ ] Every split step carries `if: always()`, verified by reading the workflow rather than assuming.
- [ ] Before/after counts for the trial job match (passed/failed/skipped/deselected), proving the
      split did not change collection semantics.
- [ ] CLAUDE.md's CI Failure Triage documents the step-conclusion technique and the partial-fetch
      caveat — **only after the user authorizes that edit**.

## Related Tickets
- `TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH` (done) — the adjacent triage gap; this extends
  the same section
- `TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2` (P3/BLOCKED) — a failure whose cause
  took two sessions partly because its logs were unreadable

## Related Docs
- `CLAUDE.md` — "CI Failure Triage", including the existing Fortinet-blocked-log-fetch guidance
  this builds on

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `.github/workflows/test.yml` (the `unit-infra` job's `Run` step; `if: always()` used 10x already)
- `CLAUDE.md`

## Assumptions / Open Questions
- **Editing CLAUDE.md requires explicit user authorization.** The user approved this ticket's
  creation; confirm the CLAUDE.md portion directly with them before touching that file, as was done
  for `TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH`.
- The right granularity is undecided: 17 separate steps may be more noise than value. Grouping into
  4-6 steps may localise well enough at lower cost. The implementer should choose and record why.
- Whether `--junit-xml` output needs one file per step or can stay combined is unverified.

## Implementation Notes
The originating session's implementer already built and then reverted a diagnostic split, so
`.github/workflows/test.yml` is byte-identical to its pre-diagnostic state — nothing is half-applied.

## Test Summary
- Chose one step per listed test path (17 steps, not a 4-6 group), matching the ticket's own
  title/AC wording ("unit-infra's steps name their own directories") for maximum diagnostic
  specificity; cost is negligible since steps already share checkout/pip-install.
- Before/after verification, run locally rather than assumed: captured the combined single-step
  baseline (`pytest <all 17 paths> -m "not slow and not extra_slow"`) → 2696 passed, 1 skipped, 0
  failed. Then ran each of the 17 paths separately with the identical marker filter and summed:
  2696 passed, 1 skipped, 0 failed — exact match, confirming the split does not change pytest
  collection semantics.
- `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml'))"` — valid YAML
  after the edit; confirmed 24 steps in the `unit-infra` job (checkout/setup/pip-install, 17 `Run:`
  steps, `Merge JUnit XML`, then the pre-existing base-branch-diff and summary steps unchanged).
- `if: always()` verified present on all 17 new `Run:` steps plus the merge step by reading the
  edited YAML directly, not assumed.
- CLAUDE.md doc addition: added `tests/docs/test_ci_per_directory_steps_documented.py` (3 tests,
  pinning the step-conclusion technique, the owning ticket ID, and the partial-fetch caveat as real
  content checks against CLAUDE.md's own text) — all pass, alongside the pre-existing
  `test_ci_triage_absent_run_branch.py` (11 total, no collision).

## Files Changed
- `.github/workflows/test.yml` — `unit-infra` job: replaced the single combined 17-path `Run` step
  with 17 per-directory `Run: <path>` steps (each `if: always()`, each writing its own
  `reports/junit/unit-infra-<name>.xml`), plus a new `Merge JUnit XML` step (`if: always()`) that
  recombines them into the same `reports/junit/unit-infra.xml` the existing "Job summary" step
  already reads — no change needed downstream of the merge.
- `CLAUDE.md` — "CI Failure Triage" section: added the step-level-conclusions diagnostic (readable
  even when raw logs are TLS-blocked) and the partial-log-fetch caveat, under item 2's existing
  TLS-block sub-bullets. **Edited only after direct `AskUserQuestion` authorization**, matching the
  precedent set for `TCK-20260915-CI-TRIAGE-HAS-NO-ABSENT-RUN-BRANCH`.
- `tests/docs/test_ci_per_directory_steps_documented.py` (new) — pins the CLAUDE.md addition.

## Completion Summary
Split only the `unit-infra` job (the trial), per the ticket's own "verify on ONE job first"
constraint — the wider rollout to other combined jobs is left for a follow-up once this trial has
run in real CI, not applied speculatively here. The technique itself was independently useful
during this same session: used to localize a real, unrelated `deploy` job failure
(`Configure Pages`) to one step with zero log access, before this ticket's own code was written.

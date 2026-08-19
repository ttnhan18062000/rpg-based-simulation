---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260819-SKILL-STALENESS-SOFT-WARNING
phase: done
date: 2026-08-19
tags: [testing, skills, agent-monitoring]
---

# TCK-20260819-SKILL-STALENESS-SOFT-WARNING

## Title
Downgrade zero-invocation skill-staleness assertions from hard CI failure to a soft warning

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Real CI failure (2026-08-19, on the `codebase-resilience-p0-batch` PR's "API / tools / logging"
job, unrelated to that PR's own changes): `tests/tools/test_generate_retro.py`'s
`test_backend_testing_post_fix_state_not_currently_flagged` and
`test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus` both hard-fail.

Root cause confirmed genuine, not a bug: `compute_zero_invocation_skill_flags()`
(`tools/agent-monitoring/generate_retro.py`) cross-references the real `.claude/skills/*/SKILL.md`
catalog against real `agent-monitoring/tools.jsonl` `Skill`-tool invocation history. 6 skills
(`backend-testing`, `observability`, `simq-dev`, `systems-economy`, `combat-mechanics`,
`progression-entities`) have `date_added: "2026-08-05"` and a 14-day grace period
(`SKILL_ZERO_INVOCATION_GRACE_PERIOD_DAYS`). Independently confirmed via a full-history scan of
`tools.jsonl` (245 real `Skill`-tool rows total): all 6 have **zero** real invocations ever
recorded (a 7th, `cognition-strategy`, has exactly 1 and correctly stays unflagged). Today
(2026-08-19) is exactly 14 days after 2026-08-05 — the grace period expired today, flipping both
tests from pass to fail purely from calendar time, independent of any code change on any branch.
This will hard-block every PR/push today and any day these skills remain genuinely unused.

The two failing tests assert a permanent invariant ("this specific skill must never appear in
`flagged_stale`") about a real, live, organically-evolving corpus that CI cannot control —
whether a domain-specific skill like `combat-mechanics` gets a real invocation depends entirely on
whether combat-domain work happens to land in a PR, which is not something a test author or CI can
force. This is the same class of problem `TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING`
already solved for performance-threshold assertions: downgrade to a non-blocking warning that
still surfaces the real signal (skill usage should be tracked and eventually acted on) without
hard-blocking unrelated work indefinitely.

## Scope
- Add a shared soft-check helper for `tools/agent-monitoring/`'s zero-invocation skill-staleness
  checks, mirroring `tests/tools/perf_assertions.py`'s exact pattern
  (`SkillStalenessWarning(UserWarning)` + a `skill_staleness_check(ok, message, *, hard=False)`
  function with a `hard=True` escape hatch) — do not invent a different shape, reuse the
  established convention for consistency and reviewability.
- Convert `test_backend_testing_post_fix_state_not_currently_flagged` and
  `test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus` in
  `tests/tools/test_generate_retro.py` to use the new soft-check helper instead of a bare
  `assert`.
- Add a `docs/testing/regression_policy.md` Soft Monitors row for doc/code parity, matching the
  precedent's own Finalize step.
- Leave `compute_zero_invocation_skill_flags()` itself, the 14-day grace period constant, and the
  `flagged_stale`/`flagged_unknown_age` classification logic completely untouched — the detection
  mechanism is correct and should keep working exactly as designed; only the *test-level assertion
  severity* for these 2 specific real-corpus tests changes.

## Out of Scope
- Any other test in `test_generate_retro.py` (only these 2 specific real-corpus tests are
  affected by this exact failure mode; do not sweep other tests in the same file).
- Actually invoking the 6 unused skills for real, or artificially bumping their `date_added` —
  neither addresses the real signal honestly.
- Changing `SKILL_ZERO_INVOCATION_GRACE_PERIOD_DAYS` (14 days) — a separate calibration question,
  not this ticket's scope.
- `tests/tools/test_parity_index_baseline.py`'s unrelated CI failure on the same PR — already
  fixed separately in `TCK-20260819-HOTFIX-PARITY-BASELINE-DEAD-INFRA-DRIFT`.

## Acceptance Criteria
- [x] `tests/tools/test_generate_retro.py::test_backend_testing_post_fix_state_not_currently_flagged`
      and `::test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus` no longer
      hard-fail when a tracked skill is genuinely past its grace period with zero invocations —
      they emit a warning instead and the test itself still passes.
      Evidence: full scoped run today (2026-08-19, grace period genuinely expired for
      combat-mechanics/observability/progression-entities/simq-dev/systems-economy) shows
      `156 passed, 2 warnings` — both named tests are in the passed count and appear in the
      `-rw` warnings summary, not the failure summary.
- [x] The real staleness signal is still visible (not silently dropped) — a
      `SkillStalenessWarning` (or equivalently-named) fires with the actual flagged skill name(s),
      the grace period, and enough detail to act on later, matching `PerformanceThresholdWarning`'s
      shape.
      Evidence: `-rw` output shows
      `SkillStalenessWarning: [...test_backend_testing_post_fix_state_not_currently_flagged] skill
      'backend-testing' flagged stale (zero invocations past 14-day grace period):
      flagged_stale=[...]` and the equivalent for the 5 flagged domain skills on the second test —
      both include skill name(s), grace period days, and full `flagged_stale` list.
- [x] `hard=True` escape hatch exists and is available for any future test that needs a genuine
      hard gate on this mechanism (mirrors `perf_check`'s own `hard` parameter).
      Evidence: `skill_staleness_check(ok, message, *, hard=False)` in
      `tests/tools/skill_staleness_assertions.py`; proven by
      `test_skill_staleness_check_hard_true_raises` (passes).
- [x] The rest of `tests/tools/test_generate_retro.py` (all other tests) still passes unchanged.
      Evidence: full scoped run `156 passed, 0 failed`; collection count confirmed 153 (baseline,
      via `git stash`) -> 156 (+3, exactly the 3 new Step 4 unit tests — Steps 2/3 converted
      existing tests in place, adding none).

## Related Tickets
- TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING (the precedent this ticket mirrors)
- TCK-20260819-HOTFIX-PARITY-BASELINE-DEAD-INFRA-DRIFT (sibling CI-failure fix from the same PR,
  unrelated root cause)
- TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC (authored the 6 domain skills these tests guard)
- TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED (authored `backend-testing`'s real `date_added`)

## Related Docs
- docs/testing/regression_policy.md (Soft Monitors section — needs a new row for this mechanism,
  matching the precedent's own Finalize step)
- tests/tools/perf_assertions.py (the pattern to mirror, not to modify)

## Related Stored Artifacts
None yet.

## Related Code Areas
- tests/tools/test_generate_retro.py
- tests/tools/ (new shared helper file, e.g. `skill_staleness_assertions.py`)
- tools/agent-monitoring/generate_retro.py (read-only reference; not modified)

## Assumptions / Open Questions
- None — root cause independently confirmed via a full-history real-corpus scan (245 Skill-tool
  rows, 6 of 7 domain-relevant skills at zero invocations, grace period math verified exact).

## Implementation Notes
Followed `staging_artifacts/TCK-20260819-SKILL-STALENESS-SOFT-WARNING/plan.md`'s 5 steps
exactly, in order:

1. Created `tests/tools/skill_staleness_assertions.py`, a structural mirror of
   `tests/tools/perf_assertions.py`: `SkillStalenessWarning(UserWarning)`, a duplicated (not
   imported) private `_current_test_id()`, and `skill_staleness_check(ok, message, *,
   hard=False) -> bool` — byte-for-byte behavioral mirror of `perf_check`. No
   `assert_perf_threshold`-equivalent comparison wrapper was built (both real call sites are
   set-membership checks, not numeric comparisons — confirmed in investigation.md and by
   re-reading the two call sites directly).
   **Framing adjustment from the architecture reviewer (incorporated, not a deviation from
   plan.md's code shape):** the module docstring does NOT copy `perf_assertions.py`'s
   "STOPGAP...REVISIT" framing. `perf_assertions.py`'s stopgap is tied to a concrete future
   fix event (hardware-profiling landing in `src/perf/profiles.py`) that will convert it back
   to hard. Skill-invocation staleness has no analogous owning future engineering effort —
   whether a skill accrues invocations is open-ended and PR-landing-dependent, and some
   skills may legitimately never accrue real invocations by design. The docstring instead
   describes this explicitly as a durable, open-ended soft monitor: corpus- and
   calendar-driven, self-clearing per-skill the moment that skill records a real invocation
   or stays within grace period, with no future event that reverts it to hard.
2. Added the import
   `from tests.tools.skill_staleness_assertions import SkillStalenessWarning,
   skill_staleness_check` to `tests/tools/test_generate_retro.py`'s import block, and converted
   `test_backend_testing_post_fix_state_not_currently_flagged` from a bare `assert` to
   `skill_staleness_check(...)`, exactly per plan.md's Step 2 text.
3. Converted `test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus` from
   `assert domain_skills.isdisjoint(...)` to `skill_staleness_check(not stale_domain_skills,
   ...)` using `.intersection()` so the warning message names the specific flagged skill(s), per
   plan.md's Step 3 text and rationale.
4. Added 3 direct unit tests of `skill_staleness_check` itself immediately after the converted
   domain-skills test (before `test_zero_invocation_flag_has_derivation`), exactly per plan.md's
   Step 4 text: `test_skill_staleness_check_ok_returns_true_no_warning`,
   `test_skill_staleness_check_warns_not_raises_by_default`,
   `test_skill_staleness_check_hard_true_raises`.
5. Added one new row to `docs/testing/regression_policy.md` §3 "Soft Monitors — Alert Only",
   immediately after the "Performance-threshold assertions" row, following the same
   `Test Group | Location | Reason for Soft Status` column format. Per the reviewer's framing
   adjustment, the row's prose explicitly distinguishes this from the Performance-threshold
   row: it states there is no owning future engineering effort that converts this back to hard,
   and describes it as durable/open-ended rather than a temporary stopgap.

No deviations from plan.md's code shape or file list. The one adjustment (docstring/doc-row
framing, not "STOPGAP...REVISIT") was directed by the architecture reviewer's advisory finding
and is documented in `staging_artifacts/TCK-20260819-SKILL-STALENESS-SOFT-WARNING/plan.md`'s
Deviations section as an intentional plan refinement.

Verification: collection count went from 153 (baseline, confirmed via `git stash`) to 156
(+3, matching plan.md's AC4 expectation of "3 new unit tests, module adds none" — Steps 2/3
convert existing tests in place and add no new test functions). Full scoped run
(`tests/tools/test_generate_retro.py -m "not slow and not extra_slow" --tb=short -q -rw`):
`156 passed, 2 warnings` — both converted real-corpus tests emitted `SkillStalenessWarning`
in the `-rw` summary today (2026-08-19), because the grace period has genuinely expired for
5 of the 6 tracked domain skills plus `backend-testing`, confirming both the warn-not-fail
path (AC1) and the actionable-detail path (AC2) live, not merely via the deterministic Step 4
unit tests.

## Test Summary
- `tests/tools/test_generate_retro.py -m "not slow and not extra_slow" --tb=short -q -rw`:
  156 passed, 0 failed, 2 warnings (`SkillStalenessWarning` from both converted real-corpus
  tests, confirming the grace period is genuinely expired today for `backend-testing` and 5 of
  the 6 domain skills — `combat-mechanics`, `observability`, `progression-entities`,
  `simq-dev`, `systems-economy`).
- `tests/tools/test_generate_retro.py -k "skill_staleness_check" -v`: 3 passed (the new direct
  unit tests).
- Collection count: 153 (baseline, `git stash`) -> 156 (+3) — confirms Steps 2/3 converted
  existing tests in place (no net new test from those 2 steps) and Step 4 added exactly 3.
- `python3 -c "from tests.tools.skill_staleness_assertions import SkillStalenessWarning,
  skill_staleness_check"`: imports cleanly.
- Confirmed via `git diff --stat`/`git status --short` that `tests/tools/perf_assertions.py`
  and `tools/agent-monitoring/generate_retro.py` are untouched (Scope Guards).

## Files Changed
- `tests/tools/skill_staleness_assertions.py` (new file) — `SkillStalenessWarning`,
  `_current_test_id()`, `skill_staleness_check()`.
- `tests/tools/test_generate_retro.py` — added the new import; converted
  `test_backend_testing_post_fix_state_not_currently_flagged` and
  `test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus` to use
  `skill_staleness_check`; added 3 new direct unit tests
  (`test_skill_staleness_check_ok_returns_true_no_warning`,
  `test_skill_staleness_check_warns_not_raises_by_default`,
  `test_skill_staleness_check_hard_true_raises`).
- `docs/testing/regression_policy.md` — added one new row to §3 "Soft Monitors — Alert Only"
  for the zero-invocation skill-staleness soft monitor.
- `tickets/inprogress/TCK-20260819-SKILL-STALENESS-SOFT-WARNING.md` — this ticket (Status,
  Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary).
- `staging_artifacts/TCK-20260819-SKILL-STALENESS-SOFT-WARNING/plan.md` — Deviations section
  added documenting the reviewer's framing adjustment.

## Completion Summary
Implemented the soft-warning downgrade for the 2 real-corpus zero-invocation skill-staleness
tests in `tests/tools/test_generate_retro.py`, mirroring `tests/tools/perf_assertions.py`'s
`perf_check`/`PerformanceThresholdWarning` shape via a new parallel module,
`tests/tools/skill_staleness_assertions.py` (`SkillStalenessWarning` +
`skill_staleness_check(ok, message, *, hard=False)`), with no numeric-comparison wrapper since
neither real call site needs one. Both named tests now warn instead of hard-failing when a
tracked skill is genuinely past its grace period with zero invocations, while the other 9
tests in the same "zero invocation" test group, `compute_zero_invocation_skill_flags()`, and
`perf_assertions.py` itself were left untouched. Per the architecture reviewer's advisory
finding, the new module's docstring and the new `docs/testing/regression_policy.md` row
describe this explicitly as a durable, open-ended soft monitor (corpus- and calendar-driven,
self-clearing per skill) rather than copying the perf precedent's temporary
"STOPGAP...REVISIT" framing, since there is no single owning future engineering effort that
will convert skill-invocation staleness back to a hard check. Full scoped verification:
156 passed, 0 failed, with both converted tests visibly emitting `SkillStalenessWarning` in
the `-rw` summary today, proving the mechanism live against the real corpus, not just via the
3 new deterministic unit tests.

---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260819-SKILL-STALENESS-SOFT-WARNING
artifact_type: plan
tags: [testing, skills, agent-monitoring]
---

# Implementation Plan — TCK-20260819-SKILL-STALENESS-SOFT-WARNING

## Summary
Mirror `tests/tools/perf_assertions.py`'s exact shape into a new parallel file,
`tests/tools/skill_staleness_assertions.py` (`SkillStalenessWarning(UserWarning)` +
`skill_staleness_check(ok, message, *, hard=False)`, no `assert_perf_threshold`-equivalent
comparison wrapper — the 2 real call sites are set-membership checks, not numeric threshold
comparisons), then convert exactly the 2 named real-corpus tests in
`tests/tools/test_generate_retro.py` from bare `assert` to calls through the new helper. Add 3
direct unit tests of the new helper itself so AC2 (warning fires with actionable detail) and AC3
(`hard=True` escape hatch) are provable deterministically regardless of whether today's real
corpus happens to be in a flagged or unflagged state. Close with a `docs/testing/
regression_policy.md` Soft Monitors row mirroring the precedent ticket's own row. No other test
in the file, `compute_zero_invocation_skill_flags()`, or `perf_assertions.py` is touched.

## Steps

### Step 1 — Create the shared soft-check helper module
**Files:** `tests/tools/skill_staleness_assertions.py` (new file)
**Change:** Create a new module mirroring `tests/tools/perf_assertions.py` (read in full;
confirmed lines 1-119) structurally and by convention, but with no numeric-comparison wrapper:

- Module docstring citing this ticket (`TCK-20260819-SKILL-STALENESS-SOFT-WARNING`) and the
  precedent (`TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING`), explaining the calendar-driven
  nature of grace-period expiry (per `tools/agent-monitoring/generate_retro.py:536`, confirmed by
  direct read: `if (today - added_date).days >= SKILL_ZERO_INVOCATION_GRACE_PERIOD_DAYS:`) as the
  reason this is a soft, not hard, check — and explicitly stating (mirroring
  `perf_assertions.py:17-21`) that this is not a license to soften genuine correctness/logic
  checks elsewhere in the same test file.
- `class SkillStalenessWarning(UserWarning):` — bare docstring-only subclass, same shape as
  `perf_assertions.py:35-41`'s `PerformanceThresholdWarning`.
- A local `_current_test_id() -> str` helper, duplicated (not imported) from
  `perf_assertions.py:44-53` — reads `PYTEST_CURRENT_TEST`, strips the `" (phase)"` suffix,
  falls back to `"<unknown test>"`. Duplicated because `perf_assertions.py` does not export it
  and must not be modified (ticket's Related Docs: "the pattern to mirror, not to modify").
- `def skill_staleness_check(ok: bool, message: str, *, hard: bool = False) -> bool:` —
  byte-for-byte behavioral mirror of `perf_assertions.py:64-86`'s `perf_check`: if `ok`, return
  `True`; else build `full_message = f"[{_current_test_id()}] {message}"`; if `hard`, raise
  `AssertionError(full_message)`; else `warnings.warn(full_message, SkillStalenessWarning,
  stacklevel=3)` and return `False`.
- **No `assert_perf_threshold`-equivalent wrapper.** Decision (per investigation.md's Risks
  section, confirmed by reading both call sites at `test_generate_retro.py:2350` and `:2405`):
  both real call sites are boolean set-membership conditions (`"x" not in
  result["flagged_stale"]`, `domain_skills.isdisjoint(set(result["flagged_stale"]))`), not
  numeric threshold comparisons. `skill_staleness_check` alone is a complete, correctly-scoped
  mirror of `perf_check`; building an unused comparison-operator wrapper would be speculative
  generality with no call site, contrary to this repo's `test-driven-development`/YAGNI norms.
**Do NOT touch:** `tests/tools/perf_assertions.py` itself — read-only reference, not modified
(confirmed nothing in it is perf-specific in a way that would require generalizing for reuse; a
clean parallel file is correct, no shared base module).
**Verify:** File imports cleanly (`python3 -c "from tests.tools.skill_staleness_assertions import
SkillStalenessWarning, skill_staleness_check"` from repo root); new Step 4 unit tests exercise it
directly.

### Step 2 — Convert `test_backend_testing_post_fix_state_not_currently_flagged`
**Files:** `tests/tools/test_generate_retro.py`
**Change:** Add the import (co-located with the existing `generate_retro` import block at
lines 20-39, confirmed by direct read):
```python
from tests.tools.skill_staleness_assertions import SkillStalenessWarning, skill_staleness_check
```
Replace the test body (confirmed exact current text, lines 2343-2350):
```python
def test_backend_testing_post_fix_state_not_currently_flagged():
    """Real-corpus check: the actual, current .claude/skills/backend-testing/SKILL.md has a
    real date_added (2026-08-05, post-fix) — as of this ticket it is within the grace period, so
    it must not appear in flagged_stale on the real catalog today."""
    result = compute_zero_invocation_skill_flags(
        generate_retro.load_jsonl(generate_retro.DEFAULT_TOOLS_FILE)
    )
    assert "backend-testing" not in result["flagged_stale"]
```
with:
```python
def test_backend_testing_post_fix_state_not_currently_flagged():
    """Real-corpus check: the actual, current .claude/skills/backend-testing/SKILL.md has a
    real date_added (2026-08-05, post-fix) — as of this ticket it is within the grace period, so
    it must not appear in flagged_stale on the real catalog today. Soft-checked (TCK-20260819-
    SKILL-STALENESS-SOFT-WARNING): grace-period expiry is calendar-driven, not code-driven, so a
    miss here warns rather than hard-fails CI — see tests/tools/skill_staleness_assertions.py."""
    result = compute_zero_invocation_skill_flags(
        generate_retro.load_jsonl(generate_retro.DEFAULT_TOOLS_FILE)
    )
    skill_staleness_check(
        "backend-testing" not in result["flagged_stale"],
        f"skill 'backend-testing' flagged stale (zero invocations past "
        f"{result['grace_period_days']}-day grace period): "
        f"flagged_stale={result['flagged_stale']!r}",
    )
```
`result['grace_period_days']` confirmed present on the return dict at
`tools/agent-monitoring/generate_retro.py:540` (`"grace_period_days":
SKILL_ZERO_INVOCATION_GRACE_PERIOD_DAYS`), read directly — not inferred.
**Do NOT touch:** The other 9 tests in the same "zero invocation" group
(`test_zero_invocation_flag_excludes_skill_within_grace_period`,
`test_zero_invocation_flag_includes_skill_past_grace_period_with_zero_invocations`,
`test_zero_invocation_flag_excludes_skill_with_nonzero_invocations_regardless_of_age`,
`test_backend_testing_pre_fix_state_would_have_been_flagged`,
`test_zero_invocation_flag_function_never_crashes_on_malformed_skill_md`,
`test_zero_invocation_flag_catalog_scan_is_pure_no_file_mutation`,
`test_grace_period_missing_date_added_policy_is_explicit_not_accidental`,
`test_flagged_skills_list_never_auto_triggers_downstream_action`,
`test_six_domain_skills_verdict_not_reopened`, `test_zero_invocation_flag_has_derivation`,
`test_generate_without_all_tools_never_computes_zero_invocation_flags`) — all use `tmp_path`
synthetic fixtures or source-inspection guards, are timeless, and must stay bare `assert`.
**Verify:** `pytest tests/tools/test_generate_retro.py::test_backend_testing_post_fix_state_not_currently_flagged -v -rw` — passes today (2026-08-19) with `backend-testing` still inside its
14-day grace period per the ticket's own root-cause note (grace period expired for the *other* 5
domain skills' `date_added`, but `backend-testing` shares the same `date_added` and is explicitly
named as flagged in the ticket — re-run and read the actual result to confirm which path
(pass-clean vs. warn) executes; either is correct per AC1, only a hard failure is wrong).

### Step 3 — Convert `test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus`
**Files:** `tests/tools/test_generate_retro.py`
**Change:** Replace the test body (confirmed exact current text, lines 2393-2405):
```python
def test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus():
    """Real-corpus check (AC2): the 6 domain skills authored by
    TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC must never appear in flagged_stale today —
    either because they now have >=1 real invocation, or because they are still within the grace
    period. Never hardcodes "all 6 show zero" (that snapshot has already drifted)."""
    domain_skills = {
        "observability", "simq-dev", "systems-economy",
        "combat-mechanics", "cognition-strategy", "progression-entities",
    }
    result = compute_zero_invocation_skill_flags(
        generate_retro.load_jsonl(generate_retro.DEFAULT_TOOLS_FILE)
    )
    assert domain_skills.isdisjoint(set(result["flagged_stale"]))
```
with:
```python
def test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus():
    """Real-corpus check (AC2): the 6 domain skills authored by
    TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC must never appear in flagged_stale today —
    either because they now have >=1 real invocation, or because they are still within the grace
    period. Never hardcodes "all 6 show zero" (that snapshot has already drifted). Soft-checked
    (TCK-20260819-SKILL-STALENESS-SOFT-WARNING): see tests/tools/skill_staleness_assertions.py."""
    domain_skills = {
        "observability", "simq-dev", "systems-economy",
        "combat-mechanics", "cognition-strategy", "progression-entities",
    }
    result = compute_zero_invocation_skill_flags(
        generate_retro.load_jsonl(generate_retro.DEFAULT_TOOLS_FILE)
    )
    stale_domain_skills = domain_skills.intersection(set(result["flagged_stale"]))
    skill_staleness_check(
        not stale_domain_skills,
        f"domain skill(s) flagged stale (zero invocations past "
        f"{result['grace_period_days']}-day grace period): {sorted(stale_domain_skills)!r} "
        f"(full flagged_stale={result['flagged_stale']!r})",
    )
```
Note: `domain_skills.isdisjoint(set(result["flagged_stale"]))` is logically equivalent to `not
domain_skills.intersection(set(result["flagged_stale"]))` — switched to `intersection` so the
warning message can name the *specific* domain skill(s) that tripped it (AC2 requires "the
actual flagged skill name(s)"), which a bare `isdisjoint` boolean cannot express on its own.
**Do NOT touch:** Same 9-test exclusion list as Step 2. Do not add or remove any skill from the
`domain_skills` set — that set's membership is out of scope (a separate question from this
ticket, tracked by `TCK-20260705-SIX-SKILLS-INVESTIGATION`'s settled verdict).
**Verify:** `pytest tests/tools/test_generate_retro.py::test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus -v -rw`.

### Step 4 — Add direct unit tests for the new helper's own behavior
**Files:** `tests/tools/test_generate_retro.py` (co-located immediately after the 2 converted
tests, before `test_zero_invocation_flag_has_derivation`, per `test_plan.md`'s recommended
placement)
**Change:** Add 3 tests exercising `skill_staleness_check` directly with controlled `ok` values —
required (not merely "nice to have") because the 2 real-corpus tests in Steps 2-3 only exercise
whichever branch (pass vs. warn) the real corpus happens to be in *today*; only a direct unit
test can deterministically prove AC2 (warning fires with detail) and AC3 (`hard=True` raises) on
every future CI run regardless of corpus drift:
```python
def test_skill_staleness_check_ok_returns_true_no_warning(recwarn):
    assert skill_staleness_check(True, "unused message") is True
    assert len(recwarn) == 0


def test_skill_staleness_check_warns_not_raises_by_default():
    with pytest.warns(SkillStalenessWarning, match="some-skill flagged stale"):
        result = skill_staleness_check(False, "some-skill flagged stale: detail")
    assert result is False


def test_skill_staleness_check_hard_true_raises():
    with pytest.raises(AssertionError, match="some-skill flagged stale"):
        skill_staleness_check(False, "some-skill flagged stale: detail", hard=True)
```
`pytest` is already imported at `test_generate_retro.py:14`; `recwarn` is a built-in pytest
fixture, no new import needed.
**Do NOT touch:** The other 9 "zero invocation" tests, or `compute_zero_invocation_skill_flags`
in any way — these 3 new tests call only `skill_staleness_check` with literal `bool`/`str`
arguments, never the real corpus or the catalog-scan function.
**Verify:** `pytest tests/tools/test_generate_retro.py -k "skill_staleness_check" -v`.

### Step 5 — Document the new soft-monitor mechanism
**Files:** `docs/testing/regression_policy.md`
**Change:** Add one new row to the §3 "Soft Monitors — Alert Only" table (confirmed current
table at lines 56-68, existing "Performance-threshold assertions" row at line 67), immediately
after that row, following its exact column format (`Test Group | Location | Reason for Soft
Status`):
```
| Zero-invocation skill-staleness assertions | `tests/tools/test_generate_retro.py::test_backend_testing_post_fix_state_not_currently_flagged`, `::test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus` | **TCK-20260819-SKILL-STALENESS-SOFT-WARNING**: these 2 tests cross-reference the real `.claude/skills/*/SKILL.md` catalog against real `agent-monitoring/tools.jsonl` invocation history via `compute_zero_invocation_skill_flags()` (`tools/agent-monitoring/generate_retro.py`) — whether a domain-specific skill accrues a real invocation depends on which PRs happen to land, not something a test author or CI can force, and a skill's grace-period expiry is purely calendar-driven. A flag miss emits `tests/tools/skill_staleness_assertions.SkillStalenessWarning` (visible in pytest's `-rw` warnings summary, with the flagged skill name(s), grace period, and test id) instead of failing the test. The other 9 tests in the same "zero invocation" test group (synthetic `tmp_path` fixtures and source-inspection guards on `compute_zero_invocation_skill_flags()` itself) stay hard failures — see `tests/tools/skill_staleness_assertions.py`'s module docstring. This mirrors the Performance-threshold assertions row above (same soft-monitor pattern, different subsystem). |
```
**Do NOT touch:** Any other row or section in `regression_policy.md`, including the
Performance-threshold row itself.
**Verify:** Visual diff — table renders correctly, row count in §3 increases by exactly 1.

## Scope Guards
- Do not convert any of the other 9 tests in the "zero invocation" test group (`test_generate_retro.py:2291-2427`, excluding the 2 named tests) from `assert` to `skill_staleness_check` — they are synthetic/structural/source-inspection checks and must stay hard per investigation.md's confirmed audit.
- Do not modify `compute_zero_invocation_skill_flags()`, `SKILL_ZERO_INVOCATION_GRACE_PERIOD_DAYS`, or any classification logic in `tools/agent-monitoring/generate_retro.py` — read-only reference throughout this plan.
- Do not modify `tests/tools/perf_assertions.py` in any way — reference pattern only, confirmed unmodified by `git diff` per test_plan.md's Anti-Drift Test Guards.
- Do not change the `domain_skills` set's membership (the 6 named skills) in Step 3 — that is `TCK-20260705-SIX-SKILLS-INVESTIGATION`'s settled scope, not this ticket's.
- Do not artificially bump any skill's `date_added` in `.claude/skills/*/SKILL.md`, or fabricate `Skill`-tool rows in `agent-monitoring/tools.jsonl`, to make the real-corpus tests pass "for real" — defeats the honest-signal purpose of the mechanism.
- Do not build an `assert_perf_threshold`-equivalent numeric-comparison wrapper in the new helper module — no call site needs it (Step 1 decision, explicit).
- Do not touch any other test in `test_generate_retro.py` outside the "zero invocation" group (skill usage section, retro metrics, tag breakdown, KGMCP cache efficiency, reason-code sections, etc.).

## Dependency Map
- Step 1 (helper module) must land before Steps 2, 3, and 4 — all three import from it.
- Steps 2 and 3 are independent of each other (different test functions, same file — sequential edits, no functional coupling).
- Step 4 depends only on Step 1 (does not depend on Steps 2 or 3's specific wording).
- Step 5 (docs) is independent of Steps 2-4's exact code and can be done last, matching the precedent ticket's own Finalize-step convention; sequenced last here only by convention, not by a hard dependency.

## Acceptance Criteria Map
| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: the 2 named tests no longer hard-fail when a tracked skill is past grace with zero invocations — they warn instead and the test itself still passes | Steps 1, 2, 3 | `pytest tests/tools/test_generate_retro.py -k "backend_testing_post_fix or zero_invocation_flag_current_domain" -v -rw` |
| AC2: the real staleness signal is still visible — a `SkillStalenessWarning` fires with the actual flagged skill name(s), the grace period, and actionable detail | Steps 1 (class + message format), 2, 3 (message content), 4 (deterministic proof) | `test_skill_staleness_check_warns_not_raises_by_default`; manual `-rw` inspection of Steps 2/3 output |
| AC3: `hard=True` escape hatch exists and is available for any future test needing a genuine hard gate | Step 1 (function signature), Step 4 (direct proof) | `test_skill_staleness_check_hard_true_raises` |
| AC4: the rest of `test_generate_retro.py` (all other tests) still passes unchanged | Scope Guards (no other test touched) | `pytest tests/tools/test_generate_retro.py -m "not slow and not extra_slow" --tb=short -q -rw` (full-file run); collection-count check (`--collect-only -q` before/after, 135 + 4 new = 139) |

## Anti-Drift Notes
- The grace period expired *today* (2026-08-19) for 5 of 6 domain skills' `date_added:
  "2026-08-05"`; `backend-testing` shares that same `date_added`. Step 2/3's real-corpus test
  runs may observe either the pass-clean path or the warn path depending on exact execution
  timing/timezone — both are correct outcomes per AC1 (the test process itself must not hard-fail
  either way); do not "fix" this by adjusting dates or corpus data.
- `test_flagged_skills_list_never_auto_triggers_downstream_action` and
  `test_six_domain_skills_verdict_not_reopened` are source-inspection guards on
  `compute_zero_invocation_skill_flags()`'s own code/`derivation` string — both untouched by this
  plan, but re-run them explicitly (part of the full-file verification in the AC4 row) since they
  sit in the same function's blast radius.
- `perf_assertions.py`'s `_current_test_id()` is intentionally duplicated, not imported, into
  `skill_staleness_assertions.py` — it is a private (underscore-prefixed) helper not part of
  `perf_assertions.py`'s public surface, and importing a private helper across modules would
  create an undocumented coupling the "not to be modified" instruction is meant to avoid.
- The message format in Steps 2 and 3 embeds `result['grace_period_days']` and the flagged-skill
  list directly in the warning text (not just a bare boolean) — this is required by AC2's "enough
  detail to act on later" wording, not optional embellishment.

## Deviations

**Architecture-review framing adjustment (Steps 1 and 5 prose only — code shape unchanged).**
The architecture reviewer flagged (non-blocking advisory, approved otherwise) that Step 1's
plan text drew the module docstring from `perf_assertions.py`'s "STOPGAP...REVISIT" framing
too literally. That framing is correct for the perf precedent because it is tied to a concrete
future fix event (hardware-profiling work landing in `src/perf/profiles.py`) that will convert
it back to a hard check. Skill-invocation staleness has no analogous future "fix" event —
whether a skill accrues invocations depends on which PRs happen to land, which is open-ended,
and some tracked skills may legitimately never accrue real invocations by design.

Implemented as directed: `tests/tools/skill_staleness_assertions.py`'s module docstring (Step 1)
and the `docs/testing/regression_policy.md` row (Step 5) describe this mechanism explicitly as
a durable, open-ended soft monitor — corpus- and calendar-driven, self-clearing per-skill once
that skill records a real invocation or stays within grace period, with no owning future
engineering effort that will revert it to hard. This is a framing/documentation adjustment
only: the code shape (`SkillStalenessWarning` + `skill_staleness_check(ok, message, *,
hard=False)`, mirroring `perf_check`'s structure), file list, and scope are unchanged from the
plan as originally written and approved.

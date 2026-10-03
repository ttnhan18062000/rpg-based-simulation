---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260819-SKILL-STALENESS-SOFT-WARNING
artifact_type: test_plan
tags: [testing, skills, agent-monitoring]
---

# Test Plan — TCK-20260819-SKILL-STALENESS-SOFT-WARNING

## Regression Surface

**Unit (`tests/tools/test_generate_retro.py` — must all still pass, 135 `test_` functions in
this file total):**
- The remaining 9 tests in the "zero invocation" test group (lines 2291-2427), unchanged and
  still hard-asserting:
  `test_zero_invocation_flag_excludes_skill_within_grace_period`,
  `test_zero_invocation_flag_includes_skill_past_grace_period_with_zero_invocations`,
  `test_zero_invocation_flag_excludes_skill_with_nonzero_invocations_regardless_of_age`,
  `test_backend_testing_pre_fix_state_would_have_been_flagged`,
  `test_zero_invocation_flag_function_never_crashes_on_malformed_skill_md`,
  `test_zero_invocation_flag_catalog_scan_is_pure_no_file_mutation`,
  `test_grace_period_missing_date_added_policy_is_explicit_not_accidental`,
  `test_flagged_skills_list_never_auto_triggers_downstream_action`,
  `test_six_domain_skills_verdict_not_reopened`,
  `test_zero_invocation_flag_has_derivation`,
  `test_generate_without_all_tools_never_computes_zero_invocation_flags`.
- Every other test in the file (skill usage section, retro metrics, tag breakdown, KGMCP
  cache efficiency, reason-code sections, etc.) — none of these touch
  `compute_zero_invocation_skill_flags()` or the new helper, but the file must still fully
  collect and pass since the import block (lines 20-39) is shared.

**Unit — the perf precedent, unmodified control group (confirm no accidental coupling):**
- `tests/tools/perf_assertions.py` itself is not imported by or modified for this ticket; no
  direct test file exists for it today (it is exercised indirectly via `tests/perf/`,
  `tests/arena/`, `tests/certification/` per the precedent ticket) — out of this ticket's
  regression surface, listed here only to confirm it is not touched.

**Integration:** none — this is pure test-infrastructure/tooling, no `src/` runtime code
changes, no integration surface.

**Arena-combat:** none — unrelated subsystem.

## New Tests Required

Per the ticket's acceptance criteria, the primary changes are *conversions* of 2 existing
tests, not new test authorship. One new smoke-level test is warranted to directly exercise the
new helper module's own mechanics (mirroring the fact that `perf_assertions.py`'s `perf_check`/
`assert_perf_threshold` behavior is implicitly covered only through its call sites in
`tests/perf/` — this ticket can do slightly better since the new helper is small):

- **Test name:** `test_skill_staleness_check_warns_not_raises_by_default` (or similar)
  **Category:** unit
  **What it verifies:** `skill_staleness_check(False, "msg")` (default `hard=False`) returns
  `False` and emits `SkillStalenessWarning` (via `pytest.warns`), does not raise.
  **Where it should live:** `tests/tools/test_generate_retro.py` (co-located with the 2
  converted tests) or a small dedicated `tests/tools/test_skill_staleness_assertions.py` —
  either is acceptable; the precedent (`perf_assertions.py`) has no dedicated test file of its
  own, so co-locating in `test_generate_retro.py` next to the converted tests is the lower-
  friction choice and keeps the "zero invocation" test group self-contained.

- **Test name:** `test_skill_staleness_check_hard_true_raises`
  **Category:** unit
  **What it verifies:** `skill_staleness_check(False, "msg", hard=True)` raises
  `AssertionError` instead of warning — the AC3 escape-hatch requirement.
  **Where it should live:** same file as above.

- **Test name:** `test_skill_staleness_check_ok_returns_true_no_warning`
  **Category:** unit
  **What it verifies:** `skill_staleness_check(True, "msg")` returns `True` and emits no
  warning (`recwarn`/`pytest.warns(None)`-style check) — confirms the pass-through path
  mirrors `perf_check`'s `if ok: return True` short-circuit exactly.
  **Where it should live:** same file as above.

These 3 are optional-but-recommended hardening beyond the ticket's literal AC (which only
requires the 2 conversions to pass + a warning to fire + a `hard=True` escape hatch to exist) —
flag to the planner/implementer as a judgment call, not a hard requirement, since the AC's own
bar is met by the 2 converted tests plus manual/`pytest.warns` verification inline in those 2
tests.

**Converted tests themselves (existing tests, behavior changes, not "new" but worth stating
explicitly since their assertion shape changes):**
- `test_backend_testing_post_fix_state_not_currently_flagged` — replace the bare
  `assert "backend-testing" not in result["flagged_stale"]` with a call through the new soft
  helper (e.g. `skill_staleness_check("backend-testing" not in result["flagged_stale"],
  f"backend-testing flagged stale: {result['flagged_stale']!r} (grace_period_days=
  {result['grace_period_days']})")`), and the test function itself keeps a bare
  `assert True`-shaped tail (or simply ends after the helper call) so the test still reports
  PASS even on a soft-check miss, per AC1.
- `test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus` — same
  pattern, checking `domain_skills.isdisjoint(set(result["flagged_stale"]))` through the
  helper instead of a bare `assert`.

## Scoped Pytest Commands

Primary (matches the real CI job this failure came from — `.github/workflows/test.yml`'s
`api-tools` job, "API / tools / logging"):
```
pytest tests/tools/test_generate_retro.py -m "not slow and not extra_slow" --tb=short -q -rw
```
(`-rw` surfaces the warnings summary so `SkillStalenessWarning` is visible when a converted
test's underlying condition is currently failing — needed to confirm AC2's "not silently
dropped" requirement.)

Narrower, targeted to just the "zero invocation" test group during development:
```
pytest tests/tools/test_generate_retro.py -k "zero_invocation or backend_testing or six_domain" -v -rw
```

Full regression surface for the affected file plus its sibling tools tests (pre-merge
verification, still scoped — not full `tests/`):
```
pytest tests/tools/test_generate_retro.py tests/tools/test_skill_usage_metric.py -m "not slow and not extra_slow" --tb=short -q
```

If a new dedicated `tests/tools/test_skill_staleness_assertions.py` file is created for the
helper's own smoke tests:
```
pytest tests/tools/test_generate_retro.py tests/tools/test_skill_staleness_assertions.py -m "not slow and not extra_slow" --tb=short -q -rw
```

## Anti-Drift Test Guards

- **Collection-count check**: `pytest tests/tools/test_generate_retro.py --collect-only -q |
  tail -1` before and after — must report the same test count (135, plus any new tests
  explicitly added and accounted for) to confirm no test was silently deleted rather than
  converted.
- **The other 9 "zero invocation" tests must remain bare `assert`** (not routed through the
  new soft helper) — a grep-based guard: `grep -A3
  "^def test_zero_invocation_flag_excludes_skill_within_grace_period" tests/tools/
  test_generate_retro.py` (and the other 8 names) should still show a bare `assert`, not a
  call to `skill_staleness_check`/`skill_staleness_warning`. This directly guards against the
  scope-creep this investigation flagged as the primary hazard.
- **`compute_zero_invocation_skill_flags()` byte-for-byte unmodified**: `git diff tools/
  agent-monitoring/generate_retro.py` must be empty for this ticket's commit — the detection
  mechanism (function body, grace period constant, classification logic) is explicitly out of
  scope.
- **`tests/tools/perf_assertions.py` byte-for-byte unmodified**: `git diff tests/tools/
  perf_assertions.py` must be empty — confirms the new helper is a parallel file, not a shared-
  base refactor that could destabilize the precedent's own passing perf/arena/certification
  suites.
- **Warning class distinctness**: the new `SkillStalenessWarning` must not subclass or alias
  `PerformanceThresholdWarning` — a test asserting `not issubclass(SkillStalenessWarning,
  PerformanceThresholdWarning)` (or simply that they are different classes) prevents the two
  soft-monitor domains from being silently conflated in a shared `-W` filter or warnings
  summary triage.
- **`test_flagged_skills_list_never_auto_triggers_downstream_action` and
  `test_six_domain_skills_verdict_not_reopened` still pass unchanged** — both are source-
  inspection guards on `compute_zero_invocation_skill_flags()`, sitting in the same function's
  blast radius as this ticket's work; explicit re-run confirms no accidental coupling.

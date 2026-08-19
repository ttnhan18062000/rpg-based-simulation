---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260819-SKILL-STALENESS-SOFT-WARNING
artifact_type: investigation
tags: [testing, skills, agent-monitoring]
---

# Investigation — TCK-20260819-SKILL-STALENESS-SOFT-WARNING

## Context Scan
- `mcp__knowledge-search__search_docs("skill staleness zero invocation soft warning perf
  threshold precedent")` surfaced the precedent ticket `tickets/done/TCK-20260818-STANDARD-
  PERF-THRESHOLD-SOFT-WARNING.md` (confirms the exact soft-warning pattern this ticket must
  mirror), `TCK-20260810-SKILL-USAGE-RETRO-TRACKING` (authored
  `compute_zero_invocation_skill_flags()`/`build_skill_usage_section()`), `TCK-20260705-SIX-
  SKILLS-INVESTIGATION` (the settled "6 zero-invocation skills are correctly redundant"
  verdict that `test_six_domain_skills_verdict_not_reopened` guards against re-litigating —
  not touched by this ticket), and `TCK-20260704-SKILL-TRIGGER-COVERAGE` (earlier skill-
  invocation-history investigation).
- `graphify query "skill staleness zero invocation compute_zero_invocation_skill_flags
  perf_assertions"` (BFS depth=2 from `compute_zero_invocation_skill_flags()`) confirmed the
  call graph: `compute_zero_invocation_skill_flags()` (`tools/agent-monitoring/
  generate_retro.py:476`) depends on `build_skill_usage_section()` (`:435`) and
  `extract_frontmatter()` (`tools/validate_frontmatter.py:69`); `generate()` (`:1467`) only
  reaches it when `all_tools` is explicitly passed (guarded by
  `test_generate_without_all_tools_never_computes_zero_invocation_flags`). No graph edge
  exists yet between `compute_zero_invocation_skill_flags` and any warning/soft-check
  mechanism — confirming this is genuinely new wiring, not a duplicate of existing code.

## Current Behavior

### `compute_zero_invocation_skill_flags()` — `tools/agent-monitoring/generate_retro.py:476-557`
Read-only, all-time (never period-scoped) cross-reference of the real `.claude/skills/*/
SKILL.md` catalog against `build_skill_usage_section(tools)["per_skill"]` invocation counts.
For each skill directory with zero invocations: a skill with a real, parseable `date_added`
older than `SKILL_ZERO_INVOCATION_GRACE_PERIOD_DAYS` (14 days) goes into `flagged_stale`; a
skill with no/unparseable `date_added` goes into `flagged_unknown_age` (fail-open, lower-
certainty signal). Returns a dict with `grace_period_days`, `flagged_stale`,
`flagged_unknown_age`, `catalog_parse_errors`, and a `derivation` string. This function itself
is explicitly out of scope for this ticket (per the ticket's Scope section) and was **not**
modified during this investigation — read only for context.

### Failing tests — `tests/tools/test_generate_retro.py`
- `test_backend_testing_post_fix_state_not_currently_flagged` (line 2343-2350): calls
  `compute_zero_invocation_skill_flags(generate_retro.load_jsonl(generate_retro.
  DEFAULT_TOOLS_FILE))` against the **real** `agent-monitoring/tools.jsonl` and real
  `.claude/skills/` catalog (no `skills_dir`/`today` override), then bare-asserts
  `"backend-testing" not in result["flagged_stale"]`.
- `test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus` (line
  2393-2405): same real-corpus call pattern, bare-asserts
  `domain_skills.isdisjoint(set(result["flagged_stale"]))` for the 6 domain skills
  (`observability`, `simq-dev`, `systems-economy`, `combat-mechanics`, `cognition-strategy`,
  `progression-entities`).
Both tests hard-fail today (2026-08-19) because `backend-testing`'s and 5 of the 6 domain
skills' `date_added: "2026-08-05"` crossed the 14-day grace period exactly today, and none of
the 6 have ever recorded a real `Skill`-tool invocation in `tools.jsonl` (245 total `Skill`
rows scanned; `cognition-strategy` has 1 and correctly stays excluded).

### Surrounding "zero invocation" test group — same file, lines 2291-2427
Confirmed by full read: every other test in this group uses `tmp_path`-scoped synthetic
fixtures via `_write_skill()` (a local helper that writes a fabricated `SKILL.md` into a
temp dir) and passes explicit `skills_dir=`/`today=` parameters — they test
`compute_zero_invocation_skill_flags()`'s **logic** against controlled inputs, not the real
catalog's current state:
- `test_zero_invocation_flag_excludes_skill_within_grace_period` (2307)
- `test_zero_invocation_flag_includes_skill_past_grace_period_with_zero_invocations` (2316)
- `test_zero_invocation_flag_excludes_skill_with_nonzero_invocations_regardless_of_age` (2325)
- `test_backend_testing_pre_fix_state_would_have_been_flagged` (2333) — synthetic
  reconstruction of the *pre-fix* state (no `date_added`), not the real corpus
- `test_zero_invocation_flag_function_never_crashes_on_malformed_skill_md` (2353)
- `test_zero_invocation_flag_catalog_scan_is_pure_no_file_mutation` (2362)
- `test_grace_period_missing_date_added_policy_is_explicit_not_accidental` (2370)
- `test_flagged_skills_list_never_auto_triggers_downstream_action` (2377) — source-inspection
  guard via `inspect.getsource`
- `test_six_domain_skills_verdict_not_reopened` (2385) — source-string guard on the
  `derivation` text
- `test_zero_invocation_flag_has_derivation` (2408)
- `test_generate_without_all_tools_never_computes_zero_invocation_flags` (2414) —
  `monkeypatch`-based call-boundary guard

None of these 9 tests read the real `.claude/skills/` catalog or real `tools.jsonl`; none are
subject to calendar-time drift. **Confirmed: only the 2 tests named in the ticket need
conversion.** Converting any of the other 9 would be scope creep — they assert genuine,
timeless structural/logic invariants about the function itself, exactly the kind of check
`perf_assertions.py`'s docstring says must stay hard (`hash/state equality, invariant checks,
structural correctness, gate-logic-against-synthetic-fixtures... stay hard failures`).

### `tests/tools/perf_assertions.py` — the pattern to mirror (read-only reference)
- `PerformanceThresholdWarning(UserWarning)` (line 35) — bare warning subclass, docstring only.
- `_current_test_id()` (line 44) — reads `PYTEST_CURRENT_TEST` env var, strips the `" (phase)"`
  suffix, falls back to `"<unknown test>"`.
- `perf_check(ok, message, *, hard=False)` (line 64) — returns `True` if `ok`; if not `ok` and
  `hard=True` raises `AssertionError(full_message)`; if not `ok` and `hard=False` calls
  `warnings.warn(full_message, PerformanceThresholdWarning, stacklevel=3)` and returns `False`.
- `assert_perf_threshold(actual, limit, message, *, op="<=", hard=False)` (line 89) — a
  convenience wrapper that formats a comparison detail string and delegates to `perf_check`.
  This ticket's AC only requires the `perf_check`-equivalent shape (a boolean-in, warn-or-raise
  helper) — there is no numeric threshold/comparison in the skill-staleness case, so no
  `assert_perf_threshold`-equivalent wrapper is needed; `flagged_stale`/`flagged_unknown_age`
  membership is a set-membership check, not a numeric comparison.

## Mechanics / Engine Constraints
None. This is agent-tooling/test-infrastructure (`tools/agent-monitoring/`,
`tests/tools/`), not simulation logic. No `docs/mechanics/` chapter or `docs/engine/` contract
governs this behavior.

## Docs Requiring Update
- `docs/testing/regression_policy.md`: add a new row to the §3 "Soft Monitors — Alert Only"
  table (after the existing "Performance-threshold assertions" row at line 67), following the
  exact same format, naming this ticket, `tests/tools/skill_staleness_assertions.py`'s
  `SkillStalenessWarning`, and the 2 specific converted tests — matching the precedent's own
  Finalize step referenced in the ticket's Related Docs.

## Parity Ledger Overlap
None. This is agent-tooling test-infrastructure work, not a simulation-law behavior change —
no `docs/parity_ledger/*.yaml` entry exists or is needed for skill-usage tracking. (Grep
across `docs/parity_ledger/` for "skill" only matches incidental words like "skilled" inside
unrelated combat/progression entries — confirmed no real overlap.)

## Prior Work
- `TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING` (`stored_artifacts/TCK-20260818-
  STANDARD-PERF-THRESHOLD-SOFT-WARNING/`) — the exact precedent this ticket mirrors. Its
  `investigation.md` documents a full per-file audit distinguishing genuine calibration
  questions (soft) from correctness checks (stay hard); this ticket's equivalent audit is the
  "surrounding zero invocation test group" section above — much smaller scope (2 of 11 tests
  in one group, vs. dozens of files). Its `test_plan.md` used non-standard section headers
  ("Normal flow/Edge cases/Failure modes/Regression-prone paths") rather than this role's
  mandated template (Regression Surface/New Tests Required/Scoped Pytest Commands/Anti-Drift
  Test Guards) — this ticket's `test_plan.md` follows the mandated template instead, since
  that is the current binding format for this artifact.
- `TCK-20260810-SKILL-USAGE-RETRO-TRACKING` — authored `compute_zero_invocation_skill_flags()`
  and `build_skill_usage_section()` (both left untouched by this ticket).
- `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC` — authored the 6 domain skills whose
  `date_added: "2026-08-05"` triggered this failure.
- `TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED` — gave `backend-testing` its real
  `date_added` field (previously had none, which is what
  `test_backend_testing_pre_fix_state_would_have_been_flagged` reconstructs as a synthetic
  fixture).
- `TCK-20260705-SIX-SKILLS-INVESTIGATION` — the settled verdict (all 6 zero-invocation skills
  are "correctly redundant") that `test_six_domain_skills_verdict_not_reopened` guards against
  re-litigating. Not reopened by this ticket; the soft-warning mechanism does not assert
  anything about whether the skills *should* be used, only that a staleness signal exists.

## Risks and Open Questions
- **Naming**: the ticket's Scope says "e.g. `skill_staleness_assertions.py`" and AC2 says "a
  `SkillStalenessWarning` (or equivalently-named)" — both are suggestions, not hard
  requirements. Recommend using exactly `tests/tools/skill_staleness_assertions.py` and
  `SkillStalenessWarning`/`skill_staleness_check` for consistency with the precedent's naming
  scheme (`perf_assertions.py`/`PerformanceThresholdWarning`/`perf_check`) and because no
  countervailing reason to deviate was found. Not a blocking open question — safe default.
- **No `assert_perf_threshold`-equivalent needed**: confirmed above under Current Behavior —
  the skill-staleness case is a set-membership check, not a numeric comparison, so only the
  `perf_check`-equivalent primitive is required. Flagging this so the implementer does not
  over-build a comparison-operator wrapper that has no real call site.
- **`perf_assertions.py` itself is not modified**: confirmed by direct docstring/content read
  — nothing in it references anything perf-specific that would need generalizing to be
  reused, and the ticket's own Related Docs explicitly says "not to be modified." A clean
  parallel file is correct; no shared base module refactor is in scope or warranted for a
  single second consumer.
- **`docs/testing/regression_policy.md` row wording**: the ticket only requires "a new row...
  matching the precedent's own Finalize step" — exact wording is an implementer/doc-updater
  judgment call, not specified further here.

## Anti-Drift Hazards
- Do not convert any of the other 9 tests in the "zero invocation" test group (lines
  2291-2427) — they are synthetic/structural and must stay hard per this investigation's
  confirmation above. Converting them would silently weaken genuine logic-correctness
  coverage of `compute_zero_invocation_skill_flags()`.
- Do not touch `compute_zero_invocation_skill_flags()`, `SKILL_ZERO_INVOCATION_GRACE_PERIOD_
  DAYS`, or the `flagged_stale`/`flagged_unknown_age` classification logic in
  `tools/agent-monitoring/generate_retro.py` — explicitly out of scope; the detection
  mechanism itself is correct.
- Do not modify `tests/tools/perf_assertions.py` — the ticket's Related Docs explicitly marks
  it "the pattern to mirror, not to modify."
- Do not artificially bump the 6 skills' `date_added` or fabricate invocations to make the
  tests pass "for real" — explicitly out of scope and would defeat the honest-signal purpose
  of the mechanism (same reasoning `perf_assertions.py`'s docstring gives for not silently
  degrading correctness checks).
- Do not change `SKILL_ZERO_INVOCATION_GRACE_PERIOD_DAYS` (14 days) — explicitly out of scope,
  a separate calibration question.
- `test_six_domain_skills_verdict_not_reopened` and
  `test_flagged_skills_list_never_auto_triggers_downstream_action` must keep passing unchanged
  — they are source-inspection guards on `compute_zero_invocation_skill_flags()`'s own code
  and `derivation` string, both untouched by this ticket, so they should not be affected, but
  are worth explicitly re-running since they sit in the same function's blast radius.

---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260810-SKILL-USAGE-RETRO-TRACKING
artifact_type: test_plan
tags: [skills, agent-monitoring, observability, process-improvement]
---

# Test Plan — TCK-20260810-SKILL-USAGE-RETRO-TRACKING

## Regression Surface

**Unit:**
- `tests/tools/test_skill_usage_metric.py` (12 existing tests) — `build_skill_usage_section` must
  stay byte-for-byte unmodified in behavior (Out of Scope). All 12 must still pass unchanged,
  including the two reuse-not-reimplement AST guards (`test_reuses_generate_retro_loader_not_a_second_loader`,
  `test_never_calls_json_loads_on_input_summary`) and the zero-mutation guard
  (`test_causes_zero_diff_on_real_corpus`).
- `tests/tools/test_generate_retro.py` (2134 lines, 121+ tests at last count in
  `SKILL-USAGE-METRIC`'s Test Summary, more added since by `CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`)
  — every existing section (Tag Breakdown, Outliers, Retrieval Quality, Shadow vs. Baseline, Search
  & Investigation Effort, Tool Safety Audit, Parity Index Read-Path Usage) must render unchanged;
  this ticket is purely additive.

**Integration:**
- Live-corpus checks in both files above (e.g. `test_live_corpus_matches_independently_derived_counts`
  in `test_skill_usage_metric.py`, `test_correlation_real_corpus_produces_a_real_number` in
  `test_generate_retro.py`) — these read the real `agent-monitoring/tools.jsonl` /
  `agent-monitoring/events.jsonl` and must keep passing against the live, growing corpus.
- `main()`'s end-to-end report generation (`python3 tools/agent-monitoring/generate_retro.py --all`)
  must still succeed and write `agent-monitoring/retro/RETRO-ALL.md` without error.

**Arena-combat:** N/A — no `src/` file touched, no simulation/combat code affected.

## New Tests Required

Per acceptance criteria (`tickets/inprogress/TCK-20260810-SKILL-USAGE-RETRO-TRACKING.md`):

**AC1 — `## Skill Usage` section renders real, non-fabricated per-skill counts, reusing
`build_skill_usage_section`, not reimplementing it:**
- `test_generate_retro_imports_build_skill_usage_section_not_a_reimplementation` — category:
  architecture guard (AST, mirrors `test_reuses_generate_retro_loader_not_a_second_loader`'s
  pattern). Verifies the module actually calling `build_skill_usage_section` in its call chain
  (whichever file Plan places the wiring in) imports the real function rather than containing a
  second `_SKILL_NAME_RE`-shaped regex literal. Lives in `tests/tools/test_generate_retro.py`.
- `test_skill_usage_section_present_in_generated_report` — category: unit. Synthetic `tools`
  fixture with 2-3 distinct `Skill` invocations; asserts `## Skill Usage` heading and each skill's
  real count appear in `generate()`'s rendered Markdown output. Lives in `test_generate_retro.py`.
- `test_skill_usage_section_matches_real_corpus_counts` — category: integration (real-corpus).
  Loads real `tools.jsonl`, calls the wiring function, and asserts its `per_skill` output equals
  `build_skill_usage_section(load_jsonl(DEFAULT_TOOLS_FILE))["per_skill"]` directly (not a frozen
  fixture — corpus drifts, per Investigation's live-corpus-drift finding on `cognition-strategy`).
  Lives in `test_generate_retro.py`.
- `test_skill_usage_trend_column_in_retro_index` (only if Plan adds a trend column to
  `_update_index()`, matching Search Calls/Read Calls precedent) — category: unit. Lives in
  `test_generate_retro.py`.

**AC2 — zero-invocation-after-grace-period flag: excludes the 6 domain skills today (all younger
than the grace period), and correctly would have flagged `backend-testing` prior to its
`TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED` fix:**
- `test_zero_invocation_flag_excludes_skill_within_grace_period` — category: unit (synthetic
  fixture). A skill with `date_added` inside the grace-period window (e.g. "today minus 1 day") and
  zero invocations must NOT appear in the flagged list.
- `test_zero_invocation_flag_includes_skill_past_grace_period_with_zero_invocations` — category:
  unit (synthetic fixture). A skill with `date_added` older than the grace period and zero
  invocations must appear in the flagged list.
- `test_zero_invocation_flag_excludes_skill_with_nonzero_invocations_regardless_of_age` —
  category: unit. A skill past the grace period but with >=1 real invocation must never be flagged.
- `test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus` — category:
  integration (real-corpus, AC2's first half, literal). Runs the flag function against the real
  catalog + real `tools.jsonl` *as of the day the ticket is implemented* and asserts none of
  `observability`, `simq-dev`, `systems-economy`, `combat-mechanics`, `cognition-strategy`,
  `progression-entities` appears in the flagged list — reads each skill's real `date_added` from
  its live `SKILL.md`, not a hardcoded "2026-08-05," so it stays correct as the corpus/grace-period
  window moves. **Caution**: `cognition-strategy` now has a real nonzero count (1, confirmed this
  session) — the assertion should be "not flagged," which holds either because it's within grace
  period OR because it has a nonzero count; do not assert "flagged list is empty of exactly 6
  skills with zero invocations," since that specific sub-claim already drifted.
- `test_backend_testing_pre_fix_state_would_have_been_flagged` — category: unit **regression test,
  synthetic fixture, not live-corpus** (AC2's historical sanity check — this is the load-bearing
  test the ticket explicitly asks for). Construct a fixture SKILL.md-catalog entry for
  `backend-testing` mirroring its real, confirmed pre-2026-08-05 shape: no `date_added` field, no
  `source` field (`TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED`'s own Request Summary: "without
  their `source: community` frontmatter" — i.e. undisclosed, no disclosure frontmatter at all
  pre-fix), and a synthetic `tools.jsonl` fixture with zero `Skill`+`backend-testing` rows (matches
  `SIX-SKILLS-INVESTIGATION`'s real, independently-verified finding: `backend-testing` 0/41 as of
  2026-07-05, unbroken through the 2026-08-05 fix). Assert the flag function includes it in the
  flagged output under whatever missing-`date_added` policy Plan adopts (see Investigation Risk 2)
  — **this test only passes if Plan resolved Risk 2 in the fail-open direction**; if it resolved
  fail-closed instead, this test must fail, and that failure is the correct, honest signal that
  AC2 as literally written cannot be satisfied by that design (do not weaken the test to pass
  regardless of the missing-`date_added` policy chosen). Do NOT assert anything about
  `backend-testing`'s *current*, post-fix, `date_added`-bearing state in this same test — that is a
  different, separately-testable scenario (see next test).
- `test_backend_testing_post_fix_state_not_currently_flagged` — category: integration (real-corpus).
  `backend-testing` today has `date_added: "2026-08-05"` (10 days old as of this investigation,
  still real corpus 0 invocations) — asserts it is correctly excluded while still inside its own
  grace period, distinct from the pre-fix synthetic scenario above.

**AC3 — every new section has a `derivation` string:**
- `test_skill_usage_section_has_derivation` — category: unit. Mirrors
  `test_parity_index_readpath_section_never_silent_has_derivation`'s pattern.
- `test_zero_invocation_flag_has_derivation` — category: unit. Same pattern applied to the flag
  function's own return dict.
- `test_all_new_sections_have_derivation_key` (extend the existing cross-cutting test at
  `test_generate_retro.py:2106`, do not duplicate it) — add both new functions to its assertion
  list, matching how `CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s 3 functions were added there.

**AC4 — new tests mirror existing test patterns (never-silent, derivation-matches-fields,
real-corpus checks, reuse-not-reimplement AST guards):**
- `test_skill_usage_and_flag_functions_never_write_any_file` — category: architecture guard. Extend
  `test_new_sections_never_write_any_file` (`test_generate_retro.py:2118`) to include the two new
  functions, same `inspect.getsource` string-absence checks (`write_lines(`, `EVENTS_FILE`,
  `RUNS_FILE`, `DEFAULT_TOOLS_FILE` literal, etc.).
- `test_zero_invocation_flag_function_never_crashes_on_malformed_skill_md` — category: unit
  (failure mode). A `SKILL.md` fixture with unparseable/missing frontmatter must be skipped or
  counted under an explicit "unparseable" bucket (mirroring `skill_usage_metric.py`'s own
  `unparseable` convention for `input_summary`), never raise.
- `test_zero_invocation_flag_catalog_scan_is_pure_no_file_mutation` — category: unit. Mirrors
  `test_causes_zero_diff_on_real_corpus`'s `git status --porcelain` before/after check, scoped to
  `.claude/skills/`.

**AC5 — `docs/agent-monitoring/README.md`/`schema.md` updated:**
- No pytest test enforces doc prose content directly (matches existing convention — no test file
  greps README.md's prose). Verified instead via `tools/doc_staleness_check.py` (existing repo
  mechanism, already required at Finalize per CLAUDE.md) and manual done-checker review of the
  Docs Requiring Update bullets in `investigation.md`.

## Scoped Pytest Commands

```
pytest tests/tools/test_generate_retro.py tests/tools/test_skill_usage_metric.py -v
```

Broader regression sweep (matches `SKILL-USAGE-METRIC`'s own precedent scoping):
```
pytest tests/tools/ -k "generate_retro or retro or skill_usage" -v
```

Never: `pytest tests/` (full suite) — out of scope per CLAUDE.md's Testing Rule; this ticket
touches zero `src/` files, so no `src/`-domain test directory needs running.

## Anti-Drift Test Guards

- **`test_build_skill_usage_section_signature_unchanged`** — category: architecture guard. Asserts
  `build_skill_usage_section`'s existing 12-test suite in `test_skill_usage_metric.py` still passes
  verbatim (no test file edit needed there at all is itself the guard — Out of Scope forbids
  touching that function's logic; if any of those 12 tests need modification to pass, that is
  itself a scope violation to flag, not fix quietly).
- **`test_six_domain_skills_verdict_not_reopened`** — category: architecture guard /
  anti-scope-creep. Asserts no new test or doc change in this ticket references
  `SIX-SKILLS-INVESTIGATION`'s 6 pre-existing skills' verdicts as being overturned, confirmed, or
  re-scored — the new flag is a forward signal generator only (Out of Scope).
- **`test_new_flag_never_writes_to_claude_skills_directory`** — category: unit (durable-state
  guard, mirrors CLAUDE.md's Architecture Rule — read-only decision logic must not mutate). The
  flag function reads `.claude/skills/*/SKILL.md` and `tools.jsonl`; asserts zero `Path.write_text`/
  `open(..., "w")` calls anywhere in its source (`inspect.getsource` string-absence check, same
  technique as `test_new_sections_never_write_any_file`).
- **`test_grace_period_missing_date_added_policy_is_explicit_not_accidental`** — category:
  architecture guard. Asserts the flag function's `derivation` string explicitly states which
  policy it applies to skills with no `date_added` (fail-open vs. fail-closed, per Investigation
  Risk 2) — catches a silent, undocumented default from passing review.
- **`test_flagged_skills_list_never_auto_triggers_downstream_action`** — category: architecture
  guard. Greps the diff/new code for any deprecation, removal, or auto-invocation side effect keyed
  off the flagged-skills list (Out of Scope: "any decision to act on a flagged skill is a separate,
  later, human-reviewed step").

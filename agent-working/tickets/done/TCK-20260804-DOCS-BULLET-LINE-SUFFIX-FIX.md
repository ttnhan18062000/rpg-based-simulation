---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260804-DOCS-BULLET-LINE-SUFFIX-FIX
phase: done
date: 2026-08-04
tags: [ai, agent-monitoring]
---

# TCK-20260804-DOCS-BULLET-LINE-SUFFIX-FIX

## Title
Make `done_checker_static.py`'s `_DOCS_BULLET_RE` tolerant of `` `docs/path:line` `` bullet forms

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tools/gate_checks/done_checker_static.py`'s `_DOCS_BULLET_RE` regex only matches bare
`` `docs/path` `` bullets in investigation.md's "## Docs Requiring Update" section — a
`` `docs/path:123` `` form (line number baked inside the backticks) is captured whole, including
the `:123` suffix, and then never matches `git status`'s bare path during coverage verification.

Confirmed real via `TCK-20260804-EXPANSION-RATE-WIRING`'s own `agent-monitoring/events.jsonl`
evidence text ("BLOCKED - docs_to_update_coverage failed on investigation.md bullet format (:line
baked inside backticks)") — that ticket worked around the bug by hand-editing its own
investigation.md bullet to the bare-path form, rather than fixing the parser.

This was investigated as a candidate fix for `TCK-20260804-AGENT-DEF-GAP-FIXES` (which folded in a
different, unrelated "Docs Requiring Update" parsing bug — the `_DOCS_NONE_PHRASES` exact-match
check's intolerance of trailing rationale prose after "None.") but explicitly excluded from that
ticket's scope: none of that ticket's 3 evidenced fresh-Verify-failure occurrences were actually
caused by this `:line`-suffix bug (all 3 traced to the None-phrase issue instead). Tracked here as
its own, separately-scoped fix rather than left silently unaddressed.

## Scope
- Change `_DOCS_BULLET_RE` (currently `` r"^-\s+`(docs/[^`]+)`" ``) to tolerate an optional
  `:digits` suffix without capturing it into the extracted path — e.g. a lazy capture group plus a
  non-capturing optional `(?::\d+)?` before the closing backtick.
- Add regression tests reproducing the real observed form
  (`` - `docs/agent-monitoring/schema.md:287`: reason `` style bullets) at both the parse level
  (`_parse_docs_to_update`) and the integration level (`check_docs_to_update_coverage`).
- Verify no regression to bullets containing a colon for an unrelated reason (checked precedent
  during `TCK-20260804-AGENT-DEF-GAP-FIXES`'s review: real corpus examples include
  `` `docs/parity_ledger/world_dynamics.yaml::WORLD-103` `` and range-style `` `...md:3,5` `` —
  the fix must not corrupt these).

## Out of Scope
- The `_DOCS_NONE_PHRASES`/`_is_none_section()` mechanism — already fixed separately by
  `TCK-20260804-AGENT-DEF-GAP-FIXES`.
- Any change to `investigator.md`'s guidance — this is a parser-side fix, matching the precedent
  `TCK-20260804-AGENT-DEF-GAP-FIXES` already established for the sibling None-phrase bug (root-cause
  the parser rather than the agent instructions, since agent-instruction drift has already proven
  recurrence-prone this session).

## Acceptance Criteria
- [x] `_DOCS_BULLET_RE` correctly extracts `docs/path` from both bare and `:line`-suffixed bullet
      forms — changed to `` r"^-\s+`(docs/[^`]+?)(?::\d+)?`" `` (lazy capture + optional
      non-capturing `:digits` suffix, per the ticket's own suggested construction).
- [x] New regression tests reproduce the real observed failure form
      (`` `docs/agent-monitoring/schema.md:287` ``), at both parse level and integration level.
- [x] No regression to existing non-line-suffix colon forms — verified by dedicated tests for
      `` `docs/parity_ledger/world_dynamics.yaml::WORLD-103` `` and `` `docs/x.md:3,5` ``, both
      confirmed to survive uncut.
- [x] `pytest tests/tools/test_done_checker_static.py -v` — 94 passed, zero regressions.

## Related Tickets
- TCK-20260804-AGENT-DEF-GAP-FIXES (found and disclosed this bug, fixed the sibling None-phrase bug instead)
- TCK-20260804-EXPANSION-RATE-WIRING (hit this exact bug, worked around by hand rather than fixing the parser)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- `tools/gate_checks/done_checker_static.py`
- `tests/tools/test_done_checker_static.py`

## Assumptions / Open Questions
None — the fix shape is well-understood; only the exact regex construction needs care to avoid
regressing the other colon-bearing bullet forms already confirmed present in the real corpus.

## Implementation Notes
Changed `_DOCS_BULLET_RE` from `` r"^-\s+`(docs/[^`]+)`" `` to
`` r"^-\s+`(docs/[^`]+?)(?::\d+)?`" `` — a lazy path-capture group followed by an optional
non-capturing `:digits` group before the closing backtick, exactly the construction the ticket's
own Scope suggested. Traced the regex engine's backtracking behavior by hand for all 4 relevant
forms before writing tests, to confirm correctness ahead of time rather than test-and-guess:
- Bare `` `docs/path` `` → lazy group expands to consume the whole path, optional suffix group
  matches zero-length, backtick matches. Unchanged from prior behavior.
- `` `docs/path:123` `` → lazy group stops at "docs/path" once `(?::\d+)?` + backtick can match
  the remaining ":123" + closing backtick. Captures "docs/path", suffix dropped.
- `` `docs/path::WORLD-103` `` (double colon, not digits-only) → `:\d+` never matches (second char
  after `:` isn't a digit), so the optional group always matches zero-length at every lazy-expansion
  attempt; the backtick literal never matches until the lazy group has consumed the ENTIRE
  remaining string. Captures the whole thing uncut.
- `` `docs/path:3,5` `` (comma-range) → `:\d+` matches only ":3" (digit run stops at the comma),
  leaving ",5" unconsumed before the required backtick — fails, so backtracking continues until the
  lazy group again consumes everything. Captures the whole thing uncut.
Updated `_parse_docs_to_update`'s docstring with this behavior, citing the real corpus precedent
forms from the ticket's own Scope.

Done directly (no subagents — hard 200-agent session spawn cap from earlier in this session).

## Test Summary
Added 6 new tests to `tests/tools/test_done_checker_static.py`: 4 parse-level
(`test_parse_docs_strips_line_number_suffix`,
`test_parse_docs_line_suffix_multiple_bullets_mixed_with_bare`,
`test_parse_docs_does_not_strip_compliance_id_suffix`,
`test_parse_docs_does_not_strip_comma_range_suffix`) and 1 integration-level
(`test_docs_coverage_line_suffix_bullet_matches_bare_git_path`, reproducing the exact real failure
this ticket cites — a `:line`-suffixed bullet against real `git status` output for a bare-path
file). `pytest tests/tools/test_done_checker_static.py -v` → **94 passed**, zero regressions (all
prior tests, including the `::PARITY-ID` and `:3,5` precedent forms implicitly covered by the new
negative tests, still pass). `doc_staleness_check.py` → PASS (no `src/`/`config/`/
`.claude/workflows/*.js` path touched, no `docs/` update required).
`clean_data_runs_early()` → PASS. `expected_subsystems_for_files()` → `{}` — no parity ledger
entry needed (no `src/` path touched).

## Files Changed
- `tools/gate_checks/done_checker_static.py` — fixed `_DOCS_BULLET_RE`, updated
  `_parse_docs_to_update`'s docstring.
- `tests/tools/test_done_checker_static.py` — 6 new regression tests.

## Completion Summary
Fixed the confirmed-real bug: a `:line`-suffixed `` `docs/path:123` `` bullet form (baked-in line
number) now correctly extracts the bare `docs/path`, matching `git status`'s bare-path form during
coverage verification. Verified by hand-tracing the regex's backtracking behavior for all 4
relevant real-corpus forms before writing tests, then confirmed by 6 new regression tests (4
parse-level, 1 end-to-end integration-level, explicitly including 2 negative tests proving the two
other real colon-bearing forms — `::COMPLIANCE-ID` and comma-range `:3,5` — survive uncut, per the
ticket's own explicit non-regression requirement. No known material gap.

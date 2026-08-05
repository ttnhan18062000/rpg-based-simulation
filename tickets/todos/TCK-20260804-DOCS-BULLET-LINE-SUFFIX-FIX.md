---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260804-DOCS-BULLET-LINE-SUFFIX-FIX
phase: open
date: 2026-08-04
tags: [ai, agent-monitoring]
---

# TCK-20260804-DOCS-BULLET-LINE-SUFFIX-FIX

## Title
Make `done_checker_static.py`'s `_DOCS_BULLET_RE` tolerant of `` `docs/path:line` `` bullet forms

## Status
OPEN

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
- [ ] `_DOCS_BULLET_RE` (or its replacement) correctly extracts `docs/path` from both bare and
      `:line`-suffixed bullet forms.
- [ ] New regression tests reproduce the real observed failure form.
- [ ] No regression to existing non-line-suffix colon forms (`::PARITY-ID`, range-style `:3,5`).
- [ ] `pytest tests/tools/test_done_checker_static.py -v` passes with zero regressions.

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
(filled during Implement)

## Test Summary
(filled during Test)

## Files Changed
(filled during Implement)

## Completion Summary
(filled during Finalize)

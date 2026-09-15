---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-EVENT-SUMMARY-TRUNCATION
phase: done
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# TCK-20260915-EVENT-SUMMARY-TRUNCATION

## Title
47 event summaries land on exactly 200 characters — a hard truncation boundary that silently discards the rest, reported by no mechanism

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Summary length across the 1,897 events in the 2026-09-01 → 2026-09-15 window:

| Statistic | Value |
|---|---|
| min | 8 |
| p25 | 70 |
| median | 95 |
| p90 | 184 |
| max | 1,055 |
| **exactly 200 chars** | **47** |

A clean spike at exactly 200 in an otherwise smooth distribution is a truncation boundary, not
natural length. `generate_retro.py`'s Summary Quality section already counts these — it reports
"Truncated (>200 chars): 98" — but only as a statistic. Nothing warns at write time, and the
discarded text is gone.

The summaries are the only human-readable record of what a phase actually did; they are what this
very review read to classify Review-phase failures. A summary cut mid-sentence at 200 characters is
a degraded audit trail.

Note the max of 1,055 shows longer summaries *can* be stored — so the 200 boundary is imposed by a
specific writer, not by the schema.

**The short tail is mostly fine and should not be "fixed"**: `'489 passed, 0 failed'`,
`'READY_TO_CLOSE 13/13'`, `'APPROVED'` are legitimately terse. One is not: `'9-step plan'` is the
entire summary for a Plan phase and records nothing about what was planned.

## Scope
- Find which writer imposes the 200-character limit (the schema evidently does not) and decide
  whether to raise it, or to truncate visibly with an explicit marker so a reader knows text was
  cut.
- Do not simply remove the limit without checking why it exists — an unbounded summary field has
  its own costs.

## Out of Scope
- Rewriting historical truncated summaries; the text is not recoverable.
- The short-summary cases, other than noting `'9-step plan'` as a prompt-quality signal rather than
  a bug in this subsystem.

## Acceptance Criteria
- [x] The writer imposing the 200-char boundary is identified: `pushEvent()` in
      `.claude/workflows/implement-ticket.js` (`summary: (summary || '').toString().slice(0, 200)`),
      plus 10 further call sites that pre-sliced their own string to 200 chars before ever reaching
      `pushEvent` (9 of which fed straight into `pushEvent`, redundantly) or built an event object
      literal directly (2 shadow-call sites: ArchVerify, Security-Review).
- [x] Truncation is made visible via a trailing marker: a new `truncateSummary(s)` helper truncates
      to 196 chars + `' […]'` (4 chars, total 200) only when the input actually exceeds 200 chars;
      short/exact-200 strings pass through unchanged. Applied at `pushEvent`'s own assignment and at
      both shadow-call object literals; the other 9 sites had their now-redundant pre-slice removed
      since their full string now reaches `pushEvent`, which truncates centrally.
- [x] `docs/agent-monitoring/schema.md`'s `summary` field row states the 200-char limit, names the
      writer/helper, and documents the marker behavior.

## Related Tickets
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (parent)

## Related Docs
- `docs/agent-monitoring/schema.md`
- `agent-monitoring/retro/RETRO-LAST14D.md` (Summary Quality section)

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `tools/agent-monitoring/record_events.py`
- `.claude/workflows/implement-ticket.js` (`pushEvent` call sites)
- `tools/agent-monitoring/generate_retro.py` (Summary Quality section)

## Assumptions / Open Questions
- Whether the 200 limit is deliberate (cost, readability) or incidental is unknown. If deliberate,
  visible truncation is the better fix than raising it.

## Implementation Notes
Reproduce by measuring summary lengths across the shards; the spike at exactly 200 is unmistakable.

Root cause: `pushEvent()`'s own `summary` field assignment did a plain `.slice(0, 200)` with no
marker. Additionally, 10 call sites elsewhere in the file pre-sliced their own string to 200 chars
before it ever reached `pushEvent` (a leftover from before `pushEvent` centralized the limit, or
independent shadow-call object literals that never went through `pushEvent` at all) — meaning a fix
inside `pushEvent` alone would not have made every truncation visible.

Fix: added `truncateSummary(s)` immediately before `pushEvent`'s definition — `str.length > 200 ?
str.slice(0, 196) + ' […]' : str`, keeping the total length at 200 by design (the 200-char
convention itself is deliberate: every agent prompt in this file already instructs "one sentence,
<=200 chars"; there is no schema-level limit, since real summaries up to 1,055 chars already exist
in the corpus predating this fix). `pushEvent`'s own field assignment now calls
`truncateSummary(summary)`. The two shadow-call sites that build event objects directly
(`archVerifyShadow`, `securityReviewShadow`) also call `truncateSummary(...)` directly, since they
never go through `pushEvent`. The other 9 sites (Investigate/Plan/Implement's advisory-summary
line, Test's cleanup-evidence line, Parity's cross-ref evidence, and 4 Finalize failure-evidence
lines) had their now-redundant `.slice(0, 200)` removed — they feed their full, untruncated string
into `pushEvent`, which is the single place truncation now happens for those.

Verified with a standalone Node snippet (this repo has no JS test runner for
`.claude/workflows/*.js` — confirmed via existing test docstrings, e.g.
`tests/tools/test_monitoring_bypass_fix.py`): short strings and exact-200 strings pass through
unchanged; a 1,055-char string truncates to exactly 200 chars total and ends with the marker;
`null`/`undefined` are handled safely (matches the pre-existing `(summary || '')` guard).

One pre-existing static-parsing test, `tests/tools/test_shadow_packet_call_site.py::test_call_site_does_not_break_writesidecar_agent_adjacency`,
hardcoded the exact literal `pushEvent('Investigate', ..., investigationText.slice(0, 200), ...)`
as an anchor string. Its actual assertion (the shadow-packet call site appears strictly after this
`pushEvent` call, not before) is unaffected by removing the redundant slice — updated only the
hardcoded literal to match the new call shape, not the assertion's substance. No other test in the
repo referenced the removed slice sites (confirmed via `grep -rn "slice(0, 200)" tests/`).

## Test Summary
- New: `tests/tools/test_event_summary_truncation.py` (5 tests) — helper defined with the correct
  196+marker shape; `pushEvent` calls it instead of a raw slice; no `.slice(0, 200)` remains
  anywhere in the file (regression guard against reintroducing a silent-truncation site); both
  shadow-call sites use the helper.
- Updated: `tests/tools/test_shadow_packet_call_site.py` — one hardcoded literal updated to match
  the new (unsliced) `pushEvent` call shape; the test's real assertion is unchanged.
- Full existing static-parsing suite against `implement-ticket.js` re-run (91 pre-existing tests
  across `test_current_run_sidecar_orchestrator.py`, `test_step0_ts_orchestrator.py`,
  `test_monitoring_bypass_fix.py`, `test_shadow_reviewer_call_site.py`,
  `test_finalize_tag_drift_wiring.py`, `test_document_update_phase_wiring.py`,
  `test_doc_staleness_gate_wiring.py`, `test_scope_orphan_fix.py`,
  `test_shadow_packet_call_site.py`, `test_tag_skill_mapping_check.py`,
  `test_classify_checklist_failure_js_mirror.py`) — all pass after the one literal update above.
- `node --check .claude/workflows/implement-ticket.js` confirms the file still parses as valid JS.

## Files Changed
- `.claude/workflows/implement-ticket.js` — added `truncateSummary()` helper; `pushEvent` and the 2
  shadow-call object literals now call it; removed 9 redundant pre-slice call sites.
- `docs/agent-monitoring/schema.md` — `summary` field row documents the 200-char limit, the writer,
  and the marker behavior.
- `tests/tools/test_event_summary_truncation.py` (new) — 5 regression tests.
- `tests/tools/test_shadow_packet_call_site.py` — one hardcoded literal updated to match the new
  call shape.

## Completion Summary
Identified `pushEvent()` in `.claude/workflows/implement-ticket.js` as the writer imposing the
200-char summary boundary, plus 10 further sites that pre-sliced independently of it. Replaced
silent truncation with a `truncateSummary()` helper that appends a visible `' […]'` marker only
when a real cut occurs, applied consistently at every summary-producing call site in the file
(not only `pushEvent`'s own internal slice), so a reader can always distinguish a truncated summary
from a complete one. Documented the limit and the new marker behavior in
`docs/agent-monitoring/schema.md`. Historical summaries already truncated before this fix remain
unrecoverable and were intentionally not rewritten (out of scope, per the ticket's own text).

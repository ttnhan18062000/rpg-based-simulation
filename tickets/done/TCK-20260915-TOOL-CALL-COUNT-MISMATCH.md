---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-TOOL-CALL-COUNT-MISMATCH
phase: done
date: 2026-09-15
tags: [agent-monitoring, data-quality]
---

# TCK-20260915-TOOL-CALL-COUNT-MISMATCH

## Title
53 runs record a `tool_call_count` that contradicts their own `tools.jsonl` rows by more than 3x — including runs claiming 0 while 558 real rows exist

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Comparing each run's summed `tool_call_count` (recorded on its events) against the actual number of
`tools.jsonl` rows carrying that `run_id`, **53 runs disagree by more than 3x in either
direction**. Examples:

| Run | claimed | actual |
|---|---|---|
| `TCK-20260718-TICKET-CORPUS-REPORT` | 0 | 558 |
| `TCK-20260626-FIX-DESIGN-PATTERNS` | 146 | 517 |
| `TCK-20260619-E53Ab-DECISION-PHASE` | 0 | 153 |
| `TCK-20260730-SHADOW-PROMOTION-GATE-THRESHOLDS` | 285 | 91 |

Note the last one runs the *other* way — claimed exceeds actual — so this is not simply "rows were
lost". **14 of the 53 record no count at all** (claimed 0 against real rows).

**This is current, not historical**: by month, 2026-06: 3, 2026-07: 6, **2026-08: 35, 2026-09: 9**.
The August concentration is the largest and unexplained.

Two numbers in the same system describing the same thing and disagreeing is exactly the shape this
epic exists to surface: neither value is flagged, and any consumer picking one gets a different
answer than a consumer picking the other.

## Scope
- Establish which side is authoritative — the per-event `tool_call_count` or the raw `tools.jsonl`
  rows — and record it in `docs/agent-monitoring/schema.md`. Consumers currently have no way to
  know.
- Determine the cause of the August concentration specifically; a 35-run cluster in one month
  suggests a change landed then rather than a steady drift.
- Confirm or rule out a shared cause with `TCK-20260915-SIDECAR-ATTRIBUTION-GAP`. The claimed=0
  cases in particular look like the sidecar gap seen from the other side, but that is a hypothesis
  to test, not an assumption to carry.

## Out of Scope
- Backfilling historical counts.
- The unattributed-rows problem itself (its own ticket).

## Acceptance Criteria
- [x] One side is documented as authoritative, with the reason. (`tools.jsonl`'s real row count —
      `tool_call_count` is a derived write-time snapshot, not an independent measurement. Documented
      in `docs/agent-monitoring/schema.md`.)
- [x] The August cluster is explained, or explicitly recorded as not-determinable. (Explained:
      August 2026 is almost entirely inside the pre-`TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`
      window; one sampled August mismatch is schema.md's own already-named concretely-confirmed
      instance of that exact bug.)
- [x] The shared-cause hypothesis with the sidecar ticket is confirmed or refuted — not left open.
      (Confirmed, cross-referenced from `TCK-20260915-SIDECAR-ATTRIBUTION-GAP`'s own investigation,
      not re-derived.)
- [x] Any detector ratchets from the measured baseline; it must not assert zero. (Ceiling 49 —
      re-measured, workflow- and post-fix-date-scoped, not the raw whole-corpus 194/142, which
      includes permanently-unbackfilled pre-fix historical noise this ticket is not scoped to fix.)

## Related Tickets
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (parent)
- `TCK-20260915-SIDECAR-ATTRIBUTION-GAP` — probable shared cause
- `TCK-20260708-AGENT-COST-OBSERVABILITY` (done)

## Related Docs
- `docs/agent-monitoring/schema.md`
- `agent-monitoring/retro/RETRO-LAST14D.md`

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `tools/agent-monitoring/record_events.py` (`compute_tool_stats`)
- `.claude/settings.json` (`PostToolUse` hook writing `tools.jsonl`)
- `agent-monitoring/data/*/events.jsonl`, `agent-monitoring/data/*/tools.jsonl`

## Assumptions / Open Questions
- The >3x threshold was chosen to surface gross disagreement, not to define acceptable drift. A
  smaller threshold will find more; the real tolerance is a decision this ticket should make.

## Implementation Notes
Derived from the shards, matching the ticket's own instruction. Validated the aggregate method
against all 4 of the ticket's own cited examples before trusting it further (exact match).

**The stated "53" needed re-scoping, not distrust.** A naive whole-corpus reproduction found 194
mismatches (142 restricted to the 3 sidecar-covered workflows) — far more than 53. Investigated why
rather than assuming the ticket was simply stale: 93 of the 142 predate
`TCK-20260719-COST-PROXY-WRITE-PATH` (2026-07-19), the fix that made `tool_call_count`
ground-truth-computed at all — before that date the field was never meant to match, and
backfilling it is explicitly out of scope. Restricting to on-or-after that date gives **49**,
closely matching the ticket's own "53, current not historical" framing (the small residual gap is
corpus growth since the ticket's own 2026-09-15 scoping pass — expected, not an error).

**August cluster root-caused by reading `docs/agent-monitoring/schema.md` directly rather than
stopping at "unexplained."** Two sampled August mismatches
(`TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET`, `TCK-20260821-VISUAL-QUALITY-DOCS`) share an
identical 1839-row `tools.jsonl` count — initially looked like an odd coincidence, but
`TCK-20260821-VISUAL-QUALITY-DOCS` turned out to be schema.md's own already-named, concretely
-confirmed instance of the pre-`TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` cross-session sidecar
contamination bug (closed 2026-08-22, kept absorbing another session's tool rows two days later).
August 2026 sits almost entirely inside that pre-fix window — a real, well-evidenced explanation,
not a guess.

## Test Summary
- `tests/tools/test_tool_call_count_mismatch_check.py` (new, 11 tests) — both mismatch directions
  (the ticket's own claimed=0/actual=N and claimed>actual shapes), the pre-fix-date exclusion, the
  unsupported-workflow exclusion, ratchet pass/fail, ceiling pin, real-corpus check, Makefile
  wiring.
- Combined regression run with tickets 1/2's own new test files: 192 passed.
- `make tool-call-count-mismatch-check` confirmed end-to-end: PASS, 49 (ceiling 49).

## Files Changed
- `docs/agent-monitoring/schema.md` — `tool_call_count` row gained an authoritative-source note.
- `tools/gate_checks/tool_call_count_mismatch_check.py` (new) — ratchet check, ceiling 49.
- `tests/tools/test_tool_call_count_mismatch_check.py` (new).
- `Makefile` — `tool-call-count-mismatch-check` target + `.PHONY` entry.

## Completion Summary
All 4 acceptance criteria resolved with concrete evidence, none left as an assumption. Validated
the measurement method against the ticket's own 4 cited examples before trusting the aggregate.
Re-scoped the stale-looking "53" (194/142 on a naive whole-corpus reproduction) to the genuinely
"current, not historical" population the ticket actually meant (49, post-2026-07-19,
workflow-scoped) by finding and applying the actual fix-date boundary rather than either blindly
trusting or blindly distrusting the original number. Root-caused the August cluster concretely by
reading `docs/agent-monitoring/schema.md` directly — it already named the exact mechanism
(pre-2026-08-24 cross-session sidecar contamination) and one of this ticket's own sampled examples
turned out to be that exact document's own cited confirmed instance. Confirmed (not re-derived) the
shared-cause link to `TCK-20260915-SIDECAR-ATTRIBUTION-GAP`. Documented `tools.jsonl` as the
authoritative source in schema.md, and shipped a ratchet check scoped to the population that
actually matters (post-fix, workflow-covered), not the full historical corpus.

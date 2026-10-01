---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-SKILL-PATH-MONITORING-NULL-TS-AND-VERDICT-STRICTNESS
phase: done
date: 2026-09-30
tags: [ai, agent-monitoring]
---

# TCK-20260930-SKILL-PATH-MONITORING-NULL-TS-AND-VERDICT-STRICTNESS

## Title
Two skill-path hand-execution gaps: `record_events.py` aborts on a null-`ts` skipped event, and verdict gates accept only an exact string

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P3

## Request Summary
Two findings from test-architecture-implementer's real `/implement-ticket` skill-path run
(2026-10-01). Both are confirmed by reading the code. Neither is a gate bug: the second one stops
safely. The open question for each is whether to change the tool or the instruction.
1. `implement-ticket.js` ~L1403 pushes the Parity-skipped event with no `ts`, and the
   writeMonitoring prompt (~L439) says to set a null ts to END_TS. `record_events.py` (line 17:
   `REQUIRED` includes `ts`) instead aborts the whole batch atomically ("missing fields ['ts']",
   exit 1, nothing written). The same hotfix-tier skip events (Investigate, Plan, Review) would
   hit it. In the native path the agent follows the prompt; on the skill path the hand-executor can
   miss the substitution.
2. Verdict gates (`review.verdict`, `archVerify.verdict`, `securityReview.verdict` at ~L791, 1157,
   1632, `doneCheck.verdict` at ~L1725) compare against an exact string. An agent returned
   `"APPROVED (no confirmed real violations)"`, which would stop the run. The schema `enum` is
   only a prompt hint on the skill path. Stopping is the safe direction.

## Scope
1. Decide for item 1: have `record_events.py` accept a null/missing `ts` with an explicit
   `--default-ts`, or keep it strict and make the skill's instructions say so. Do not make it
   silently invent a timestamp. Monitoring write failure must never fail the workflow, so check
   the atomic abort against that rule.
2. Decide for item 2: validate the verdict against the enum in the skill path and re-ask the agent
   once on a near-miss, or leave the gate strict and document the hand-executor's duty. A gate
   must never be loosened to a prefix match.
3. Record both decisions and update the skill/docs to match.

## Out of Scope
- Native-path porting (`TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION`).

## Acceptance Criteria
1. Each item has a recorded decision with its reasoning.
2. Any code change has a regression test using the exact failing input quoted above.
3. No gate is loosened to make a near-miss pass.

## Related Tickets
- TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION
- TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP (run that exposed it)

## Related Docs
- `.claude/skills/implement-ticket/SKILL.md`

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/agent-monitoring/record_events.py`
- `.claude/workflows/implement-ticket.js`

## Assumptions / Open Questions
- Whether hand-executors miss the null-ts substitution often enough to justify a tool change.

## Implementation Notes
**Decision, item 1 (null `ts`): change the tool, explicitly.** `record_events.py` gains `--default-ts <ISO>`: it fills only records whose `ts` is missing or null and never overrides an existing `ts`. Without the flag a missing `ts` still aborts the batch exactly as before, and the tool never invents a timestamp. Reasoning: the atomic abort loses every event of a run, which defeats the Hard Rule's intent ("monitoring write failure must never fail the workflow" is about the outcome of monitoring, and a whole-batch drop on one skipped event is a failure of it), while a hand-executor missing the prompt's substitution is a documented, recurring skill-path risk. The writeMonitoring prompt in `implement-ticket.js` and the skill now pass `--default-ts "<END_TS>"` as a mechanical safety net behind the existing "set ts to END_TS" instruction.
**Decision, item 2 (verdict strictness): leave every gate strict and document the duty.** No code change. On the native path the schema `enum` is enforced at the tool-call layer; the gap is skill-path only. The skill now tells the hand-executor: never map or prefix-match a near-miss like `"APPROVED (no confirmed real violations)"`; re-dispatch the same agent once asking for exactly one enum value; if still not exact, stop and report the gate unresolved. Stopping is the safe direction, and a comparison loosened to a prefix match would let `"APPROVED ... but X"` pass.
**Gate integrity:** nothing was edited to change a gate result; the quoted failing inputs are used verbatim in the tests.

## Test Summary
`tests/tools/test_record_events.py` +3 (35 pass), using the exact failing input (a Parity-skipped event with no `ts`): without the flag the whole batch aborts and nothing is written (strictness unchanged); with `--default-ts` only the missing/null `ts` is filled and an existing one is not overridden; `--default-ts` does not rescue any other invalid field. No test changes for item 2 (no code change).

## Files Changed
- `tools/agent-monitoring/record_events.py`, `tests/tools/test_record_events.py`
- `.claude/workflows/implement-ticket.js` (writeMonitoring prompt, `--default-ts`), `.claude/skills/implement-ticket/SKILL.md` (verdict strictness duty, null-ts)
- `stored_artifacts/<this ticket>/`; this ticket

## Completion Summary
Done. AC1: each item has a recorded decision with reasoning (above). AC2: the code change (item 1) has regression tests on the exact failing input. AC3: no gate was loosened; item 2 documents the duty and keeps the comparison strict.

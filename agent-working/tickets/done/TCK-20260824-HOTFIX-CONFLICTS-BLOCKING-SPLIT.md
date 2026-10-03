---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260824-HOTFIX-CONFLICTS-BLOCKING-SPLIT
phase: done
date: 2026-08-24
tags: [ai, workflows, process-improvement, ticket-scoper, agent-monitoring]
---

# TCK-20260824-HOTFIX-CONFLICTS-BLOCKING-SPLIT

## Title
Split `conflicts` into blocking vs. non-blocking informational disclosure in the Scope-phase ticket-scoper contract

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`agent-monitoring/retro/RETRO-2026-W34.md` ("## Notes" → item 1) found `CONFLICTS_DETECTED` fired
2/2 times this week, both cases where the ticket-scoper agent's `conflicts` array held genuinely
non-blocking informational disclosure (e.g. "a related prior ticket exists, but this isn't
duplicate work — it's the ticket that caused the bug being fixed here") rather than a real,
blocking scope conflict. The gate in `.claude/workflows/implement-ticket.js` (confirmed at line
418: `if (ticketInfo.conflicts && ticketInfo.conflicts.length > 0) { ... }`) treats ANY non-empty
`conflicts` array as an unconditional hard stop — it logs the conflict (line 419), writes a
`CONFLICTS_DETECTED` monitoring record via `writeMonitoring('CONFLICTS_DETECTED')` (line 421), and
returns immediately (lines 422-427) — forcing a full extra Scope-resume round-trip (a second
ticket-scoper dispatch via the "Load the existing ticket" branch, lines 99-127, plus its own
monitoring write) before the pipeline can continue, even when nothing was actually blocking. This
happened twice this week, both from the same session, on `TCK-20260823-LIVE-TEST-API-KEY-AUTH` and
`TCK-20260823-HOTFIX-PRESCAN-DRAFT-TEST-SHALLOW-CLONE-FALSE-POSITIVE`, each costing a wasted agent
round-trip for good-faith disclosure the ticket-scoper agent was correctly encouraged to surface
per its own Mandatory Scan step 1 ("flag it as a conflict/duplicate candidate") and its Output
contract item 2 ("any duplicates, mechanic constraints, or parity entries the implementer must
know about" — a description that itself does not distinguish blocking from informational).

Root cause: `TICKET_SCHEMA` (confirmed at `.claude/workflows/implement-ticket.js` lines 73-92) and
both Scope-phase prompt branches' Return-field instructions (the "Load the existing ticket" branch,
line 122: `conflicts=(["ticket file not found for ${ticketId}"] if ticket_path is empty, else [])`;
the "Create a new ticket" branch, line 167: `conflicts (list of any duplicates or conflicts found —
empty array if none)`) never distinguish "genuine blocking duplicate/contradictory work" from
"informational, worth-noting-but-not-blocking context" — both get stuffed into the same `conflicts`
array field, and the gate (which only inspects array length, not content) can't tell them apart, so
it conservatively — and in these 2 cases, incorrectly — treats every non-empty array as a hard
stop.

Precedent for the fix shape already exists in the same schema: `mistag_warning` (schema line 88)
and `suggested_skills` (schema line 84) are both surfaced via `log()` (lines 410-416) without
blocking the pipeline — this ticket extends that same non-blocking-disclosure pattern to cover
informational conflict-adjacent findings, while leaving the `conflicts` field's blocking behavior
completely intact for genuine duplicates/contradictions.

## Scope
- Add a new, clearly-named, optional field to `TICKET_SCHEMA` (`.claude/workflows/implement-ticket.js`
  lines 73-92) for non-blocking informational disclosure — naming is the implementer's judgment
  call (e.g. `related_context`), informed by re-reading the schema/prompt text directly at
  implementation time. The field must NOT be added to the schema's `required` array (line 75), so
  existing in-flight ticket-scoper responses that don't yet return it remain schema-valid.
- Update both Scope-phase prompt branches' Return-field instructions to reflect the new distinction:
  - "Load the existing ticket" branch (lines 99-127, Return statement at line 120-127): clarify that
    `conflicts` is for genuine blocking duplicates only, and instruct the new field for informational
    disclosure.
  - "Create a new ticket" branch (lines 128-172, Return statement at line 166-172): same
    clarification, plus updating step 1's Mandatory-Scan-equivalent instruction (step 1, line 139)
    if its "flag it as a conflict/duplicate candidate" phrasing needs to route genuinely
    non-blocking backlog hits toward the new field instead of `conflicts` — re-read the current text
    directly before deciding whether step 1 itself needs a wording change or only the Return-field
    instruction does.
- Add a `log()` call (mirroring the existing `mistag_warning` pattern at lines 414-416, and the
  `suggested_skills` pattern at lines 410-412) that surfaces the new field's contents for
  human/reviewer visibility without affecting `writeMonitoring`'s final_status or the gate's return
  value.
- Do NOT change the gate condition itself (line 418: `if (ticketInfo.conflicts &&
  ticketInfo.conflicts.length > 0)`) — it must keep firing on a genuinely non-empty `conflicts`
  array exactly as today, including `scopeReasonCode`'s `'conflicts_detected'` branch (lines
  403-405) and the `pushEvent` status logic (lines 406-408). The fix is entirely about which
  findings get PLACED into `conflicts` vs. the new field, driven by clearer prompt instructions —
  not about how the gate reacts to a non-empty `conflicts` array.
- Check `.claude/agents/ticket-scoper.md`'s "Output" section (item 2, line 83: "A short conflict
  report: any duplicates, mechanic constraints, or parity entries the implementer must know about")
  for whether it needs a matching update to describe the new field and to narrow item 2's own
  conflict-report description to blocking findings only. This file is not out of scope here (unlike
  `mistag_warning`'s introduction, TCK-20260705-WORKFLOW-SECURITY-GATE, which explicitly excluded
  it) — update it if the implementer judges its current wording would otherwise perpetuate the same
  conflation this ticket fixes.

## Out of Scope
- `create-tickets.js`'s Structure-phase conflict-dedup logic (`is_duplicate`/`duplicate_of` boolean
  fields on each investigation, confirmed at lines 253-259, filtered at line 340
  `activeInvestigations = validInvestigations.filter(i => !i.is_duplicate)`) — this is a
  structurally different mechanism (a per-investigation boolean flag that skips-and-reports rather
  than an array-length hard-stop gate) and does not exhibit the same conflation bug on inspection;
  no fix needed there. Worth noting for awareness only, not pursued in this ticket.
- The gate condition's blocking behavior itself (`if (ticketInfo.conflicts &&
  ticketInfo.conflicts.length > 0)`, line 418) — must remain unchanged; this ticket only changes
  what gets routed into that array.
- `writeMonitoring`'s `CONFLICTS_DETECTED` final_status value, `scopeReasonCode`'s
  `'conflicts_detected'` value, and `pushEvent`'s Scope-phase status logic (lines 403-408) — no
  change to monitoring taxonomy for genuine conflicts.
- Retroactively re-classifying the 2 historical occurrences this week (`TCK-20260823-LIVE-TEST-API-KEY-AUTH`,
  `TCK-20260823-HOTFIX-PRESCAN-DRAFT-TEST-SHALLOW-CLONE-FALSE-POSITIVE`) or editing their
  agent-monitoring records — those are historical facts, not to be rewritten.
- `TICKET_SCHEMA`'s other fields (`suggested_skills`, `mistag_warning`, `tags`, `todos_source_path`)
  and any tier-inference or staging-directory logic — unrelated, and the staging-directory gap was
  already fixed separately by `TCK-20260824-HOTFIX-STAGING-DIR-SCOPE-GAP`.
- Ticket body sections/format (`## Related Tickets`, `## Scope`, etc.) — this ticket only concerns
  the orchestrator's structured JSON return contract (`TICKET_SCHEMA`) and gate logic, not the
  markdown ticket body the agent also produces.

## Acceptance Criteria
- `TICKET_SCHEMA` gains a new optional field for non-blocking informational disclosure; the
  schema's `required` array is unchanged (still excludes the new field), verified by `node --check`
  passing and a manual read confirming `required` was not edited.
- Both Scope-phase prompt branches' Return-field instructions explicitly distinguish "genuine
  blocking duplicate/contradictory work → `conflicts`" from "informational disclosure → the new
  field," in prose an agent can act on.
- A `log()` call surfaces the new field's contents (when non-empty) without altering
  `writeMonitoring`'s final_status or the function's return value in the non-conflict path.
- The gate at line 418 (`if (ticketInfo.conflicts && ticketInfo.conflicts.length > 0)`) is
  byte-for-byte unchanged, confirmed by diff.
- A ticket-scoper response with only informational disclosure (empty `conflicts`, non-empty new
  field) no longer triggers `CONFLICTS_DETECTED` — the Scope phase proceeds normally.
- A ticket-scoper response with a genuine duplicate/contradiction in `conflicts` still triggers
  `CONFLICTS_DETECTED` exactly as before — verified by tracing the unchanged gate condition against
  a non-empty `conflicts` array.

## Related Tickets
- TCK-20260824-HOTFIX-STAGING-DIR-SCOPE-GAP (done) — sibling hotfix from the same
  `RETRO-2026-W34.md` retro note, also touching `implement-ticket.js`'s Scope phase (the "Create a
  new ticket" branch's step 7, now tier-conditional). That ticket's own Out of Scope explicitly
  deferred this exact finding ("`CONFLICTS_DETECTED` treated as an unconditional hard stop even for
  non-blocking disclosure") as a separate, distinct gate-design issue — this ticket is that
  deferred filing. No line-range overlap expected: that ticket edited step 7 (line 162 pre-edit,
  now the tier-conditional prose); this ticket edits `TICKET_SCHEMA` (lines 73-92), the Return-field
  instructions in both branches (around lines 120-127 and 166-172), and the gate's surrounding
  `log()`/monitoring block (around lines 400-428) — re-read the file directly at implementation time
  since both tickets touch the same file and line numbers may have shifted.
- TCK-20260823-LIVE-TEST-API-KEY-AUTH (done) — first occurrence this week of the wasted
  CONFLICTS_DETECTED round-trip for non-blocking disclosure.
- TCK-20260823-HOTFIX-PRESCAN-DRAFT-TEST-SHALLOW-CLONE-FALSE-POSITIVE (done) — second occurrence
  this week, same root cause.
- TCK-20260705-WORKFLOW-SECURITY-GATE — introduced `mistag_warning` as a non-blocking `log()`-only
  field alongside the existing `conflicts` field; explicitly left `ticket-scoper.md` unedited at the
  time ("Out of Scope for TCK-20260705-WORKFLOW-SECURITY-GATE forbids touching that file" — schema
  comment at line 87). This ticket's fix follows the same non-blocking-field pattern that ticket
  established, and (unlike that one) does consider updating `ticket-scoper.md` if warranted.

## Related Docs
- `agent-monitoring/retro/RETRO-2026-W34.md` — "## Notes" → item 1, source of this finding (2/2
  reproducible occurrences this week).
- `CLAUDE.md` (project instructions) — "Hard Rules" section, gate-integrity rule ("Never edit an
  artifact to make an automated gate/check pass instead of fixing the underlying substance... A
  gate's blocking result... is correct information to report, not an obstacle to route around") —
  this ticket does not weaken the gate's behavior for genuine conflicts; it only narrows what
  legitimately counts as one.
- `docs/agent-monitoring/schema.md` — referenced in the surrounding code comment (implement-ticket.js
  line 231-233) for the existing reason-code disambiguation pattern (`CONFLICTS_DETECTED`,
  `NEEDS_HUMAN_INPUT`, etc.) that this ticket's monitoring behavior must remain consistent with.

## Related Stored Artifacts
None found covering this exact gap. `stored_artifacts/TCK-20260619-E53Ca-CONFLICT-PHASE/` was
checked and is unrelated — it covers `MilitaryConflictPhase` (a gameplay engine pipeline phase),
not the ticket-scoper/Scope-phase workflow gate.

## Related Code Areas
- `.claude/workflows/implement-ticket.js`:
  - `TICKET_SCHEMA` definition (lines 73-92)
  - "Load the existing ticket" Scope-phase prompt branch (lines 99-127), specifically its Return
    statement (lines 120-127)
  - "Create a new ticket" Scope-phase prompt branch (lines 128-172), specifically its Mandatory
    Scan step 1 (line 139) and Return statement (lines 166-172)
  - The CONFLICTS_DETECTED gate block and surrounding monitoring/log logic (lines 400-428)
- `.claude/agents/ticket-scoper.md` — "Output" section item 2 (line 83), a candidate update to
  describe the new field and narrow the conflict-report description to blocking findings only.
- `.claude/workflows/create-tickets.js` — read-only reference for its structurally different
  `is_duplicate`/`duplicate_of` mechanism (lines 253-259, 335-340); confirmed not to need an
  analogous fix, listed for completeness per the Out of Scope note above.

## Assumptions / Open Questions
- Assumes `layer: ai` is correct — matches the layer used by the sibling ticket
  (TCK-20260824-HOTFIX-STAGING-DIR-SCOPE-GAP) and every other `implement-ticket.js`/workflow-prompt
  gap ticket found during scoping. If wrong, only the frontmatter `layer:` value needs correcting.
- Assumes Priority P2 is correct — real, reproducible process friction with a known, cheap manual
  workaround (re-running Scope with `ticket_id` to resume), not a production/user-facing defect or
  a block on any in-flight ticket. Matches the request's explicit framing.
- Assumes Tier `hotfix` is correct — a targeted, self-evident schema-and-prompt-text fix with no
  investigation phase needed, matching the sibling ticket's tier. Per
  `TCK-20260824-HOTFIX-STAGING-DIR-SCOPE-GAP`'s own fix (now live in this file's "Create a new
  ticket" branch, step 7, line 162), hotfix tier means NO `staging_artifacts/{ticket_id}/` directory
  should be created for this ticket.
- Assumes the new field's exact name is an implementation-time judgment call, not fixed by this
  ticket — `related_context` is offered only as an example in the request; the implementer should
  pick a name that reads clearly against the existing `conflicts`/`suggested_skills`/`mistag_warning`
  field-naming conventions already in `TICKET_SCHEMA`.
- Assumes `.claude/agents/ticket-scoper.md` is in scope to edit this time (unlike the precedent-setting
  `mistag_warning` ticket, which explicitly excluded it) — if the implementer judges the current
  Output section wording (item 2) does not actually need a change to remain accurate once the new
  field exists, leaving it unedited is an acceptable outcome, not a scope violation.
- Assumes no change is needed to `create-tickets.js` — confirmed during scoping that its
  `is_duplicate`/`duplicate_of` mechanism is structurally different (a per-investigation boolean
  flag filtered before ever reaching a hard-stop gate, not an array-length check) and does not
  exhibit the same "severity gets collapsed into one field" conflation. If a future retro finds an
  analogous issue there, it should be filed as its own ticket.
- Assumes exact line numbers cited here (73-92, 99-127, 128-172, 400-428) may drift slightly before
  implementation begins, since this is a shared, actively-edited file (the sibling ticket above
  already shifted lines once this week) — implementer must re-read the file directly rather than
  trust these line numbers as literal patch targets.

## Implementation Notes

Re-read `.claude/workflows/implement-ticket.js` directly before editing (line numbers had drifted
slightly from the ticket's citations, as anticipated — e.g. the gate block landed at 418-428 pre-edit,
matching the ticket's estimate closely but not exactly). Changes made:

1. `TICKET_SCHEMA` (was lines 73-92): added `related_context: { type: 'array', items: { type:
   'string' }, description: ... }` immediately after the existing `conflicts` field. NOT added to
   `required` (line 75, unchanged — still `['ticket_id', 'ticket_path', 'status', 'conflicts',
   'tier', 'tags', 'summary']`).
2. "Load the existing ticket" branch: added a clarifying paragraph distinguishing `conflicts`
   (blocking only) from `related_context` (informational) directly before the Return statement, and
   added `related_context=(...)` to the Return field list.
3. "Create a new ticket" branch: reworded step 1's "flag it as a conflict/duplicate candidate"
   instruction to route non-blocking backlog hits to `related_context` and reserve `conflicts` for
   genuine blocking duplicates; added `related_context (...)` to the Return field list, and narrowed
   the `conflicts` field's own description in that same Return list to "ONLY genuine blocking
   duplicate/contradictory work."
4. Added a `log()` call for `ticketInfo.related_context` immediately after the existing
   `mistag_warning` log block (same file, ~line 420) and before the `conflicts` gate check —
   mirrors that block's style exactly (non-blocking, prefixed `Related context (non-blocking): `,
   joined with ` | `).
5. Did NOT touch the gate condition (`if (ticketInfo.conflicts && ticketInfo.conflicts.length > 0)`),
   `scopeReasonCode`, or `pushEvent`'s Scope-phase status logic — confirmed via `git diff` that this
   block is untouched. Per the ticket's own AC ("A log() call surfaces the new field's contents...
   without altering writeMonitoring's final_status or the function's return value in the
   non-conflict path"), `related_context` must never influence `ok`/`failed` status the way
   `unregisteredTags` does — that's the entire point of the fix (informational disclosure must not
   collapse into a blocking signal). So no `unregisteredTags`-style second disambiguating branch was
   added to `scopeReasonCode`/`pushEvent`; the precedent-shape instruction in the ticket's Scope
   section was read as "follow that shape IF you add anything here," and nothing needed adding.
6. Updated `.claude/agents/ticket-scoper.md`: Mandatory Scan item 1 and Output item 2 both
   previously used the same "conflict/duplicate candidate" language that caused the underlying
   conflation described in the Request Summary — judged that leaving this file's wording unchanged
   would perpetuate the exact bug this ticket fixes, so both were reworded to reference `conflicts`
   vs `related_context` explicitly, without renumbering (later items 5/6 refer back to "item 2" by
   number — preserved that reference by editing item 2's text in place rather than inserting a new
   item).
7. `create-tickets.js` untouched, confirmed out of scope per the ticket's own Out of Scope section.

Verified: `node --check .claude/workflows/implement-ticket.js` passes; `git diff` confirms the gate
block (`if (ticketInfo.conflicts...) { ... return { status: 'CONFLICTS_DETECTED', ... } }`) and the
`scopeReasonCode`/`pushEvent` block are byte-for-byte unchanged; `required` array unchanged (grep
confirmed only 7 original entries, no `related_context`).

## Test Summary

No automated test can verify LLM prompt *semantics* (whether the agent actually routes findings
into `conflicts` vs. `related_context` correctly — only observable via future real ticket runs).
But 5 real structural-conformance tests DO cover this file mechanically:
`tests/tools/test_workflow_meta_conformance.py`, `tests/agent_orchestration_claude_adapter/
test_phase_order_conformance.py`, `tests/agent_orchestration_claude_adapter/
test_terminal_status_conformance.py`, `tests/tools/test_done_checker_static.py`,
`tests/tools/test_step0_ts_orchestrator.py` (the last one asserts `TICKET_SCHEMA`'s `required`
array by exact content — confirmed `related_context` correctly excluded). Command:
`pytest tests/tools/test_workflow_meta_conformance.py tests/agent_orchestration_claude_adapter/
test_phase_order_conformance.py tests/agent_orchestration_claude_adapter/
test_terminal_status_conformance.py tests/tools/test_done_checker_static.py
tests/tools/test_step0_ts_orchestrator.py -v`. Initial run: 126 passed, 1 failed (see Deviation
below); after the deviation fix: 127 passed, 1 pre-existing unrelated xfail.

## Files Changed
- `.claude/workflows/implement-ticket.js` — added `related_context` to `TICKET_SCHEMA` (optional,
  not in `required`); updated both Scope-phase prompt branches' Return-field instructions and the
  "Create a new ticket" branch's step 1 wording; added a non-blocking `log()` call for
  `related_context`.
- `.claude/agents/ticket-scoper.md` — reworded Mandatory Scan item 1 and Output item 2 to
  distinguish blocking `conflicts` from non-blocking `related_context`.
- `docs/ai/ticket-lifecycle.md` — Document-Update phase added a sentence to the Scope-phase Gate
  paragraph clarifying that `conflicts` is reserved for genuine blocking work while non-blocking
  disclosure now goes into `related_context` (logged, never gates the pipeline), citing this
  ticket by ID.
- `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py` — updated a
  hardcoded `FINALIZE_INCOMPLETE` call-site line-number baseline (`[1498, 1510]` → `[1507, 1519]`)
  that legitimately drifted from this ticket's own +9-line diff above those call sites. Not a
  regression: independently re-ran the real extractor (`extract_all_terminal_statuses`) to confirm
  `[1507, 1519]` is the true current value before editing, per the project's documented
  hardcoded-baseline-drift pattern (never silently edited without independent verification first).
- `tickets/inprogress/TCK-20260824-HOTFIX-CONFLICTS-BLOCKING-SPLIT.md` — this file (Status,
  Implementation Notes, Test Summary, Files Changed, Completion Summary).

**Deviation from original scope**: the Test phase surfaced a real, mechanical test-baseline drift
(a hardcoded line-number assertion) caused directly by this ticket's own diff shifting line counts.
Fixed in-scope (small, single-file, independently-verified baseline update) rather than filed as a
separate ticket, since it's a direct, expected consequence of this exact change — not an unrelated
bug.

## Completion Summary
Split the ticket-scoper's single `conflicts` field into a blocking `conflicts` field (unchanged
semantics and gate behavior) and a new optional, non-blocking `related_context` field, so
good-faith informational disclosure (e.g. "a related prior ticket exists but this isn't duplicate
work") no longer misfires the `CONFLICTS_DETECTED` hard-stop gate. Updated `TICKET_SCHEMA`, both
Scope-phase prompt branches' instructions and Return statements, added a mirrored `log()` call for
the new field, and clarified `.claude/agents/ticket-scoper.md`'s matching guidance — all without
touching the gate condition, `scopeReasonCode`, `pushEvent`'s status logic, or `create-tickets.js`.

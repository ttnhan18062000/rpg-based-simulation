---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260804-CREATE-TICKETS-SKILL-SYNC
phase: open
date: 2026-08-04
tags: [skills, workflows]
---

# TCK-20260804-CREATE-TICKETS-SKILL-SYNC

## Title
Sync .claude/skills/create-tickets/SKILL.md with create-tickets.js (missing tag-registry gate and short_scope dedup step)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Same drift class as `TCK-20260804-SKILL-JS-PHASE-SYNC` (which fixed `implement-ticket/SKILL.md`), found during a data-mining audit of agent-monitoring records: `.claude/skills/create-tickets/SKILL.md` — the doc a hand-orchestrating agent follows since the real `Workflow` tool is unavailable — has no orchestrator-run-bash row in its phase-translation table at all, and two real behaviors implemented directly in `create-tickets.js` between Structure and Write are completely undocumented there:

1. **`short_scope` dedup** (`create-tickets.js:559-574`) — plain JS Set-based logic (no bash call): if the Structure agent produces two tasks with the same `short_scope` despite instructions, the second is silently dropped with a `WARNING:` log, not written.
2. **Tag-registry gate** (`create-tickets.js:576-614`) — an orchestrator-run bash call to `tag_registry.check_tags_registered()` against the full batch's tag set. Any task carrying an unregistered tag is filtered OUT of `tasksReadyToWrite` (skipped, not written), with a `blocked`-status event pushed and a log line telling the user how to register the tag and re-run. This does not abort the whole batch — it silently narrows which tickets actually get written.

`create-tickets` is the 3rd-most-used workflow in the agent-monitoring corpus (26 runs) — a hand-orchestrating agent unaware of either step would silently write duplicate-`short_scope` ticket files or write tickets carrying unregistered tags that the real JS would have filtered out, directly undermining the tag-registry's append-only-registration discipline CLAUDE.md establishes.

## Scope
- Add an "orchestrator-run bash" row to SKILL.md's phase-translation table, matching the one just added to `implement-ticket/SKILL.md` (same wording: run directly, never delegate to a sub-agent, never skip).
- Add a short description of the `short_scope` dedup step to the Structure phase description (step 3) or a note immediately after it.
- Add a description of the tag-registry gate to the pipeline section, positioned between Structure and Write (matching the real JS's ordering), including: the exact CLI invocation shape, that it narrows `tasksReadyToWrite` rather than aborting, the `blocked`-status event it pushes, and the user-facing remediation message (register the tag, re-run to pick up the skipped concern).
- Full read-through of the rest of `create-tickets.js` (Comprehend, Investigate, Write, Link phases) to confirm no other orchestrator-run step is undocumented — same completeness bar as the implement-ticket sync ticket.

## Out of Scope
- Changing `create-tickets.js` itself.
- Any change to `implement-ticket.js`/`SKILL.md` (already fixed by the sibling ticket).
- A general drift-detection mechanism (noted as a future follow-up in the sibling ticket, not this one's job).

## Acceptance Criteria
- [ ] SKILL.md's phase-translation table includes the orchestrator-run-bash row.
- [ ] SKILL.md describes the `short_scope` dedup behavior.
- [ ] SKILL.md describes the tag-registry gate: invocation, narrowing (not abort) semantics, and remediation message.
- [ ] Full read-through confirms no other undocumented orchestrator-run step in `create-tickets.js`.
- [ ] No change to `create-tickets.js` itself.

## Related Tickets
- TCK-20260804-SKILL-JS-PHASE-SYNC (sibling fix, same drift class, `implement-ticket/SKILL.md`)
- TCK-20260706-CREATE-TICKETS-TAG-CHECK (built the tag-registry gate being newly documented here)

## Related Docs
- `.claude/skills/create-tickets/SKILL.md`
- `docs/ai/agent_definition_gap_audit_2026-08-04.md` (evidence base for this ticket and its siblings)

## Related Code Areas
- `.claude/skills/create-tickets/SKILL.md`
- `.claude/workflows/create-tickets.js` (read-only reference, not modified)

## Assumptions / Open Questions
None — direct transcription of already-shipped JS behavior, same pattern as the sibling ticket.

## Implementation Notes
Rewrote `.claude/skills/create-tickets/SKILL.md`:
- Added the orchestrator-run-bash row to the phase-translation table (matching
  `implement-ticket/SKILL.md`'s row in intent — "run directly, never delegate, never skip" — not
  a verbatim copy, since `implement-ticket/SKILL.md`'s extra clause cites a specific silent-skip
  warning from `implement-ticket.js`'s own comments that doesn't have an equivalent in
  `create-tickets.js`. Flagged by Verify's own re-check as a precision correction, not a
  substantive gap — the AC's actual requirement, semantic equivalence, is fully met.).
- Added the top-of-Action authoritative-source note pointing at this ticket as precedent.
- Step 3 (Structure) now describes both the `short_scope` dedup (plain JS, no bash — drop
  duplicate, warn) and the tag-registry gate (orchestrator-run bash, narrows the write set,
  `blocked`-status event, remediation message) with their exact JS line citations.
- Step 4 (Write) now states explicitly it only writes tasks that survived both checks.

Full read-through of `create-tickets.js` confirmed via direct grep of `await bash(` (2 hits total:
line 123's trivial `date` capture, already implicitly covered by existing per-phase timestamp
handling, and line 583's tag-registry check, now documented) and `phase(` (5 hits: Comprehend,
Investigate, Structure, Write, Link — matches SKILL.md's existing pipeline list exactly, no
missing/extra phase). No other undocumented orchestrator-run step found.

No change made to `create-tickets.js` itself, per Out of Scope.

## Test Summary
No pytest coverage applies (pure prose). Dogfooded the two newly-documented steps directly
against this ticket's own real `files_changed`:
- `doc_staleness_check.py True ".claude/skills/create-tickets/SKILL.md"` → PASS (0 flagged paths).
- `cross_reference_touched(['.claude/skills/create-tickets/SKILL.md'], [])` → `[]` (no failures).
Re-read the final SKILL.md; confirmed the phase-translation table row and the Structure/Write
step descriptions render correctly and match the real `create-tickets.js` line citations
verified during Implementation Notes' read-through.

## Files Changed
- `.claude/skills/create-tickets/SKILL.md` — added orchestrator-run-bash translation-table row;
  documented `short_scope` dedup and the tag-registry gate in Structure; clarified Write only
  uses tasks surviving both checks.

## Completion Summary
Second fix in the same drift class as `TCK-20260804-SKILL-JS-PHASE-SYNC`, found during the
agent-monitoring-driven audit documented in `docs/ai/agent_definition_gap_audit_2026-08-04.md`.
`.claude/skills/create-tickets/SKILL.md` was missing documentation of two real
`create-tickets.js` behaviors: the `short_scope` dedup (silently drops duplicate concerns) and
the tag-registry gate (silently filters unregistered-tag tasks out of the write set, non-abort).
Both now documented with exact line citations, independently re-verified. Document-Update found
all higher-level docs (`docs/ai/workflows.md`, `system_overview.md`, `agents.md`, etc.) already
correctly describe this behavior — only the skill-wrapper prose itself had drifted. Parity made
the same reasoned no-entry-needed call as the sibling ticket. Verify caught one minor precision
slip (Implementation Notes claimed verbatim wording match with the sibling skill's translation
row when it was actually a semantic-equivalent paraphrase) — corrected, non-blocking. Hotfix
pipeline: Scope → Implement → Document-Update (no updates needed) → doc-staleness gate (PASS) →
Test (dogfooded) → Parity (no entry needed) → cross-reference gate (no failures) → Verify (READY
TO CLOSE, 11 PASS / 2 N/A) → Finalize. No change to `create-tickets.js` itself.

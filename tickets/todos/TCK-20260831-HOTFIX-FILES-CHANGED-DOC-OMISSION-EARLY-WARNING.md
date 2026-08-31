---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260831-HOTFIX-FILES-CHANGED-DOC-OMISSION-EARLY-WARNING
phase: open
date: 2026-08-31
tags: [architecture]
---

# TCK-20260831-HOTFIX-FILES-CHANGED-DOC-OMISSION-EARLY-WARNING

## Title
Warn at Document-Update Time When a Ticket's `## Files Changed` Section Omits a Doc-Updater-Touched Path

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Filed from `agent-monitoring/retro/RETRO-2026-W35.md`'s "What to change?" item 1, confirmed
recurring across 4+ M1-batch tickets (`WOUND-THRESHOLD-DECISION`, `TACTICAL-WOUND-SCAR-WIRING`,
`REPUTATION-WITNESSED-EVENT-WIRING`, `AFFECTION-CONTRACT-GATE`): the ticket's own `## Files
Changed` section omitting a doc the Document-Update phase had legitimately touched, caught only
reactively at Verify (6+ phases later) via the `done-checker` agent's own judgment, always fixed
correctly but always late.

The data needed to catch this early already exists inside `.claude/workflows/implement-ticket.js`'s
Document-Update phase: `combinedFilesChanged` (`implement-ticket.js` around line 884-887) already
merges `implementation.files_changed` (the Implement phase's own self-report) with
`docUpdate.docs_updated`'s paths (the Document-Update phase's own real output) for the
doc-staleness gate's purposes — but this merged list is never cross-checked against the ticket
`.md` file's own literal `## Files Changed` prose section, which is what `done-checker` actually
reads at Verify.

## Scope
- Immediately after `combinedFilesChanged` is computed in `.claude/workflows/implement-ticket.js`'s
  Document-Update phase, read the ticket file's current `## Files Changed` section text and check
  whether every path in `docUpdate.docs_updated` appears in it.
- If any path is missing, emit a clear, non-blocking **warning** (into the phase's own event/log
  output, matching this codebase's established fail-open observability pattern — do not fail the
  gate or block the pipeline) naming the specific missing path(s), so whoever runs Finalize sees it
  immediately rather than only at Verify.
- Do NOT auto-edit the ticket file's `## Files Changed` prose programmatically — a warning is the
  right scope here (per the retro's own "warning/auto-fill" framing, choosing the lower-risk
  option); auto-mutating ticket markdown prose from a JS orchestration script is a separate,
  larger, more error-prone piece of scope not justified by this finding alone.
- Add a test exercising this new warning path (a case where `docs_updated` includes a path absent
  from a fixture ticket's `## Files Changed` text, and a case where it's present — no warning).

## Out of Scope
- Auto-filling/auto-editing the `## Files Changed` section itself.
- Making this check blocking/gate-failing — it must remain a warning, not a new hard gate.
- Any other `done-checker`/Verify-phase gate logic.

## Acceptance Criteria
- Running the Document-Update phase with a `docs_updated` path missing from the ticket's current
  `## Files Changed` section produces a visible warning at that point, not just at Verify.
- The pipeline does not fail or block on this warning alone.
- A regression test covers both the warning-fires and no-warning cases.

## Related Docs
- `agent-monitoring/retro/RETRO-2026-W35.md` (§ "What to change?" item 1, and item 2's precedent —
  two gate-checker false-positive tickets fixed the same week this finding was filed in)
- `docs/architecture/doc_updater_agent.md`

## Related Code Areas
- `.claude/workflows/implement-ticket.js` (Document-Update phase, `combinedFilesChanged`)

## Assumptions / Open Questions
Exact warning format/placement (event message vs. a dedicated log line) left to implementation
judgment, matching existing patterns elsewhere in this same phase (e.g. the doc-staleness gate's
own ADVISORY-entry shape).

## Implementation Notes
(Not yet implemented — filed and deferred.)

## Test Summary
(Not yet implemented.)

## Files Changed
(Not yet implemented.)

## Completion Summary
(Not yet implemented.)

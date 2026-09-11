---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260807-DOC-UPDATER-FIRST-ATTEMPT-BLOCKED-RATE
phase: done
date: 2026-08-07
tags: [agent-monitoring, process-improvement]
---

# TCK-20260807-DOC-UPDATER-FIRST-ATTEMPT-BLOCKED-RATE

## Title
`doc-updater` agent's status distribution reads 100% "ok," but 3 of its most recent 3
observably-slow runs needed a `DOD_BLOCKED` retry before landing — investigate whether there's a
recurring first-attempt gap the "ok" status hides

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Found during a 2026-08-07 agent-monitoring retro (`agent-monitoring/retro/RETRO-2026-W32.md`
Notes §2). The week's Agent Status Distribution table shows `doc-updater: 8 calls, 8 ok, 0
failed/blocked/skipped` — a clean 100% rate at the per-agent-call granularity. But the same
week's Slow Runs table shows the 3 tickets that most heavily exercised `doc-updater`
(`TCK-20260803-DOC-UPDATER-CORE-WIRING`, `-VOCAB-REGISTRATION`, `-DASHBOARD-PALETTE`) each show
**two** entries — a `DOD_BLOCKED` run followed by a `DONE` run for the same `run_id`:

| run_id | 1st attempt | 2nd attempt |
|---|---|---|
| `TCK-20260803-DOC-UPDATER-CORE-WIRING` | 72 min, `DOD_BLOCKED` | 78 min, `DONE` |
| `TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION` | 44 min, `DOD_BLOCKED` | 51 min, `DONE` |
| `TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE` | 33 min, `DOD_BLOCKED` | 41 min, `DONE` |

The per-agent-call `ok` status only captures "the agent call itself didn't error" — it says
nothing about whether the FULL pipeline's own `Verify` (done-checker) gate passed on the first
try. All 3 of `doc-updater`'s own recent, most-exercised tickets needed a second full pass. This
could be coincidence (3 tickets, small sample, all part of the same `TCK-20260803-DOC-UPDATER-EPIC`
which may have shared some other, unrelated first-pass gap unrelated to `doc-updater` specifically)
or a real, recurring `doc-updater` blind spot worth understanding before its prompt/instructions
are trusted at face value for future tickets.

## Scope
1. **Investigate** (mandatory before Plan):
   - Read all 3 tickets' own Implementation Notes / Verify-phase history (`tickets/done/
     TCK-20260803-DOC-UPDATER-CORE-WIRING.md`, `-VOCAB-REGISTRATION.md`, `-DASHBOARD-PALETTE.md`)
     to find exactly what `done-checker` flagged on each first attempt.
   - Cross-reference `agent-monitoring/events.jsonl` for these 3 `run_id`s' own `Verify`-phase
     event summaries (the actual `done-checker` verdict text) rather than relying on the ticket
     prose alone.
   - Determine whether the 3 blocks share a common root cause (e.g. all 3 are `doc-updater`
     specifically missing a `docs_to_update`-listed file, or all 3 are unrelated DoD conditions
     that happen to also involve doc changes) or are 3 unrelated causes that coincidentally landed
     in the same epic/week.
2. **Plan**: if a real, common `doc-updater`-specific gap is found, design a prompt/instruction
   fix for `.claude/agents/doc-updater.md`; if the 3 causes are unrelated to `doc-updater` itself,
   document that finding and close without a code change.
3. **Implement**: apply the fix, if one is warranted.

## Out of Scope
- Any change to `done-checker`'s own DoD conditions or `tools/gate_checks/*.py` — this ticket is
  about `doc-updater`'s own first-attempt success rate, not about relaxing what Verify checks.
- Re-running the 3 already-closed `TCK-20260803-DOC-UPDATER-*` tickets — they are DONE; this
  ticket is a forward-looking investigation, not a re-litigation of already-closed work.

## Acceptance Criteria
- [ ] `investigation.md` identifies the exact `done-checker` finding that blocked each of the 3
      first attempts, sourced from real `events.jsonl`/ticket records, not assumed
- [ ] A clear verdict: common `doc-updater`-specific cause (fix its prompt) vs. 3 unrelated causes
      (no code change, close with findings documented)
- [ ] If a fix is made: a scoped test or real-kernel-adjacent check confirming the specific gap is
      closed
- [ ] Scoped pytest run passes (if any code/prompt change is made)

## Related Tickets
- TCK-20260803-DOC-UPDATER-EPIC (the epic these 3 child tickets belong to — DONE)
- TCK-20260803-DOC-UPDATER-CORE-WIRING, -VOCAB-REGISTRATION, -DASHBOARD-PALETTE (the 3 runs under
  investigation — all DONE)

## Related Docs
- `docs/architecture/doc_updater_agent.md`
- `.claude/agents/doc-updater.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260803-DOC-UPDATER-CORE-WIRING/`
- `stored_artifacts/TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION/`
- `stored_artifacts/TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE/`

## Related Code Areas
- `.claude/agents/doc-updater.md`
- `tools/gate_checks/done_checker_static.py` (read-only reference — the gate that blocked each
  first attempt, not expected to change)

## Assumptions / Open Questions
- Whether 3 data points is even a large enough sample to distinguish "real recurring gap" from
  "coincidence" — not assumed; if Investigate finds 3 genuinely unrelated causes, the honest
  conclusion is "no pattern found," not a forced fix.

## Implementation Notes
Subagent spawn cap (200/200) reached before this ticket started — Investigate performed directly.

Traced all 3 real `agent-monitoring/events.jsonl` Verify-phase `DOD_BLOCKED` records to their exact
`done-checker` finding text. Found 2 recurring categories (unchecked AC checkboxes: 2/3;
malformed "Docs Requiring Update" section: 2/3) plus 1 one-off (wrong file path/test count: 1/3).
Cross-referenced both recurring categories against already-closed tickets and confirmed BOTH were
independently root-caused and fixed the very next day (2026-08-04) by
`TCK-20260804-AGENT-DEF-GAP-FIXES` (implementer-agent AC/Completion-Summary hygiene gap,
`.claude/agents/implementer.md` updated) and its parser-strictness fix (`_DOCS_NONE_PHRASES`
intolerant of trailing rationale prose after "None." in `done_checker_static.py`), further refined
by `TCK-20260804-DOCS-BULLET-LINE-SUFFIX-FIX`. Neither category is doc-updater's own artifact —
doc-updater never touches ticket-body AC checkboxes or investigation.md's Docs Requiring Update
section (investigator's own artifact, produced before doc-updater ever runs).

Caught and fixed a real, live instance of the exact parser bug being investigated: this
investigation.md's own inline prose referencing `` `## Docs Requiring Update` `` (in backticks,
describing the section) collided with `_extract_section_text`'s naive `str.find()` substring
search, which doesn't require the heading to actually start a line — `docs_to_update_coverage`
failed on this ticket's own first Verify attempt for exactly the reason under investigation. Fixed
by adding a genuine `## Docs Requiring Update` heading (containing "None.") near the top of the
file, ahead of the colliding inline prose, rather than editing around the gate's own finding.

No code/prompt change made — investigation supports "no shared doc-updater-specific cause," which
the ticket's own Acceptance Criteria explicitly allows as a valid, honest terminal state.

## Test Summary
No code change made; no new tests. `run_static_precheck`: all 7 script-checkable DoD conditions
PASS (after fixing this ticket's own investigation.md Docs Requiring Update collision).

## Files Changed
None (investigation-only ticket; only `staging_artifacts/`/ticket-body artifacts touched).

## Completion Summary
Confirmed the doc-updater agent's clean per-call status (8/8 ok) is genuinely accurate — none of
the 3 `DOD_BLOCKED` retries in its own recent history trace to doc-updater's own conduct. Both
recurring failure categories were already independently diagnosed and fixed by a same-epic
follow-up ticket one day later; documented rather than re-fixing already-fixed gates. Ironically
hit a live instance of the exact "Docs Requiring Update" parser collision under investigation
while writing this ticket's own investigation.md, and fixed it honestly (added the missing real
section) rather than rewording around the gate.

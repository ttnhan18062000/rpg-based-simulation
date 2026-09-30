---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-PLANNING-DOC-STALENESS-DETECTOR
phase: open
date: 2026-09-30
tags: [documentation, process-improvement, planning]
---

# TCK-20260930-PLANNING-DOC-STALENESS-DETECTOR

## Title
Report-only detector for planning docs whose claimed status ('idea' / 'ready, schedule later') is stale against tickets/done/

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The author noticed that several docs/plans/ planning documents still claim an item is open (frontmatter status: idea, or body text like "Horizon 2 — ready, schedule later") even though a real ticket in tickets/done/ already shipped exactly that item, and nothing currently re-checks a planning doc's own claimed status against tickets/done/ once the ticket it describes closes. The goal is a detector — either a close-time prompt (when a closing ticket's Related Docs names a planning doc as the source of the shipped work) or a periodic sweep (diff docs/plans/*idea*.md / 'ready, schedule later' items against tickets/done/ titles/keywords) — that flags this drift for a human or agent to resolve, and must never auto-edit the doc since only a person can judge whether the shipped ticket covers the full idea or just part of it. This matters because a reader landing on a stale doc could reasonably conclude unstarted work remains and duplicate it — the exact failure mode create-tickets.js's duplicate-detection step exists to catch, but only if the investigating agent happens to search tickets/done/ for the right keywords instead of trusting the planning doc's stated status.

## Scope
- Add a new report-only detector function/script (location alongside tools/gate_checks/doc_staleness_check.py or tools/agent-monitoring/epic_staleness_check.py, matching their 'never fails, returns findings' shape) for docs/plans/
- Detector scans docs/plans/*.md for frontmatter status: idea (primary, structured signal) and body text matching 'ready, schedule later' or the doc's own analogous phrasing (secondary heuristic, since that exact phrase currently appears in only one doc)
- Cross-references matched planning-doc items against tickets/done/ ticket titles/IDs via title/keyword matching, returning a list of (doc_path, matched_ticket_id, matched_text) findings for human/agent review
- Detector never auto-edits the flagged doc and never returns a blocking FAIL/exit-nonzero verdict, consistent with every other detector in this corpus
- Add tests covering the two already-confirmed real drift cases as fixtures, plus a read-only/no-mutation guarantee test
- Ticket's own Implementation Notes or Assumptions/Open Questions section must explicitly decide and record the rationale for: (a) close-time prompt vs. periodic sweep as the trigger mechanism, and (b) which resolution convention (archive to docs/plans/archive/, frontmatter status flip, or inline dated note) is recommended once a doc is confirmed fully shipped

## Out of Scope
- Auto-editing, auto-archiving, or auto-flipping frontmatter status on the flagged planning doc — resolution stays a human/agent judgment call
- Building a structured back-link mechanism from tickets to the planning docs they trace to (a real limitation noted in the investigation, not solved by this ticket)
- Wiring the detector into any blocking gate or making ticket-close/CI fail on its output — it must remain report-only/advisory like doc_staleness_check.py and epic_staleness_check.py
- Actually resolving the two already-known stale docs (idea_agent_monitoring_active_duration.md, standalone_items.md) beyond using them as test fixtures for the detector

## Acceptance Criteria
- [ ] A new report-only detector function (mirroring check_doc_staleness/check_drift's 'never fails, returns findings' shape) takes docs/plans/ files carrying frontmatter status: idea or body text matching 'ready, schedule later' plus tickets/done/ ticket titles/IDs, and returns a list of (doc_path, matched_ticket_id, matched_text) findings — it never returns a blocking FAIL/exit-nonzero verdict
- [ ] Running the detector against the two real, already-confirmed-in-repo cases (docs/plans/agent_infrastructure/idea_agent_monitoring_active_duration.md vs TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT/TCK-20260822-DASHBOARD-DURATION-GAP-AWARE; docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md items 3-4 vs TCK-20260904-WORKING-LOG-CSV-PARSER/TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST) surfaces both as flagged mismatches in a test
- [ ] A test asserts the target planning doc's file bytes/mtime are unchanged after the detector runs against it, proving the never-auto-edit constraint holds in code
- [ ] The ticket's own Implementation Notes or Assumptions/Open Questions section explicitly resolves both open design questions (close-time prompt vs periodic sweep; archive vs frontmatter-flip vs inline dated note for a confirmed-shipped doc) with a stated rationale rather than silently picking one

## Related Tickets
- TCK-20260711-DOC-STALENESS-GATE-CHECK
- TCK-20260710-EPIC-STALENESS-CHECK
- TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK
- TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC
- TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE
- TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION
- TCK-20260719-AGENTOPS-DASHBOARD-DOCS-CLOSURE
- TCK-20260719-AGENT-MONITORING-DOCS-CLOSURE
- TCK-20260710-WORKFLOW-EXECUTION-DETERMINISM-EPIC
- TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT

## Related Docs
- docs/plans/idea_stale_planning_doc_status_after_ship.md
- docs/plans/agent_infrastructure/idea_agent_monitoring_active_duration.md
- docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md
- docs/plans/archive/agent_infrastructure/idea_agent_monitoring_pause_resume_seq_collision.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/gate_checks/doc_staleness_check.py
- tools/agent-monitoring/epic_staleness_check.py
- tools/mechanism_registry/mechanism_registry_changed_code_check.py
- tools/open_ticket_overlap.py
- docs/plans/idea_stale_planning_doc_status_after_ship.md
- docs/plans/agent_infrastructure/idea_agent_monitoring_active_duration.md
- docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md
- docs/plans/archive/agent_infrastructure/idea_agent_monitoring_pause_resume_seq_collision.md

## Assumptions / Open Questions
- Title/keyword matching between a planning-doc item and a shipped ticket is inherently fuzzy — no structured back-link exists from most tickets to the planning doc they trace to, so false negatives (and possibly false positives on coincidental keyword overlap) are likely with a naive implementation
- The repo currently resolves a confirmed-shipped planning doc three different ways (archive to docs/plans/archive/, frontmatter status flip, dated inline note); picking one convention now is a real design decision this ticket must record, not a free choice
- A close-time-prompt implementation only fires when the closing ticket's own Related Docs correctly names the source planning doc; traceability is often implicit or missing, which is a real limitation relative to a periodic sweep
- 'ready, schedule later' is today's literal wording in exactly one doc (standalone_items.md); a text-match sweep keyed to that exact phrase is brittle against paraphrasing elsewhere, so the detector should be scoped primarily to frontmatter status: idea (structured) with this phrase as a secondary heuristic, not the reverse
- `layer: ai` was chosen (per registry note: "Claude agent/orchestration tooling") over `guidelines` or `observability` since this detector is agent-workflow tooling analogous to doc_staleness_check.py/epic_staleness_check.py, not a convention doc itself or a monitoring/telemetry system

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

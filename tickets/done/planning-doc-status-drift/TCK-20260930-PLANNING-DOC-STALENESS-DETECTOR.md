---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-PLANNING-DOC-STALENESS-DETECTOR
phase: done
date: 2026-09-30
tags: [documentation, process-improvement, planning]
---

# TCK-20260930-PLANNING-DOC-STALENESS-DETECTOR

## Title
Report-only detector for planning docs whose claimed status ('idea' / 'ready, schedule later') is stale against tickets/done/

## Status
DONE

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
- [x] A new report-only detector function (mirroring check_doc_staleness/check_drift's 'never fails, returns findings' shape) takes docs/plans/ files carrying frontmatter status: idea or body text matching 'ready, schedule later' plus tickets/done/ ticket titles/IDs, and returns a list of (doc_path, matched_ticket_id, matched_text) findings — it never returns a blocking FAIL/exit-nonzero verdict
- [x] Running the detector against the two real, already-confirmed-in-repo cases (docs/plans/agent_infrastructure/idea_agent_monitoring_active_duration.md vs TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT/TCK-20260822-DASHBOARD-DURATION-GAP-AWARE; docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md items 3-4 vs TCK-20260904-WORKING-LOG-CSV-PARSER/TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST) surfaces both as flagged mismatches in a test
- [x] A test asserts the target planning doc's file bytes/mtime are unchanged after the detector runs against it, proving the never-auto-edit constraint holds in code
- [x] The ticket's own Implementation Notes or Assumptions/Open Questions section explicitly resolves both open design questions (close-time prompt vs periodic sweep; archive vs frontmatter-flip vs inline dated note for a confirmed-shipped doc) with a stated rationale rather than silently picking one

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
- docs/plans/archive/idea_stale_planning_doc_status_after_ship.md
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
- docs/plans/archive/idea_stale_planning_doc_status_after_ship.md
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
**Design decision (a), trigger: a periodic sweep, not a close-time prompt.** A close-time prompt only
fires when the closing ticket's `## Related Docs` correctly names the source planning doc, and the
two confirmed cases show that traceability is often implicit or absent (the tickets that shipped
them never named the docs). A sweep catches drift regardless, at the cost of a standing script,
which is cheap here: it is one file, runs in ~0.2 s, and is report-only. `make
planning-doc-staleness-check` runs it on demand; it is not wired into any gate or hook.

**Design decision (b), resolution convention: archive with `status: historical` for a fully shipped
idea doc; an inline dated note for a shipped item inside a still-active doc.** Archiving has the
repo's own precedent (`docs/plans/archive/agent_infrastructure/idea_agent_monitoring_pause_resume_
seq_collision.md`, which the stale idea doc itself points at) and removes the doc from the sweep's
scope (`archive/` is skipped); a frontmatter flip alone leaves a shipped idea among live ones, and an
inline note is the only option for one item inside a doc that stays active. A heading that already
says SHIPPED / CLOSED / "was:" is skipped by the sweep, so the inline-note convention closes its own
finding. Closed tickets that cite an archived doc's old path are historical records and are not
rewritten. Applied once, to `idea_stale_planning_doc_status_after_ship.md` (this ticket ships it).

**Matching rule** (documented in the module and `docs/ai/ticket-lifecycle.md`): done-ticket slug (after
the date, generic words dropped) has >= 3 tokens and >= 75% of them appear in the doc's identity text
(file stem + H1 for idea docs; the heading for a "ready, schedule later" item); the ticket is dated on
or after the doc; a `## Disposition` closure never matches. First cut returned 17 findings, mostly
coincidental word overlap with 2026-06-19 tickets; the date guard and the narrower identity text give
5. Real run: the two confirmed cases plus two real extras (`idea_semantic_entity_index.md`,
`world_rendering/idea_world_rendering_core.md`).

**Deliberately not done** (ticket Out of Scope): resolving the five flagged docs. They are a person's
call (whole idea vs part), and the sweep now lists them.

## Test Summary
`tests/tools/test_planning_doc_staleness_check.py`, 8 tests: both confirmed drift cases (frozen
fixtures), unshipped item and already-resolved heading not flagged, ticket older than the doc not
matched, `## Disposition` closure not matched, `archive/` skipped, no mutation of any doc (bytes and
mtime, also through the CLI), missing directories return [], CLI exits 0 with and without findings.
All pass. Real-repo run of the CLI: 5 findings, exit 0.

## Files Changed
- `tools/gate_checks/planning_doc_staleness_check.py` (new), `tests/tools/test_planning_doc_staleness_check.py` (new)
- `Makefile` (`planning-doc-staleness-check`), `docs/ai/ticket-lifecycle.md`
- `docs/plans/archive/idea_stale_planning_doc_status_after_ship.md` (moved from `docs/plans/`, status flipped)
- this ticket and its artifacts; `docs/REGISTRY.yaml`

## Completion Summary
Done. The detector, its make target and tests are in; both design questions are decided with
rationale above. AC1: `find_stale_planning_docs()` returns `(doc_path, matched_ticket_id, matched_text,
signal)` findings, never a failing verdict (the CLI always exits 0). AC2: both real cases are flagged in
a test (frozen fixtures) and on the live tree. AC3: a test asserts bytes and mtime are unchanged after a
run. AC4: both open questions are resolved in Implementation Notes. Follow-up for a person: the five
flagged docs listed by `make planning-doc-staleness-check`.

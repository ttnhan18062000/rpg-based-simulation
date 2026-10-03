---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-PLANNING-DOC-STALENESS-DETECTOR
artifact_type: plan
tags: [documentation]
---

# Plan

1. New `tools/gate_checks/planning_doc_staleness_check.py`: `find_stale_planning_docs(plans_dir, done_dir)` returns `Finding(doc_path, matched_ticket_id, matched_text, signal)` tuples; CLI prints them and always exits 0; never writes.
2. Candidates under `docs/plans/` (archive/ skipped): frontmatter `status: idea` (identity text = file stem + H1) and headings containing "ready, schedule later" (identity text = the heading; headings already saying SHIPPED/CLOSED/"was:" are skipped).
3. Match rule against `tickets/done/**/TCK-*.md`: the ticket slug (after the date, generic words dropped) has >= 3 tokens, >= 75% appear in the identity text, the ticket is dated on or after the doc, and the ticket carries no `## Disposition` (a WONT-DO/STALE-PREMISE closure shipped nothing).
4. `make planning-doc-staleness-check`; document in `docs/ai/ticket-lifecycle.md` (trigger decision + resolution convention).
5. Tests use frozen fixtures of the two real drift cases, so they survive the real docs being resolved.
6. Decisions recorded in the ticket: (a) periodic sweep, not a close-time prompt; (b) archive with `status: historical` for a fully shipped idea doc, inline dated note for a shipped item inside an active doc.
7. Archive the source idea doc (`idea_stale_planning_doc_status_after_ship.md`) as the first application of convention (b).

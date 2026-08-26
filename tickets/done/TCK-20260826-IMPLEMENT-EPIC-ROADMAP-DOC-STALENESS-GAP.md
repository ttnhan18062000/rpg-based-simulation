---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260826-IMPLEMENT-EPIC-ROADMAP-DOC-STALENESS-GAP
phase: open
date: 2026-08-26
tags: [workflows, documentation, process-improvement]
---

# TCK-20260826-IMPLEMENT-EPIC-ROADMAP-DOC-STALENESS-GAP

## Title
`implement-epic.js` folder mode has no mechanism to keep a batch's own source-of-truth roadmap doc
in sync as child tickets complete

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Found live during the `m1-quick-wins` batch run (`TCK-20260824-ROLLOUT-FLAG-DECISIONS` and
siblings): `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`'s M1 section still said "ready to
ticket now" and "Tracking epic: `TCK-...-EPIC-RPG-M1-QUICK-WINS` (not yet created)" after 3 tickets
had already landed on the `m1-quick-wins` branch and the batch was running via the folder-based
`implement-epic folder=tickets/todos/m1-quick-wins/` flow (no separate epic ticket was ever
created for this batch). Nothing in `.claude/workflows/implement-epic.js`'s Discover/Implement/
Report phases, nor in `implement-ticket.js`'s per-ticket Document-Update phase, updates a doc like
this — it isn't in any single ticket's own "Docs Requiring Update" list (it's not about that
ticket's behavior change), and it isn't a per-ticket artifact at all; it's a fact about the batch as
a whole. The staleness was caught only by a direct user prompt asking whether tracking docs were
being kept current, not by any gate. This ticket exists to close that structural gap rather than
rely on it being noticed by chance on future batches.

## Scope
- Investigate whether other completed/in-flight epics (`docs/plans/rpg_design_roadmap/` siblings,
  and any other `docs/plans/*/*.md`-style roadmap docs referencing a tracking epic or ticket
  folder) have the same kind of staleness right now, not just the M1 case that surfaced this
- Decide a concrete mechanism for `implement-epic.js`'s `folder` mode to declare (optionally) a
  `tracking_doc:` path — e.g. a new field readable from `SEQUENCE.md`'s own frontmatter/header, or
  a sibling metadata file in the ticket folder — and, when present, have the Report phase (or a new
  small phase) update a bounded, clearly-delimited status block in that doc (not free-form prose
  rewriting) after each batch run, reflecting done/remaining counts and the real tracking mechanism
  in use (folder-based vs. formal epic ticket)
- Decide what happens when no `tracking_doc:` is declared (the common case today) — likely a no-op,
  but state it explicitly rather than leaving it implicit
- Update `.claude/skills/implement-epic/SKILL.md` to match the JS change, per this repo's own
  "if the two disagree, the JS wins, but keep them in sync" convention
- Do not attempt to retrofit this into currently-running batches (e.g. `m1-quick-wins`) as part of
  this ticket — that's an operational concern, handled by hand for now; this ticket is about the
  reusable mechanism for all future folder-mode batches

## Out of Scope
- Manually fixing every currently-stale roadmap doc found during investigation beyond disclosing
  them — file a lightweight follow-up ticket per stale doc found, if any exist, rather than folding
  arbitrary doc fixes into this tooling ticket
- Any change to `epic_id` mode (reading `## Related Tickets` from a real epic ticket) — that mode
  already has a natural home (the epic ticket itself) for a status field if one is ever wanted;
  this ticket is specifically about `folder` mode's structural gap

## Acceptance Criteria
- [x] Investigation discloses whether any other roadmap/plan doc referencing a tracking epic or
      ticket folder is currently stale, with specifics
- [x] A concrete `tracking_doc:` declaration mechanism for `implement-epic.js` folder mode is
      designed and implemented, with an explicit no-op behavior when undeclared
- [x] `.claude/skills/implement-epic/SKILL.md` is updated to match
- [x] A real batch run (can be a scratch/test folder, does not need to be a live epic) demonstrates
      the status block updating correctly after Implement

## Related Tickets
- TCK-20260824-ROLLOUT-FLAG-DECISIONS (where the staleness was found and manually patched)
- TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP (same genre: a real hand-orchestration
  gap found live, fixed via a dedicated tooling ticket rather than a silent workaround)
- TCK-20260807-SEARCH-BEFORE-GREP-OBSISO-EPIC-GAP (same genre, epic-orchestration process gap)

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_design_roadmap.md (the doc that was found stale)
- .claude/skills/implement-epic/SKILL.md
- .claude/workflows/implement-epic.js

## Related Stored Artifacts
- stored_artifacts/TCK-20260826-IMPLEMENT-EPIC-ROADMAP-DOC-STALENESS-GAP/{plan,investigation,test_plan}.md

## Related Code Areas
- .claude/workflows/implement-epic.js
- .claude/skills/implement-epic/SKILL.md
- tools/gate_checks/epic_tracking_doc_static.py
- tests/tools/test_epic_tracking_doc_static.py

## Assumptions / Open Questions
- Whether the status block should live inline in the roadmap doc (as done by hand for M1) or in a
  separate generated status file the roadmap doc links to is an open design call for the
  Investigate/Plan phases to resolve
- Whether this same gap class applies to `epic_id` mode in some other form (e.g. a stale summary
  line inside the epic ticket itself, not auto-refreshed) is worth a quick check even though it's
  formally out of scope, per the note above

## Implementation Notes
See `stored_artifacts/TCK-20260826-IMPLEMENT-EPIC-ROADMAP-DOC-STALENESS-GAP/investigation.md` and
`plan.md` for full detail. Summary: chose an optional `tracking_doc: <path>` plain-text line inside
`SEQUENCE.md` (folder mode only — `epic_id` mode already has a natural home, the epic ticket
itself, per this ticket's own Out of Scope). Chose two literal markers
(`<!-- IMPLEMENT-EPIC-STATUS:BEGIN -->`/`END`) that must already exist in the tracking doc, placed
manually once, rather than auto-inserting at a guessed location — the mechanism only ever replaces
content strictly between an existing pair. New Python helper
`tools/gate_checks/epic_tracking_doc_static.py` (mirroring this repo's own established
`parity_updater_static.py`/`mechanics_auditor_static.py`/`done_checker_static.py` pattern of real,
testable logic backing agent workflows rather than opaque agent-prompt English) backs both the
Discover-phase parse and the Report-phase update. Wired into `.claude/workflows/implement-epic.js`:
Discover's `folder` branch now also returns a `tracking_doc` field; Report runs the update on
*every* batch invocation (not gated on full completion), a true no-op (no `agent()` call at all)
when nothing was declared. `.claude/skills/implement-epic/SKILL.md` updated to match.

Investigation (Scope item 1) found `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`'s M1
section (the case that triggered this ticket) already manually patched, and
`docs/plans/hud_delivery_roadmap.md`'s 4 tracked epics still accurate. Found one genuinely stale
doc in a different tracking mode: `docs/plans/live_map_scaling_roadmap.md`'s M1 section didn't
reflect that `TCK-20260821-EPIC-LIVE-MAP-RECONNECTION` had already completed — filed and fixed as
its own lightweight follow-up, `TCK-20260826-HOTFIX-LIVE-MAP-RECONNECTION-ROADMAP-STALE`, per this
ticket's own Out-of-Scope instruction rather than folded in here.

No `src/` files touched by this ticket — parity ledger unaffected, confirmed no candidate shard for
`.claude/workflows/`, `.claude/skills/`, or `tools/gate_checks/` paths.

## Test Summary
`.venv/bin/python3 -m pytest tests/tools/test_epic_tracking_doc_static.py -v` — 13 passed (new
file; doubles as AC4's real demonstration, exercising the exact function
`implement-epic.js`'s Report phase calls, against a scratch `SEQUENCE.md`-equivalent input and
scratch tracking doc with markers). `node --check .claude/workflows/implement-epic.js` — syntax
OK. Broader regression: `pytest tests/tools/test_epic_tracking_doc_static.py
tests/tools/test_parity_updater_static.py tests/tools/test_mechanics_auditor_static.py
tests/tools/test_done_checker_static.py -q` — 140 passed, 0 failed.

## Files Changed
- `tools/gate_checks/epic_tracking_doc_static.py` — new module.
- `tests/tools/test_epic_tracking_doc_static.py` — new test file, 13 tests.
- `.claude/workflows/implement-epic.js` — Discover's `folder`/`epic_id` branches gain a
  `tracking_doc` field; Report phase gains the status-block-update step (folder mode only).
- `.claude/skills/implement-epic/SKILL.md` — documents the new `tracking_doc:` convention and the
  Report-phase behavior, including its explicit no-op/`markers_missing` semantics.

## Completion Summary
Closed the confirmed structural gap: `implement-epic.js` `folder` mode now has a real, tested
mechanism (an optional `tracking_doc:` declaration in `SEQUENCE.md`, updating a bounded,
marker-delimited status block after every batch invocation) to keep a batch's own roadmap doc in
sync, rather than relying on a human noticing by chance. `epic_id` mode deliberately untouched
(already has its own tracking surface). Investigation also surfaced and fixed one genuinely stale
roadmap doc from a different tracking mode as its own small follow-up ticket, per this ticket's own
Out-of-Scope instruction not to fold arbitrary doc fixes into the tooling work itself.

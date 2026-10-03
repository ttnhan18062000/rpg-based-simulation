---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260826-IMPLEMENT-EPIC-ROADMAP-DOC-STALENESS-GAP
artifact_type: investigation
tags: [workflows, documentation, process-improvement]
---

# Investigation — TCK-20260826-IMPLEMENT-EPIC-ROADMAP-DOC-STALENESS-GAP

## Confirmed: no existing mechanism
Read `.claude/workflows/implement-epic.js` in full (356 lines). Zero mentions of `tracking_doc`,
`roadmap`, or `docs/plans` anywhere. Discover reads `SEQUENCE.md` purely for ticket ordering;
Report only summarizes done/remaining counts to the log/return value, never writes to any doc.
The batch-monitoring-write and folder-cleanup steps (after Implement, before Report) are the only
other file-touching side effects, and neither concerns a roadmap doc. Confirms the ticket's core
claim is accurate, not overstated.

## Other-doc staleness audit (Scope item 1)
`grep -rln "Tracking epic\|Tracking:" docs/plans/` finds exactly 3 docs using this convention:

1. **`docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`** (the M1/folder-mode case that
   triggered this ticket) — already manually patched by hand (per this ticket's own Out-of-Scope
   note). Current M1 status block reads "(IN PROGRESS)" and points to a live `ls`/`working_log.csv`
   check rather than a static count — well-designed to not re-go-stale on its own. Not currently
   stale.
2. **`docs/plans/hud_delivery_roadmap.md`** — 4 `epic_id`-mode tracking epics
   (`TCK-20260822-EPIC-HUD-DESIGN-SYSTEM-FOUNDATION`, `-CORE-PANEL-WIRING`,
   `-CONTEXTUAL-PANEL-WIRING`, `-CONTENT-POLISH-MEASUREMENT`). Checked all 4 against real ticket
   state: all still in `tickets/todos/`, none done. Not stale.
3. **`docs/plans/live_map_scaling_roadmap.md`** — 3 `epic_id`-mode tracking epics
   (`TCK-20260821-EPIC-LIVE-MAP-RECONNECTION`, `-RENDERING-PERFORMANCE`, `-INTEREST-MANAGEMENT`).
   Checked all 3: **`-RECONNECTION` is confirmed DONE** (`tickets/done/live-map-reconnection/`),
   but the roadmap doc's M1 section header still just reads "M1 — Core Reconnection (ships a real,
   working, connected map)" with no completion marker at all — **genuinely stale**, a real finding
   distinct from the M1(RPG) case this ticket was filed for, and in a different tracking mode
   (`epic_id`, not `folder`). The other 2 epics (`-RENDERING-PERFORMANCE`, `-INTEREST-MANAGEMENT`)
   remain accurately scope-only/not-started.
   Also found: the epic's own detailed plan doc, `docs/plans/live_map_reconnection_epic.md`, still
   carries `status: active` frontmatter despite its tracked epic being fully done — same staleness
   class, different file.

Per this ticket's own Out of Scope ("file a lightweight follow-up ticket per stale doc found,
rather than folding arbitrary doc fixes into this tooling ticket"), filing
`TCK-20260826-HOTFIX-LIVE-MAP-RECONNECTION-ROADMAP-STALE` as a separate, small hotfix — not fixed
here.

## Design: tracking_doc declaration mechanism
Scope explicitly limits this to `folder` mode (`epic_id` mode already has a natural home — the
epic ticket itself — per this ticket's own Out of Scope). Chosen mechanism: an optional
`tracking_doc: <path>` line inside `SEQUENCE.md` itself (plain text, not YAML frontmatter — matches
`SEQUENCE.md`'s existing plain-markdown style, no new file needed, no new Discover read step since
`SEQUENCE.md` is already read there).

Checked compatibility with the existing `tools/agent-monitoring/epic_staleness_check.py`, which
already scans `SEQUENCE.md` via `CHILD_ID_PATTERN = re.compile(r"TCK-\d{8}-[A-Z0-9-]+")` — a
`tracking_doc:` line contains no such pattern, so it cannot be misparsed as a child ticket ID.
Confirmed safe to add without touching that script.

## Design: bounded status-block mechanism
Rejected free-form prose rewriting (ticket's own Scope explicitly excludes it) and rejected
auto-inserting a new block at a guessed location when markers are absent (fragile heading-matching
heuristics, risk of inserting content somewhere a doc author didn't want it). Chosen design:
require two literal HTML-comment markers, `<!-- IMPLEMENT-EPIC-STATUS:BEGIN -->` /
`<!-- IMPLEMENT-EPIC-STATUS:END -->`, placed manually once by whoever authors the tracking doc,
wherever they want the block to render. The mechanism only ever replaces content strictly between
an existing pair of markers — never guesses placement. If `tracking_doc:` is declared but the
markers are absent, this is reported as a warning (not a silent no-op), so the gap is visible
rather than invisible.

Implemented as a real, testable Python helper (`tools/gate_checks/epic_tracking_doc_static.py`),
following this repo's own established pattern for logic backing agent workflows
(`parity_updater_static.py`, `mechanics_auditor_static.py`, `done_checker_static.py`) rather than
leaving the logic as opaque agent-prompt English with no test coverage.

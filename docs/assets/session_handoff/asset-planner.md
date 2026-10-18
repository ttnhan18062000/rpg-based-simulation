---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-18
tags: [architecture, documentation]
---

# Handover — asset-planner

> Snapshot of the gitignored `.claude/handover/asset-planner.md` taken on 2026-10-18 while the visual-asset-docs-sync batch was in flight (the planner's live handover is authoritative; its own `Updated:` line below says how current it is); on a new machine copy it to `.claude/handover/asset-planner.md`. Refreshed in `TCK-20261018-VISUAL-ASSETS-HANDOFF-SNAPSHOTS`. Paths of the form `/data/...` or `rpg-asset-planner` name the machine that wrote it; the repo-relative paths work anywhere.

Role: asset-planner · Domain/worktree: asset / this machine's worktree `rpg-asset-planner` (clean, detached at 13e5d97ef, the batch branch tip; a path on the machine that wrote this note)
Branch / PR: visual-asset-docs-sync (local, 13e5d97ef off origin/main 013a9f275), no PR yet · previous batch #608 MERGED as d7831efab
Updated: 2026-10-18 (owner "continue asset" via lead; batch visual-asset-docs-sync filed and dispatched to asset-implementer on the user's "Dispatch now").

## Open
- IN FLIGHT: batch visual-asset-docs-sync (docs only, 2 hotfix tickets, agent-working/tickets/todos/visual-asset-docs-sync/SEQUENCE.md):
  TCK-20261018-VISUAL-ASSETS-GAP-REPORT-CURRENT (committed 178de1ea4, reviewed and approved by asset-planner), then
  TCK-20261018-VISUAL-ASSETS-HANDOFF-SNAPSHOTS (in progress). Dispatched to the asset-implementer seat 2026-10-18.
  The implementer asks the planner before `make knowledge-index-update` (the lead sequences heavy work this week). Push/PR only on the owner's yes via lead.
- OWNER DECISIONS 2026-10-18 (via lead, neutral options): G6 "Keep scaled icons" (no 16x16 building glyph); G4 "Leave as is" (no grassland
  offset redraw). Recorded in docs/assets/sample_map/gap_report.md (2026-10-18 update, "Open now" list).
- NEW BACKLOG: TCK-20261018-VISUAL-ASSETS-ASEPRITE-JOB-TIMEOUT-UNDER-LOAD (todos/, P3, standard): the 30 s JOB_TIMEOUT_S vs a 0.258 s
  slowest job means a hang, not load; guarded drawing/** so proof refresh + lead heavy-run OK. Waits for a quieter week (lead).
- DONE: batch visual-asset-main-green (#608, d7831efab): TCK-20261015-VISUAL-ASSETS-ICON-SCENE-RC11-KEYS (#598 closed) and
  TCK-20261015-VISUAL-ASSETS-SANDBOX-BWRAP-USERNS-ERROR (#555 closed; the host fix on u24desktop is still the owner's, with sudo).
  The Frontend path-filter gap is #607 (testing-planner owns it, not us). Proof record refreshed by a real run (215/0/0).
- LESSON: a guarded-file change (sandbox.py, visual_assets conftest/strict_aseprite) needs the Aseprite local proof refresh, and a new
  numeric bound needs a budgets.md row. Put both in the ticket's AC and get lead's heavy-run OK up front.
- GATED: entity markers, agent-working/tickets/todos/visual-asset-entity-markers/ (TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS, OPEN).
  Waits on rpg #523 merging AND an owner choice: key on role id (`kind`, rpg-planner, emitted today) vs species+size (rpg-designer,
  not emitted yet). #548 answered with those two views.
- Item icons: NO batch (owner 2026-10-15). Items stay on six icon.item.<family> keys. #543 CLOSED with a correction.
- Backlog (not started): TCK-20261011-VISUAL-ASSETS-BUILD-EXPORTS-FRAME-ONE-ONLY (P3, trigger = client animation activation, parked);
  registry comment nit ("mapped to existing art by these aliases (registry-only)"), carry into a batch that edits the registry anyway;
  16x16 building map glyph: owner said no on 2026-10-18 (G6).
- Pending user decisions: push/PR of visual-asset-docs-sync when ready. Awaiting: the asset-implementer seat (batch).
- Resource rule (lead): heavy suites one at a time across both asset seats, under systemd-run --user --scope -q -p MemoryMax=3G.
- Issues: #523 OPEN (rpg's), #548 OPEN (rpg's, entity keys; answered with two views), #607 OPEN (testing's, the filter fix); #519 CLOSED
  (answered 2026-10-11); #555, #598, #543, #559 closed.

## State after batch A (for reference)
- rc-0011 = 105 entries (rc-0010's 87 byte-identical + 18 object markers), no alias entries; set-adoption sa-6690e2619d4abb3e (18).
  Its records hold literal template placeholders; owner erratum in docs/assets/store_contract.md ("Provenance errata"); store now
  refuses placeholders (check_not_placeholder in visual_assets/store/identities.py, code placeholder_value).
- Sample map: 0 gaps on all three worlds; CITY = plate only; alias view == exact view. Gap report G6/G8/G9 closed, G10 moved.
- Known flaky: tests/visual_assets/drawing/integration/test_ops.py Aseprite 30 s timeout under host load (passes alone).

## Pointers
- agent-working/tickets/done/visual-asset-map-markers/ (SEQUENCE.md, epic) + done child tickets TCK-20261013-VISUAL-ASSETS-*, TCK-20261014-*
- agent-working/tickets/todos/visual-asset-entity-markers/
- docs/assets/{store_contract.md,budgets.md,sample_map/gap_report.md,icon_style_guide.md,session_handoff/}

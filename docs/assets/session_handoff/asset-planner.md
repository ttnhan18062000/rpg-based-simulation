---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-15
tags: [architecture, documentation]
---

# Handover — asset-planner

> Snapshot of the gitignored `.claude/handover/asset-planner.md` taken on 2026-10-15 at the review of the map-markers batch (the planner's live handover is authoritative; its own `Updated:` line below says how current it is); on a new machine copy it to `.claude/handover/asset-planner.md`. Refreshed in `TCK-20261013-VISUAL-ASSETS-MARKERS-RC-AND-CLOSE`.

Role: asset-planner · Domain/worktree: asset / /data/vboxuser/Work/rpg-asset-planner (clean, on local branch visual-asset-map-markers @ ecedda71d, upstream unset)
Branch / PR: visual-asset-map-markers (planning 16fe7012c + child 5 filing ecedda71d, unpushed; batch branch visual-asset-map-markers-impl) · PR none. Previous batch #545 merged as 06aa3a20c.
Updated: 2026-10-15 (batch A head 39ee26895 REVIEWED + APPROVED with 3 asks; waiting on implementer's fix-up head, then owner push/PR question). Full prior note: .claude/handover/archive/asset-planner-2026-10-13-full.md

## Open
- ADOPTED 2026-10-14: sa-6690e2619d4abb3e (18, CLEARED, verify 0). Child 2 CLOSED at 8ff9c2603 (impl branch). PROVENANCE DEFECT: all 18 records hold my
  template placeholders (<your name>/<your role>/<your own licence evidence reference>). OWNER: "Keep, add an owner erratum" (nhan / owner;
  licence "Own pixels, Aseprite + API" = "Own pixels drawn in this repo with the Aseprite MCP tools and the visual_assets drawing API they wrap,
  from palette icons-v1; no outside art copied or traced, no AI generator (ADR D20, theme D21)"); store guard "Yes, queue a store fix".
  Child 5 DONE at 3b4a2ad5d (after merge 250a8614d of my ecedda71d), APPROVED: guard placeholder_value; erratum in store_contract.md.
  #548 ANSWERED (rpg-planner: key on the role id `kind` today; rpg-designer: present `species` + `size`, not emitted yet). #523 still OPEN.
  OWNER 2026-10-14: "Objects now, entities later" (child 3 moves to todos/visual-asset-entity-markers/, OPEN, in child 4's closure);
  "Assemble rc-0011 (105)". Child 4 DONE at 20ae9f54f (+ main merge db4c63269, fixes b0af3c90d, proof 39ee26895). REVIEWED 2026-10-15: rc-0011 = 87 byte-identical
  + 18 (rc-0010.json unchanged vs 06aa3a20c), 0 gaps in all 3 worlds, CITY plate_only, alias crops dropped (alias view == exact), gap report
  G6/G8/G9 closed, G10 moved; batch folder in done/, entity-markers folder OPEN. Guard moved to identities.py (layer boundary) ACCEPTED.
  ASKS sent: (1) child 5 done ticket note on the move, (2) store_list ceiling per item not a fixed 30,000, (3) one full tests/visual_assets
  run under the 3G cap. My planner snapshot refreshed on my branch for the implementer to merge. NEXT: confirm the fix-up head -> owner
  push/PR question -> CI -> lead review -> --admin merge.
- #559 CLOSED: frame-one-only ticket QUEUED in the backlog (P3, trigger = client animation). #555 ACKED (open as tracker): affects u24desktop only;
  this host works via the packaged /etc/apparmor.d/bwrap-userns-restrict; QUEUED: sandbox.py clear error + test skip in the next sandbox-touching batch.
- Batch A in flight (see Next). Lead ACKED the plan 2026-10-13; keep 16fe7012c local, it goes in the batch PR.
- RESOURCE RULE (lead = machine-resource owner since 2026-10-13): while perf T08 runs, heavy suites (tests/tools, full visual_assets)
  run under `systemd-run --user --scope -p MemoryMax=3G`, never two at once across asset-planner + asset-implementer. Small targeted files OK.
- Terrain variants MERGED #545 -> 06aa3a20c.
- Pending user decisions: delete leftover LOCAL branches (visual-asset-terrain-variants, visual-asset-slices,
  visual-asset-real-art-proof, visual-asset-sample-map); confirm my worktree.
- Code health "import contracts" advisory warning shows on main too; lead sent it to codebase. Not ours.
- #519 CLOSED. #543 OPEN until the item-icon ticket (grass_cover, raw_meat) is filed; decision is posted on the issue.

## Next, in order
Batch A = TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS (agent-working/tickets/todos/visual-asset-map-markers/, SEQUENCE.md has the decisions).
1. DONE: child 1 at d2ce35b8d on the implementer's branch visual-asset-map-markers-impl (= the batch branch, based on my 16fe7012c). APPROVED by me.
   Option (b) withdrawn (pickDetail picks per cell). ~543 B per key, 95 keys = 47,231 B (10.3 %), 0.10 s. Fix for child 3: 11 entity kinds incl. wild_creature.
   OWNER ANSWERS 2026-10-13: nodes "13 keys, one per kind"; buildings "24x24 panel icons only" (16x16 building map glyph = later choice);
   aliases shop->store, camp->enemy_camp, ruin->ruins, dungeon->dungeon_entrance, lair->boss_arena; CITY "Location plate alone".
2. Child 2 at bd0b1db77 (impl branch): 18 keys + 5 aliases (83 keys, 8 aliases, 42,024 B), 18 specs + `node` family, silhouette sheet tool.
   RED SET (expected, re-point in child 4): 14 failed + 14 errors = registry_mismatch exports of rc-0010 (test_atlas x5, release_byte_repro x7,
   sample_map_render x4) + registry/icon count pins (x10) + icon spec pins (x2). Specs/keys APPROVED.
   Silhouette sheet sent back once (bd0b1db77: layout + misreads), revised at 39e54745f.
   OWNER 2026-10-13: silhouettes "Approve all as shown" (saw the weak list: nest, wood_node, spirit_wisp, iron_vein, moon_resin_tree);
   town hall "A: charter scroll"; mine entrance "A: pickaxe".
   DRAWN at 390b5eba5: draft set object-markers-v1 (18, intakes PASS). Blind check round 4: 16/18 right; berry_thicket ("bug") and spirit_wisp
   ("gem") misread -> OWNER 2026-10-14: keep both silhouettes. My ruling: 17 icons applied via drawing.api (same Lua pin, MCP for lint/export) accepted.
   Sheet 01 fixed at a45983e42. OWNER 2026-10-14: "Adopt, give me the command" -> command given; owner runs adopt-set object-markers-v1 in
   ~/Work/rpg-aseprite-mcp. Implementer told to HOLD. NEXT: confirm adoption (store list), then child 2 close + child 4 (rc-0011 question).
3. Child 3 ENTITY-MARKER-DRAFTS GATED: #523 merged + rpg-planner answers #548 (filed 2026-10-13). If still shut when child 2 is adopted -> owner question
   "objects only, entities in their own batch".
4. Child 4 RC-AND-CLOSE: rc-0011 (owner), the renderer draws markers, gap report, closure. Then push/PR owner question, then lead review, then --admin merge.
5. After A: item-icon ticket (grass_cover, raw_meat), then close #543.

## Not started
- Registry comment nit ("mapped to existing art by these aliases (registry-only)"): carry to a later batch that edits the registry anyway.
- Backlog: TCK-20261011-VISUAL-ASSETS-BUILD-EXPORTS-FRAME-ONE-ONLY.

## Decisions recorded this batch (owner, 2026-10-12/13)
- Detail values: grassland tufts/flowers/clover/bare; mountain crag/scree; cave stalagmite/rubble; ruins moss/fallen;
  swamp reeds/puddle; shallow_water ripple/pebbles (default base). adopt-set sa-34445853fa87089b (14). "Assemble rc-0010".
- "Accept detail: base"; "Registry-only aliases" terrain.plain->grassland, ruin->ruins, river->shallow_water (Known gap in
  store_contract: no runtime consumer; #523 is rpg's colour-by-name fix).
- My closed-gate ruling (lead-accepted, narrowed): closed fixtures exact; a fresh export may only ADD a details row for the 6 keys in
  AXES_DECLARED_AFTER_THE_GATES (forest excluded) equal to the registry axis; zero fixture bytes; test_closed_details_rule.py.

## Pointers
- agent-working/tickets/done/visual-asset-terrain-variants/ (SEQUENCE.md + 5 tickets)
- docs/assets/{budgets.md,store_contract.md,sample_map/}; issues #519, #523, #543
- Env: my venv lacks complexipy (one tests/codebase env failure; CI covers). MCP restart confirmed (pin_check_scratch2).

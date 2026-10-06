---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-06
tags: [architecture, documentation]
---

# Handover — asset-planner

> Snapshot of the gitignored `.claude/handover/asset-planner.md` on 2026-10-06 at 91949ef96 (the icon batch's last code commit; the closing docs commit follows it); on a new machine copy it to `.claude/handover/asset-planner.md`.

Updated: 2026-10-06 (icon key-set batch filed and handed off)

## Open
- 2026-10-06 (later): user lifted the pause for ICONS only and asked for deep research first. Research done
  (scratchpad of session cdf02383: research_games.md, research_icon_craft.md, research_packs_palettes.md,
  icon_research_synthesis.md; copy them into the batch as docs, scratchpad is not durable).
  User decisions (blocking question, 2026-10-06): style B + tier badges (16px map glyph on per-category plate,
  24px panel icons, 8px shape-escalating tier badge, status frames with up/down chevrons); palette = terrain-v1
  base + ramps + small accent set, sheet-level icon colour-vision rule; outside art REFERENCE ONLY (recorded
  TASL), no AI generators; map zoom snaps to whole-number scales (frontend ticket). Batch FILED: branch visual-asset-icon-key-set in rpg-aseprite-mcp, planning commit 657c552e3 (local,
  not pushed); epic TCK-20261006-EPIC-VISUAL-ASSET-ICON-KEY-SET + 6 children in todos/visual-asset-icon-key-set/;
  research committed in child 1's staging folder. Handed to asset-implementer 2026-10-06. Awaiting: review requests.
  Child 1 approved (123f7b20d). Rulings: plate+glyph separate 16x16 keys, glyph live 12x12; ticket's tier ladder kept.
  Child 2: registry_hash move breaks rc-0005 fixture guards (my ticket was wrong); user chose (a) assemble rc-0006
  (blocking question 2026-10-06). Child 2 APPROVED (6a855754b): rc-0006 = rc-0005's 34 entries on the new registry;
  pilot fixture guard = forest slots of fresh rc-0006 export + equality with stored rc-0004 (planner ruling). Child 3 APPROVED
  (amended to e7bfcf631, notes only): user answers I1 3/6 px (E,D may share silhouette), I2 L* 6 (interior mean), I3 L* 12; palette icons-v1 52
  colours. Planner accepted LIGHT plate rim #9ea4b6 (dark rim can't clear dark terrain) -> name it to the user at the gate.
  Confirmed: the user saw interior-mean numbers. Child 4 APPROVED as f8751f0d8, final d11cdde78 (monitoring shard only): user chose (blocking
  question 2026-10-06) a FLAT-COLOUR OVERVIEW level at 0.5x (snapping alone removed it at DPR 1); asked implementer to add
  one overview level + pure isOverviewZoom() for the wiring batch's art path (done). Child 5 in progress: 14 drafts kept as icons-key-v1;
  rule measured I1 min 4 px, I2 8.74/14.2, I3 18.0. Deviations to NAME AT THE GATE: light plate rim; S/SS/SSS are
  diamonds with 0/1/2 pip cut-outs (true stars don't fit 8x8 with outline); 0.5x overview = flat colours. Icon fixture
  guard ignores registry_hash only (planner ruling). Child 5 APPROVED as 5d2792464 (debuff redrawn as
  a down arrow, I2 frames 7.66; draft set hash sha256:29854e8b...). User ADOPTED icons-key-v1 (sa-b4bb738d6b5526f0,
  2026-10-06T15:21:47Z, own terminal; adopt-set refuses without a TTY so agents can't run it). Child 6 handed off.
  Preview server tip: Vite listens on [::1] only -> http://[::1]:5173/rehearsal-icons.html. For the wiring batch: frontend fallback.ts has no `icon` family glyph (gets "?").
- Nothing in flight. Last: PR #361 (terrain set review, 7 tickets) squash-merged as 47931fa54 on 2026-10-06 (--admin, the user's
  own answer). Branch visual-asset-terrain-set-review finished; rpg-aseprite-mcp detached at origin/main. Awaiting: nothing.
- W05 stays INCONCLUSIVE because the gate is "no critical distinction is hue-only" (the hover-text route is unexercised, AM-M6),
  not the colour-vision rule (which passes).
- The tracked snapshots in docs/assets/session_handoff/ are the 2026-10-06 copy (#361); refresh them in the next asset batch PR.
- ASSET WORK PAUSED again (user 2026-10-04 pause, lifted for this batch only). Parked, no tickets: icons and
  other kinds (entities, buildings, items, UI; reuse draft sets + adopt-set), charter signing, AM-M6.
- Ignore (user, 2026-10-04): the agent-monitoring retro hook and the TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN staleness nag.
- FYI codebase-planner (2026-10-05): advisory import contracts c14/c15 (visual_assets <-> src, no imports either way) in
  codebase/structure/importlinter.toml, may turn blocking after a 2-week soak; exceptions are our call (ask for ignore_imports).
  Code-health gates BLOCKING on main since 2026-10-05 14:47Z: `Code health` + `Type check` on src/ only. If a batch ever edits
  src/, run `make code-health` + `make typecheck-py` first.

## What this batch did (user decisions by blocking question, 2026-10-05/06)
- Set colour-vision rule `AM5-S` (all 253 pairs x 4 visions; S1 `dE_tile >= dE_fill - 2.0` or `>= 10`; S2 texture >= 2.0),
  committed before any art. Baseline terrain-v1 FAIL (30/1012) from mean-to-fill drift; no subset redraw passes, so (planner
  decision) all 22 drafts re-tinted onto their fills: PASS "by construction" = "no worse than the hue-only flat fills";
  closest pair-vision 0.857 dE (jungle/lava protan; fills 0.784).
- Borders: user found hard terrain edges weird; chose Wesnoth-style layered fringes. Contract v1 (ADR D19): 15 ranked terrains
  (water lowest ... forest highest), 8 crisp built terrains (no fringe either way), 4 px cap, C6 added to W03-SET; one shared
  mask family `border.edge|outer_corner|inner_corner` x v1-v3, client compositor `terrainBorders.ts` + `borderRender.ts`.
- User adopted terrain-v1 (22 tiles + 9 masks) by adopt-set: sa-f4c541f25f112221, 2026-10-05T18:17:03Z; guards re-pinned by
  equality (tests/visual_assets/adopted_facts.py). Releases: rc-0004 (registry hash move, forest only), rc-0005 (34 entries,
  user-approved); fixture `__fixtures__/terrainset/` (pilot fixture untouched).
- M5 rerun on rc-0005: W03-SET PASS (user: yes for all 23 on C1-C6, one reviewer); W07 PASS (4 clients); fallback and rollback
  drill recorded; overall M5 still INCONCLUSIVE (no M1/M2/M4 PASS record). Known fragility, not fixed:
  `pilot_colour_vision.tile_pixels()` takes the first PNG of the pilot export.

## State worth knowing
- Merged epics: foundation (#286, #299), hardening + M5 rehearsal (#309), pilot readiness (#317), detail variants + draft
  sets (#327), AM-M1 docs (#330), AM-M1 unblock (#334), handoff snapshots (#337).
- AM-M0 INCONCLUSIVE (user kept it), AM-M1 BLOCKED only on M0 (register 55 MET / 7 GAP / 6 N/A; owner decisions ADR D13-D18),
  AM-M2 BLOCKED, AM-M6 NO-GO, charter unsigned. Gates are never reworded to pass.
- Approved docs: `fallback_safety.md` (W06; borders are decorative), `m2_evidence_charter.md` (W11 rerun rule).
- Decided: Profile A (D8), no signing (D9), Aseprite local only (batch mode, no app window needed), detail axis (D11), draft
  sets (D12), borders (D19); retention 30 days; rollback/recall owner "nhan (owner)".

## Pointers
- Criteria + results: `docs/assets/pilot_terrain_m5_criteria.md` (AM5-S, AM5-B, AM5-W03-SET), `docs/assets/pilot_terrain_m5_results.md`
- Contract: `docs/assets/store_contract.md`; ADR: `docs/architecture/visual_asset_foundation_adr.md`; register: `docs/assets/m1_contract_register.md`
- Charter draft: `docs/assets/pilot_charter_am6.md`; M5: `docs/assets/surface_rehearsal_result.md`
- Done batches: `agent-working/tickets/done/visual-asset-m1-unblock/`, `.../visual-asset-terrain-set-review/`
- Delivery rules: `docs/guides/delivery_process.md`

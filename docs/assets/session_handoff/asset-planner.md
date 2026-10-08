---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-08
tags: [architecture, documentation]
---

# Handover — asset-planner

> Snapshot of the gitignored `.claude/handover/asset-planner.md` on 2026-10-08 after the icon set v2 adoption was recorded; on a new machine copy it to `.claude/handover/asset-planner.md`.

Updated: 2026-10-08 (icon set v2 complete locally, PR next)

## Open
- 2026-10-08: batch visual-asset-icon-set-v2 COMPLETE locally (children 1-5 + 4b/4c, last d5d38b908), not pushed.
  Implementer next: merge origin/main, tests, pr_render (theme + hand-written Review notes), push/PR blocking question;
  merge = user's --admin. Planner reviews the PR when opened.
- User decisions 2026-10-07/08: DRAW ONLY, NO WIRING (app use gated by AM-M6 NO-GO, charter unsigned, scope = one forest
  tile); 6 item families (one per first category; catalog has 6, my '~15' was a raw-grep error); 3 rarity badges
  (legendary none); I1 24x24 = 8 px; subject groups I1 only; rc-0007 (= rc-0006's 34 slots); 'Fix the process now'
  after the owner found the sword wrong; adopted icons-v2 (sa-c9082d078b954f6b, 2026-10-08T00:40:15Z, 22 icons).
- Recognisability process (style guide step list): per-icon spec (visual_assets/icons/icon_specs.yaml), reference study,
  owner-approved silhouette sheet, draw, sheet rule + blind recognition check (evidence, noisy) + whole-sheet look-alike
  report + MEASURED spec compliance table (icon_compliance.py), owner gate. Naming alone missed the sword.
- Owner findings carried into the PR notes: ruins (brick wall, 4th idea) still free-text 'building blocks'; common bead vs
  tier D/E look-alike at common scale; tool = wrench, spirit_lantern unmatched; adopted buff frame reads 'green gem';
  blade motifs repeat across families. Adopted totals: 70 sources (34 terrain-era + 14 key + 22 v2) and 77 revisions (the owner adopted seven r0002 revisions from `icons-owner-fixes-v1` on 2026-10-08); no rc covers icons.
- Next icon work (not filed; ask the user): activation path (charter/AM-M6+ is the owner's), rc with icon slots, `icon`
  fallback glyph, Live Map art path must use isOverviewZoom(). Follow-up idea: decouple fixture guards from current-rc pin.
- Earlier: PR #388 (icon key set) merged as bc4f7553c on 2026-10-06; PR #361 (terrain set) as 47931fa54.
- Known: E/D badges weak on a dark panel; 16 stray intakes in main checkout quarantine (30-day retention);
  Vite dev server listens on [::1] only (use http://[::1]:5173/...); adopt-set refuses without a TTY (owner runs it).
- Icon decisions: ADR D20, docs/assets/icon_style_guide.md, icon_criteria.md (I1 3/6, I2 6, I3 12), icon_key_set_review.md.
- W05 stays INCONCLUSIVE because the gate is "no critical distinction is hue-only" (the hover-text route is unexercised, AM-M6),
  not the colour-vision rule (which passes).
- Tracked snapshots in docs/assets/session_handoff/: the implementer refreshes them in each batch PR from this file.
- Asset pause (user 2026-10-04) is LIFTED FOR ICONS ONLY (2026-10-06). Still parked, no tickets: other kinds
  (entities, buildings as map sprites, UI beyond icons), charter signing, AM-M6.
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

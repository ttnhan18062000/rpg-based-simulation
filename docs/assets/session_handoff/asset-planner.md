---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-08
tags: [architecture, documentation]
---

# Handover — asset-planner

> Snapshot of the gitignored `.claude/handover/asset-planner.md` on 2026-10-08 after PR #418 merged (4a2141df9); on a new machine copy it to `.claude/handover/asset-planner.md`.

Updated: 2026-10-08 (PR #418 merged; idle)

## Open
- Nothing in flight. Last: PR #418 (icon set v2 + owner fixes, 12 tickets) squash-merged as 4a2141df9 on
  2026-10-08T15:14:54Z (--admin, user's answer; head 91a9fcd9c after a main merge; heavy lanes re-sync-skipped, same
  patch as green 328af73db). rpg-aseprite-mcp detached at origin/main. Branch finished, never pushed again.
- Adopted icons: 36 keys (14 key set + 22 v2), 7 of them at r0002 (hero house cottage, inn tankard, rogue cowl, tool
  hammer+tongs, common silver bead, buff up-arrow, debuff spiked ring). Ruins brick wall + camp crossed swords kept.
  No rc covers icon slots (rc-0007 = 34 terrain-era). Nothing wired into the app (AM-M6 gate, owner's choice).
- Decisions: D20 (style), D21 (theme: medieval fantasy + magic, nothing modern), icon_criteria (I1 3/6/8, I2 6, I3 12),
  6 item families, 3 rarity badges. Process (style guide): spec (+theme fields) -> reference study -> owner-approved
  silhouettes (spec numbers agreed there) -> draw -> sheet rule + measured compliance + blind/era check + look-alikes
  -> review folder ~/Work/asset-review/<set>/ (python -m visual_assets.review.review_sheets --set <id>) -> owner gate.
  Revisions of adopted icons: per-slot `review` + `adopt --parent rNNNN` (adopt-set cannot revise).
- 2026-10-08: owner asked for the activation path; gate map done (7-step chain M0->M1->M2->M4->M5->M6 forest pilot->M7
  icons family). Owner chose "Record the map, park it" (resume when RPG core lands). Batch visual-asset-activation-roadmap
  (1 docs ticket, planning commit on that branch) handed to implementer; also refreshes this snapshot in the repo.
  Known gap: 36 adopted icons lack a declared fallback-safety class (fallback_safety rules 1-3; W02.7 field).
- Next (not filed; ask the user): rc with icon slots, `icon` fallback
  glyph, isOverviewZoom() in the Live Map art path; optional store ticket: set-level revisions; decouple fixture guards
  from the current-rc pin. Refresh docs/assets/session_handoff/asset-planner.md in the next asset PR (stale in #418).
- Owner-accepted known weak reads: tool reads 'hammer and wrench', debuff ring reads 'gear', ruins 'building blocks'.
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

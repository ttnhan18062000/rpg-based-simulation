---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-10
tags: [architecture, documentation]
---

# Handover — asset-planner

> Snapshot of the gitignored `.claude/handover/asset-planner.md` taken on 2026-10-10 at the close of the store-tooling batch (its own `Updated:` line below says how current it is); on a new machine copy it to `.claude/handover/asset-planner.md`. Refreshed in `TCK-20261010-VISUAL-ASSETS-STORE-TOOLING-DOCS-AND-CLOSE`.
Updated: 2026-10-10 (store-tooling: owner gates answered, c3-c7+c9 reviewed)

## Open
- 2026-10-10 IN FLIGHT: batch visual-asset-store-tooling FILED + DISPATCHED to asset-implementer (msg). Epic
  TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING + 9 children (todos/visual-asset-store-tooling/SEQUENCE.md), branch
  visual-asset-store-tooling off 312fbd78c, planning commit 4c4b0b8d5, upstream unset (implementer checks it out in
  rpg-aseprite-mcp). Owner answers 2026-10-10: store tooling, all 4 groups; reverse D18 -> D24 (lock refuses 2nd writer,
  append-only gc deletion log, kill tests); keep D10 + committed local proof record + CI staleness test (no self-hosted
  runner); decoder pure Python, bounds unchanged. MY GATES: child1 design (owner approves D24 text), child4 guarded paths
  + record shape (owner approves D10 addendum), child7 field placement (default per-artifact; registry 90% full),
  child8 clear non-asset frontend files with rpg-planner (no rpg-planner session was live). Review each commit.
  Child 1 design APPROVED (plan.md in implementer staging); OWNER APPROVED D24 text verbatim (lock on catalog/.store.lock,
  refuse 2nd writer, local gitignored hash-chained deletion log, manual orphans) + MAX_DELETION_LOG_BYTES 1 MiB (full ->
  archive + re-anchor chain on old last hash). My adds: draft export/export-runtime take lock, non-Linux refuse at acquire,
  gc never deletes lock/log, drop unverified AM1-W10.4 cite. Child 2 may start in parallel / land first.
  Child 1 COMMITTED 43ef881db -> APPROVED (245 tests pass in project venv /data/vboxuser/Work/rpg-based-simulation/.venv;
  system python3 lacks mcp). Nits sent: ADR status-line comma; narrow .deletions prefix in test_no_ignored_files.
  Child 2 COMMITTED 11ace7957 -> APPROVED (1311 store tests pass; ~2x faster, bounds unchanged, 2048 px still 2.53 s >
  2 s line so no bound raise; memo lru 4 frozen results). Nit sent: state ~32 MiB resident memo worst case in budgets.md.
  Next: child 3, then child 4 (my design gate).
  2026-10-10 (session 3, after restart): implementer had committed c3-c9 meanwhile. OWNER ANSWERS (my blocking Qs):
  D10 addendum "Approve as written"; MAX_ATLAS_DIM 1024 approved; MAX_ANIMATION_FRAMES/TAGS 16/16 approved; child 8's two
  new frontend files (vite.rehearsal-bundle.config.ts, playwright.bundle.config.ts) "Clear both" (rpg-planner not live).
  lead-planner: YES to Makefile `visual-assets-bundle-capture` w/ 4 conditions (aseprite-local shape, adjacent, NO new dep
  -> ask lead first, output reports/visual_assets/). All relayed. REVIEWED: c3 835db787e, c4 9a4083372+2e608382e (broad
  guarded set, full-target-only record, dirty-tree refusal), c6 17d43c792, c7 5c4d34ff9+43469ba16 (sec NEEDS_CHANGES fixed:
  hostile tag name -> raise; choices a-e confirmed), c9 dedb16d9b (research move) APPROVED. c5 de963439e FIX asked:
  runtime_export keeps all decoded images even without --atlas (~4 GiB worst case) -> only if atlases + fit check first.
  Next: c5 fix, c8 code, proof-record re-run commit (once, after last store edit), c9 close, PR question (implementer).
  7dbe534b6 (owner decisions recorded; D10 addendum verbatim in ADR, checked) + f2287f94e (c5 fix: no retained images,
  fit check before decode; MAX_FINDING_DETAIL dropped for budgets_parity) APPROVED. c8 scope OK: pixel verdicts only for
  3 rehearsal.html cells, loading-only for other pages (say so per page, gate stays INCONCLUSIVE); TS pixels-v1 hash
  proven equal to Python on known vectors; DPR pinned 1.
  c8 507bb4979+dd3e46ac0 APPROVED (footprint = 2 cleared frontend configs + Makefile target only; real run: rehearsal
  3 cells pixel-verified, 4 pages loading-only, planted 1-px change caught; deviations a bundle.check.ts, b
  assetsInlineLimit 0 [doc must say real build may inline, untested], c dirty-tree refusal: confirmed). Next: proof-record
  re-run commit, c9 closure (batch_hand_close), main merge + final pass, then implementer asks owner push/PR.
- 2026-10-10: PR #480 MERGED cfad712cf at 2026-10-10T02:54:01Z (owner --admin pinned to c3e01d71d). Branch
  visual-asset-icon-release-candidate finished, never pushed again. rc-0008 (70 entries: 34 terrain + 36 icons) is the
  current rc. Main checkout NOT fast-forwarded (dirty with other sessions' files) - leave it.
  Open for owner: own asset-planner worktree (exists now: ~/Work/rpg-asset-planner, confirm); everything else parked
  (activation incl. Live Map icon glyph until RPG core lands). Superseded detail below is history.
- IN FLIGHT (2026-10-09): owner said "start order as your recommendation" (A bookkeeping -> B icon rc -> C glyph).
  A folded into B's first commit (EPIC_SCOPED and DONE both legal; cosmetic). C DROPPED for now: store side done in #471,
  only the client Live Map glyph remains = parked with activation. B filed: batch visual-asset-icon-release-candidate,
  ticket TCK-20261009-VISUAL-ASSETS-ICON-RELEASE-CANDIDATE (standard), branch of the same name in rpg-aseprite-mcp from
  0c3a5654b, planning commit bc088f6ab, upstream unset. Handed to asset-implementer by message. Build 36 icons (agent
  may build/release; only adopt/adopt-set/revoke need a TTY), rc-0008 = rc-0007's 34 + 36 icons = 70, ONLY after the
  owner's blocking answer (rc-0005/0007 precedent). Next for me: review each commit the implementer reports.
  PROGRESS: f7d3ffb98 (bookkeeping) + 03fba7da3 (36 icons built, terrain byte-identical) APPROVED; owner answered
  "Assemble rc-0008" (70 entries, uncommitted until commit 3). FINDING: building icons grew fresh draft-preview exports of
  the 3 CLOSED icon draft sets (48/56/43 -> 70) -> 3 py guards + 15 IconHarness vitest fail if regenerated. RULING (c):
  keep draftexport + frontend as-is; re-anchor guards for gate-closed sets (pinned set->adoption ids): drafts exact,
  refs byte-equal to the named catalog artifact, no stray entries, new post-gate refs not required; open sets keep full
  equality; 4 mutation proofs. Owner informed; may overrule.
  Commit 3 e734ca7c9 (rc-0008 + re-anchored guards) reviewed: approved EXCEPT gap -> closed check accepted a --write
  regeneration (new refs are real artifacts); asked to pin each closed fixture's manifest sha256 + a "--write over a
  copy fails" mutant; nit: narrow `except Exception` in _reference_problems. Fix 2eb885539 APPROVED (pins verified
  against the files; frontend untouched). Waiting on commit 4 (docs + BOTH snapshots), final test pass, then the
  implementer asks the owner push/PR.
  2026-10-10: docs d0ef62c74 + main merge + snapshots 1e916663d APPROVED; tests green except one ENVIRONMENTAL failure
  (test_handover_transit memory-dir slug: two memory dirs -data-... and -home-... after the ~/Work move; agent-working
  domain, raised to owner, no asset ticket). BLOCKED on ticket closure (still in todos, no working_log row/monitoring):
  told implementer to close (hand-orchestrated closure tool + done_checker_static) BEFORE any push.
  Closure e7151e61f APPROVED (done_checker PASS; path_reason "other" kept, use batch_hand_close next time per 25
  precedents). PR #480 open, head 40e2d3051, CI running; implementer asks owner --admin merge after green.
  Lesson for my test plans: include a "## Proof Plan" section (test_plan_proof_fields advisory).
  PR #480 went CONFLICTING after #476/#478: dry merge-tree shows docs/REGISTRY.yaml ONLY (expected GitHub-side);
  implementer told to merge main locally + push.
  2026-10-10 (session 2): implementer merged main twice more (65d89be67 + REGISTRY regen c3e01d71d) + gate-verdict
  records 40e2d3051/1828628a4 (1 jsonl line each) -> REVIEWED OK: PR footprint all asset scope (73 catalog, 11 tests,
  4 docs/assets, bookkeeping). PR #480 MERGEABLE at head c3e01d71d; CI ALL GREEN (2026-10-10), owner
  merges (--admin pinned to head). #476 MERGED: asset domain registered with all my corrections
  (frontend/src/visualAssets, rehearsal-capture, ADR, staging_artifacts in may_write); planner worktree still
  "proposed ~/Work/rpg-asset-planner (owner decides)" -> still open.
- PR 476 (session-role registration, owner's draft): replied for BOTH asset seats 2026-10-09 (issuecomment-6084929712):
  add frontend/src/visualAssets/** + frontend/rehearsal-capture/** (split rpg/asset) + the asset ADR; planner may_write
  needs agent-working/staging_artifacts/**; sessions launch in main checkout, implementer writes in rpg-aseprite-mcp;
  disclosed planner planning commits in the implementer's worktree -> recommended own asset-planner worktree; OWNER
  DECIDES. Until then: no planner writes in that worktree while an implementer batch is in progress. Implementer told.
- Foundation hardening batch (TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING, 8 tickets)
  squash-merged as 0c3a5654b on 2026-10-09T15:53:32Z (PR #471, --admin pinned to head 0302a10f4, owner ran it).
  Branch visual-asset-foundation-hardening finished, never pushed again. Main checkout fast-forwarded to 0c3a5654b.
  Child follow-ups checked 2026-10-09: assert -> raise already done (tests/visual_assets/derived_runtime.py:39);
  registry budget is a standing rule in docs/assets/budgets.md (review MAX_REGISTRY_BYTES BEFORE the next per-key
  field) -> apply it when scoping any schema growth, no ticket. Bookkeeping drift: epics HARDENING and ICON-SET-V2
  in tickets/done/ still say EPIC_SCOPED with an unchecked AC; hardening SEQUENCE.md says "PR awaits" (it merged).
  Still parked: animation fields, visual evidence capture, decoder,
  real-Aseprite CI, atlases, LFS.
- Earlier: PR #418 (icon set v2 + owner fixes, 12 tickets) squash-merged as 4a2141df9 on
  2026-10-08T15:14:54Z (--admin, user's answer; head 91a9fcd9c after a main merge; heavy lanes re-sync-skipped, same
  patch as green 328af73db). rpg-aseprite-mcp detached at origin/main. Branch finished, never pushed again.
- Adopted icons: 36 keys (14 key set + 22 v2), 7 of them at r0002 (hero house cottage, inn tankard, rogue cowl, tool
  hammer+tongs, common silver bead, buff up-arrow, debuff spiked ring). Ruins brick wall + camp crossed swords kept.
  No rc covers icon slots (rc-0007 = 34 terrain-era). Nothing wired into the app (AM-M6 gate, owner's choice).
- Decisions: D20 (style), D21 (theme: medieval fantasy + magic, nothing modern), icon_criteria (I1 3/6/8, I2 6, I3 12),
  6 item families, 3 rarity badges. Process (style guide): spec (+theme fields) -> reference study -> owner-approved
  silhouettes (spec numbers agreed there) -> draw -> sheet rule + measured compliance + blind/era check + look-alikes
  -> review folder ~/Work/asset-review/<set>/ (python -m tests.visual_assets.review_sheets --set <id>) -> owner gate.
  Revisions of adopted icons: per-slot `review` + `adopt --parent rNNNN` (adopt-set cannot revise).
- 2026-10-08: owner asked for the activation path; gate map done (7-step chain M0->M1->M2->M4->M5->M6 forest pilot->M7
  icons family). Owner chose "Record the map, park it" (resume when RPG core lands). Batch visual-asset-activation-roadmap
  (1 docs ticket, planning commit on that branch) handed to implementer; also refreshes this snapshot in the repo.
  Known gap (corrected): icon descriptions state class + fallback in PROSE (35 identifying, 1 decorative); missing is
  the structured W02.7 registry field and a check reading it. Roadmap merged: PR #450, 48c9785c3. ACTIVATION PARKED
  until the RPG core lands (owner).
- 2026-10-08: owner asked what to build next for the foundation; chose ALL of: set-level revisions (+draft drop), M1
  code gaps (W02.7/W03.1/W06.3), fixture-guard decoupling from current rc, worktree-aware MCP. Owner then asked if we
  researched what we lack: NOT systematically -> 2 research agents running (internal gap audit; external pipeline
  practices, report to scratchpad research_asset_pipeline.md). Gap research done (internal 19 gaps; external 15
  practices; copies in the batch's epic staging folder). Owner chose 7 items -> batch visual-asset-foundation-hardening
  FILED and handed off (epic TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING): 1 guard decoupling (planner approves
  design), 2 MCP worktree root, 3 safety/fallback/label fields + verify (owner approves labels), 4 set revisions + draft
  drop (owner approves D22 design first; security review), 5 review tooling in store CLI + tile_pixels, 6 key-usage
  report, 7 docs drift. Parked: animation fields, visual evidence capture, decoder, real-Aseprite CI, atlases, LFS.
  Child 1 design APPROVED (derive manifest from stored rc + artifacts; drift guard vs export_runtime; inventory pins
  untouched; + artifact PNG decodes to recorded pixel_hash). Child 1 APPROVED (d9d2c1555; follow-up: bare assert -> raise).
  Child 2 APPROVED (e0f0c3689): VISUAL_ASSETS_CHECKOUT=<abs worktree> selects the store DATA root (code still from the
  launching checkout); follow-up asked: refuse on STORE_FORMAT version mismatch. Start sessions with
  `VISUAL_ASSETS_CHECKOUT=/home/vboxuser/Work/rpg-aseprite-mcp claude`. Child 3 APPROVED (a98012d87, follow-up ecf075d20): fields safety_class/fallback/label_key/label, loader rules, W06.3 at
  release+export, D23, register 58 MET / 4 GAP, M1 still BLOCKED; owner approved 35 labels. Registry realistic max at 90%
  of MAX_REGISTRY_BYTES -> budget review before next schema growth. Child 4 design APPROVED by planner (draft keep --revises,
  adopt-set NEW/REVISION listing, ALL-or-NONE, draft drop w/o confirmation); added: tighten per-slot adopt --parent to
  keep key/detail (found gate weakness). Owner asked 3 questions by implementer (design+D22, tightening, no drop in
  icons-owner-fixes-v1). Owner approved all 3. Child 4 APPROVED (20445f675): draft keep --revises, adopt-set
  mixed NEW/REVISION ALL-or-NONE, draft drop, adopt --parent keeps slot; security review clean. PAUSED: user told the implementer "temporary
  stop" (2026-10-09) before child 5; resume only on the user's word. Branch local, children 1-4 committed (20445f675).
  Remaining: 5 review tooling in store CLI + tile_pixels + one adopt-set in review README for revision sets; 6 key-usage
  report; 7 docs drift + close; then PR.
  RESUMED 2026-10-09 (user: "Resume tickets 5-7"). Child 5 plan approved: new package visual_assets/review/ (own CLI,
  boundary row), no shims, active docs updated (historical records untouched), TWO commits (pure move + cmp proof, then
  generic evaluate/sets.py + one-adopt-set + tile_pixels). Before PR: merge main, regen REGISTRY, run tests/unit/tools + tests/tools.
  Child 5 committed (4a8c0f6d3 move, 5c43b8fbb generic) BUT b02ebb8b3 (child 2 fix) swept in the 18 renames -> rewritten:
  7a9574fff / 731ff30d5 (18 R) / 628843680; child 5 APPROVED (python -m visual_assets.review evaluate|review-sheets
  --set <id>; byte-for-byte proof). Child 6 APPROVED (4c872d4a2: python -m visual_assets.review key-usage).
  FINDING: .gitignore `agent-working/stored_artifacts/**/*.json` hid visual-asset evidence JSON (blind checks, M5
  captures, ~356 KB) from merged PRs; child 7 commits .json.txt twins + a guard; shared .gitignore untouched. Child 7 APPROVED (e0443bf0e;
  47 twins); main merged; BATCH READY (14 ahead) -> implementer asks the user push/PR, then merge (--admin).
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

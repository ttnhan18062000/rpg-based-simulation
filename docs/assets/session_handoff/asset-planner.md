---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-13
tags: [architecture, documentation]
---

# Handover — asset-planner

> Snapshot of the gitignored `.claude/handover/asset-planner.md` taken on 2026-10-13 at the close of the terrain-variants batch (the planner's live handover is authoritative) (its own `Updated:` line below says how current it is); on a new machine copy it to `.claude/handover/asset-planner.md`. Refreshed in `TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT`.

Updated: 2026-10-12 (terrain-variants batch FILED + DISPATCHED)

## Open
- IN FLIGHT: batch visual-asset-terrain-variants. Epic TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS + REGISTRY-BUDGET-AND-DETAIL-DESIGN
  -> V2-TERRAIN-ALIASES -> TERRAIN-VARIANT-DRAFTS -> TERRAIN-VARIANTS-RC-AND-CLOSE (todos/visual-asset-terrain-variants/SEQUENCE.md).
  Planning commit 9b87a6649 (off origin/main 6ba9083ef, REGISTRY regen, my W42 shard), upstream unset; my worktree detached. Dispatched.
  Owner: next art = terrain variants; #523 answered = V2 names canonical, keys follow V2, aliases reuse art; client colour-by-name is rpg's.
  Lead order: budget review -> aliases -> ~14 variants. Aliases: terrain.plain->grassland, terrain.ruin->ruins, terrain.river->shallow_water
  (no terrain.PLAIN: lowercase pattern identities.py:16; lowercasing name rule). Variants = detail axis values, default `base`.
  Planner split: grassland +4, mountain/cave/ruins/swamp/shallow_water +2, road none (owner decides).
  LEAD ack: cite #523 in the name-rule docs (rpg: no V2 names differing only by case); child 1 showing ANY existing rc-0009 slot
  changing bytes -> STOP -> lead/owner. Send child 1's design note to lead too.
  CHILD 1 STOPS -> OWNER ANSWERED (2026-10-12, direct, neutral): (1) 'Accept detail: base' = 6 rc entries gain detail base, same
  artifact+hash (forest rc-0001->0002 precedent verified); guard pins 67 identical + 6 = rc-0009 entry + detail base. (2) FINDING:
  aliases have no runtime consumer (only key_usage.py) -> owner 'Registry-only aliases'; Known gap in store_contract (cite #523);
  sample map may resolve via Registry.resolve but must say the live client does not. Child 1 design+budgets APPROVED (29,852 B 6.5 %;
  worst 367,838 B 1.01 s). Told lead (alias gap may need #523 note / backlog: lead's call).
  Child 1 e2f3565e4 + child 2 15288b81a APPROVED (my run: exact red 16 = atlas 5 + release_repro 7 + sample_map_render 4, all
  rc-0009 registry_mismatch; child 4 must green them; nit: alias comment wording). Child 3 next: MCP pin check first; refuse -> STOP,
  get launch cmd/cwd for owner restart; detail-value owner question only once drawing works.
  Child 3: MCP PIN CHECK PASSED (restart confirmed, pin_check_scratch2). OWNER detail values: grassland tufts/flowers/clover/bare;
  mountain crag/scree; cave stalagmite/rubble; ruins moss/fallen; swamp reeds/puddle; shallow_water ripple/pebbles. Drawing.
  My art gate before adopt-set question: blind naming check via fresh subagent, fringe sample, grassland 16x16 pick vs base patch.
  Child 3 ART DONE (uncommitted): 14 variants drafts set terrain-variants-v1, intake PASS, 360-406 B; review folder
  ~/Work/asset-review/terrain-variants-v1/; blind 20/20 (pre edge fix; re-run asked). 12 NEW reds: closed-gate fixtures (10) +
  derived old candidates (2) from declared axes. RULING: closed comparator may only ADD details rows for keys fixture shows w/o
  detail and equal to registry axis; derived_runtime rows only for keys with detail entries; sha256 pins + zero fixture bytes;
  4 mutants; rule test; red back to exactly 16. Lead ACCEPTED + narrowed: allowance only for the
  pinned 6 keys (axis declared after the gate; forest exact) + mutant (e); PR body names the 12 tests citing rc-0008 (c). Then my check, then owner adopt-set question.
  Child 3 COMMITTED 5ef660231 -> APPROVED (exact 16 red, zero fixture bytes, pins unchanged, axes = owner values; blind 20/20 final).
  Observation passed to owner via README/question: grassland variant features sit at the same in-tile spot -> visible 16-px grid.
  Implementer asks owner adopt-set (adopt / redraw named / decline; decline -> STOP to me). Then child 4.
  OWNER ADOPTED terrain-variants-v1: sa-34445853fa87089b (14 entries, 2026-10-12T17:02:15Z). Implementer: pins commit -> child 4
  (build 14, owner rc-0010 question, sample map re-render). I review pins commit + red set before the rc-0010 question.
  MY GATES: child 1 design note (detail axis on adopted keys: adoption, rc slot identity, pickDetail, manifest size) before any registry
  edit; red set exact from child 2 until rc-0010; review each commit; pre-check closure from my worktree.
  Owner steps: detail values (child 3), adopt-set (review folder ~/Work/asset-review/terrain-variants-v1/), rc-0010, merge.
- After this: A (markers) with V2 kind names as the presenter emits them.
- History:
- NOTHING IN FLIGHT. D (sample map) MERGED: PR #526 squash 6ba9083ef at 2026-10-12T15:40:12Z (owner --admin pinned e0366f77e).
  Branch visual-asset-sample-map finished, never pushed again. Evidence + gap report: docs/assets/sample_map/.
- NEXT (owner, 2026-10-12): TERRAIN VARIANTS (gap G4, ~14 tiles; starts with a MAX_REGISTRY_BYTES budget review, registry ~90 %
  realistic max). BLOCKED on #523 (rpg: do art keys follow V2 names PLAIN/plain/river/ruin, or V2 maps onto the 23 Live Map names?).
  Lead takes the vocabulary question to owner/rpg. Then A (markers), also gated on #523. G12: sample worlds are rectangles over
  one default fill (rpg worldgen), caps what variants show. Owner question asked with neutral options (no Recommended).
- B MERGED earlier: PR #521 squash 5951fdb71 (rc-0009 = 73 current; Git LFS keep closed; no bound raise).
  Backlog: TCK-20261011-VISUAL-ASSETS-BUILD-EXPORTS-FRAME-ONE-ONLY (trigger: before client animation).
- My worktree: untracked 2026-W42/asset-planner-planning.gate_verdicts.jsonl (my own pre-check lines) -> next planning commit.
- Session name: relaunch as asset-planner (shows as rpg-based-simulation-0b).
- Owner's call: delete leftover local branches visual-asset-slices, visual-asset-real-art-proof, visual-asset-sample-map;
  confirm my worktree. MCP restart unconfirmed until a fresh session's first new_sprite.
- History (superseded):
- IN FLIGHT (2026-10-12): batch D visual-asset-sample-map DISPATCHED to asset-implementer. Epic TCK-20261011-EPIC-VISUAL-ASSET-SAMPLE-MAP
  + DATA -> RENDER -> GAP-REPORT (todos/visual-asset-sample-map/SEQUENCE.md). Branch visual-asset-sample-map head 83a8ccefe (my
  planning 773feea4a + origin/main 5951fdb71 merged + REGISTRY regen + my gate_verdicts shard), upstream unset; my worktree detached.
  Lead guards: no activation (src/ read-only import only, no frontend/), output reports/visual_assets/sample_map/, evidence only in
  docs/assets/sample_map/ <= 256 KiB, never adopted/rc, #519 corrects gap report only, every source cited, gap rows with size+needed-by.
  DATA GATE DONE -> approved: frontier_living_world, highland_traverse, dungeon_crawl (thin); exact-name rule; 87.9 % cells
  unmapped (PLAIN 54,661). ADDED: second render view 'proposed_aliases' (PLAIN/plain->grassland, ruin->ruins, river->shallow_water,
  shop->store, CAMP->enemy_camp, RUIN->ruins), labelled unconfirmed, tool data only, never registry aliases.
  FINDING (code reading) posted on #519 + sent to lead: present_map per-world codes vs client fixed TILE_COLORS -> Live Map likely
  draws wrong colours; V2 vocabulary (PLAIN/plain/river/ruin) != 23-code set. rpg decides; bears on A's key vocabulary.
  MY GATE (was): DATA's 3 worlds + terrain-name->key table before commit. STOP cases: a write outside reports/; renderer cannot match
  terrainBorders.ts test vectors. Then review each commit; pre-check closure from my worktree.
- B DONE: PR #521 MERGED squash 5951fdb71 at 2026-10-12T14:26:06Z (owner --admin pinned eaa9195a0; lead approved by review).
  Branch visual-asset-real-art-proof finished, never pushed again. rc-0009 (73) is current. Verdicts: Git LFS keep closed; raise bounds none.
  Backlog: TCK-20261011-VISUAL-ASSETS-BUILD-EXPORTS-FRAME-ONE-ONLY (todos, trigger before client animation).
  MCP restart: unconfirmed until a fresh session's first new_sprite.
- PR #526 OPEN head e0366f77e (diffed: main + REGISTRY only), CI green 18/18, owner --admin merge pending (implementer asked).
  OWNER ANSWERED art priority 2026-10-12: NEXT = TERRAIN VARIANTS (G4 ~14 tiles + registry budget review); WAIT for #523 vocabulary.
  A stays after, also gated on #523. Told lead; lead takes the vocabulary question to owner/rpg. After #526 merges: idle until #523.
- D fix fad0360ad (REGISTRY only) -> APPROVED FOR PR. Implementer merges main, I diff merged head, owner push/PR, then I ask the
  owner the art-priority question.
- D CLOSED at 0b72cd21b -> pre-check FAILED on REGISTRY drift only (artifact_files [] for DATA/RENDER/GAP-REPORT; generated while
  stored artifacts untracked). Implementer to regenerate after git add, send new head. Else PASS (footprint, done_checker x4, 137 KiB).
  My worktree: untracked 2026-W42/asset-planner-planning.gate_verdicts.jsonl (my own) -> carry into my next planning commit.
- D children committed: DATA 8ca3eabea, RENDER 8a001d17a, GAP-REPORT d9189ff7e -> ALL APPROVED (asked: add G12 'worlds are rectangles
  over one fill', needed by rpg worldgen). rpg answered #519 (2026-10-11, reconciled). Differential TS test skips without node/esbuild.
  My venv lacks complexipy (env failure in tests/codebase). NEXT: pre-check closure head; after PR up, I ASK THE OWNER the drafted
  art-priority question (gap_report.md, neutral options).
- LEAD 2026-10-12: colour bug filed as rpg #523. D's gap report = #523 evidence (cells per V2 name per world + alias table, link #523).
  A is GATED on #523's vocabulary answer (keys follow V2 names vs V2 maps to 23 codes); if D closes first, TELL LEAD (lead asks owner).
- Next after D: A (entity markers, gated on #523), starting with the MAX_REGISTRY_BYTES budget review; C waits for rpg-planner.
- Session name: relaunch as asset-planner (shows as rpg-based-simulation-0b after the restart; lead asked).
- Leftover local branches visual-asset-slices, visual-asset-real-art-proof: owner's call to delete.
- Open for OWNER: confirm own worktree; test_handover_transit env failure may be fixed by #518 (unchecked).
- History (superseded):
- IN FLIGHT (2026-10-11): batch visual-asset-real-art-proof (candidate B), chosen by lead-planner on the owner's authority.
  Epic TCK-20261011-EPIC-VISUAL-ASSET-REAL-ART-PROOF + 4 children (KEYS, DRAFTS, RELEASE-PROOF, BUDGETS-AND-CLOSE),
  todos/visual-asset-real-art-proof/SEQUENCE.md. Planning commit 8ed564419 on local branch visual-asset-real-art-proof
  (off origin/main 9a9058808, upstream unset), made in MY worktree (now detached at 8ed564419). Dispatched to
  asset-implementer by message; the epic ID was sent to lead-planner.
  Lead conditions: (1) bound exceeded -> STOP, its own owner question, no bound change; (2) adopt + rc approval with the owner,
  listed as asks in the PR body (done as blocking questions during the batch; the PR body lists their status); (3) a budgets.md row per
  bound (fits too) + the Git LFS and raise-bounds verdicts in the epic's closing summary; (4) the handoff refresh goes in this PR.
  Planner choices (owner may overrule): optional keys ui.panel_frame / fx.selection_ring / fx.campfire (64x64, 16 frames);
  no store/drawing code. Fact to record, not fix: the build exports frame 1 only (build/exportconfig.py:53).
  Backlog ticket TCK-20261011-VISUAL-ASSETS-BUILD-EXPORTS-FRAME-ONE-ONLY (lead's ask; trigger: before client animation) committed
  df1cb3be5 in my worktree; the implementer cherry-picks it onto the batch branch. Lead ACCEPTED the ui/fx families.
  Child 1 key text REVIEWED -> approved with edits (no slice geometry or names in descriptions; registry 6.4 % does not change the realistic-max row).
  STOP from implementer: any registry edit -> export-runtime of rc-0008 refuses registry_mismatch (runtime_export.py:87). RULING: option B,
  per-ticket commits kept; branch red on EXACTLY 11 tests (test_atlas 4, test_release_byte_reproducibility 7) until child 3's rc-0009
  turns them green (re-point from rc-0008 if named; send me the diff); content pins 62->65 allowed (exact values); owner declines -> STOP.
  Finding for child 4 docs: a registry edit makes older candidates unexportable (no rollback break: rollback redeploys the frontend build).
  Child 1 COMMITTED 0abcc3153 -> APPROVED (my worktree: 2427 pass; 12 red = 11 registry_mismatch errors + test_the_cli_flag_is_opt_in
  exit 2, same cause; child 3 must make all 12 green). Child 2 drawn (uncommitted): 3 intake PASS, no bound exceeded (campfire 10,154 B =
  9.9 % of MAX_SOURCE_BYTES). DEVIATION accepted: stale MCP server (Lua pin guard, started before #499) -> drove the drawing api from
  the worktree; pixels from deterministic scripts (owner told). Cleared owner adopt question; asked: real adopted SourceRecord bytes in
  child 4 + one scratch measurement of a noisy 64x64x16 case for the D2 verdict. OWNER/USER: the aseprite MCP server needs a restart.
  OWNER ADOPTED all 3 (ad-89f6a62b866bba54 ui.panel_frame, ad-6b7562f0799be9ea fx.selection_ring, ad-27d874d5da867cc0 fx.campfire).
  Child 2 COMMITTED d94f58b69 -> APPROVED (2427 pass, same 12 red, store verify ok; real SourceRecord 520/669/677 B). Nits folded into
  child 3: rename no_animation/no_slices tests, module-level import, ==REVISION_COUNT, pin proof metadata exactly. Implementer asks owner
  rc-0009 directly; child 3 re-points the 12 tests (send me the diff). Child 4 still owes the noisy 64x64x16 scratch measurement.
  Owner: "Assemble rc-0009". Child 3 a28282206 + proof re-run 96ca645f9 APPROVED (2441 pass, 0 red; record rc-0009 73/73). Child 4 docs
  4692f2149 APPROVED: Git LFS keep closed (campfire 9.9 %; noisy 16-col 53 %, full-colour noise 2.2x = not pixel art), raise bounds: none.
  PR #521 OPEN (head eaab84ff9, merge head checked OK) -> CONFLICTING on GitHub after #518 (REGISTRY, server-side, no driver;
  local merge-tree clean); no CI yet. Implementer told: merge main, push same branch, send me head to diff, then CI, then owner --admin.
  CLOSED at 3b3838ed4 -> PRE-CHECKED from my worktree: footprint asset-only, done_checker rc 0 x5, registry in sync, capped
  unit/tools+docs+static+architecture 1170 pass; full tests/tools not run (CI). BATCH APPROVED FOR PR. Implementer merges main, sends
  head (I diff: REGISTRY/main only), asks owner push/PR; I record PR #, then dispatch D after merge. My worktree has my own
  gate_verdicts shard modified (carry into D's commit). MCP restart: not confirmed from the implementer's older session.
  (old) Implementer closing; NEXT FOR ME: pre-check the closure head from my worktree (done_checker_static x5, footprint, tests), then
  implementer asks owner push/PR; after merge dispatch D.
  MY GATES: child 1 key text before commit (done); review each commit; checks only from the main checkout or my worktree.
- D FILED (lead order B -> D -> A; D does not block on #519): epic TCK-20261011-EPIC-VISUAL-ASSET-SAMPLE-MAP + DATA/RENDER/GAP-REPORT,
  planning commit 773feea4a on local branch visual-asset-sample-map (upstream unset). DISPATCH ONLY AFTER B CLOSES (merge main first).
  Finding: present_map codes are per world (state_presenter.py:183); map by terrain name.
- (history) Candidate D (offline sample Live Map from rc-0009 + gap list; owner asked 2026-10-11): issue #519 for:rpg-planner (terrain
  grid, locations, entities, current drawing) opened; ordering D-before-A proposed to lead (my rec), awaiting lead's decision.
- Next after this: candidate A (entity markers) starts with a MAX_REGISTRY_BYTES budget review; C (surface gate) waits for rpg-planner.
- The local branch visual-asset-slices (=10c826ea3, PR #499 head) is leftover from the squash merge; deleting it is the owner's call.
- Open for OWNER: confirm own worktree; env failure test_handover_transit (two memory dirs; owner decides).
- History (superseded):
- NOTHING IN FLIGHT (2026-10-11). Slices batch (epic TCK-20261010-EPIC-VISUAL-ASSET-SLICES + 4) MERGED: PR #499 squash
  595021d6d at 2026-10-11T03:54:51Z (owner --admin pinned 10c826ea3; only change after my pre-check = REGISTRY regen,
  verified). Branch visual-asset-slices finished, never pushed again. Shipped: D25, SourceRecord.slices (16/16 bounds,
  SLICE_* codes), export-runtime --slices (artifact px), drawing op set_slice + handoff slice_count. Gates unmoved.
- Next batch: implementer cuts a NEW branch from origin/main; FIRST asset PR refreshes both docs/assets/session_handoff/*
  (merged ones say "awaiting push/PR"). Store/drawing edits -> one proof-record re-run after the last edit
  (`make PYTHON3=<project venv> visual-assets-aseprite-local`). Planning commits: in MY worktree
  /data/vboxuser/Work/rpg-asset-planner (used this batch; owner has not formally confirmed it). Lesson: regenerate
  REGISTRY after the final stored-artifact move, before push (PR #499 CI failed once on stale artifact_files).
- My worktree is detached at 91e0306db with ONE untracked file: 2026-W41/asset-planner-planning.gate_verdicts.jsonl (my
  own done_checker pre-check lines for the slices batch). Carry it into the next planning commit (stage monitoring).
- Open for OWNER: confirm own worktree; env failure test_handover_transit (two memory dirs; owner decides).
- Still parked: activation (incl. client use of slices/atlases/animation, Live Map icon glyph) until RPG core lands; Git
  LFS; raising bounds; self-hosted runner; other asset kinds.
- History of the slices batch (superseded):
- IN FLIGHT (2026-10-10): batch visual-asset-slices FILED + DISPATCHED to asset-implementer (msg). Epic
  TCK-20261010-EPIC-VISUAL-ASSET-SLICES + 4 children (todos/visual-asset-slices/SEQUENCE.md). Planning commit 27f62cf39
  on local branch visual-asset-slices (off origin/main cbfe372b0), made in MY worktree /data/vboxuser/Work/rpg-asset-planner
  (now detached so the implementer can check the branch out in rpg-aseprite-mcp). Owner answers 2026-10-10: store +
  drawing tool; MAX_SOURCE_SLICES 16 / MAX_SLICE_KEYS 16 approved. Planner: SourceRecord.slices only (no registry field),
  export in artifact px (source px x build scale), pivot inside rect inclusive, single-key slices from the drawing tool.
  MY GATES: c1 D25 draft (I review; implementer asks owner to approve text), c3 op shape before code. Review each commit;
  run checks only from main checkout / my worktree, never theirs.
  c1 built (uncommitted): 40 tests, real-Aseprite parity passes; D25 draft REVIEWED -> 2 adds asked (handoff declared
  count only cross-checked; export scales to artifact px + drawing tool single-key), deviations 1-4 accepted (synthetic
  multi-key, flags file-level, negative origins + empty slices=() refused, worst record 30,683 B). Implementer now asks
  owner D25; commits c1 after owner answer + security review.
  c1 COMMITTED 20c146af4 -> APPROVED (owner approved D25 with my 2 sentences; security review approved, 80k fuzz;
  store tests 1287 pass in my worktree). Nits sent: ADR status-line comma; stage monitoring shards per commit; child 4
  docs state zero-size-key limit. Handoff slice_count moved to c3 (agreed). Next: c2 export, then c3 op shape (my gate).
  c2 COMMITTED 76418d7a5 -> APPROVED (208 targeted tests pass in my worktree; scale cross-checked vs artifact w/h ->
  BuildError slices_scale_unresolved). c3 op `set_slice` (apply_ops, make-or-replace, single key, tool name pattern,
  slice_count omitted when 0, SLICE_COUNT_MISMATCH) APPROVED with edits: final-canvas check of all slices before save
  (resize shrink test), always declare count when >=1 slice + both-direction mismatch tests + absence=unchecked doc,
  describe whole-slice replace. Monitoring shards staged at c4 closure (no shards in their worktree yet).
  c3 COMMITTED b30ae1663 -> APPROVED (1420 pass incl. real-Aseprite test_slices, my worktree). LUA_SHA256 re-pinned
  (enters NEW artifacts' fingerprint only). c4 conditions sent: proof re-run must show rc-0008 70/70 identical (else STOP,
  no re-pin around), one proof commit, both snapshots, 5 closures, main merge + final pass, then I pre-check.
  c4 DONE: docs 5270c653b, proof e03f08ded (215/215, rc-0008 70/70 identical), main merge 0d682bb9e + REGISTRY 12f01cf60,
  closure 91e0306db. PRE-CHECKED at 91e0306db from my worktree: footprint asset-only (55 files), done_checker PASS x5,
  working-log rows in per-batch shard visual-asset-slices.working_log.jsonl (by design), proof tests 55 pass -> BATCH
  APPROVED for PR. Implementer asks owner push/PR, then --admin merge; I record PR # and merge commit.
- PREVIOUS (2026-10-10): Store-tooling batch (epic TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING + 9) MERGED:
  PR #487 squash 231e35f77 at 2026-10-10T10:37:15Z (owner --admin pinned 37b9d0620). Branch visual-asset-store-tooling
  finished, never pushed again. Shipped: store lock + hash-chained gc deletion log (D24), PNG decoder ~2x, release byte
  reproducibility, committed local Aseprite proof record + CI staleness test (D10 addendum), opt-in atlases
  (MAX_ATLAS_DIM 1024), palettes as data, animation metadata per source revision (16/16), real-bundle evidence capture
  (rehearsal pixel-verified, 4 pages loading-only; real app build may inline small images: untested). Gates unmoved.
- Next batch: implementer cuts a NEW branch from origin/main in rpg-aseprite-mcp. FIRST asset PR must refresh
  docs/assets/session_handoff/* (merged ones say "awaiting push/PR decision"). Any store/** or drawing/** code edit
  makes the proof record stale -> re-run `make visual-assets-aseprite-local` once after the last store edit.
- Open for OWNER: own asset-planner worktree (~/Work/rpg-asset-planner exists; confirm); env failure
  test_handover_transit (two memory dirs -data-/-home-; agent-working domain; owner decides, delete nothing).
- Still parked: activation (incl. Live Map icon glyph) until RPG core lands; Git LFS; slices/9-slice/pivots; client use
  of atlases/animation; raising bounds; self-hosted runner; other asset kinds.
- History of the store-tooling batch (superseded):
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
  PRE-CHECKED at head ebd336942: proof record re-run a90818a7e (run dd3e46ac0, 205/205, rc-0008 70/70), closure
  449900fd8 (done_checker_static PASS x10), main merged twice, proof test 49/49 at head -> BATCH APPROVED for PR.
  Implementer asks owner push/PR, then --admin merge; I record the merge commit.
  Final report: head c2807c840 (24 commits), all suites green except the known env memory-dir failure; closure filled
  real artifacts for c4/c7/c8/c9; owner push/PR question pending (implementer). MY SLIP: my done_checker runs wrote
  gate_verdicts lines into the implementer's worktree (committed by it in c2807c840) -> run checks only from main
  checkout/own worktree (memory: gate-checks-write-monitoring-shards). Branch tracks origin/main by mistake: push with
  explicit `-u origin visual-asset-store-tooling`.
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

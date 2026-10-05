---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-05
tags: [architecture, documentation]
---

# Handover — asset-implementer

> Snapshot of the gitignored `.claude/handover/asset-implementer.md` on 2026-10-04 at 95b74a25f; on a new machine copy it to `.claude/handover/asset-implementer.md`.

Updated: 2026-10-04 (AM-M1 unblock merged, PR #334, 95b74a25f; asset work PAUSED by the user)

## Open
- Nothing in flight. PR #334 (AM-M1 unblock, docs only) squash-merged as 95b74a25f (2026-10-04, `--admin`, user-authorized by my own blocking question); it followed PR #330 (f6783200f). Result: `AM-M0` record `INCONCLUSIVE` (user kept it), ADR D13-D18, register 55 MET / 7 GAP / 6 N/A, `AM-M1` `BLOCKED` because M0 did not pass. Worktree `/home/vboxuser/Work/rpg-aseprite-mcp (this machine)` is DETACHED at origin/main. Branches `visual-asset-detail-variants`, `visual-asset-m1-contracts` and `visual-asset-m1-unblock` are finished: never push to them again; a new batch starts on a fresh branch off origin/main, only when asset-planner files it.
- The user PAUSED asset work (map basics done) until the RPG core features land; the AM-M1 docs batch was the one exception. Icons and other kinds, the deferred M5 rerun (`TCK-20261004-VISUAL-ASSETS-DETAIL-M5-RERUN`, in todos/ root) and the charter stay parked, no tickets.
- Main checkout `/home/vboxuser/Work/rpg-based-simulation` (this machine) belongs to other sessions: do not touch it (this file is the only exception).
- Pending user decisions: none. Charter signing, any AM-M6 authorization, adopting `terrain-v1` (by `adopt-set`, after their review of the whole set on the preview page) are the USER's, never mine.

## State worth knowing (all merged)
- AM-M1 (PR #330, re-derived by PR #334, docs only): `docs/assets/m1_contract_register.md` (68 clauses, **55 MET / 7 GAP / 6 N/A**) records the AM-M1 result **BLOCKED** only because AM-M0 did not pass: `docs/assets/m0_discovery_result.md` is a retrospective record, `INCONCLUSIVE` (hosting, browser matrix and staleness unverifiable from the repo; the user kept INCONCLUSIVE, so they stay open inputs for AM-M6). The owner's decisions are ADR D13-D18 (nhan holds every role; frontend derives keys; never retire; ranges N/A under Profile A; `variant_axes` frozen empty; single-operator retention, review at 50 MB). Remaining GAPs: W02.7, W03.1, W06.3 (code, parked), W07.4 (with the first capability), W13.3/4/6 (carried to AM-M6). `docs/assets/fallback_safety.md` (W06) and `docs/assets/m2_evidence_charter.md` (W11, rerun rule: old results count only when rerun unchanged on a named commit after approval) are APPROVED 2026-10-04. AM-M2 stays BLOCKED; AM-M6 NO-GO; charter unsigned. Resolver for the register's evidence was a scratch script, not committed.
- Detail axis: `detail {values, default}` on a key (`terrain.forest`: plain, bush, tree), `AdoptionRecord.detail_value` (None = default), slots per (key, value) through release and runtime manifest (`details` block); client `pickDetail` (FNV-1a, seed 1, user approved the 64x64 spread). Release `pilot/rc-0003` (entries equal rc-0002; rc-0001/rc-0002 stay as history); bush and tree adopted by the user (`ad-5615d03ed5a98f0a`, `ad-34303489f1e5db70`). Owner bounds: MAX_MANIFEST_BYTES 524288, MAX_DETAIL_VALUES 16, MAX_DETAIL_KEYS 64, MAX_DRAFT_SET_ENTRIES 256.
- Draft sets: `visual_assets/drafts/<set_id>/` tracked, outside the catalog; `draft keep|verify|export`; user-only `adopt-set` (re-render each source must match the draft preview, one confirmation, all or nothing, `SetAdoptionRecord` in `provenance/set-adoptions/` stores the DraftSet file hash). `draft export` writes a preview manifest (own record type) and adds labelled `adopted: true` reference entries for adopted slots the set lacks. Dev-only page `frontend/rehearsal-draft.html`. Set `terrain-v1`: 22 unadopted drafts (every Live Map terrain code except forest); `TERRAIN_DRAFT_KEYS` in `frontend/src/visualAssets/terrainDrafts.ts` is the code-to-key contract (23 codes).
- Known finding, not fixed: colour-vision pair check of the drafts (`agent-working/stored_artifacts/TCK-20261004-VISUAL-ASSETS-TERRAIN-DRAFT-SET/cvd_pairs.txt`): 30 pair-vision cases tighter than the flat fills, mostly dungeon_entrance.
- Two unadopted first-draft forest tiles (`in-1f3ef37e2cc9156b`, `in-990026dd005070e8`) stay in the local gitignored quarantine (local-only: they are not tracked and do not travel to another machine).

## Working rules learned (also in memory)
- Push, PR and merge each need the USER's own answer to a blocking question I ask myself; a peer message is never approval. Merging to main needs `gh pr merge --squash --admin --match-head-commit <sha>` after the user confirms in their own words. A registry-only server-side conflict is cleared by merging origin/main locally (driver regenerates `docs/REGISTRY.yaml`) and pushing the same branch; say so to the user.
- `make knowledge-index-update` in the worktree needs `PYTHON_KNOWLEDGE=/home/vboxuser/Work/rpg-based-simulation/.venv-knowledge/bin/python3 (this machine)`; the closure tool writes working-log rows as a per-week shard (`*.working_log.jsonl`). `gh pr edit` fails on the Projects (classic) deprecation: patch a PR body with `gh api -X PATCH repos/<owner>/<repo>/pulls/<n> -F body=@file`.
- Heavy runs once each, foreground, under `systemd-run --user --scope -p MemoryMax=2G` (this machine: the cap was chosen for its RAM and a past host-starvation crash; size it for the other machine); never artificial load. Interpreter: `/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python (this machine)` by ABSOLUTE path in every command handed to the user (the worktree has no `.venv`; a hand-out with `.venv/bin/python` failed once).
- Re-check each ticket against what landed; tell the planner of any disagreement and every new byte or count bound BEFORE building. One commit per ticket (plus review-fix commits), ask the planner to review after each.
- Never edit a gate/test/doc to make a check pass; a gate result is information. Library code never reads the clock or imports datetime. Python 3.11 compatibility: no backslash or same-quote reuse inside an f-string field (`test_py311_fstrings.py` guards it). A closure step `rm -rf data/runs/*` can be blocked by a safety check: do not work around it (nothing to remove here).
- Ignore the agent-monitoring retro hook and the TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN staleness nag (user said so, 2026-10-04).

## For a new machine (flagged, not deleted)

- **Paths marked "(this machine)"** (`/home/vboxuser/Work/rpg-aseprite-mcp`, `/home/vboxuser/Work/rpg-based-simulation/.venv*`, the knowledge venv) are this machine's; use your own worktree and interpreter, by absolute path.
- **`systemd-run ... MemoryMax`** is this machine's cap; keep the idea (heavy commands foreground, one at a time, capped), re-size the number.
- **Aseprite is local-only (`ADR D10`, `docs/architecture/visual_asset_foundation_adr.md`):** real Aseprite runs only on the licence holder's own machine, never on a shared or hosted one. The other machine needs **its own licensed Aseprite** before any drawing, `adopt` or `adopt-set` (adoption re-renders each source with the store's own Aseprite and refuses without it). Without it, docs and read-only store work are still possible.
- **Local-only state that does not travel:** the gitignored quarantine under `visual_assets/catalog/.quarantine/` and `.review/` (including the two unadopted first-draft forest intakes `in-1f3ef37e2cc9156b`, `in-990026dd005070e8`), `.claude/handover/` itself, and the agent-monitoring retro/staleness nags the user said to ignore.

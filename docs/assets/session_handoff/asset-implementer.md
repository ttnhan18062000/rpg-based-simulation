---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-08
tags: [architecture, documentation]
---

# Handover — asset-implementer

> Snapshot of the gitignored `.claude/handover/asset-implementer.md` on 2026-10-08 after PR #418 merged (4a2141df9); on a new machine copy it to `.claude/handover/asset-implementer.md`.

Updated: 2026-10-08 (PR #418 merged as 4a2141df9; activation-roadmap docs ticket in progress on `visual-asset-activation-roadmap`)

## Open
- PR #418 (icon set v2 + owner fixes, 12 tickets) is MERGED (squash 4a2141df9, `--admin`, user's answer, head 91a9fcd9c after a main merge; heavy CI lanes were re-sync-skipped with the same patch as green 328af73db). Next time also reproduce `registry_resync_skip` locally before merging over skipped lanes (planner's note).
- Adopted icons: 36 keys, 7 of them at `r0002` (owner-adopted 2026-10-08T14:23:46Z to 14:24:07Z: hero house cottage, inn tankard, rogue cowl, tool hammer and tongs, common silver bead, buff up arrow, debuff spiked ring). 70 sources, 77 adoptions and revisions; ruins and enemy camp kept as adopted. No release candidate covers an icon slot; nothing is wired (AM-M6 parked by the owner).
- Current ticket: `TCK-20261008-VISUAL-ASSETS-ACTIVATION-ROADMAP` (docs only: parked activation roadmap in the plan README, a known-gap note in `fallback_safety.md`, handoff snapshots). One commit, ask the planner to review, then ask the user the push/PR question.
- The Vite dev server on `[::1]:5173` is the planner's; leave it running.

## State worth knowing
- Process rule (style guide): spec (with theme fields) -> reference study -> owner-approved one-colour silhouette sheet -> draw -> compliance table -> checks (sheet rule, blind check with the era question, look-alike report) -> owner gate with the review folder `~/Work/asset-review/<set>/`. Step 4b: spec numbers guessed before the silhouette are re-agreed at the owner's silhouette question, never restated after drawing.
- Theme rule D21: medieval fantasy plus magic, nothing modern. The review folder README reads the owner's decisions and findings from `visual_assets/icons/owner_fixes_decisions.yaml`.
- Adoption facts live in `tests/visual_assets/adopted_facts.py` (ADOPTION_COUNT 77, REVISION_COUNT 77, ICON_FIX_*); revisions of adopted icons go through `adopt --parent`, human-only.
- The blind check is evidence, not a gate, and noisy. Drawing goes through `visual_assets.drawing.api` in-process; intakes by the worktree CLI. TRAP: the aseprite MCP server runs from the MAIN checkout.

## Working rules learned (also in memory)
- Push, PR and merge each need the USER's own answer to a blocking question I ask myself; a peer message is never approval; a merge pins `--match-head-commit` to the REAL head (read it with `git rev-parse HEAD`, never type it from memory).
- Re-verify every planner citation before quoting it: in the gate map two were wrong and one claim (icon keys without a class) was false.
- `make knowledge-index-update` works in the worktree; closure tool `tools/agent-monitoring/record_hand_orchestrated_closure.py` (needs `--title`, `--log-summary`; it appends the working-log row itself).
- Heavy runs foreground under `systemd-run --user --scope -p MemoryMax=4G`; interpreter `/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python` by ABSOLUTE path.
- One commit per ticket, planner review after each; a gate result is information (never tuned).

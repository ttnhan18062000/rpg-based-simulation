---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-06
tags: [architecture, documentation]
---

# Handover — asset-implementer

> Snapshot of the gitignored `.claude/handover/asset-implementer.md` on 2026-10-06 at 2c793286f (the batch's code commit; the closing docs commit follows it); on a new machine copy it to `.claude/handover/asset-implementer.md`.
Updated: 2026-10-06 (batch `visual-asset-terrain-set-review` built and recorded on branch `visual-asset-terrain-set-review` in `/home/vboxuser/Work/rpg-aseprite-mcp`; NOT pushed, no PR yet; asset work paused again after this batch)

## Open
- Branch `visual-asset-terrain-set-review` (off origin/main 58aa22f67; behind origin/main by a few merged PRs, ahead by ~13 commits): planning commits, children 1-4 (rule, re-tint, border contract, border masks), recording child (`6b1243af7`), DETAIL-M5-RERUN code commit `2c793286f` and a docs/close commit. Last steps: handoff snapshot refresh (done with the close commit), planner's final review, then the user decides push / PR / merge (blocking questions; merging needs `gh pr merge --squash --admin --match-head-commit <sha>`; merge origin/main locally first so the PR reports the renamed checks `Code health` and `Type check`, and `pr_render` does not list unrelated tickets).
- Worktree `/home/vboxuser/Work/rpg-aseprite-mcp`. Main checkout `/home/vboxuser/Work/rpg-based-simulation` belongs to other sessions (this file is the only exception).
- Pending user decisions: none. Charter signing, any AM-M6 authorization are the USER's.

## State worth knowing
- The USER adopted `terrain-v1` themselves on 2026-10-05T18:17:03Z (`sa-f4c541f25f112221`, hash `sha256:287ab36c0299f9180b2ebf47afc84c95babf612818f80af3e0eeb78457023eb2`): 22 terrain tiles + 9 `border.*` masks = 31 adoptions; with forest's 3 the catalog holds 34 sources. `tests/visual_assets/adopted_facts.py` pins these facts (equality only); change it in the same commit as any new adoption.
- Release: user approved `build` + `pilot/rc-0005` (34 slots, same registry as rc-0004) + export on 2026-10-06. Fixture `frontend/src/visualAssets/__fixtures__/terrainset/` (own fresh-export test); pilot fixture (rc-0004, forest only) untouched. Registering the `border.*` keys earlier moved the registry hash -> `pilot/rc-0004` (user approved).
- Set colour-vision rule `AM5-S` (`tests/visual_assets/set_colour_vision.py`): PASS 0/1012 only "by construction" (all 22 tiles re-tinted so mean == fill; offset rule in `tile_retint.py`, stored artifacts of TCK-20261005-...-REDRAW); closest pair-vision 0.857 dE (jungle/lava protan). Never reword; the honest meaning is "no worse than the flat fills".
- Borders: contract in `docs/assets/pilot_terrain_m5_criteria.md` (AM5-B: 15-rank order, 8 `crisp`, 4 px cap, 8 neighbours, greedy inner corners, outer-corner condition, missing mask = hard edge, missing inner corner = two edges); pure compositor `frontend/src/visualAssets/terrainBorders.ts`, renderer `borderRender.ts` (a mask counts only if its image is loaded), dev-only pages `rehearsal-draft.html` (borders toggle) and `rehearsal-map.html` (whole-map scene; capture `npx playwright test -c playwright.map.config.ts` with `--setenv=PILOT_CHROMIUM=<chrome-headless-shell>` when run under systemd-run; kill a leftover `vite --port 5176` first).
- M5 rerun result 2026-10-06 (all checks on commit 2c793286f): W03-SET PASS (user: "Yes for all 23 terrains" x C1..C6), W07 PASS in the approved matrix (16/16), W05 gate stays INCONCLUSIVE, overall M5 INCONCLUSIVE, no gate reworded. Known fragility, not fixed: `pilot_colour_vision.tile_pixels()` takes the first PNG of the pilot export (the tree slot here).
- `adopt-set` render match with alpha was proven read-only with `rendering.compare_preview` (31/31 MATCH, script in stored artifacts of the BORDER-MASKS ticket).
- Draft intakes (the 22 first tiles, replaced intakes, nine masks) stay in the gitignored quarantine; workspace sprites `tdraft_*_a/_b`, `tmask_*` stay in `~/.cache/rpg-aseprite-mcp`.

## Working rules learned (also in memory)
- Push, PR and merge each need the USER's own answer to a blocking question I ask myself; a peer message is never approval. A registry-only server-side conflict is cleared by merging origin/main locally and pushing the same branch.
- `make knowledge-index-update` in the worktree needs `PYTHON_KNOWLEDGE=/home/vboxuser/Work/rpg-based-simulation/.venv-knowledge/bin/python3`; the closure tool writes working-log rows as a per-week shard. `gh pr edit` fails on the Projects (classic) deprecation: patch a PR body with `gh api -X PATCH repos/<owner>/<repo>/pulls/<n> -F body=@file`.
- Heavy runs once each, foreground (or background with an output file when over 2 min), under `systemd-run --user --scope -p MemoryMax=2G`; env vars need `--setenv=`. Interpreter: `/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python` by ABSOLUTE path in every command handed to the user.
- Re-check each ticket against what landed; tell the planner of any disagreement BEFORE building. One commit per ticket (plus review-fix commits); ask the planner to review after each.
- Never edit a gate/test/doc to make a check pass; a gate result is information. Re-point a guard only when the owner's legitimate state change made it stale, by exact equality, and say so in the commit. `stored_artifacts/**/*.json` is gitignored: store JSON evidence as `.txt`.
- Ignore the agent-monitoring retro hook and the TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN staleness nag (user said so, 2026-10-04).

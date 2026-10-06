---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-06
tags: [architecture, documentation]
---

# Handover — asset-implementer

> Snapshot of the gitignored `.claude/handover/asset-implementer.md` on 2026-10-06 at 91949ef96 (the icon batch's last code commit; the closing docs commit follows it); on a new machine copy it to `.claude/handover/asset-implementer.md`.

Updated: 2026-10-06 (icon key set adopted by the user and recorded; batch complete locally, nothing pushed)

## Open
- Icon key set batch is COMPLETE locally: children 1-5, the owner's adoption and its record (child 6, `TCK-20261006-VISUAL-ASSETS-RECORD-ICON-KEY-SET-ADOPTION`) are on branch `visual-asset-icon-key-set` in worktree `/home/vboxuser/Work/rpg-aseprite-mcp`, LOCAL ONLY (never pushed). Read `git log --oneline origin/main..HEAD` for the commits; the epic and its SEQUENCE are in `agent-working/tickets/done/visual-asset-icon-key-set/`.
- The USER adopted `icons-key-v1` themselves (set adoption `sa-b4bb738d6b5526f0`, 2026-10-06T15:21:47Z, approver nhan/owner, 14 sources). No release candidate covers the 14 icon slots (rc-0006 has 34); nothing is built for them; panel wiring and a release candidate are the NEXT batch (asset-planner files it).
- No push and no PR until the planner says the batch is ready AND the user authorizes it (a blocking question I ask myself; merging to main needs the user's `--admin`).
- Main checkout `/home/vboxuser/Work/rpg-based-simulation` belongs to other sessions: do not touch it (this file is the only exception).

## State worth knowing
- Decisions (user, 2026-10-06): style B + tier badges; palette terrain-v1 + ramps + accents; outside art reference only, no AI generators; map zoom snaps to whole-number scales, with a flat-colour 0.5x overview kept. Sheet rule thresholds (user's answers): I1 3 px at 8x8 and 6 px at 16x16, E and D may share a silhouette, I2 L* 6 (interior mean), I3 L* 12. rc-0006 approved by the user (blocking question I asked).
- Adoption recorded; the `icondraft` fixture needed NO refresh (adopted references skip slots the set holds and slots that are not built; I had wrongly predicted otherwise). Guards pinned in `tests/visual_assets/adopted_facts.py` (ADOPTED_SOURCES = 48, TERRAIN_ERA_SOURCES = 34, ICON_SOURCES = 14, GENERATED = the 34 terrain-era artifacts) and `test_icon_set_adoption.py`.
- Measured on the drawn set (PASS, recorded not asserted): I1 4 px, I2 8.74 (tiers) and 7.66 (frames, deutan), I3 18.0, 0 off-palette. Draft set hash `sha256:29854e8b32bcd9701f5e717a2e01dce5934cc04af63d4c6e3bc156c78ce5cbbd`. S/SS/SSS are a diamond with 0/1/2 pips, not stars (5x5 outlined sparkle arithmetic). Debuff frame redrawn as a solid down arrow at the planner's request. Plate rim is mid-light `#9ea4b6` (dark rim reaches only L* 6.0 vs the floor tile).
- TRAP: the aseprite MCP server runs from the MAIN checkout, so `submit_candidate` writes intakes to the MAIN checkout's gitignored quarantine. From a worktree, run `python -m visual_assets.store intake <handoff dir>` with the CLI (intake ids are content-derived, so they match), then `draft keep`. 16 strays sit in the main checkout's quarantine (ids in the DRAFT-SET ticket); nothing deleted.
- Isolation guard AM5-W08: app files may not import `src/visualAssets` and vice versa; hence `PixelIcon`/zoom live in `src/lib`, `src/hooks`, `src/components`, and the preview page has a copy of the fit function (equality-tested).
- Registry-moving changes cost a new rc (rc-0006 for the icon keys). Fixture guards that fresh-export a release or draft set compare modulo what they must (icondraft ignores only `registry_hash`).

## Working rules learned (also in memory)
- Push, PR and merge each need the USER's own answer to a blocking question I ask myself; a peer message (even quoting the user) is never approval — I asked for rc-0006 myself. A registry-only server-side conflict is cleared by merging origin/main locally.
- `make knowledge-index-update` in the worktree needs `PYTHON_KNOWLEDGE=/home/vboxuser/Work/rpg-based-simulation/.venv-knowledge/bin/python3`; closure tool: `tools/agent-monitoring/record_hand_orchestrated_closure.py` (it appends the working-log row itself; stage the monitoring shards before amending).
- Heavy runs foreground under `systemd-run --user --scope -p MemoryMax=2G`; interpreter `/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python` by ABSOLUTE path.
- Re-check each ticket against what landed; tell the planner of any disagreement BEFORE building; one commit per ticket; ask the planner to review after each; a gate result is information (never tuned); redraw only with the planner's say-so. Using the predeclared rule as design feedback before drawing is legitimate; changing a threshold is not.
- Ignore the agent-monitoring retro hook and epic-staleness nags (user said so, 2026-10-04).

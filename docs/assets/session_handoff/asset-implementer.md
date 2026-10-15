---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-15
tags: [architecture, documentation]
---

# Handover — asset-implementer

> Snapshot of the gitignored `.claude/handover/asset-implementer.md` taken on 2026-10-15 at the close of the map-markers batch (its own `Updated:` line below says how current it is); on a new machine copy it to `.claude/handover/asset-implementer.md`. Refreshed in `TCK-20261013-VISUAL-ASSETS-MARKERS-RC-AND-CLOSE`.


Updated: 2026-10-15 (map-markers batch COMPLETE locally on `visual-asset-map-markers-impl`, NOT pushed; waiting on the Aseprite proof run, one full tests/visual_assets run, planner review and the user's push decision)

## Open
- STATE: worktree `/home/vboxuser/Work/rpg-aseprite-mcp`, branch `visual-asset-map-markers-impl` (off origin/main `06aa3a20c`, merged with origin/main on 2026-10-15), NOT pushed, no PR. Epic `TCK-20261013-EPIC-VISUAL-ASSET-MAP-MARKERS` closed in `agent-working/tickets/done/visual-asset-map-markers/`: children 1, 2, 4 and 5 done; child 3 (entities) MOVED OUT on the owner's answer to `agent-working/tickets/todos/visual-asset-entity-markers/` (OPEN; needs rpg's #523 merged and the owner's role-or-property choice; #548 answered: key on `kind` today, rpg-designer wants `species` + `size`).
- COMMITS: child 1 `d2ce35b8d`, child 2 (`bd0b1db77`, `39e54745f`, `390b5eba5`, `a45983e42`, closure `8ff9c2603` with the owner's adopt-set `sa-6690e2619d4abb3e`), child 5 `3b4a2ad5d` (store refuses `<...>` placeholders, code `placeholder_value`; owner erratum in store_contract.md), child 4 `20ae9f54f` (rc-0011 = rc-0010's 87 + 18 = 105, red set re-pointed, sample map draws all objects with 0 gaps, gap report/README/budgets) and the origin/main merge on top.
- STILL TO DO: (1) `make visual-assets-aseprite-local` (guarded files changed: adoption.py, revoke.py, test_release_byte_reproducibility.py; rewrites docs/assets/aseprite_local_proof.json), commit it; (2) one full `tests/visual_assets` run under MemoryMax=3G (ask lead-planner first); (3) refresh `docs/assets/session_handoff/*` snapshots; (4) send asset-planner the head sha for review; (5) push question to the USER myself (blocking), `tools/delivery/pr_render.py --theme "<headline>"`, poll CI, read Code health, merge question pinned to head; `gh pr merge --admin` is denied in my session: give the user the exact command for `!`.
- Never run `adopt`, `adopt-set`, `revoke`; never `icon_draft_fixture --write` on the closed fixtures. Heavy suites only under `systemd-run --user --scope -p MemoryMax=3G`, one at a time, lead-planner told first. No `pkill -f`.

## State worth knowing
- Registry 83 keys + 8 aliases, `visual_keys.yaml` 42,024 B (9.2 % of the bound); rc-0011 candidate 18,092 B, runtime manifest 27,268 B, evidence crops 120,273 B (exact view only: the alias view equals it now).
- The object-marker adoption records hold the template placeholders for approver, role and licence evidence; the owner's erratum (nhan / owner, licence text) is in `docs/assets/store_contract.md` ("Provenance errata"). berry_thicket and spirit_wisp still misread in the blind check; the owner kept them.
- The live client does NOT resolve registry aliases (Known gap); a 16 px building map glyph is a later owner choice (in the gap report).
- Interpreter `/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python`; the aseprite MCP server runs from the main checkout (intakes via the store CLI from the worktree, then `draft keep`). The sample-map data tool compiles the three worlds (reads src/ read-only).
- `tests/tools/test_handover_transit.py::test_default_memory_dir_slug_maps_checkout_path` fails on this machine; not ours.

## Working rules learned (also in memory)
- Push, PR and merge each need the USER's own answer to a blocking question I ask myself; a peer message is never approval; merge pinned to `--match-head-commit`.
- Merge `origin/main` locally before the push question; every sync changes the head. `generate_registry.py --check` from a clean tree after `git add`.
- Before every commit run `git status` and `git diff --cached --stat`. Never `ruff check --fix` over a whole test tree. Never `git stash` in a shared checkout (the stash list is shared).
- `record_hand_orchestrated_closure.py` needs per-ticket event summaries (it refuses reused payloads) and `--path-reason batch_hand_close`; it writes the working-log row itself.
- A command template with `<...>` placeholders gets recorded literally if the store does not refuse it: the guard now does.

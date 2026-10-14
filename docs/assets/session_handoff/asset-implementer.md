---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-13
tags: [architecture, documentation]
---

# Handover — asset-implementer

> Snapshot of the gitignored `.claude/handover/asset-implementer.md` taken on 2026-10-13 at the close of the terrain-variants batch (its own `Updated:` line below says how current it is); on a new machine copy it to `.claude/handover/asset-implementer.md`. Refreshed in `TCK-20261011-VISUAL-ASSETS-SAMPLE-MAP-GAP-REPORT`.

Updated: 2026-10-13 (terrain-variants batch COMPLETE on `visual-asset-terrain-variants`, awaiting the user's push decision; real-art #521 and sample-map #526 merged)

## Open
- BATCH COMPLETE, NOT PUSHED: epic `TCK-20261012-EPIC-VISUAL-ASSET-TERRAIN-VARIANTS` (4 children, closed in `agent-working/tickets/done/visual-asset-terrain-variants/`), branch `visual-asset-terrain-variants` in `/home/vboxuser/Work/rpg-aseprite-mcp` (off origin/main `6ba9083ef`). Next: planner pre-check, merge origin/main locally, then ask the user the push question (blocking, my own AskUserQuestion), PR (the body names the 12 tests the axes broke and why, citing the planner's ruling and the rc-0008 ruling (c) precedent), poll CI, then the `--admin` merge question pinned to the head.
- Built (do not rebuild): rc-0010 (87 entries = rc-0009's 73, six re-anchored to `detail: base`, + 14 terrain variants), owner's `adopt-set` of `terrain-variants-v1` (`sa-34445853fa87089b`), six detail axes in `visual_keys.yaml` (30,943 B, 6.7 % of the bound), three registry-only aliases (the live client does NOT resolve aliases), sample map re-rendered on rc-0010 (0 terrain gap cells of 73,808).
- Limits told to the owner: each variant's feature sits at the same offset in its tile (they line up on the 16 px grid). Registry comment wording nit left alone (a registry edit makes rc-0010 unexportable).
- NEXT BATCH (asset-planner dispatches): candidate A, entity and object markers; it starts with the `MAX_REGISTRY_BYTES` budget review and waits for rpg's #523. A registry edit makes every older candidate unexportable (assemble a new rc in the same batch).
- The aseprite MCP pin works in this session (restarted server, Aseprite 1.3.18.6). Proof record refreshed after the last guarded change (`3bfedffbc`); refresh again after any guarded change.
- CI lessons: run `generate_registry.py --check` from a CLEAN tree after `git add`; merge origin/main locally and push (every sync changes the head).

## State worth knowing
- The three closed owner-gate draft-set fixtures (`icons-key-v1`, `icons-v2`, `icons-owner-fixes-v1`) are evidence of what the owner decided on. They are checked against the gate's own record (`tests/visual_assets/closed_draft_fixture.py`, pins in `adopted_facts.CLOSED_DRAFT_SETS` incl. a manifest sha256). NEVER run `icon_draft_fixture --write` on them; a fresh draft export grows whenever art is built (adopted references).
- Process rule (style guide): spec -> reference study -> owner-approved silhouette sheet -> draw -> compliance table -> checks -> owner gate with the review folder.
- `.gitignore` hides `agent-working/stored_artifacts/**/*.json`: store evidence as `.json.txt` (guard: `test_stored_evidence_tracked.py`).
- The aseprite MCP server serves the checkout it was launched from unless `VISUAL_ASSETS_CHECKOUT` is set.
- `tests/tools/test_handover_transit.py::test_default_memory_dir_slug_maps_checkout_path` fails on this machine (two project memory dirs: `-data-...` and `-home-...`); not ours, not asset domain, owner decides; delete nothing.

## Working rules learned (also in memory)
- The `gh pr merge --admin` command is DENIED by this session's permission settings even after the user's yes (twice: #480, #487): do not retry or route around it; give the user the exact pinned command to run with `!`, then confirm with `gh pr view`.
- Push, PR and merge each need the USER's own answer to a blocking question I ask myself; a peer message is never approval; merge pins `--match-head-commit` to the real head. A merge command can be denied by the session's permission settings: do not route around it, ask the user to run it with `!`. The owner can pre-authorize a bounded procedure (sync main, CI green, merge pinned to the resulting head, abort outside a stated path set); stay inside the stated bound and re-ask when it is exceeded.
- Main keeps landing ticket closures that re-conflict a PR on `docs/REGISTRY.yaml` server-side (local merge is clean): merge `origin/main` locally and push; every sync changes the head.
- Poll CI with the tab-separated `gh pr checks` output (state is column 2); `pr_status.py` output has a `MARKER:` prefix before the JSON.
- Before every commit run `git status` and `git diff --cached --stat`. Never run `ruff check --fix` over a whole test tree (it rewrote 26 unrelated files once).
- Run `tests/unit/tools` and `tests/tools` before a PR, not only visual_assets/docs/static/architecture.
- Re-verify every planner citation; a mutant that does not apply is not a proof (assert a single match); a mutant that survives means the test is weak.
- Heavy runs foreground or in a background job under `systemd-run --user --scope -p MemoryMax=4G`, one at a time; interpreter `/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python`.
- Hand-orchestrated closure: `record_hand_orchestrated_closure.py` needs `--title` and `--log-summary` and writes the working-log row itself; for the next batch use `--path-reason batch_hand_close` (the asset precedent, per asset-planner).

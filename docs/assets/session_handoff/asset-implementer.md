---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-10
tags: [architecture, documentation]
---

# Handover — asset-implementer

> Snapshot of the gitignored `.claude/handover/asset-implementer.md` taken on 2026-10-10 at the close of the store-tooling batch (its own `Updated:` line below says how current it is); on a new machine copy it to `.claude/handover/asset-implementer.md`. Refreshed in `TCK-20261010-VISUAL-ASSETS-STORE-TOOLING-DOCS-AND-CLOSE`.

Updated: 2026-10-10 (store-tooling batch complete on `visual-asset-store-tooling`, awaiting the user's push/PR decision)

## Open
- BATCH COMPLETE, NOT PUSHED: epic `TCK-20261010-EPIC-VISUAL-ASSET-STORE-TOOLING`, branch `visual-asset-store-tooling` in `/home/vboxuser/Work/rpg-aseprite-mcp` (all nine children committed, every child approved by asset-planner, the four owner decisions recorded, tickets closed in `agent-working/tickets/done/visual-asset-store-tooling/`). Next: the final suite pass numbers go to asset-planner, then ASK THE USER the push/PR question (never infer yes), then CI poll, then the separate `--admin` merge question pinned to the real head (re-fetch origin/main first; a bounded procedure the owner pre-authorizes must be stated with its path set).
- What the batch built (for the PR): store lock + deletion log (ADR D24), faster PNG decoder (bounds unchanged), release byte reproducibility tests, the committed local Aseprite proof record (ADR D10 addendum, `make visual-assets-aseprite-local`), opt-in atlases (`export-runtime --atlas`, `MAX_ATLAS_DIM` 1024) and opt-in animation metadata (`--animation`, 16 frames / 16 tags), terrain/icon palettes as data, and the bundle capture (`make visual-assets-bundle-capture`, local only). Owner decisions: "Approve as written" (D10 addendum), "Approve 1024", "Approve 16 / 16", "Clear both" (two frontend config files; rpg-planner seat not live).
- If the proof record goes stale again (any change under `visual_assets/store/**`, `drawing/**`, the build config, the marked tests or the two runner tools): re-run `make visual-assets-aseprite-local` once, as its own commit, after the LAST such change. Guarded files must be committed first.
- Earlier batches merged: PR #471 (`0c3a5654b`) and PR #480 (`cfad712cf`). Those branches are finished: never push to them again.
- Activation of adopted art is parked (owner, 2026-10-08) until the RPG core lands.

## State worth knowing
- The three closed owner-gate draft-set fixtures (`icons-key-v1`, `icons-v2`, `icons-owner-fixes-v1`) are evidence of what the owner decided on. They are checked against the gate's own record (`tests/visual_assets/closed_draft_fixture.py`, pins in `adopted_facts.CLOSED_DRAFT_SETS` incl. a manifest sha256). NEVER run `icon_draft_fixture --write` on them; a fresh draft export grows whenever art is built (adopted references).
- Process rule (style guide): spec -> reference study -> owner-approved silhouette sheet -> draw -> compliance table -> checks -> owner gate with the review folder.
- `.gitignore` hides `agent-working/stored_artifacts/**/*.json`: store evidence as `.json.txt` (guard: `test_stored_evidence_tracked.py`).
- The aseprite MCP server serves the checkout it was launched from unless `VISUAL_ASSETS_CHECKOUT` is set.
- `tests/tools/test_handover_transit.py::test_default_memory_dir_slug_maps_checkout_path` fails on this machine (two project memory dirs: `-data-...` and `-home-...`); not ours, not asset domain, owner decides; delete nothing.

## Working rules learned (also in memory)
- Push, PR and merge each need the USER's own answer to a blocking question I ask myself; a peer message is never approval; merge pins `--match-head-commit` to the real head. A merge command can be denied by the session's permission settings: do not route around it, ask the user to run it with `!`. The owner can pre-authorize a bounded procedure (sync main, CI green, merge pinned to the resulting head, abort outside a stated path set); stay inside the stated bound and re-ask when it is exceeded.
- Main keeps landing ticket closures that re-conflict a PR on `docs/REGISTRY.yaml` server-side (local merge is clean): merge `origin/main` locally and push; every sync changes the head.
- Poll CI with the tab-separated `gh pr checks` output (state is column 2); `pr_status.py` output has a `MARKER:` prefix before the JSON.
- Before every commit run `git status` and `git diff --cached --stat`. Never run `ruff check --fix` over a whole test tree (it rewrote 26 unrelated files once).
- Run `tests/unit/tools` and `tests/tools` before a PR, not only visual_assets/docs/static/architecture.
- Re-verify every planner citation; a mutant that does not apply is not a proof (assert a single match); a mutant that survives means the test is weak.
- Heavy runs foreground or in a background job under `systemd-run --user --scope -p MemoryMax=4G`, one at a time; interpreter `/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python`.
- Hand-orchestrated closure: `record_hand_orchestrated_closure.py` needs `--title` and `--log-summary` and writes the working-log row itself; for the next batch use `--path-reason batch_hand_close` (the asset precedent, per asset-planner).

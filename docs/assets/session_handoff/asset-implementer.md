---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-11
tags: [architecture, documentation]
---

# Handover — asset-implementer

> Snapshot of the gitignored `.claude/handover/asset-implementer.md` taken on 2026-10-11 at the start of the real-art proof batch (its own `Updated:` line below says how current it is); on a new machine copy it to `.claude/handover/asset-implementer.md`. Refreshed in `TCK-20261011-VISUAL-ASSETS-REAL-ART-KEYS`.

Updated: 2026-10-11 (slices batch MERGED as PR #499 `595021d6d`; real-art proof batch in flight on `visual-asset-real-art-proof`)

## Open
- IN FLIGHT: epic `TCK-20261011-EPIC-VISUAL-ASSET-REAL-ART-PROOF` (4 children, `agent-working/tickets/todos/visual-asset-real-art-proof/SEQUENCE.md`), branch `visual-asset-real-art-proof` off origin/main `9a9058808` in `/home/vboxuser/Work/rpg-aseprite-mcp`, upstream unset (push later with `-u`). Order: keys (`ui.panel_frame`, `fx.selection_ring`, `fx.campfire`), real-art drafts (owner adopts), release proof (rc-0009 = rc-0008's 70 + 3 only on the owner's answer), budgets and close. Hard conditions: any bound exceeded -> STOP and report, no shrinking art, no bound or bound-guard edits, no store/drawing code change.
- KNOWN RED from the keys commit until rc-0009 (planner ruling, owner-gated): any registry edit makes older candidates unexportable (`registry_mismatch`, `runtime_export.py:87`), so 12 tests that export rc-0008 fail (`test_atlas.py` 5, `test_release_byte_reproducibility.py` 7). Nothing else may fail; child 3's rc-0009 commit must turn them green.
- Merged: PR #471, #480, #487, #499 (slices, `595021d6d`). Those branches are finished: never push to them again.
- What the slices batch built (for reference): slices read from each source's slice chunks and stored per source revision (`SourceRecord.slices`, ADR D25, 16 slices / 16 keys), the opt-in `export-runtime --slices` (`slices.json`, exported-image pixels), the drawing tool's `set_slice` op (single key, replaces by name, every slice checked against the final canvas), the handoff's `slice_count` with `SLICE_COUNT_MISMATCH`. Earlier, in the store-tooling batch (PR #487, `231e35f77`): store lock + deletion log (D24), faster PNG decoder, release byte reproducibility, the local Aseprite proof record (D10 addendum), opt-in atlases and animation metadata, palettes as data, the bundle capture.
- The Lua of the drawing tool is hash-pinned: this batch re-pinned it (`python -m visual_assets.drawing.pin`); pin changes affect only newly built artifacts' fingerprints.
- If the proof record goes stale again (any change under `visual_assets/store/**`, `drawing/**`, the build config, the marked tests or the two runner tools): re-run `make visual-assets-aseprite-local` once, as its own commit, after the LAST such change. Guarded files must be committed first.
- Activation of adopted art is parked (owner, 2026-10-08) until the RPG core lands.

## State worth knowing
- The three closed owner-gate draft-set fixtures (`icons-key-v1`, `icons-v2`, `icons-owner-fixes-v1`) are evidence of what the owner decided on. They are checked against the gate's own record (`tests/visual_assets/closed_draft_fixture.py`, pins in `adopted_facts.CLOSED_DRAFT_SETS` incl. a manifest sha256). NEVER run `icon_draft_fixture --write` on them; a fresh draft export grows whenever art is built (adopted references).
- Process rule (style guide): spec -> reference study -> owner-approved silhouette sheet -> draw -> compliance table -> checks -> owner gate with the review folder.
- `.gitignore` hides `agent-working/stored_artifacts/**/*.json`: store evidence as `.json.txt` (guard: `test_stored_evidence_tracked.py`).
- The aseprite MCP server serves the checkout it was launched from unless `VISUAL_ASSETS_CHECKOUT` is set.
- `tests/tools/test_handover_transit.py::test_default_memory_dir_slug_maps_checkout_path` fails on this machine (two project memory dirs: `-data-...` and `-home-...`); not ours, not asset domain, owner decides; delete nothing.

## Working rules learned (also in memory)
- The `gh pr merge --admin` command is DENIED by the session's permission settings even after the user's yes (#480, #487): give the user the exact pinned command to run with `!`, then confirm with `gh pr view`.
- Push, PR and merge each need the USER's own answer to a blocking question I ask myself; a peer message is never approval; merge pins `--match-head-commit` to the real head. A merge command can be denied by the session's permission settings: do not route around it, ask the user to run it with `!`. The owner can pre-authorize a bounded procedure (sync main, CI green, merge pinned to the resulting head, abort outside a stated path set); stay inside the stated bound and re-ask when it is exceeded.
- Main keeps landing ticket closures that re-conflict a PR on `docs/REGISTRY.yaml` server-side (local merge is clean): merge `origin/main` locally and push; every sync changes the head.
- Poll CI with the tab-separated `gh pr checks` output (state is column 2); `pr_status.py` output has a `MARKER:` prefix before the JSON.
- Before every commit run `git status` and `git diff --cached --stat`. Never run `ruff check --fix` over a whole test tree (it rewrote 26 unrelated files once).
- Run `tests/unit/tools` and `tests/tools` before a PR, not only visual_assets/docs/static/architecture.
- Re-verify every planner citation; a mutant that does not apply is not a proof (assert a single match); a mutant that survives means the test is weak.
- Heavy runs foreground or in a background job under `systemd-run --user --scope -p MemoryMax=4G`, one at a time; interpreter `/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python`.
- Hand-orchestrated closure: `record_hand_orchestrated_closure.py` needs `--title` and `--log-summary` and writes the working-log row itself; for the next batch use `--path-reason batch_hand_close` (the asset precedent, per asset-planner).

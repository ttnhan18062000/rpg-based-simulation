---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-18
tags: [architecture, documentation]
---

# Handover — asset-implementer

> Snapshot of the gitignored `.claude/handover/asset-implementer.md` taken on 2026-10-18 while the visual-asset-docs-sync batch was in flight (the implementer's live handover is authoritative; its own `Updated:` line below says how current it is); on a new machine copy it to `.claude/handover/asset-implementer.md`. Refreshed in `TCK-20261018-VISUAL-ASSETS-HANDOFF-SNAPSHOTS`. Paths of the form `/home/...` or `/data/...` name the machine that wrote it; the repo-relative paths work anywhere.

Updated: 2026-10-18 (batch `visual-asset-docs-sync` in flight, docs only, local branch, NOT pushed; previous batch #608 MERGED as `d7831efab`)

## Open
- IN FLIGHT: batch `visual-asset-docs-sync` (2 docs-only hotfix tickets, `agent-working/tickets/todos/visual-asset-docs-sync/SEQUENCE.md`) on local branch `visual-asset-docs-sync` (off origin/main `013a9f275`). Ticket 1 `TCK-20261018-VISUAL-ASSETS-GAP-REPORT-CURRENT` is committed (`178de1ea4`): the gap report has a 2026-10-18 "what is open now" section and records the owner's answers G6 "Keep scaled icons" and G4 "Leave as is"; the art-priority and candidate-A sections are marked answered. Ticket 2 `TCK-20261018-VISUAL-ASSETS-HANDOFF-SNAPSHOTS` is this file and the planner's snapshot. Then: hand-orchestrated close (`record_hand_orchestrated_closure.py`, `batch_hand_close`), planner review, and push/PR only on the owner's answer. `make knowledge-index-update` only after asking the planner (the lead sequences heavy work).
- DONE (#608, `d7831efab`): #598 (the icon page carries the 18 rc-0011 fallbacks, counts by named set 14 + 22 + 18 = 54 registered, 40 undrawn) and #555 (bwrap userns `AdapterError`, cached `sandbox.bwrap_problem()` probe on `config.JOB_TIMEOUT_S`, named skip with the `requires aseprite and bwrap` prefix, strict mode still fails). The Aseprite local proof was refreshed from a real strict run (215 passed, 0 skipped). The host fix for the userns error on the Ubuntu desktop is the owner's (needs sudo).
- GATED: entity markers, `agent-working/tickets/todos/visual-asset-entity-markers/` (`TCK-20261013-VISUAL-ASSETS-ENTITY-MARKER-DRAFTS`). It waits on the rpg bug #523 merging AND an owner choice: key on role id (`kind`, emitted today) or species + size (not emitted yet; #548). Take direction from the planner.
- NOT started: `TCK-20261018-VISUAL-ASSETS-ASEPRITE-JOB-TIMEOUT-UNDER-LOAD` (backlog, P3; touches guarded files, so it needs a proof refresh and the lead's heavy-run OK); `TCK-20261011-VISUAL-ASSETS-BUILD-EXPORTS-FRAME-ONE-ONLY` (parked until the client animates).
- Standing: never `adopt`/`adopt-set`/`revoke`; never `icon_draft_fixture --write` on closed fixtures; heavy suites only with the lead's gate open, under `systemd-run --user --scope -q -p MemoryMax=3G`, one at a time; no `pkill -f`.

## Lessons from #608
- Editing a GUARDED file (anything under `visual_assets/store`, `drawing`, the marked tests, `conftest.py`, `strict_aseprite.py`) stales `docs/assets/aseprite_local_proof.json`: plan the strict run (`make visual-assets-aseprite-local PYTHON3=<venv python>`, about 72 s, heavy-gate OK first) BEFORE the first push. A new constant in `visual_assets/` needs a `budgets.md` row (human-approved) or must reuse an existing bound.
- Run at least `test_budgets_parity` and `test_aseprite_local_proof` (ideally the full `tests/visual_assets`, with the gate open) before the first push of any `visual_assets/` change; scoped runs alone missed both failures on #608.
- The Frontend CI lane is path-filtered; it skipped on #596 because `visual_keys.yaml` is not in the filter, and `iconScene.test.ts` reads it (the filter fix is #607, testing's).

## State worth knowing
- Registry 83 keys + 8 aliases, `visual_keys.yaml` 42,024 B (9.2 % of the bound); rc-0011 candidate 18,092 B, runtime manifest 27,268 B, evidence crops 120,273 B (exact view only: the alias view equals it now).
- The object-marker adoption records hold the template placeholders for approver, role and licence evidence; the owner's erratum (approver and licence text) is in `docs/assets/store_contract.md` ("Provenance errata"). The store now refuses `<...>` placeholders. berry_thicket and spirit_wisp still misread in the blind check; the owner kept them.
- The live client does NOT resolve registry aliases (Known gap). The owner decided on 2026-10-18 that there is no 16 x 16 building map glyph (G6) and no grassland offset redraw (G4); both are in the gap report.
- Interpreter: the repo's `.venv/bin/python`. The aseprite MCP server runs from the main checkout (intakes via the store CLI from a worktree, then `draft keep`). The sample-map data tool compiles the three worlds (reads `src/` read-only).
- `tests/tools/test_handover_transit.py::test_default_memory_dir_slug_maps_checkout_path` fails on the machine that wrote this note; not ours.

## Working rules learned
- Push, PR and merge each need the USER's own answer to a blocking question I ask myself, naming the sha; a peer message is never approval. Merge is pinned to `--match-head-commit`. After merging `origin/main` the sha changes, so ask again.
- Merge `origin/main` locally before the push question. `generate_registry.py --check` from a clean tree after `git add`. After a ticket edit, `pr_render --check --pr N` drifts: refresh the body with the REST PATCH and read it back (`gh pr edit` fails silently).
- Before every commit run `git status` and `git diff --cached --stat`. Never `ruff check --fix` over a whole test tree. Never `git stash` in a shared checkout.
- `record_hand_orchestrated_closure.py` needs per-ticket event summaries (it refuses reused payloads) and `--path-reason batch_hand_close`; it writes the working-log row itself.

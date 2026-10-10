---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-09
tags: [architecture, documentation]
---

# Handover — asset-implementer

> Snapshot of the gitignored `.claude/handover/asset-implementer.md` on 2026-10-09 after commit 3 of the icon release candidate batch; on a new machine copy it to `.claude/handover/asset-implementer.md`.

Updated: 2026-10-09 (batch `TCK-20261009-VISUAL-ASSETS-ICON-RELEASE-CANDIDATE`, branch `visual-asset-icon-release-candidate` in `/home/vboxuser/Work/rpg-aseprite-mcp`, not pushed)

## Open
- PR #471 (foundation hardening) is MERGED (squash `0c3a5654b`, owner `--admin`); that branch is finished, never push to it again.
- Batch `TCK-20261009-VISUAL-ASSETS-ICON-RELEASE-CANDIDATE` (planner-approved): commit 1 `f7d3ffb98` bookkeeping, commit 2 `03fba7da3` the 36 icons built at x1 (terrain tree hash unchanged), commit 3 `e734ca7c9` rc-0008 (the owner answered "Assemble rc-0008") plus the closed draft-set fixture guards re-anchored (planner ruling, option c: `adopted_facts.CLOSED_DRAFT_SETS`, `tests/visual_assets/closed_draft_fixture.py`; fixtures, export and frontend untouched). Commit 4 is the docs; commit 3 awaits the planner's review.
- Next: finish commit 4 (docs + `make knowledge-index-update`), merge origin/main, regenerate docs/REGISTRY.yaml, run tests/unit/tools, tests/tools, visual_assets, docs, static, architecture and frontend `vitest run src/visualAssets`, report to asset-planner, then ask the user the push/PR question (never infer yes). Merge needs the user's `--admin`, pinned to the real head. Set your own upstream when a push is authorized (tracking is unset on purpose).
- Activation of adopted art is parked (owner, 2026-10-08) until the RPG core lands.

## State worth knowing
- Process rule (style guide): spec -> reference study -> owner-approved silhouette sheet -> draw -> compliance table -> checks (sheet rule, blind check with the era question, look-alike report) -> owner gate with the review folder; spec numbers guessed before the silhouette are re-agreed there, never restated after drawing.
- Recorded results reproduce byte for byte from the generic command (`evaluate --set <id> --recorded` equals the committed `rule_result.json`).
- `.gitignore` hides `agent-working/stored_artifacts/**/*.json`: store evidence as `.json.txt` (guard: `test_stored_evidence_tracked.py`).
- The aseprite MCP server serves the checkout it was launched from unless `VISUAL_ASSETS_CHECKOUT` is set.
- Building art grows every fresh draft export (adopted references). The preview fixtures of the closed owner gates are evidence: never regenerate them with `icon_draft_fixture --write`; they are guarded by the gate's own record.

## Working rules learned (also in memory)
- Push, PR and merge each need the USER's own answer to a blocking question I ask myself; a peer message is never approval; merge pins `--match-head-commit` to the real head from `git rev-parse HEAD`.
- Before every commit run `git status` and `git diff --cached --stat` (a staged `git mv` leaked into an unrelated commit and had to be rewritten).
- Run `tests/unit/tools` and `tests/tools` before a PR, not only visual_assets/docs/static/architecture.
- Re-verify every planner citation; a mutant that does not apply is not a proof (assert a single match); a mutant that survives means the test is weak.
- Never run `ruff check --fix` over a whole test tree (it rewrote 26 unrelated files once); format only the files you wrote.
- Heavy runs foreground under `systemd-run --user --scope -p MemoryMax=4G`, one at a time; interpreter `/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python`.

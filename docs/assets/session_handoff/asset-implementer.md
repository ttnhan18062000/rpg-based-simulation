---
status: active
layer: architecture
authority: P2
audience: agent
date: 2026-10-09
tags: [architecture, documentation]
---

# Handover — asset-implementer

> Snapshot of the gitignored `.claude/handover/asset-implementer.md` on 2026-10-09 after the foundation hardening batch (children 1-7); on a new machine copy it to `.claude/handover/asset-implementer.md`.

Updated: 2026-10-09 (foundation hardening batch: children 1-7 committed locally on `visual-asset-foundation-hardening`, branch not pushed; PR needs the user's answer)

## Open
- Batch `TCK-20261008-EPIC-VISUAL-ASSET-FOUNDATION-HARDENING` (7 children, planner-approved): fixture guards derive from the stored candidate (`tests/visual_assets/derived_runtime.py`); the drawing MCP server serves `VISUAL_ASSETS_CHECKOUT` (start a session with it to serve a worktree; refuses a bad root or another store format version); registry keys carry `safety_class`, structured `fallback` and icon labels (owner-approved), loader rejects variant axes, release and export check alternatives (D23; register W02.7/W03.1/W06.3 MET, M1 still BLOCKED by M0); `adopt-set` adopts revisions with new icons (`draft keep --revises`), `draft drop`, `adopt --parent` keeps the slot (D22); review tooling lives in `visual_assets/review/` (`python -m visual_assets.review evaluate|review-sheets|key-usage`); docs drift fixed; ignored evidence JSON now has tracked `.json.txt` twins and a guard.
- Next: merge origin/main, regenerate docs/REGISTRY.yaml, run tests/unit/tools, tests/tools, visual_assets, docs, static, architecture, then ask the user the push/PR question (never infer yes). Merge of the PR needs the user's `--admin`, pinned to the real head.
- Activation of adopted art is parked (owner, 2026-10-08) until the RPG core lands; PR #418 and #450 are merged.

## State worth knowing
- Process rule (style guide): spec -> reference study -> owner-approved silhouette sheet -> draw -> compliance table -> checks (sheet rule, blind check with the era question, look-alike report) -> owner gate with the review folder; spec numbers guessed before the silhouette are re-agreed there, never restated after drawing.
- Recorded results reproduce byte for byte from the generic command (`evaluate --set <id> --recorded` equals the committed `rule_result.json`).
- `.gitignore` hides `agent-working/stored_artifacts/**/*.json`: store evidence as `.json.txt` (guard: `test_stored_evidence_tracked.py`).
- The aseprite MCP server serves the checkout it was launched from unless `VISUAL_ASSETS_CHECKOUT` is set.

## Working rules learned (also in memory)
- Push, PR and merge each need the USER's own answer to a blocking question I ask myself; a peer message is never approval; merge pins `--match-head-commit` to the real head from `git rev-parse HEAD`.
- Before every commit run `git status` and `git diff --cached --stat` (a staged `git mv` leaked into an unrelated commit and had to be rewritten).
- Run `tests/unit/tools` and `tests/tools` before a PR, not only visual_assets/docs/static/architecture.
- Re-verify every planner citation; a mutant that does not apply is not a proof (assert a single match); a mutant that survives means the test is weak.
- Heavy runs foreground under `systemd-run --user --scope -p MemoryMax=4G`, one at a time; interpreter `/home/vboxuser/Work/rpg-based-simulation/.venv/bin/python`.

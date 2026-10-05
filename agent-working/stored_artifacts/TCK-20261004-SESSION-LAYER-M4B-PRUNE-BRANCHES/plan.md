---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261004-SESSION-LAYER-M4B-PRUNE-BRANCHES
phase: open
date: 2026-10-05
tags: [ai]
---

# plan — TCK-20261004-SESSION-LAYER-M4B-PRUNE-BRANCHES

One module plus tests, no schema change beyond the confirmed owns line.

`tools/sessions/prune_branches.py`. Classes: merged-PR (tip == a merged PR head, the only deletable class), hint-only (all subjects in main, or no commits beyond main; informational), unique-commits (includes "PR merged but tip moved"), skipped (worktree, open PR, < 7 days, main, or `gh` unavailable). Dry run by default. `--execute` writes a name-to-SHA backup (default `~/Working/branch-backup-<date>.txt`, never overwrites: suffixes `-2`), reads it back, prints restore commands and then deletes with `git update-ref -d <ref> <sha>` (a moved branch is left alone). Remote: `--remote` too; PR merged and remote-tracking tip == PR head; one `git push --force-with-lease=<ref>:<sha> origin :<ref>` per branch. **No `--execute` or remote delete was run**; the first real run needs the owner's go.

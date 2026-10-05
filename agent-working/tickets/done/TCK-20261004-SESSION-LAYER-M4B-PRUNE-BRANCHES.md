---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261004-SESSION-LAYER-M4B-PRUNE-BRANCHES
phase: done
date: 2026-10-04
tags: [ai, process-improvement, governance]
---

# TCK-20261004-SESSION-LAYER-M4B-PRUNE-BRANCHES

## Title
Session-layer M4b: `prune_branches.py` dry-run classification, backup and guarded execution

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Codify the branch cleanup done by hand on 2026-10-02 as `tools/sessions/prune_branches.py`: dry-run by default, conservative classes, a name-to-SHA backup written first, execution only on the owner's explicit flag (plan 8).

Child of `TCK-20261002-EPIC-SESSION-LAYER-OPERATIONS`. Hold rule met: M1 merged.

## Scope
- Classes, printed with counts: **merged-PR** (the only deletable class), **hint-only** (all commit subjects already in main: informational, never deletion safety), **unique-commits** (listed with owner, never deleted), **skipped** (checked out in any worktree, open PR, or newer than 7 days).
- Local deletion only for merged-PR branches whose tip equals the merged PR's head SHA (a moved tip may hold later work). Remote deletion only if the PR merged **and** the remote tip equals the merged PR's head; one `--force-with-lease=<name>:<sha>` push per branch.
- Backup first: write a name-to-SHA file (default `~/Working/branch-backup-<date>.txt`, the 2026-10-02 convention, overridable by a flag) and verify it is readable before the first deletion; print the restore commands (`git branch <name> <sha>`, `git push origin <sha>:refs/heads/<name>`).
- Execution needs `--execute` and prints the exact list first; remote deletion needs a separate `--remote` flag. A remote delete is visible to everyone and stays the owner's call.
- PR state comes from `gh pr list --state merged`; `gh` failure means no branch is classed merged (everything becomes `skipped`, never deletable).

## Out of Scope
- Auto-run on any schedule, worktree removal, anything deleted without `--execute`, relying on the commit-subject hint for safety.

## Acceptance Criteria
1. Dry-run is the default and changes no ref; a test snapshots refs before and after.
2. A seeded repository proves a **squash-merged branch with unique, unmerged commits is never classed deletable**, and a hint-only branch is reported in its own class.
3. The backup is written before any deletion; restoring a deleted branch from it works (test); a remote branch whose tip moved after the merge is skipped.
4. A branch checked out in a worktree, with an open PR, or younger than 7 days is skipped.
5. `gh` unavailable classes everything `skipped`.
6. Reproducing the 2026-10-02 run on a copy of the data classes the same branches the same way, with the hint-only class reported separately; result pasted into the ticket. Scoped tests green; docs and `docs/REGISTRY.yaml` regenerated.

## Related Tickets
- `TCK-20261002-EPIC-SESSION-LAYER-OPERATIONS` (parent), M4a (parallel); recorded backups `~/Working/branch-backup-2026-10-02.txt` and `remote-branch-backup-2026-10-02.txt`

## Related Docs
- `docs/plans/agent_infrastructure/session_layer_working_process.md` (binding)
- `docs/guides/delivery_process.md`, `agent-working/stored_artifacts/` (2026-10-02 cleanup record, if present)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261002-EPIC-SESSION-LAYER-FOUNDATION/external_reviews/`

## Related Code Areas
- `tools/sessions/prune_branches.py` (new), `tests/tools/`.

## Assumptions / Open Questions
- Executing a remote delete or a first real `--execute` run needs the owner's go in the implementer's terminal, not a peer's. The 7-day staleness constant is the plan's value; it is not tuned here.

## Implementation Notes
`tools/sessions/prune_branches.py`. Classes: merged-PR (tip == a merged PR head, the only deletable class), hint-only (all subjects in main, or no commits beyond main; informational), unique-commits (includes "PR merged but tip moved"), skipped (worktree, open PR, < 7 days, main, or `gh` unavailable). Dry run by default. `--execute` writes a name-to-SHA backup (default `~/Working/branch-backup-<date>.txt`, never overwrites: suffixes `-2`), reads it back, prints restore commands and then deletes with `git update-ref -d <ref> <sha>` (a moved branch is left alone). Remote: `--remote` too; PR merged and remote-tracking tip == PR head; one `git push --force-with-lease=<ref>:<sha> origin :<ref>` per branch. **No `--execute` or remote delete was run**; the first real run needs the owner's go.

Reproduction of the 2026-10-02 data (scratch clone of the shared object store, the 240 backed-up branches restored, real PR data, clock set to 2026-10-02 12:00): 241 branches -> 65 merged-PR, 6 hint-only, 169 unique-commits, 1 skipped (main). So the hand run's 240 deletions are not all reproduced as deletable: only the 65 with a merged PR whose head equals the tip are, by design; the rest are reported for the owner. A first version classed a branch with no commits beyond main as unique; the control caught it and it is now hint-only.

## Test Summary
`tests/tools/test_session_prune_branches.py` (13): merged-PR class; squash-merged branch with later unmerged commits never deletable; hint-only separate; worktree/open-PR/young skipped; `gh` unavailable skips all; dry run changes no ref; backup exists before the deletion and restore works; a moved branch is left alone; remote deleted only when tip equals the merged head and only with `--remote`; backup never overwrites; `fetch_prs` failure -> None.

## Files Changed
`tools/sessions/prune_branches.py`, `tests/tools/test_session_prune_branches.py`, `docs/guides/delivery_process.md`.

## Completion Summary
Tool delivered, dry-run verified on the real repo (see Implementation Notes for the 2026-10-02 reproduction: 65 merged-PR of 241). Execution against real branches awaits the owner.


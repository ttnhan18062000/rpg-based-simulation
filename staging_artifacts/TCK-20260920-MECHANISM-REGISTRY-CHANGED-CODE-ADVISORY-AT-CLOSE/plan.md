# Plan — TCK-20260920-MECHANISM-REGISTRY-CHANGED-CODE-ADVISORY-AT-CLOSE

1. `tools/mechanism_registry/mechanism_registry_changed_code_check.py`:
   - Add `get_changed_files_for_ticket(ticket_id, base_ref="origin/main") -> Set[str]` — the
     ticket-scoped "changed files" definition from the investigation: union of every file in every
     commit whose message matches `ticket_id` (`git log --grep=<ticket_id>`) plus the current
     uncommitted working tree (`git status --porcelain`, staged/unstaged/untracked). Docstring
     records both the "why not origin/main diff" reasoning and the pre-merge-only boundary.
   - Add `check_drift_for_ticket(ticket_id, base_ref="origin/main") -> (List[DriftFinding],
     List[ReplacementFinding])` — close-time entry point: old registry at `base_ref`, new registry
     at `WORKTREE` (so in-progress uncommitted state counts), changed_files from the function above.
   - Extend `main()` with an optional `--ticket-id` argument; when given, use
     `check_drift_for_ticket` instead of `check_drift_from_git` and print the same report shape.
     `--base`/`--head` stay as-is for the existing CI usage (unchanged, backward compatible).
2. `.claude/workflows/implement-ticket.js`: add a fourth Finalize-tail advisory block, immediately
   after the existing `phaseMetaCheck` block, in the exact same shape (runs after status is already
   `'DONE'`, prints a WARNING via `log()`, never changes `status` or the exit code). Calls
   `check_drift_for_ticket(tid)` via the same `sys.path.insert(0, 'tools')` + package-import pattern
   the sibling checks use.
3. `CLAUDE.md`'s "After Work" section: one short bullet, next to the existing
   `record_hand_orchestrated_closure.py` bullet, telling a hand-orchestrating closer to run
   `python3 tools/mechanism_registry/mechanism_registry_changed_code_check.py --ticket-id <TCK-ID>`
   and read its output — non-blocking, no exit-code implication. This is the only reachability path
   for the (common) hand-orchestrated case, mirroring how `record_hand_orchestrated_closure.py`
   itself is documented there.
4. Tests: extend `tests/unit/tools/test_mechanism_registry_changed_code_check.py` with the planted
   cases the AC requires — a planted-drift case (real temp git repo, ticket-ID-tagged commit
   changing a cited file, entry untouched → advisory fires) and a planted-no-drift case (same shape,
   entry updated too → silent). Also cover: `origin/main...HEAD`-style contamination is avoided (a
   second, unrelated ticket's commit on the same branch is NOT included), uncommitted working-tree
   changes are picked up, and `main()`'s `--ticket-id` path still always returns 0.
5. Run the planted cases against a disposable git repo (not this repo's own history) via `tempfile`
   + `subprocess`, so the test doesn't depend on or mutate this repo's real commits.
6. Regenerate `docs/REGISTRY.yaml`, close the ticket via the hand-orchestrated path
   (`record_hand_orchestrated_closure.py`), fold into the already-open PR #231 branch
   (`headroom-batch3-work`) — no new PR.

---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX
phase: inprogress
date: 2026-09-13
tags: [data-quality, process-improvement]
---

# Plan: TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX

## Chosen approach

Option A (regenerate-on-conflict), in the **corrected two-part shape** found during investigation
(see `investigation.md` for the scratch-repo proof and the ordering bug it caught):

1. A trivial, always-succeeding merge driver for `docs/REGISTRY.yaml` — the literal command `true`.
   Git seeds the driver's working file (`%A`) with the "ours" side's content before invoking the
   driver; a no-op command that exits 0 leaves that content as the resolved result, so the merge
   completes with **zero conflict markers**, no script needed for this half.
2. A `post-merge` git hook that does the actual regeneration — chosen over regenerating inside the
   driver itself because a custom merge driver runs per-path with no ordering guarantee relative to
   other paths in the same merge (docs/ticket files also being merged); a `post-merge` hook runs
   only after every path in the merge is fully resolved on disk, which is what makes the
   regeneration correct. Confirmed live: regenerating inside the driver produced a merge that
   "succeeded" but silently dropped an entry the merge itself had just added.
3. `make setup-merge-drivers` — one command, installs both pieces (git config is unversioned local
   state and can't be shipped any other way; the hook file is copied the same way
   `make install-hooks` already installs `post-commit-reindex.sh`).
4. Acceptance Criterion #4 ("a CI check fails when the committed file differs from a fresh
   regeneration") is **already satisfied by existing, shipped code — not a gap to fill.**
   `tests/tools/test_generate_registry.py::TestRealDocsTree::
   test_check_flag_detects_no_drift_against_real_registry` already calls
   `generate_registry(..., check=True)` against the real, live `docs/REGISTRY.yaml`, and is
   already collected by the "API / tools / logging" CI job (`.github/workflows/test.yml:266`,
   `pytest tests/tools ...`). Shipped by `TCK-20260709-REGISTRY-DRIFT-CHECK-GATE`, re-confirmed by
   `TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS`. This ticket cites it rather than building a
   duplicate — see investigation.md's correction note. It remains the essential backstop against
   a **partial install** of this ticket's new merge-driver mechanism (driver configured, hook
   missing/non-executable), which was confirmed live to succeed silently with stale content — no
   error, no warning — so its presence is load-bearing for this ticket even though it predates it.

## Files to add / change

| File | Change |
|---|---|
| `tools/hooks/registry_post_merge_regen.sh` (new) | Post-merge hook body: regenerate via `python3 tools/generate_registry.py`, compare parsed entries against the committed file (reuse the same drift comparison `_check_drift` does — do not hand-roll a second one), and if different, `git add docs/REGISTRY.yaml && git commit -m "auto-regenerate docs/REGISTRY.yaml after merge"`. Modeled directly on `tools/hooks/post-commit-reindex.sh`'s style (strict mode, guard clauses, one-line install comment). |
| `Makefile` | New `setup-merge-drivers` target (next to `install-hooks`): `git config merge.registry-regen.driver true`, `git config merge.registry-regen.name "regenerate docs/REGISTRY.yaml on conflict"`, copy the hook script to `.git/hooks/post-merge` + `chmod +x`. New `docs-registry-check` target: `python3 tools/generate_registry.py --check` (mirrors `parity-index-check`'s style). Add both to `.PHONY`. |
| `.gitattributes` | Add `docs/REGISTRY.yaml merge=registry-regen` (currently only a comment saying this path is deliberately *not* merge=union'd). Keep the existing explanatory comment, add one line noting the driver is opt-in local config installed via `make setup-merge-drivers`, with a fallback note that CI's `--check` step catches drift either way. |
| *(none — already shipped)* | `tests/tools/test_generate_registry.py::TestRealDocsTree::test_check_flag_detects_no_drift_against_real_registry` already covers Acceptance Criterion #4; no new drift-check test file is added by this ticket. |
| `tests/integrity/test_registry_merge_driver.py` (new) | See test_plan.md — a static `.gitattributes` assertion plus the durable, repo-committed version of the scratch-repo proof (both the clean-merge case and the fully-uninstalled loud-failure case), following `test_merge_union_gitattributes.py`'s exact `_run_git`/`tmp_path` pattern. |
| `CLAUDE.md` | Update the `docs/REGISTRY.yaml` bullet under "After Work": mention `make setup-merge-drivers` as the one-time local setup that removes the manual conflict-resolution step, while keeping the existing "take either side + `make docs-registry`" instruction as the fallback for anyone who hasn't installed it. |
| `docs/ai/ticket-lifecycle.md` or nearest doc covering PR conflict handling | Mirror the same guidance (found via search during Document-Update). |

## Explicitly out of scope

- Option B (stop committing the generated file) and Option C (stop regenerating at Finalize) —
  ticket already rejects/defers both; not revisited here.
- Making the generator's own timestamp header deterministic — not needed; `--check` already
  compares parsed entries, not raw bytes, so the header is a non-issue for this ticket's purpose.
- Any change to `generate_registry.py`'s generation logic itself — it is correct and sorted today;
  only a CI wiring gap and a merge-time mechanism are being added.
- Retrofitting the merge driver onto any other generated file (e.g. `parity-index`'s SQLite
  artifact) — out of scope; this ticket is `docs/REGISTRY.yaml` only.

## Conflict frequency, re-measured from real git history (not just the ticket's own table)

Ticket Scope requires this independently, not trusted from the ticket's own pre-recorded table.
`git log --all` (since PR branches are squash-merged, so the actual conflict-resolution commits
live only on now-often-deleted PR branches, not on `main` — see below for why) filtered for the
established convention this session and prior sessions used ("regenerate REGISTRY.yaml post-merge"
/ "resolve docs/REGISTRY.yaml conflict") finds **at least 17 distinct real conflict-resolution
commits** spanning 2026-08-22 through 2026-09-13 (about 3 weeks), across at least 6 distinct
branch lineages: PR #167's branch (3 occurrences), PR #171's branch (4), PR #177's branch (4, one
resolved live during this ticket's own investigation as its 9th occurrence per the peer's report),
a `visual-connectivity-metric` branch, a `working-log-union-recurrence` branch, and a
`MIGRATE-MONITORING` hotfix branch, plus several isolated `docs: regenerate REGISTRY.yaml ...`
commits whose originating branch is no longer identifiable (deleted after merge). This corroborates
the ticket's own narrower table (7 occurrences across PRs #160/#164/#167/#171, measured
2026-09-10..12) as an undercount of the true, longer-running rate — the real pattern goes back at
least three weeks, not three days. Methodology caveat: this is commit-message-based detection
(the only durable trace available, since squash-merge discards the PR branch's own intermediate
merge commits once merged) — not a perfect proxy for "conflict markers literally appeared," but
the most defensible signal obtainable after the fact, and consistent with this session's own
first-hand experience resolving these conflicts in real time.

## Worktree/git-config sharing, verified (not assumed)

This repo runs many concurrent `.claude/worktrees/<name>` checkouts (`git worktree list` shows 8
at time of writing). Verified directly in this worktree: `git rev-parse --git-common-dir` →
`/home/u24desktop/Working/rpg-based-simulation/.git` — the same shared directory for every
worktree of this repo. `git config --get extensions.worktreeConfig` is unset (exit 1), so this repo
does not use per-worktree config overrides — a local `git config merge.registry-regen.driver`
write from *any* worktree lands in the one shared `.git/config` and is immediately visible to every
other worktree. Likewise `git config --get core.hooksPath` is unset, and `git rev-parse
--git-path hooks` resolves to the same shared `/home/u24desktop/Working/rpg-based-simulation/
.git/hooks` for this worktree — hooks are not per-worktree either. **Conclusion: `make
setup-merge-drivers` needs to run exactly once, from any one worktree, to cover every worktree of
this repo.** This resolves in the *opposite* direction from the risk Review raised: it is not a
reason the partial-install gap becomes the common case — it means installation is genuinely
one-time and repo-wide, not per-worktree. (A fresh clone elsewhere, or a different repository
entirely, still needs its own install — that part of the residual risk stands unchanged.)

## Acceptance-criteria map

| Ticket AC | Satisfied by |
|---|---|
| Conflict frequency re-measured from real merge history | See "Conflict frequency, re-measured" above — 17+ real occurrences, 2026-08-22 to 2026-09-13, across 6+ branch lineages |
| One option implemented, rejected ones and reasons recorded | Option A chosen; B and C's rejection reasons carried from the ticket's own text (see "Explicitly out of scope") |
| Two branches that both close a ticket merge without a manual regeneration step | The driver + post-merge hook, proven in the scratch repo |
| One-command install | `make setup-merge-drivers` |
| Uninstalled → fails loudly, never silently takes a side | Confirmed for the fully-uninstalled case: git falls back to its ordinary 3-way merge, leaving real conflict markers and a non-zero exit (corrected during Implement from an earlier, unreproducible claim of a hard `fatal: ... lacks command line` abort — see investigation.md's correction note); still fully loud and safe, just a simpler mechanism. The **partially**-installed case is not loud on its own — flagged as a residual risk covered by the existing CI check, documented explicitly rather than glossed over |
| CI check fails when committed file differs from fresh regeneration | Already shipped: `tests/tools/test_generate_registry.py::TestRealDocsTree::test_check_flag_detects_no_drift_against_real_registry`, cited not duplicated |
| Every consumer listed in the ticket still works from a plain checkout | By construction, not runtime probing: this design changes nothing about `generate_registry.py`'s logic, schema, or output format (explicitly Out of Scope) — only *when* regeneration happens around a merge. A plain checkout that never runs `make setup-merge-drivers` gets the exact same committed `docs/REGISTRY.yaml` as today, read by all 9 listed consumers exactly as before. Nothing to spot-check at runtime since nothing in the read path changes. |

## Risks / open items for Review

- The partial-install silent-staleness gap (driver on, hook off) is real and only caught by CI,
  after the fact, on push — not at merge time. Raising this explicitly for architecture-reviewer:
  is documenting-and-CI-backstopping this sufficient, or does it warrant a stronger local guard
  (e.g., `setup-merge-drivers` also drops a sentinel file the hook checks isn't stale, or a
  pre-push hook re-running `--check` locally)? Leaning toward "documented + CI-backstopped is
  enough" since CI already gates merge to `main` and this is materially better than today's 9+
  manual conflicts per PR — but flagging rather than deciding unilaterally.
- `post-merge` hooks do not run on `git rebase` or `git cherry-pick`, only real merges. Today's
  actual pain (per the ticket's own measurements) is PR-branch merges of `origin/main`, which do
  fire `post-merge` — but this should be stated as a documented boundary, not silently assumed.

## Deviations (Implement)

- **Worktree gitlink bug, self-caught before shipping**: the first draft of `setup-merge-drivers`
  used a hardcoded relative path `.git/hooks/post-merge`. This repo runs almost entirely through
  `.claude/worktrees/<name>` checkouts, where `.git` is a *file* (a gitlink to the real shared
  location), not a directory — a literal `.git/hooks/` path would silently fail (or worse, create
  a bogus `.git/hooks/` path) in every worktree except the main checkout. Fixed by resolving the
  real path dynamically via `git rev-parse --path-format=absolute --git-path hooks` in the Makefile
  target itself, and verified live: `make setup-merge-drivers` run from this worktree correctly
  installed the hook into the actual shared `/home/u24desktop/Working/rpg-based-simulation/
  .git/hooks/post-merge`, confirmed by reading that file directly afterward. `make
  docs-registry-check` also verified working live (`"In sync: 2367 entries match ..."`).
- **Fatal-error claim corrected while writing the durable test** — see investigation.md's own
  correction note and `test_merge_with_no_driver_configured_fails_loudly`'s docstring. The
  uninstalled-driver fallback is an ordinary 3-way merge conflict, not a hard abort; still fully
  loud and safe, just a different mechanism than originally documented. All ticket ACs concerning
  this are still satisfied — "never silently takes a side" holds either way.
- All new/changed files verified with real command runs, not just written and assumed: the new
  `tests/integrity/test_registry_merge_driver.py` (4 tests, all passing, including two real
  failures caught and fixed during writing — the fatal-error assumption above, and a blank-line
  `IndexError` in the `.gitattributes` static assertion), plus `tests/integrity`, `tests/tools/
  test_generate_registry.py`, and the full `arch-docs` job scope (`tests/architecture tests/docs
  tests/integrity tests/static tests/refactor`) re-run clean.

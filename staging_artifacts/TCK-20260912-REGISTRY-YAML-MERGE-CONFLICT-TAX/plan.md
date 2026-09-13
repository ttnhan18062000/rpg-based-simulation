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

## Acceptance-criteria map

| Ticket AC | Satisfied by |
|---|---|
| Two branches that both close a ticket merge without a manual regeneration step | The driver + post-merge hook, proven in the scratch repo |
| One-command install | `make setup-merge-drivers` |
| Uninstalled → fails loudly, never silently takes a side | Confirmed for the fully-uninstalled case (git's own `fatal: custom merge driver ... lacks command line`); the **partially**-installed case is not loud on its own — flagged as a residual risk covered by the existing CI check, documented explicitly rather than glossed over |
| CI check fails when committed file differs from fresh regeneration | Already shipped: `tests/tools/test_generate_registry.py::TestRealDocsTree::test_check_flag_detects_no_drift_against_real_registry`, cited not duplicated |

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

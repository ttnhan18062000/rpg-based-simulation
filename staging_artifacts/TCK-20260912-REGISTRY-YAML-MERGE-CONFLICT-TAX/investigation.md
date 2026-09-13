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

# Investigation: TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX

## Facts independently confirmed

- `tools/generate_registry.py` uses sorted enumeration (`sorted(docs_dir.rglob(...))`,
  `sorted(done_dir.glob(...))`) and an explicit `sort_entries()`. Grep confirms both.
- **The generator is NOT byte-deterministic.** Direct diff of two consecutive runs against the
  same tree shows only a `# Generated: <timestamp>` header line differing — the ticket's own claim
  ("the same tree produces the same bytes") is imprecise. The *entries* are deterministic; the raw
  bytes are not, because of the header timestamp.
- **No `.github/workflows/*.yml` references `REGISTRY.yaml` or `generate_registry` at all** —
  `grep -rl "REGISTRY" .github/workflows/` returns zero hits. Confirmed again during this
  investigation pass.
- **An existing `--check` CLI flag already does the right comparison, AND it is already wired
  into CI today — Acceptance Criterion #4 is already satisfied, not a gap to fill.**
  `generate_registry.py`'s `main()` wires `--check` to `generate_registry(root, output,
  check=True)` (`tools/generate_registry.py:495-518`), which calls `_check_drift(output,
  output_entries)` (`tools/generate_registry.py:470`) — a comparison of *parsed YAML entries*, not
  raw bytes, so it is naturally immune to the timestamp-header issue. Verified live on this branch:
  `python3 tools/generate_registry.py --check` → `"In sync: 2367 entries match ..."`, exit 0.

  **Correction, found via `search_docs` (should have been run before the first grep pass — see
  Process Note below):** `tests/tools/test_generate_registry.py::TestRealDocsTree::
  test_check_flag_detects_no_drift_against_real_registry` (confirmed present at
  `tests/tools/test_generate_registry.py:534-538`) already calls exactly this `--check` path
  against the real, live `docs/REGISTRY.yaml`, and **this file is already collected by the "API /
  tools / logging" CI job** (`.github/workflows/test.yml:266`, which runs `pytest tests/tools ...`
  broadly). This test was added by `TCK-20260709-REGISTRY-DRIFT-CHECK-GATE` and re-confirmed
  still-live by `TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS` (2026-08-26), which explicitly
  investigated a custom merge driver for this exact file, found the CI-check route already
  sufficient for the *drift-detection* half of the problem, and deliberately did not build one.
  My initial `grep -rl "REGISTRY" .github/workflows/` (zero hits) is why this was missed on the
  first pass — the workflow file never names "REGISTRY" as a string; it just runs a broad
  `pytest tests/tools`, the exact same "no workflow YAML edit needed" mechanism this ticket's own
  plan (before this correction) proposed re-inventing under a new test file. **Acceptance
  Criterion #4 requires no new code — cite the existing test, do not duplicate it.**

  This does **not** make the rest of this ticket redundant: `TCK-20260826`'s own investigation was
  scoped narrowly to "does drift get caught after the fact" and concluded yes, sufficient — it
  never addressed *merge-conflict frequency* (the actual, measured pain this ticket exists for:
  9+ conflicts, each costing a manual resolution and a full CI re-run). The CI check is a
  correctness backstop; a merge driver is a toil-reduction mechanism. They are complementary, not
  duplicative, but this ticket must fold in and cite the existing check rather than re-implement
  it.
- No existing custom git merge driver config anywhere in the repo (`git config --get-regexp
  "^merge\."` → empty; merge drivers are unversioned local config by design, so this is expected,
  not a gap).
- `.gitattributes:38-41` already documents the deliberate `merge=union` exclusion for this file
  and instructs resolving conflicts by taking either side and rerunning `make docs-registry` —
  the exact manual step this ticket exists to remove.

## Scratch-repo proof of Option A (regenerate-on-conflict merge driver)

Built a scratch repo (`/tmp/.../scratchpad/registry_merge_driver_test/repo`) modeling the real
shape of the problem: two branches each add an *independent new file* under `entries/` (standing
in for a new ticket/doc file — these never conflict with each other, matching real ticket closes)
and each regenerate an aggregate `REGISTRY.yaml` from `entries/*.txt` (standing in for the real
generator's sorted rglob). `.gitattributes` declares `REGISTRY.yaml merge=registry-regen`; the
driver is wired via local (unversioned) `git config merge.registry-regen.driver`.

**First design tried (regenerate synchronously inside the merge driver) — found broken.**
The driver ran `python3 regen.py` against the live working tree and copied the result into `%A`.
Merging branch-a into branch-b succeeded with **zero conflict markers** — but the resulting
`REGISTRY.yaml` was **missing branch-a's own entry** (`ticket-a.txt`), even though git's own merge
output confirmed `entries/ticket-a.txt` was added by that same merge. Re-running the generator
immediately afterward (all files now present) produced the correct 3-entry union, proving the
generator itself was fine — the bug is that **git invokes a custom merge driver per-path with no
guaranteed ordering relative to other paths in the same merge**. When `REGISTRY.yaml`'s driver ran,
`entries/ticket-a.txt` had not yet been materialized to disk, so the driver silently regenerated
from an incomplete tree. This is worse than a conflict: the merge reports success (exit 0, no
markers) while the committed result is wrong. Reproduced deterministically across two independent
scratch-repo builds — not observed once and dismissed.

**Corrected design (two-part, verified working):**
1. The merge driver itself does nothing but `exit 0` — git seeds `%A` with the "ours" side's
   content before invoking the driver, so a no-op driver is a trivial, always-succeeding
   conflict resolution (no markers, no regeneration attempted here).
2. A `post-merge` git hook does the actual regeneration, since post-merge hooks run only after
   **all** paths in the merge are fully resolved and committed to the working tree — no ordering
   hazard. It regenerates, compares against the committed file ignoring the timestamp header line
   (mirroring `_check_drift`'s parsed-entry comparison, not a raw byte diff), and if they differ,
   stages and creates a small automatic follow-up commit.

Verified live: merging branch-a into branch-b with this design produced the merge commit with no
conflict markers, immediately followed by an automatic `auto-regenerate REGISTRY.yaml after merge`
commit containing the full, correct 3-entry union (`base.txt`, `ticket-a.txt`, `ticket-b.txt`).

**Fallback behavior, both failure modes tested:**
- **Fully uninstalled** (no local `git config merge.registry-regen.driver` at all): git fails the
  merge outright — `fatal: custom merge driver registry-regen lacks command line`, exit 128. Loud,
  as required.
- **Partially installed** (driver configured, `post-merge` hook missing or not executable): the
  merge **succeeds silently** with the pre-merge "ours" content, which can be stale/incomplete —
  confirmed live by disabling the hook and re-running the merge: no error, no warning, and the
  resulting `REGISTRY.yaml` was missing the entry the merge itself had just added. **This is a real
  residual gap**: the ticket's own fallback requirement ("if not installed, merge must fail loudly
  ... never silently take one side") holds for the fully-uninstalled case but not for a partial
  install. Two implications for the plan:
  - The one-command installer (`make setup-merge-drivers`) must install both pieces atomically —
    the git config *and* the hook file — never one without the other.
  - **The CI `--check` gate (Acceptance Criterion #4) is not an optional nice-to-have alongside
    the merge driver — it is the only backstop against exactly this silent-staleness failure
    mode**, whether caused by a partial install, a hook that didn't fire, or someone bypassing
    hooks (`git merge --no-verify` does not skip `post-merge`, but a corrupted/non-executable hook
    file would). It already exists (`generate_registry.py --check`) and just needs a workflow step.

## Process note (search-before-grep gap, self-caught)

This investigation started with direct grep/file reads before running the mandatory
`search_docs`/`graphify query` step (CLAUDE.md's Context Scan hard rule). Running `search_docs`
after the fact — "docs/REGISTRY.yaml merge conflict git merge driver regenerate" — immediately
surfaced `TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS`, a directly relevant prior ticket that a
grep-first approach had missed. Recording this as a reminder that the ordering rule is not
optional even when a ticket looks self-contained: it caught a real near-duplication of already-
shipped work here, not just a hypothetical risk.

## Conclusion

Option A is viable but only in the corrected two-part shape (trivial merge-driver placeholder +
post-merge regeneration hook), not the simpler single-driver design the ticket's own text
initially sketches. This is a real, load-bearing correction to carry into plan.md, not a detail —
the naive version is an actual correctness regression (silent wrong data) worse than today's loud
conflict.

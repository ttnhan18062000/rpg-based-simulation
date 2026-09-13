---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX
phase: done
date: 2026-09-12
tags: [data-quality, process-improvement]
---

# TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX

## Title
`docs/REGISTRY.yaml` conflicts on nearly every concurrent PR — a generated file merged by hand

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`docs/REGISTRY.yaml` is regenerated unconditionally at every ticket close (CLAUDE.md's After Work
section) and committed. With several sessions closing tickets in parallel, every open PR that isn't
first to land collides on it.

**Measured, not estimated (2026-09-10..12):**

| PR | Conflicts on `REGISTRY.yaml` |
|---|---|
| #160 | 1 |
| #164 | 1 |
| #167 | 2 (merges of #165, #166) |
| #171 | 3 (merges of #168/#169, then #170) |

Seven occurrences across four consecutive PRs. Each costs: merge `main`, take main's copy, rerun
`make docs-registry`, push, and wait out a **full CI run** (~6-10 min). Worse, a conflict can land
while CI is mid-run, so a PR can be reported green and be stale minutes later — that happened twice
on #171. It is currently the single largest source of rework in the merge queue, and it is pure
overhead: no reviewer ever reads the diff, and the resolution is always "regenerate".

**Why `merge=union` is not the answer here.** `.gitattributes` deliberately excludes this path: the
file is a full-file rewrite, not an append, so unioning two regenerations produces duplicated keys
and invalid YAML. That exclusion is correct and should stay.

**Facts established before proposing options:**
- Regeneration is one command, no arguments: `python3 tools/generate_registry.py` (`make docs-registry`).
- The generator is deterministic: sorted file enumeration (`sorted(docs_dir.rglob(...))`,
  `sorted(done_dir.glob(...))`), an explicit `sort_entries()`, and fixed `yaml.dump` options. The same
  tree produces the same bytes, which is what makes regenerate-on-conflict viable.
- **No CI workflow regenerates or verifies it** — nothing in `.github/workflows/` references it. So
  today the committed copy is trusted, never checked.
- **At least 9 tools and several tests read the committed file directly**:
  `tools/registry_query.py`, `tools/gate_checks/done_checker_static.py`, `tools/hybrid_retrieval.py`,
  `tools/pr_impact_report.py`, `tools/ticket_stats_report.py`, `tools/codebase_health_baseline.py`,
  `tools/codebase_health_snapshot.py`, `tools/code_health_impact.py`, plus
  `tests/agent_codex_realrepo_pilot_harness/`, `tests/agent_codex_pilot_orchestration/`,
  `tests/agent_replay/`. A plain checkout must therefore keep working.

## Scope
- Confirm the conflict frequency independently (`git log` over recent merges) rather than trusting this
  ticket's table, and record the measured cost per occurrence.
- Choose and implement one of the options below, recording why the others were rejected.
- **Option A (recommended): a regenerate-on-conflict merge driver.** Add
  `docs/REGISTRY.yaml merge=registry-regen` to `.gitattributes` and a driver that ignores both sides
  and re-runs the generator against the merged tree. Merge drivers live in git config, which is not
  versioned, so this needs a one-command install (`make setup-merge-drivers` or similar), documented in
  CLAUDE.md, plus a graceful fallback: if the driver is not installed, the merge must fail loudly as it
  does today, never silently take one side.
- **Option B (rejected unless A proves unworkable): stop committing the file.** It would end the
  conflicts outright, but all the consumers above read it from a plain checkout, so each would need a
  generate-if-missing path or a bootstrap step. Much larger blast radius for the same benefit.
- **Option C (fallback): stop regenerating at Finalize.** Regenerate on `main` only, via a scheduled or
  post-merge CI job. One writer means no conflicts, but the file goes stale between runs and every
  consumer above then reads stale data — acceptable only if staleness is proven harmless.
- Whichever lands: add a CI check that the committed file matches a fresh regeneration, so a bad
  resolution is caught rather than trusted.

## Out of Scope
- The registry's schema or content, and `tools/generate_registry.py`'s own logic.
- Other generated artifacts (`graphify-out/`, `parity-index/`, brainstorm indexes) — same shape, but
  they are not causing this tax today. File separately if they start to.
- The `merge=union` paths (`tickets/working_log.csv`, monitoring shards): different mechanism, already
  handled by `TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION`.

## Acceptance Criteria
- [x] Conflict frequency is re-measured from real merge history and recorded. (17+ real
      conflict-resolution commits found via `git log`, 2026-08-22 to 2026-09-13, across 6+ branch
      lineages — see investigation.md's "Conflict frequency, re-measured" section.)
- [x] One option is implemented, with the rejected ones and their reasons recorded. (Option A;
      B/C's rejection reasons carried from this ticket's own Scope text.)
- [x] If Option A: the driver regenerates rather than merging, is installable in one documented command,
      and a test proves an uninstalled driver fails loudly instead of silently taking one side.
      (`make setup-merge-drivers`; `tests/integrity/test_registry_merge_driver.py::
      test_merge_with_no_driver_configured_fails_loudly` — an uninstalled driver falls back to
      an ordinary, loud 3-way merge conflict, never a silent one-sided pick; see investigation.md's
      correction note on the exact mechanism.)
- [x] A CI check fails when the committed `docs/REGISTRY.yaml` differs from a fresh regeneration.
      (Already shipped by `TCK-20260709-REGISTRY-DRIFT-CHECK-GATE` —
      `tests/tools/test_generate_registry.py::TestRealDocsTree::
      test_check_flag_detects_no_drift_against_real_registry` — cited, not duplicated.)
- [x] Two branches that both close a ticket can merge without a manual regeneration step — demonstrated
      in a scratch repo, the way `TCK-20260911`'s reproduction test does it. (Proven twice: an
      ad-hoc scratch repo during investigation, then durably in
      `tests/integrity/test_registry_merge_driver.py::
      test_merge_with_driver_and_hook_installed_regenerates_correct_union`.)
- [x] Every consumer listed above still works from a plain checkout. (By construction: this design
      changes nothing about `generate_registry.py`'s schema/logic, only when regeneration happens
      around a merge — see plan.md's Acceptance-criteria map.)

## Related Tickets
- `TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION` (done, PR #167) — the sibling merge-hygiene
  fix; established the scratch-repo reproduction pattern this ticket should reuse.
- `TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS` (done) — added the `merge=union` paths and the
  deliberate exclusion of `docs/REGISTRY.yaml`.
- `TCK-20260709-REGISTRY-DRIFT-CHECK-GATE` (done) — **already shipped this ticket's own Acceptance
  Criterion #4**: `tests/tools/test_generate_registry.py::TestRealDocsTree::
  test_check_flag_detects_no_drift_against_real_registry` already runs `generate_registry.py
  --check` against the real, live registry inside the "API / tools / logging" CI job. Found via
  `search_docs` during this ticket's own investigation (a first grep-only pass had missed it) —
  cite it, do not re-implement it. It remains the correctness backstop for this ticket's new
  merge-driver mechanism's partial-install failure mode (see investigation.md).
- `TCK-20260912-WORKING-LOG-APPEND-HELPER` (todos) — same theme: who owns writes to a shared file.

## Related Docs
- `CLAUDE.md` (After Work: registry regenerated unconditionally at Finalize, plus the new
  `make setup-merge-drivers` one-time install note)
- `.gitattributes` (`docs/REGISTRY.yaml merge=registry-regen`, and the comment explaining why
  `merge=union` is unsafe here)
- `docs/README.md` (doc registry section: `make docs-registry-check`, the merge-driver mechanism,
  and the manual fallback)

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/generate_registry.py`, `Makefile` (`docs-registry`)
- `.gitattributes`
- The consumer list in Request Summary.

## Assumptions / Open Questions
- **Resolved by direct, isolated reproduction (post-PR-review, before merge) — not left open.**
  Confirmed via three separate scratch repos: (1) the custom driver DOES apply during both `git
  rebase` and `git cherry-pick`, not only `git merge` — git invokes `.gitattributes`-declared merge
  drivers for any internal 3-way content resolution, including the ones these commands perform
  under the hood. (2) On both paths, a genuine content conflict resolves via the trivial `true`
  driver exactly like a plain merge: silently keeps one side (`rebase`: the branch being rebased
  onto; `cherry-pick`: the current branch), **with zero conflict markers and zero indication
  anything was discarded** — `rebase` reports "Successfully rebased", `cherry-pick` reports an
  "empty" cherry-pick with no error. (3) `post-merge` fires for **neither** path (confirmed: no
  hook invocation in either reproduction) — so the regeneration step never runs there. **This is a
  real, disclosed gap, not fixed by this ticket**: on `rebase`/`cherry-pick`, this mechanism
  degrades to "always silently take one side," the exact failure mode the ticket set out to avoid,
  just relocated to two different git commands. The existing CI drift check
  (`tests/tools/test_generate_registry.py::TestRealDocsTree::
  test_check_flag_detects_no_drift_against_real_registry`) remains the only backstop on these two
  paths — it still catches the resulting drift on push, before it reaches `main`, but there is no
  local, loud signal at the time of the rebase/cherry-pick itself. Durably reproduced in
  `tests/integrity/test_registry_merge_driver.py::
  test_rebase_and_cherry_pick_silently_take_one_side_no_post_merge_hook`. Not hardened further in
  this ticket (would require a `pre-rebase`/`applypatch-msg`-style safeguard, non-trivial and out
  of this ticket's scope) — recorded here plainly per the ticket's own original question, per
  Review's request.
- GitHub's own server-side merge does not run local drivers — the conflict must still be resolved
  locally before pushing; the driver saves the local step, not the server-side one. (Unchanged from
  the original assumption — this was never in question.)
- Whether regeneration is fully deterministic across machines (the sorting says yes; verify with two
  independent runs rather than assuming).
- Whether a post-merge CI job could regenerate and commit to `main` without fighting branch protection.

## Implementation Notes
Shipped Option A in a corrected two-part shape found mid-investigation: a trivial, always-
succeeding merge driver (`git config merge.registry-regen.driver true`, declared via
`.gitattributes: docs/REGISTRY.yaml merge=registry-regen`) resolves any merge conflict on this
path with zero conflict markers (git seeds its working file with the "ours" content; a no-op
driver leaves that as the result). The actual regeneration happens in a separate `post-merge` git
hook (`tools/hooks/registry_post_merge_regen.sh`), not inside the driver itself — a first design
that regenerated synchronously inside the driver was proven, via a scratch-repo reproduction, to
silently produce an incomplete registry: git invokes a custom merge driver per-path with no
ordering guarantee relative to other paths in the same merge, so the driver ran before a sibling
file the merge had just added was materialized to disk. A `post-merge` hook runs only after every
path in the merge is fully resolved, closing that gap. `make setup-merge-drivers` (new Makefile
target) installs both pieces atomically in one command, resolving the real hooks directory
dynamically via `git rev-parse --path-format=absolute --git-path hooks` rather than a hardcoded
`.git/hooks/` path — this repo runs almost entirely through `.claude/worktrees/*` checkouts where
`.git` is a gitlink file, not a directory, so a hardcoded path would silently fail there (caught
and fixed during Implement, before shipping). `make docs-registry-check` wraps the existing
`generate_registry.py --check` flag. Verified all of this against the real repo, not just written:
`make setup-merge-drivers` and `make docs-registry-check` were both run for real in this actual
worktree, and the hook was confirmed installed in the real shared `.git/hooks/post-merge`.

Two claims were found wrong and corrected honestly rather than left standing: (1) an earlier plan
draft proposed adding a duplicate CI drift-check test before `search_docs` surfaced that
`TCK-20260709-REGISTRY-DRIFT-CHECK-GATE` already shipped one, already running in CI — dropped in
favor of citing the existing test; (2) a claim that an uninstalled merge driver produces a hard
`fatal: custom merge driver ... lacks command line` abort could not be reproduced under careful,
isolated re-testing (one command per shell call) and was corrected to the real, verified behavior:
git falls back to its ordinary 3-way merge, leaving genuine conflict markers — still fully loud
and safe, just a simpler mechanism than first believed. Both corrections are recorded in
investigation.md, plan.md, test_plan.md, and reflected in the actual shipped test's assertions.

Also added `docs/parity_ledger/infrastructure.yaml`'s `INFRA-417` (this ticket self-reports
`behavior_changed=true` — new logic/config, even though pure tooling — so Parity was not
skip-eligible), cross-referenced to sibling entries INFRA-183/263/264 without duplicating them.

## Test Summary
```
pytest tests/integrity/test_registry_merge_driver.py -q
# 4 passed

pytest tests/integrity tests/tools/test_generate_registry.py tests/architecture tests/docs tests/static tests/refactor -q -m "not slow and not extra_slow"
# 304 passed, 2 skipped, 1 deselected, 2 xfailed

pytest tests/tools -q -m "not slow and not extra_slow"
# 2522 passed, 17 skipped, 28 deselected, 1 xfailed
```
Independently re-confirmed by the Verify (done-checker) pass, run separately from the above.

## Files Changed
- `tools/hooks/registry_post_merge_regen.sh` — new.
- `Makefile` — new `setup-merge-drivers` and `docs-registry-check` targets.
- `.gitattributes` — `docs/REGISTRY.yaml merge=registry-regen` line, comment updated.
- `CLAUDE.md` — After Work bullet mentions the one-time install.
- `docs/README.md` — doc registry section documents the mechanism and the manual fallback.
- `docs/parity_ledger/infrastructure.yaml` — new `INFRA-417` entry.
- `tests/integrity/test_registry_merge_driver.py` — new, 4 tests.
- `staging_artifacts/TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX/{investigation.md,plan.md,test_plan.md}`.

## Completion Summary
Implemented Option A (regenerate-on-conflict merge driver) for `docs/REGISTRY.yaml`, in a
corrected two-part shape (trivial `true` driver + separate `post-merge` regeneration hook) found
necessary mid-investigation after a naive single-driver design was proven to silently produce
incomplete data. One-command install (`make setup-merge-drivers`), verified live in this repo.
An uninstalled driver falls back to an ordinary, loud git merge conflict — never silently picks a
side. The existing CI drift check (`TCK-20260709-REGISTRY-DRIFT-CHECK-GATE`'s
`tests/tools/test_generate_registry.py::TestRealDocsTree::
test_check_flag_detects_no_drift_against_real_registry`) is cited rather than duplicated.

**This coupling is load-bearing, not incidental, and is named explicitly (per Review's request)
in both places that matter: this Completion Summary and the hook script's own header comment
(`tools/hooks/registry_post_merge_regen.sh`).** The driver+hook design is safe *only because* that
specific CI test exists and runs — it is the sole backstop for two disclosed gaps this ticket does
not close: the partial-install case below, and the rebase/cherry-pick case in Assumptions / Open
Questions. If that test is ever deleted (e.g. by someone later trimming "redundant" coverage), this
entire mechanism silently degrades to "always take one side" with zero detection.

**Disclosed residual risk, accepted, no follow-up ticket filed**: a *partially* installed state
(the merge driver configured but the `post-merge` hook missing or non-executable — e.g. a manual
config edit that skips the Makefile target) succeeds silently with stale/incomplete content: no
error, no warning. Confirmed live during investigation by disabling the hook and re-running a
merge. This is weaker than the fully-uninstalled case (an ordinary loud conflict) and weaker than
the ticket's own general "never silently takes a side" framing for that specific partial state.
Accepted rather than hardened further because: (a) `make setup-merge-drivers` installs both pieces
in one atomic command, so reaching this state requires bypassing the documented install path; (b)
the existing CI `--check` test (cited above) still catches the resulting drift on the next push,
before it reaches `main`; (c) this is materially better than today's status quo of 9+ manual
conflicts per PR. `plan.md`'s "Risks / open items for Review" raised this explicitly during Review
rather than deciding unilaterally, and Review (2 rounds, both on record) did not require a
stronger local guard.

**Second finding, discovered live during this ticket's own Finalize merge (this session's coding
assistant sandbox specifically) — not a design flaw, but a real operational caveat worth recording
plainly**: merging `origin/main` into this branch via this sandboxed environment's `Bash` tool did
not trigger the installed `post-merge` hook automatically (git committed the merge cleanly, but no
`auto-regenerate` follow-up commit appeared, and `make docs-registry-check` reported real drift
immediately after). Manually invoking the hook script directly (`bash
$(git rev-parse --git-path hooks)/post-merge`) worked exactly as designed — regenerated, detected
the real drift, and created the expected commit — proving the hook's own logic is correct; the gap
is specifically that *this coding assistant's sandboxed git wrapper* did not fire it during the
merge. The standalone scratch-repo proof (a plain, unsandboxed git binary) and this manual
invocation both confirm the mechanism works; only merges driven through this specific sandboxed
tool are affected. Practical implication for any future agent session operating in this same
sandbox: after a `git merge`, don't assume the hook fired — run `make docs-registry-check` (or
regenerate directly) and verify, the same discipline as checking any other post-merge state.

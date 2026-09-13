---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX
phase: inprogress
date: 2026-09-12
tags: [data-quality, process-improvement]
---

# TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX

## Title
`docs/REGISTRY.yaml` conflicts on nearly every concurrent PR — a generated file merged by hand

## Status
INPROGRESS

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
- [ ] Conflict frequency is re-measured from real merge history and recorded.
- [ ] One option is implemented, with the rejected ones and their reasons recorded.
- [ ] If Option A: the driver regenerates rather than merging, is installable in one documented command,
      and a test proves an uninstalled driver fails loudly instead of silently taking one side.
- [ ] A CI check fails when the committed `docs/REGISTRY.yaml` differs from a fresh regeneration.
- [ ] Two branches that both close a ticket can merge without a manual regeneration step — demonstrated
      in a scratch repo, the way `TCK-20260911`'s reproduction test does it.
- [ ] Every consumer listed above still works from a plain checkout.

## Related Tickets
- `TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION` (done, PR #167) — the sibling merge-hygiene
  fix; established the scratch-repo reproduction pattern this ticket should reuse.
- `TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS` (done) — added the `merge=union` paths and the
  deliberate exclusion of `docs/REGISTRY.yaml`.
- `TCK-20260912-WORKING-LOG-APPEND-HELPER` (todos) — same theme: who owns writes to a shared file.

## Related Docs
- `CLAUDE.md` (After Work: registry regenerated unconditionally at Finalize)
- `.gitattributes` (the exclusion comment explaining why union is unsafe here)

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/generate_registry.py`, `Makefile` (`docs-registry`)
- `.gitattributes`
- The consumer list in Request Summary.

## Assumptions / Open Questions
- Whether a custom merge driver runs on every path that matters here — plain merges certainly, but
  confirm behavior under `rebase` and `cherry-pick`, and under GitHub's own merge (it does not run local
  drivers, so the conflict must still be resolved locally before pushing; the driver saves the local
  step, not the server-side one).
- Whether regeneration is fully deterministic across machines (the sorting says yes; verify with two
  independent runs rather than assuming).
- Whether a post-merge CI job could regenerate and commit to `main` without fighting branch protection.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

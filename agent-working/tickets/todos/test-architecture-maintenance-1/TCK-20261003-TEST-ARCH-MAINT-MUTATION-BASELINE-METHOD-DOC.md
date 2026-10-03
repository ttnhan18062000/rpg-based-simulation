---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-TEST-ARCH-MAINT-MUTATION-BASELINE-METHOD-DOC
phase: open
date: 2026-10-03
tags: [testing]
---

# TCK-20261003-TEST-ARCH-MAINT-MUTATION-BASELINE-METHOD-DOC

## Title
A mutation-baseline method doc, `docs/testing/mutation_baseline_method.md`, plus a reach-check rule

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary

The method for a mutation baseline lives only inside the baseline JSONs and the batch reports, and was
re-derived in `TCK-20261003-SOCIAL-APPRAISAL-MUTATION-BASELINE` (C4). Write it down once, as a doc, with
one new rule from this batch's evidence. Docs only: no new tool or script.

## Scope

New `docs/testing/mutation_baseline_method.md` (frontmatter `layer: testing`, `tags: [testing]`), covering:

1. The scratch copy: `git archive` at a pinned full SHA, outside the repo.
2. Installing mutmut with `pip --target` (no change to the project environment).
3. The `setsid`-detached run (a session close kills a plain background run).
4. The selection rule: import-based, one hop; the resolved file list and its hash are recorded.
5. Green before mutation: the selected tests pass unmutated first.
6. A FRESH positive control per new target (reuse only for a rerun of the same target and selection).
7. G3: detect whether the code under test uses the kernel, then force `audit_mode=True` and a relaxed
   budget through an out-of-repo plugin, recording the as-found and the forced values.
8. Provenance and `stale_after` fields, pointing at `tests/mutation/baselines/` v3 and
   `src_systems_social_appraisal_v1.json` as the examples (referenced, not copied).
9. Separate, labelled lists for lines the world-rules catalog marks CONFLICTING.
10. NEW rule: before reporting 0% coverage or 0 kills for a file or function, run a reach check with the
    repo's other tests that touch it (search the callers' importers) and report the number with its
    selection scope. One case each, cited with SHAs: C2 (`guilds.py` 0% to 92%) and C4
    (`_appraise_position_swap` 0 of 38 killed, then 1 of 28 statements reached).

Two small links:

- `docs/plans/test_architecture/roadmap.md` §6 watch item (e): add the social baseline
  `tests/mutation/baselines/src_systems_social_appraisal_v1.json` (stale about 2026-11-02, or on
  RELATIONSHIP-VECTOR landing).
- The pilot doc's mutation update paragraph: one link to the new method doc.

Then `make knowledge-index-update`.

## Out of Scope

- Any new tool, script or plugin file in the repo; any rerun of mutation testing.
- Any edit under `tests/`, any `docs/parity_ledger/` change, any `src/` change.
- Copying baseline JSON contents into the doc.
- Any new domain or Phase 2 child (scale-out is paused).

## Acceptance Criteria

- [ ] The doc exists with valid frontmatter and covers items 1-10; every figure in it cites a SHA or a
  file, and the two reach-check cases are checked against the C2 and C4 evidence before being written.
- [ ] No sentence in the doc is a claim this session could not verify from the repo or the cited artifacts;
  anything taken from memory is re-checked against the baseline JSON `tool` block or the report.
- [ ] Roadmap §6 (e) and the pilot doc each gain the link/entry described, and nothing else changes in them.
- [ ] `make knowledge-index-update` ran; `docs/REGISTRY.yaml` regenerated and staged.
- [ ] `git diff --name-only origin/main...HEAD` shows no `tests/`, `src/` or `docs/parity_ledger/` path.

## Related Tickets

- `TCK-20261003-SOCIAL-APPRAISAL-MUTATION-BASELINE` (done; the method was re-derived here)
- `TCK-20261003-SOCIAL-TEST-LOCATE-AND-OWNER-ROUTING` (done; the `guilds.py` reach case)
- Sibling: `TCK-20261003-TEST-ARCH-MAINT-EPIC-B-COST-ROWS-292-302`

## Related Docs

- `docs/testing/social_test_report_2026-10-03.md` (§4 mutation)
- `docs/plans/test_architecture/roadmap.md` §6
- `docs/testing/test_taxonomy.md`

## Related Stored Artifacts

- `agent-working/stored_artifacts/TCK-20261003-SOCIAL-*`

## Related Code Areas

- `tests/mutation/baselines/` (read only)

## Assumptions / Open Questions

- Context scan: `search_docs` MCP failed to connect this session, the graph file is absent in the worktree
  and `tools/knowledge_search.py` needs `sentence-transformers`; the scan is by targeted reads. Disclosed.
- Which doc is "the pilot doc" is found by search at investigation and confirmed to the reviewer in the
  plan; if more than one fits, the plan asks.
- Standard tier: staging set (plan, investigation, test_plan) is created before writing the doc; the plan
  goes to the reviewer first.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

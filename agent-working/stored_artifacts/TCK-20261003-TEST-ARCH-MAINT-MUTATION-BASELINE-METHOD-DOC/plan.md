---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-TEST-ARCH-MAINT-MUTATION-BASELINE-METHOD-DOC
artifact_type: plan
tags: [testing]
---

# Plan — TCK-20261003-TEST-ARCH-MAINT-MUTATION-BASELINE-METHOD-DOC

Approved by test-architecture-reviewer at plan review of `5d2360f2229f1ae50ce9e87147803fdbafa69281`.

## Steps

1. Write `docs/testing/mutation_baseline_method.md` (frontmatter `layer: testing`, `tags: [testing]`, status
   active, authority P2, audience agent). Sections in this order: purpose and non-goals; when to use; the
   procedure (scratch copy by `git archive` at a pinned full SHA; mutmut by `pip --target`; `setsid`-detached
   run; import-based one-hop selection through the existing `tools/test_architecture/mutation_selection.py`,
   with the resolved file list and its sha256; green before mutation; a fresh positive control per new
   target; G3 kernel detection and forcing through an out-of-repo plugin, recording as-found and forced
   values); the record (provenance and `stale_after`, pointing at `src_core_conservation_v3.json` and
   `src_systems_social_appraisal_v1.json` as examples, not copied; separate labelled lists for
   catalog-CONFLICTING lines); the reach-check rule with its two cases; what a baseline is not.
2. Every figure and SHA in the doc is read from the baseline JSONs, the social report or the two closed
   tickets' artifacts in this session; nothing from memory.
3. Roadmap `docs/plans/test_architecture/roadmap.md` §6 watch item (e): add the social baseline path and its
   staleness (about 2026-11-02, or on `TCK-20260822-RELATIONSHIP-VECTOR-ADDITIVE-FIELD` landing).
4. Pilot doc `docs/testing/core_rpg_test_pilot_2026-09-30.md`: one sentence after the paragraph starting
   "**Update 2026-10-01 (v2 baseline).**" linking the method doc. Nothing else changes in that file.
5. `make knowledge-index-update`; stage the regenerated `docs/REGISTRY.yaml`.

## Scope guards

No `tests/`, `src/` or `docs/parity_ledger/` path; no new tool, script or plugin file in the repo; no rerun
of mutation testing; baseline JSON contents referenced, never copied. Gate: `git diff --name-only
origin/main...HEAD` shows no `tests/` path.

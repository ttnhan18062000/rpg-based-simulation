---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260913-PERF-M0-SOURCE-AUDIT
date: 2026-10-02
tags: [performance, architecture]
---

# Plan: TCK-20260913-PERF-M0-SOURCE-AUDIT

## Summary
Docs-only audit. Produce `source_inventory.md` from measured repository state; no `src/`, plan-doc,
or registry edits. Hand-orchestrated (no Workflow opt-in), monitoring recorded at close.

## Steps
1. Context scan (search_docs, graphify, then reads) and re-read the ticket and the roadmap's
   "Plan review, 2026-10-02".
2. Inventory: parse the sources listed in the review §9 and the M0 epic References; measure existence
   (`os.path.exists`), tracked status (`git ls-files`) and registry status (`docs/REGISTRY.yaml`).
3. Durability: record `git ls-files` counts, the introducing commit, and the committed registry
   lines; give C-17 a status from the output.
4. Citations: scan the package for backticked repo paths and report those that do not resolve.
5. Overlap: run the six search queries, locate every ticket named in the ticket, record a
   disposition per ticket without investigating any of them.
6. Write findings for the planner (not applied) and close.

## Scope guards
- Allowed diff paths: `tickets/`, `staging_artifacts/`, `stored_artifacts/`, `docs/REGISTRY.yaml`,
  `agent-monitoring/`.
- The planner's nine uncommitted files are not touched, staged, reverted or reformatted.
- `TCK-20260913-PERF-M0-OWNER-TRIAGE` is not started.

## Acceptance-criteria map
AC1 → inventory §1; AC2 → §2; AC3 → §3; AC4 → artifact path plus the `git status` check.

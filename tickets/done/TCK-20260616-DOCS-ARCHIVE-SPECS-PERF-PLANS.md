---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20260616-DOCS-ARCHIVE-SPECS-PERF-PLANS
phase: done
date: 2026-06-16
tags: [documentation, archive, migration-records]
---

# TCK-20260616-DOCS-ARCHIVE-SPECS-PERF-PLANS

## Title
Consolidate docs/specs/, historical docs/performance/ reports, and one historical docs/plans/ doc into docs/archive/

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Continuation of the same pattern found in TCK-20260616-DOCS-ARCHIVE-HISTORY-LEDGER: several doc subdirectories contain files whose own frontmatter already declares `status: archive` or `status: historical`, but which physically live outside `docs/archive/`. Found while triaging the remaining readability-cleanup scope:
- `docs/specs/` — all 35 files are `status: archive` (and the directory was already excluded from `docs/REGISTRY.yaml` via `tools/generate_registry.py`'s `_SKIP_DOC_SUBDIRS` — confirming it was already treated as archive in function, just not in location).
- `docs/performance/` — 8 of 12 files are `status: historical` (dated point-in-time hardening/perf reports); 3 remain `status: active` (`optimization_architecture.md`, `optimization_invariants.md`, `perf_baseline_policy.md`) and stay in place for the readability rewrite.
- `docs/plans/v2_signal_hardening.md` — the one `status: historical` file among otherwise-active forward-looking plan docs.

## Scope
- Move `docs/specs/*.md` (35 files) → `docs/archive/specs/`
- Move the 8 `status: historical` files from `docs/performance/` → `docs/archive/performance/`
- Move `docs/plans/v2_signal_hardening.md` → `docs/archive/plans/`
- Fix 3 files with stale cross-references to the old `docs/specs/` location: `docs/README.md`, `docs/guidelines/frontmatter_schema.md`, `docs/simulation/belief_and_detour_contract.md`
- Regenerate `docs/REGISTRY.yaml` and run incremental knowledge index update

## Out of Scope
- The remaining `docs/plans/` files (4 active plan docs) — excluded from the readability-rewrite epic entirely (different genre: forward-looking plans that legitimately sequence future phases), but NOT moved to archive since they are current/active references.
- `docs/superpowers/` — a stale reference to a now-nonexistent directory was found in `docs/guidelines/frontmatter_schema.md` and removed, but this predates this ticket's work and isn't otherwise investigated.

## Acceptance Criteria
- `docs/specs/` no longer exists; `docs/archive/specs/` contains all 35 files
- `docs/performance/` retains only the 3 active files; the 8 historical ones live under `docs/archive/performance/`
- `docs/plans/v2_signal_hardening.md` relocated to `docs/archive/plans/`
- No broken references to the old locations
- `docs/REGISTRY.yaml` regenerated; knowledge index updated

## Related Tickets
- TCK-20260616-DOCS-READABILITY-EPIC (parent)
- TCK-20260616-DOCS-ARCHIVE-HISTORY-LEDGER (same pattern, prior step)

## Related Docs
- `docs/README.md`, `docs/guidelines/frontmatter_schema.md`, `docs/simulation/belief_and_detour_contract.md` — reference fixes

## Related Stored Artifacts
None — hotfix tier.

## Related Code Areas
None — documentation-only.

## Assumptions / Open Questions
None outstanding.

## Implementation Notes
Used frontmatter `status` field as the deciding signal rather than guessing from filenames/content, consistent with how `docs/engine/history` and `docs/engine/ledger` were triaged.

## Test Summary
Not applicable. Verified via `make docs-registry` (doc count dropped from 247 to 238 — consistent with `docs/performance` losing 8 entries; `docs/specs` was already excluded from the registry so its move had no registry-count effect) and `make knowledge-index-update` (46 files deleted from index matching the 8 performance + the previously-uncounted specs files now fully out of the searchable tree, 3 files re-embedded for the reference fixes).

## Files Changed
- Moved: `docs/specs/*.md` (35 files) → `docs/archive/specs/`
- Moved: 8 `docs/performance/*.md` files → `docs/archive/performance/`
- Moved: `docs/plans/v2_signal_hardening.md` → `docs/archive/plans/`
- Edited: `docs/README.md`, `docs/guidelines/frontmatter_schema.md`, `docs/simulation/belief_and_detour_contract.md`

## Completion Summary
Consolidated 44 more mislabeled-location historical/archive-status docs into `docs/archive/`, fixed all affected cross-references, and regenerated the registry/index. Combined with the prior history/ledger move, this removes 108 files from the readability-rewrite scope, bringing the true remaining target down to 129 files (133 still-flagged minus 4 `docs/plans/` files intentionally excluded as a different genre).

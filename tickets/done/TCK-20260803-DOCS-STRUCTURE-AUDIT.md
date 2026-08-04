---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260803-DOCS-STRUCTURE-AUDIT
phase: done
date: 2026-08-03
tags: [documentation, registry]
---

# TCK-20260803-DOCS-STRUCTURE-AUDIT

## Title
Audit high-level docs/ directory structure and verify generate_registry.py's _SKIP_DOC_SUBDIRS accuracy

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Audit the HIGH-LEVEL structure of the `docs/` directory tree — folder names, file counts per
folder, whether folders are empty/orphaned/dead — and verify whether
`tools/generate_registry.py`'s `_SKIP_DOC_SUBDIRS = {"archive", "parity_ledger", "scenarios",
"entity"}` constant (line 42) still accurately reflects which top-level `docs/` subfolders should
be excluded from registry indexing. This is a prerequisite for a separate, not-yet-scoped
follow-up ticket that will design a new "doc-updater" agent for `implement-ticket.js`'s pipeline —
that follow-up needs a verified-accurate map of `docs/`'s live structure before it can define
per-folder rules.

This ticket is explicitly scoped to **structure/naming/existence questions only**. It does not
audit the prose content, accuracy, or freshness of what's written inside individual documents.

## Scope
- Enumerate every top-level `docs/` subfolder on disk (confirmed 26 at scoping time: agent-monitoring, ai, architecture, archive, audits, cognition, combat, compliance, content, core, engine, entity, guidelines, guides, mechanics, observability, parity_ledger, performance, plans, scenarios, simulation, simulation_quality, strategy, systems, testing, world) and record, per folder: file count (recursive, not just top-level), whether it's empty/near-empty, and whether it contains any obviously dead/orphaned content (e.g. a stray file with no clear purpose, an empty subdirectory).
- Verify `_SKIP_DOC_SUBDIRS`'s 4 entries (`archive`, `parity_ledger`, `scenarios`, `entity`) against actual on-disk content and against `collect_docs()`'s behavior (`tools/generate_registry.py:186-205`, which only globs `*.md` files via `docs_dir.rglob("*.md")`):
  - `archive` (146 files) and `parity_ledger` (10 files) are already confirmed correct/out of question at scoping time — re-verify only, do not re-litigate.
  - `scenarios/` and `entity/` were assumed empty (0 files) at scoping time but are **not** — `docs/scenarios/phase1/` contains 5 `.yaml` files and `docs/entity/` contains 1 `.mmd` file (`entity_aspect_relationship_diagram.mmd`). Neither is a `.md` file, so both are already excluded from the registry by `collect_docs()`'s `*.md`-only glob regardless of `_SKIP_DOC_SUBDIRS` membership — determine whether the skip-list entries for `scenarios`/`entity` are therefore redundant no-ops, and if so, whether to keep them (documented forward-compatibility, following the precedent set by `TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES`'s regression test) or remove them.
- Do a quick reference check (not a content audit) for whether `docs/scenarios/phase1/*.yaml` and `docs/entity/entity_aspect_relationship_diagram.mmd` are actively used/referenced elsewhere in the repo (tests, tooling, other docs) before concluding either is dead.
- Fix anything clearly broken within this narrow scope: remove truly-dead empty folders if safe, correct `_SKIP_DOC_SUBDIRS` drift (additions, removals, or documenting-in-place why an inert entry is intentionally retained).
- If `_SKIP_DOC_SUBDIRS` changes, update `tests/tools/test_generate_registry.py`'s existing regression test (`test_skip_doc_subdirs_exist_on_disk`, added by `TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES`) to match.
- Reconcile the folder-count discrepancy noted in this ticket's Assumptions section as part of the audit's findings.

## Out of Scope
- Prose content accuracy, staleness, or correctness review of any individual document's body text — a separate, future, separately-scoped ticket's job.
- Designing or building the "doc-updater" agent itself — a separate follow-up ticket that this audit unblocks, not part of this ticket.
- Any change to `docs/archive/`'s or `docs/parity_ledger/`'s exclusion status — both already confirmed correct at scoping time, not in question here.
- Changing `collect_docs()`'s file-type filtering behavior (the `*.md`-only `rglob`) itself — observing that it interacts with `_SKIP_DOC_SUBDIRS` is in scope; widening it to index `.yaml`/`.mmd`/other file types is a separate, larger decision and out of scope.
- `TCK-20260802-DOC-UPDATE-DISCIPLINE` / `TCK-20260802-DOC-COVERAGE-CHECK`'s doc-update-obligation workflow mechanism — related but already-closed, separate concern.
- Renaming or restructuring any `docs/` subfolder beyond removing a folder confirmed fully dead.

## Acceptance Criteria
- [x] Investigation artifact records file count (recursive) and dead/orphaned status for all 26 top-level `docs/` subfolders. See `investigation.md`'s per-folder table.
- [x] For `docs/scenarios/` and `docs/entity/`: findings explicitly state (a) actual file contents (5 `.yaml` under `phase1/`; 1 `.mmd` respectively), (b) whether either is referenced/used elsewhere in the repo, and (c) whether their `_SKIP_DOC_SUBDIRS` membership is being kept or removed, with rationale. Both confirmed actively referenced; both kept.
- [x] Any `docs/` subfolder confirmed to be genuinely dead (zero files at any depth, no active references) is removed via `git rm`, preserving history; if none qualify, the ticket states that explicitly rather than silently doing nothing. **No folder qualified.** `find docs -type d -empty` returned zero results at any depth; all 26 top-level subfolders are real and populated. This is stated explicitly as the deliberate outcome of a clean audit, not a failure to find something.
- [x] `_SKIP_DOC_SUBDIRS` in `tools/generate_registry.py` reflects the audit's conclusions (unchanged is an acceptable outcome if the audit finds no drift, but that finding must be stated explicitly, not assumed). **Set membership unchanged** (`archive`, `parity_ledger`, `scenarios`, `entity` — all four confirmed accurate); an expanded comment block now documents the per-entry rationale in-code, stated explicitly here.
- [x] If `_SKIP_DOC_SUBDIRS` changes, `tests/tools/test_generate_registry.py::test_skip_doc_subdirs_exist_on_disk` (or a successor test) is updated and passing. Not applicable — set membership did not change. `test_skip_doc_subdirs_exist_on_disk` remains unchanged and passing; a new successor guard test (`test_skip_doc_subdirs_inert_entries_documented`) was added as a bonus regression check on the new comment documentation.
- [x] `.venv/bin/python3 -m pytest tests/tools/test_generate_registry.py -q` passes after any change. Confirmed: 51 passed (run with `-v`, see Test Summary).
- [x] No individual document's prose body content is modified as part of this ticket. Confirmed — no `docs/*.md` file appears in the changeset; only `tools/generate_registry.py` (comment), `tests/tools/test_generate_registry.py` (new test), and this ticket file were touched.

## Related Tickets
- TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES — direct precedent: previously pruned dead `superpowers`/`specs` entries from this same `_SKIP_DOC_SUBDIRS` constant and added the `test_skip_doc_subdirs_exist_on_disk` regression test this ticket may need to extend.
- TCK-20260514-DOCS-REORG — established the current `docs/` nested hierarchy this audit is verifying.
- TCK-20260606-DOCSITE-FM-ARCHIVE — applied minimal frontmatter to `docs/archive/`, confirming its historical-record status (baseline, not reopened here).
- TCK-20260802-DOC-UPDATE-DISCIPLINE / TCK-20260802-DOC-COVERAGE-CHECK — related doc-tooling infrastructure (doc-update obligations in Investigate/Implement), not overlapping this ticket's structural-audit scope, but useful context for the future doc-updater agent ticket this audit unblocks.

## Related Docs
- `docs/ai/README.md` (Doc Registry Integration section) — documents the `docs/REGISTRY.yaml` convention this audit checks compliance against.
- `docs/REGISTRY.yaml` — the generated artifact whose inputs this audit is verifying.
- `docs/parity_ledger/infrastructure.yaml` — INFRA-183 (`generate_registry.py`'s output shape) and INFRA-264 (CI drift-detection backstop via `--check`); update `v2_evidence`/re-verify only if `_SKIP_DOC_SUBDIRS` actually changes.

## Related Stored Artifacts
None found covering a full-tree structural audit of `docs/`. `TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES` is the closest precedent but was hotfix-tier with no staging artifacts.

## Related Code Areas
- `tools/generate_registry.py` (`_SKIP_DOC_SUBDIRS` at line 42, `collect_docs()` at lines 186-230)
- `tests/tools/test_generate_registry.py` (existing skip-subdir coverage: `test_doc_entry_skips_archive_subdir`, `test_doc_entry_skips_parity_ledger_subdir`, `test_skip_doc_subdirs_exist_on_disk`)
- `docs/` (all 26 top-level subfolders; `docs/scenarios/` and `docs/entity/` specifically)
- `docs/ai/README.md`

## Assumptions / Open Questions
- The request's "known facts" stated docs/ has 24 top-level subdirectories, but the enumerated name list actually contains 26 names, matching the on-disk count verified during scoping (26). The Investigate phase should treat 26 as ground truth and simply note the discrepancy in the original count as resolved.
- `docs/scenarios/` and `docs/entity/` are **not** empty as originally assumed — `docs/scenarios/phase1/` holds 5 `.yaml` scenario-config files and `docs/entity/` holds 1 `.mmd` diagram file. Neither is currently indexed by `collect_docs()` regardless of `_SKIP_DOC_SUBDIRS` membership, since that function only globs `*.md`. Whether these files are still actively used (by tests, an eval harness, or another doc) is unverified and must be checked in Investigate before any deletion decision.
- Layer chosen as `guidelines` (registered, "Cross-cutting process/convention docs") following the precedent of `TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES`, which used the same layer for the same code area (`_SKIP_DOC_SUBDIRS` in `tools/generate_registry.py`). If Investigate finds `observability` (doc-registry tooling correctness) is a better fit, that's a low-cost revision, not a scope-invalidating one.
- Assumes changes to `_SKIP_DOC_SUBDIRS`, if any, are low-risk: because `collect_docs()` only indexes `.md` files, removing `scenarios`/`entity` from the skip set would currently be a behavior no-op given their actual file contents — the entries only matter as forward-compatibility documentation (same rationale the prior ticket used to justify keeping entries that are "explicitly documented in-code as intentionally forward-compatible/retained").
- If any folder is found to warrant deletion, this ticket assumes `git rm` (preserving history) is sufficient and no additional migration/redirect work is needed — if a folder turns out to be referenced by tooling/CI paths, that would invalidate this assumption and require scope expansion.

## Implementation Notes
The audit's bottom line: the `docs/` structure is healthy. All 26 top-level subfolders are
real and populated (`find docs -type d -empty` returns zero results at any depth). No folder
qualifies for deletion. `_SKIP_DOC_SUBDIRS`'s four entries (`archive`, `parity_ledger`,
`scenarios`, `entity`) were re-verified accurate; its set membership was **not changed** —
`archive`/`parity_ledger` are load-bearing real exclusions, and `scenarios`/`entity` are
currently-inert no-ops (zero `.md` files; `collect_docs()` only globs `*.md`) retained because
their non-`.md` content is actively referenced elsewhere (`docs/scenarios/phase1/*.yaml` by
`tests/unit/strategic/test_scenario_runner.py`; `docs/entity/*.mmd` by
`docs/strategy/world_capability_design.md` and `docs/guides/diagram_index.md`). This
conclusion is now recorded directly in an expanded comment block above `_SKIP_DOC_SUBDIRS` in
`tools/generate_registry.py`, backed by a new regression test
(`test_skip_doc_subdirs_inert_entries_documented`) that fails if that documentation is ever
removed. See `investigation.md`'s per-folder table for full per-folder detail (file counts,
non-`.md` file inventory, reference checks).

**Follow-up recommendation (not actioned in this ticket):** a future hotfix-tier ticket should
remove the dead `"superpowers"`/`"specs"` branches from `detect_content_type()` in
`tools/validate_frontmatter.py` (around line 123-127). `docs/specs/` and `docs/superpowers/`
no longer exist as top-level `docs/` subfolders — both were consolidated into
`docs/archive/specs/` by `TCK-20260616-DOCS-ARCHIVE-SPECS-PERF-PLANS` — and files under
`docs/archive/specs/` already classify correctly via the `"archive"` branch, so those two
branches are unreachable dead code. Direct precedent: `TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES`,
which removed the equivalent dead path-segment entries from the sibling tool
`generate_registry.py`'s `_SKIP_DOC_SUBDIRS`. No ticket file was created for this
recommendation in this pass — it is recorded here only, per this ticket's plan.

## Test Summary
`.venv/bin/python3 -m pytest tests/tools/test_generate_registry.py -v` — all tests pass,
including the new `test_skip_doc_subdirs_inert_entries_documented` and the pre-existing
`test_skip_doc_subdirs_exist_on_disk`, `test_registry_exits_zero_on_real_docs_tree`, and
`test_check_flag_detects_no_drift_against_real_registry` (both of which run against the real
`docs/` tree and would catch any accidental structural drift from this ticket's changes).

## Files Changed
- `tools/generate_registry.py` — comment-only change: expanded the comment block above
  `_SKIP_DOC_SUBDIRS` to document the audit's per-entry rationale and cite this ticket. No
  change to `_SKIP_DOC_SUBDIRS`'s set membership or to `collect_docs()`.
- `tests/tools/test_generate_registry.py` — added
  `test_skip_doc_subdirs_inert_entries_documented` to `TestRealDocsTree`, a regression guard
  asserting the comment block adjacent to `_SKIP_DOC_SUBDIRS` documents the `scenarios`/
  `entity` rationale.

## Completion Summary
No structural changes to `docs/` or to `_SKIP_DOC_SUBDIRS`'s membership were made — the audit
confirmed the existing structure and skip-list are accurate. This is the deliberate, correct
outcome of a clean audit, not a failure to find something. All 26 top-level `docs/` subfolders
were confirmed real and populated; no folder qualified for deletion; `_SKIP_DOC_SUBDIRS`'s two
currently-inert entries (`scenarios`, `entity`) were confirmed to hold actively-referenced
non-`.md` content and were kept, now with an in-code rationale comment and a regression test
guarding it. One adjacent finding (dead `"superpowers"`/`"specs"` branches in
`tools/validate_frontmatter.py`) was recorded as a follow-up recommendation for a future
hotfix-tier ticket, not actioned here. No `docs/*.md` file's prose content was modified.


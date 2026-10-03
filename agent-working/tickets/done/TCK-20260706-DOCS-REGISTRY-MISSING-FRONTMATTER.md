---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER
phase: done
date: 2026-07-06
tags: [documentation, registry, frontmatter, tagging]
---

# TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER

## Title
`make docs-registry` exits non-zero: 12 docs lack YAML frontmatter entirely

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
While implementing `TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC` (adding a new doc under
`docs/simulation_quality/`), running `make docs-registry` to pick up the new file surfaced a
pre-existing, repo-wide issue: 12 doc files under `docs/` have no YAML frontmatter block at all
(confirmed by direct inspection — e.g. `docs/simulation_quality/eval_matrix_results.md` and
`docs/engine/project_lawbook_m10.md` both start directly with a markdown `#` heading, no `---`
block). `tools/generate_registry.py` treats this as a hard error and exits 1, even though it still
successfully writes `docs/REGISTRY.yaml` with defaults substituted for the affected files — meaning
`make docs-registry` can never exit 0 cleanly today, for anyone, regardless of what they're working
on.

Affected files (from the current run's error output):
```
docs/engine/engineering_playbook_m10.md
docs/engine/legacy_replacement_ledger.md
docs/engine/phase12_entry_package.md
docs/engine/phase13_retirement_manifest.md
docs/engine/project_lawbook_m10.md
docs/engine/supported_progression_surface_phase5.md
docs/mechanics/content_usage_matrix.md
docs/simulation/domains/party_contract.md
docs/simulation_quality/eval_matrix_results.md
docs/simulation_quality/event_type_coverage.md
docs/systems/faction_contract.md
docs/world/demographics_contract.md
```

Confirmed this is pre-existing and unrelated to `TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC`'s own work
(that ticket's new doc, `docs/simulation_quality/corpus_tier_taxonomy.md`, has correct frontmatter
and is indexed successfully in the regenerated registry).

## Scope
- Add a minimal, correct YAML frontmatter block (`status`, `layer`, `authority`, `audience`, `tags`)
  to all 12 listed files, following the existing pattern used by sibling docs in the same
  directories (e.g. `docs/simulation_quality/quality_scoring_contract.md`'s frontmatter as a
  template for the two `docs/simulation_quality/` files).
- Confirm `make docs-registry` exits 0 after the fix.
- Spot-check whether any of these 12 files are themselves stale/superseded (several look like
  milestone-era artifacts — `phase12_entry_package.md`, `phase13_retirement_manifest.md`,
  `legacy_replacement_ledger.md`) — if a file is confirmed genuinely obsolete, archiving it (per
  existing `docs/archive/` convention) is an acceptable alternative to adding frontmatter, but this
  requires confirming obsolescence first, not assuming it.

## Out of Scope
- Re-litigating `TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC`'s already-completed work
- Content changes to any of the 12 files beyond adding/correcting frontmatter (or archiving, per the
  Scope item above)
- Auditing docs beyond this specific 12-file list (a broader frontmatter audit across all of
  `docs/` is a larger, separate initiative if ever warranted)

## Acceptance Criteria
- [ ] All 12 listed files have valid, correct YAML frontmatter (or are confirmed obsolete and moved
      to `docs/archive/` instead)
- [ ] `make docs-registry` exits 0
- [ ] `python3 tools/validate_frontmatter.py <each file> --content-type doc` passes for every file
      still under `docs/` after this ticket

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC — the ticket during which this pre-existing gap was
  discovered (unrelated to that ticket's own scope)
- TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC — parent epic; relocated into
  `tickets/todos/simq-deep-coverage/` as an independent housekeeping child with no subject-matter
  overlap with the epic's long-run-coverage/pillar-completeness threads (docs registry hygiene, not
  SimQ corpus/pillar work); sequenced to run in parallel per that folder's `SEQUENCE.md`

## Related Docs
(the 12 files listed above)

## Related Stored Artifacts
(none — discovered during another ticket's implementation, not its own investigation)

## Related Code Areas
- `tools/generate_registry.py` — the script that currently treats missing frontmatter as a hard
  error

## Assumptions / Open Questions
- UQ-1: Whether `tools/generate_registry.py`'s hard-error behavior itself should change (e.g. warn
  and continue with exit 0, vs. requiring every doc to have frontmatter) is a separate process
  design question from just fixing these 12 files — this ticket assumes the current hard-error
  behavior is correct and the files should conform to it, not that the tool should be relaxed.

## Implementation Notes
Followed `staging_artifacts/TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER/plan.md` Steps 1-6 exactly.

- Steps 1-4: Prepended per-file-derived YAML frontmatter blocks to all 12 listed files (no body/heading
  changes). Group A (6 `docs/engine/*.md` files) got `status: active / layer: engine / authority: P1 /
  audience: developer`, matching sibling `kernel.md`/`architecture.md`/`known_limitations.md` exactly.
  `content_usage_matrix.md` got `status: active / layer: mechanics / authority: P1 / audience:
  developer` (not `authoritative` — it self-describes as "generated dynamically" with no honest
  verification date). `faction_contract.md` got `status: authoritative` + `last_verified: 2026-06-23`
  transcribed verbatim from its own `**Status**: AUTHORITATIVE ... Last verified: 2026-06-23.` line.
  `demographics_contract.md` got `status: authoritative` + `last_verified: 2026-07-02` (git-log-last-
  modified date, no in-body date existed) + its own self-declared `tags:` list transcribed verbatim.
  `party_contract.md` got `layer: simulation` (its own inline `**Layer:** social` claim is invalid
  against `LAYER_VALUES` and was corrected in frontmatter only — the inline body text was left
  untouched, matching the plan). `event_type_coverage.md` got `status: authoritative` + `last_verified:
  2026-07-04` from its own `**Last updated:**` line. `eval_matrix_results.md` got `status: active` (no
  self-declared certification claim, analogous to `content_usage_matrix.md`).
- Step 5: Added `TestPreviouslyFrontmatterMissingDocs::test_all_previously_frontmatter_missing_docs_now_pass_validation`
  to `tests/tools/test_validate_frontmatter.py` as a `pytest.mark.parametrize`d test over the 12 explicit
  paths (each path gets its own test-case ID and failure message, rather than a single test with an
  internal loop — a stronger regression pin than the plan's literal "iterates... asserts" phrasing
  implied, still fully satisfying the intent). Added `TestRealDocsTree::test_registry_exits_zero_on_real_docs_tree`
  to `tests/tools/test_generate_registry.py`, invoking `generate_registry()` against the real repo root
  (`Path(__file__).resolve().parents[2]`) with output written to `tmp_path` so `docs/REGISTRY.yaml`
  is never touched by the test itself.
- Step 6: Ran `python3 tools/generate_registry.py` (the `make docs-registry` target) — exit code 0,
  wrote 1326 entries, all 12 previously-absent files now present in `docs/REGISTRY.yaml` (confirmed via
  grep for each of the 12 `path:` values). Ran all 12 per-file `validate_frontmatter.py --content-type
  doc` invocations individually — all pass. Ran the full scoped suite (`tests/tools/test_generate_registry.py
  tests/tools/test_validate_frontmatter.py tests/docs/ tests/integrity/test_doc_guards.py
  tests/integrity/test_manifest_guards.py -m "not slow"`) — 143 passed, 2 skipped (pre-existing,
  unrelated), 0 failed.
- `docs/simulation/domains/social_memory_contract.md` was not touched (confirmed via `git diff --stat`
  showing no changes to that path) — its pre-existing `layer: social` validation failure remains
  out of scope, as required by the plan's Scope Guards.
- No code changes were made to `tools/generate_registry.py` or `tools/validate_frontmatter.py`.

## Test Summary
- `pytest tests/docs/test_doc_integrity.py::test_manifest_file_existence
  tests/docs/test_doc_integrity.py::test_document_structural_compliance
  tests/integrity/test_doc_guards.py::test_mandatory_doc_existence
  tests/integrity/test_doc_guards.py::test_doc_header_compliance
  tests/docs/test_contributor_guardrails.py::test_extension_templates_present
  tests/docs/test_contributor_guardrails.py::test_forbidden_terminology -m "not slow"` — 6 passed.
- `pytest tests/tools/test_generate_registry.py tests/tools/test_validate_frontmatter.py -m "not slow"`
  — 123 passed (includes both new regression-guard tests).
- Final gate: `pytest tests/tools/test_generate_registry.py tests/tools/test_validate_frontmatter.py
  tests/docs/ tests/integrity/test_doc_guards.py tests/integrity/test_manifest_guards.py -m "not slow"
  --tb=short` — 143 passed, 2 skipped, 0 failed.
- 12 explicit `python3 tools/validate_frontmatter.py <file> --content-type doc` invocations — all `OK:
  1 file(s) checked — no violations`.
- `python3 tools/generate_registry.py` — exit code 0 (AC #2); all 12 files confirmed present in
  regenerated `docs/REGISTRY.yaml`.

## Files Changed
- `docs/engine/legacy_replacement_ledger.md` — added frontmatter
- `docs/engine/phase12_entry_package.md` — added frontmatter
- `docs/engine/phase13_retirement_manifest.md` — added frontmatter
- `docs/engine/engineering_playbook_m10.md` — added frontmatter
- `docs/engine/project_lawbook_m10.md` — added frontmatter
- `docs/engine/supported_progression_surface_phase5.md` — added frontmatter
- `docs/mechanics/content_usage_matrix.md` — added frontmatter
- `docs/systems/faction_contract.md` — added frontmatter
- `docs/world/demographics_contract.md` — added frontmatter
- `docs/simulation/domains/party_contract.md` — added frontmatter
- `docs/simulation_quality/event_type_coverage.md` — added frontmatter
- `docs/simulation_quality/eval_matrix_results.md` — added frontmatter
- `tests/tools/test_generate_registry.py` — added `test_registry_exits_zero_on_real_docs_tree`
- `tests/tools/test_validate_frontmatter.py` — added
  `test_all_previously_frontmatter_missing_docs_now_pass_validation` (parametrized over the 12 files)
- `docs/REGISTRY.yaml` — regenerated via `make docs-registry` equivalent (now includes all 12
  previously-absent entries)

## Completion Summary
Added YAML frontmatter (`status`, `layer`, `authority`, `audience`, `tags`/`last_verified` as
applicable) to all 12 previously-frontmatterless docs listed in scope, following each file's own
sibling-directory pattern and any self-declared status/date claims already present in the body
text. No files were archived — none were confirmed obsolete on inspection. `make docs-registry`
(`tools/generate_registry.py`) now exits 0 and `docs/REGISTRY.yaml` was regenerated with all 12
files present. Two regression tests were added
(`tests/tools/test_validate_frontmatter.py::TestPreviouslyFrontmatterMissingDocs` and
`tests/tools/test_generate_registry.py::TestRealDocsTree::test_registry_exits_zero_on_real_docs_tree`)
to pin this fix against future regressions. Full scoped test suite: 143 passed, 2 pre-existing
unrelated skips, 0 failed. `make knowledge-index-update` was run after the docs/ edits to keep the
agent context search index current, and `data/runs/` was cleaned per the Definition of Done. All
13 DoD conditions verified READY_TO_CLOSE by done-checker.

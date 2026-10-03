---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER
artifact_type: test_plan
tags: [documentation, registry, frontmatter, tagging]
---

# Test Plan — TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER

## Regression Surface

This is a doc-content-only change (frontmatter blocks added to 12 existing `docs/` files, no source
code changes expected). Regression surface is entirely the doc-integrity/tooling test suites — no
`tests/unit/`, `tests/integration/`, or arena-combat suites are implicated.

**Unit (tooling):**
- `tests/tools/test_generate_registry.py` — entirely `tmp_path`-synthetic (confirmed by reading all
  ~40 test methods); real `docs/` content changes cannot break these, but they must still pass
  unmodified (guards `collect_docs`, `collect_tickets`, `sort_entries`, YAML output shape).
- `tests/tools/test_validate_frontmatter.py` — guards the schema enum constants
  (`STATUS_VALUES`/`LAYER_VALUES`/`AUTHORITY_VALUES`/`AUDIENCE_VALUES`) that the new frontmatter blocks
  must conform to. Also synthetic/unit-scoped, but any new "layer" or "status" value used in the 12
  files that isn't already in these enums will make `validate_frontmatter.py` fail against the real
  files (see New Tests Required below for the real-file check).

**Integration (doc structure / manifest):**
- `tests/docs/test_doc_integrity.py::test_manifest_file_existence` — asserts the 6 Group A
  `docs/engine/` mandatory files still exist at their current paths. Frontmatter addition must not
  move/rename any of the 6.
- `tests/docs/test_doc_integrity.py::test_document_structural_compliance` — asserts each mandatory
  doc's `required_headers` (from `manifest.json`) still appear as `## ` headings. Frontmatter insertion
  before the first `# ` heading is safe (confirmed: the header regex is `^##\s+...`, MULTILINE, doesn't
  match YAML), but this test is the actual proof — must pass after edits, not just be assumed safe.
- `tests/docs/test_doc_integrity.py::test_terminology_alignment` — unaffected by this ticket (no enum
  changes), included for completeness of the scoped run.
- `tests/docs/test_contributor_guardrails.py::test_forbidden_terminology` — scans all `docs/engine/*.md`
  (lowercased) for forbidden terms (`manifest.json`'s `forbidden_terms` list). New frontmatter fields
  (`status: active`, `tags: [...]`, etc.) must not accidentally contain a forbidden substring — verified
  the forbidden list (`'universal performance'`, `'maximum speed'`, `'unlimited scaling'`,
  `'world-class throughput'`, `'fastest engine'`, `'guaranteed performance'`, `'production ready for all
  environments'`, `'best engine in the world'`) has no overlap with any planned frontmatter value, but
  the test itself is the real gate.
- `tests/docs/test_contributor_guardrails.py::test_extension_templates_present` — reads
  `docs/engine/engineering_playbook_m10.md` directly and asserts 3 exact substrings
  (`"## Extension Templates"`, `"### Runtime Profile Template"`, `"### Certification Scenario
  Template"`) are present. Must not be touched by the frontmatter edit to that file.
- `tests/integrity/test_doc_guards.py::test_mandatory_doc_existence` — same manifest-existence check as
  above, from the `integrity` suite (separate module, same guarantee).
- `tests/integrity/test_doc_guards.py::test_doc_header_compliance` — same header-compliance check as
  `test_document_structural_compliance`, separate module.
- `tests/integrity/test_doc_guards.py::test_no_broken_internal_links` — verifies no internal `docs/`
  markdown links are broken; frontmatter insertion doesn't alter any link, but any file path/rename
  drift introduced by mistake would trip this.
- `tests/integrity/test_manifest_guards.py::test_governance_enum_sync`,
  `::test_certification_enum_sync`, `::test_scenario_registration_integrity`,
  `::test_forbidden_terminology_guard` — unrelated to frontmatter but part of the same manifest-backed
  suite; run together for a clean pass/fail signal on `docs/engine/manifest.json` consumers.

## New Tests Required

The ticket's Acceptance Criteria are process/gate checks (exit codes, validator pass/fail), not new
simulation behavior — so "new tests" here means **regression-guard scripts/assertions that pin the
now-fixed state**, added under the existing tooling test files rather than new standalone test files
(consistent with how `test_generate_registry.py` already has a
`test_registry_exits_nonzero_on_missing_doc_frontmatter` synthetic guard for the opposite case).

1. **Test name:** `test_registry_exits_zero_on_real_docs_tree` (or equivalent naming already used in
   the file)
   **Category:** integration (subprocess/real-filesystem, not `tmp_path`-synthetic)
   **What it verifies:** running `python3 tools/generate_registry.py` (or invoking
   `generate_registry(Path("."), <tmp output>)` against the real repo root) returns exit code `0` —
   i.e., pins AC #2 as a regression guard so a future doc addition without frontmatter is caught in CI
   rather than only discovered manually, as this ticket's origin ticket
   (`TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC`) demonstrates can otherwise slip through silently.
   **Where it lives:** `tests/tools/test_generate_registry.py` (new test class or function using the
   real project root, writing output to a `tmp_path` so the real `docs/REGISTRY.yaml` isn't touched by
   the test run).

2. **Test name:** `test_all_previously_frontmatter_missing_docs_now_pass_validation`
   **Category:** integration
   **What it verifies:** iterates the 12 specific paths from the ticket and asserts
   `validate_file(path, content_type_override="doc", registry=None)` returns `[]` for each — a named,
   explicit regression pin (rather than relying only on the directory-wide
   `test_no_broken_internal_links`-style sweep) so a future refactor that regresses one of these 12
   specifically fails loudly with the file name in the assertion message.
   **Where it lives:** `tests/tools/test_validate_frontmatter.py` (new test function; import
   `validate_file` from `tools.validate_frontmatter`, matching existing import patterns in that file).

3. **Test name:** `test_group_a_docs_still_pass_manifest_mandatory_checks` — likely **not needed as a
   new test** since `test_mandatory_doc_existence` and `test_document_structural_compliance` /
   `test_doc_header_compliance` already cover this for the 6 Group A files unconditionally. Listed here
   only to confirm during implementation that these existing tests are re-run and pass, not to write a
   duplicate.

4. **Optional/if archiving is chosen for any file** (only if investigation's "archive none" conclusion
   is overridden after human review): a test verifying `docs/engine/manifest.json` no longer lists the
   archived path AND the corresponding `docs/archive/` destination has correct `archive` content-type
   frontmatter (`status: archive`, `layer`, `original_date` per `_validate_archive`,
   `validate_frontmatter.py:223-233`). Not expected to be needed per this investigation's findings, but
   documented here so the implementer doesn't skip it if scope changes.

## Scoped Pytest Commands

```bash
# Doc-tooling unit tests (registry generation + frontmatter validation)
pytest tests/tools/test_generate_registry.py tests/tools/test_validate_frontmatter.py -m "not slow"

# Doc-integrity / manifest-contract integration tests
pytest tests/docs/ tests/integrity/test_doc_guards.py tests/integrity/test_manifest_guards.py -m "not slow"

# Full scoped run for this ticket (recommended single command for final verification)
pytest tests/tools/test_generate_registry.py tests/tools/test_validate_frontmatter.py tests/docs/ tests/integrity/test_doc_guards.py tests/integrity/test_manifest_guards.py -m "not slow" --tb=short
```

Plus the two direct AC-verification commands (not pytest, but required by the ticket's own Acceptance
Criteria and must be run and their output captured in the ticket's Test Summary):

```bash
make docs-registry   # must exit 0
python3 tools/validate_frontmatter.py docs/engine/engineering_playbook_m10.md --content-type doc
python3 tools/validate_frontmatter.py docs/engine/legacy_replacement_ledger.md --content-type doc
python3 tools/validate_frontmatter.py docs/engine/phase12_entry_package.md --content-type doc
python3 tools/validate_frontmatter.py docs/engine/phase13_retirement_manifest.md --content-type doc
python3 tools/validate_frontmatter.py docs/engine/project_lawbook_m10.md --content-type doc
python3 tools/validate_frontmatter.py docs/engine/supported_progression_surface_phase5.md --content-type doc
python3 tools/validate_frontmatter.py docs/mechanics/content_usage_matrix.md --content-type doc
python3 tools/validate_frontmatter.py docs/simulation/domains/party_contract.md --content-type doc
python3 tools/validate_frontmatter.py docs/simulation_quality/eval_matrix_results.md --content-type doc
python3 tools/validate_frontmatter.py docs/simulation_quality/event_type_coverage.md --content-type doc
python3 tools/validate_frontmatter.py docs/systems/faction_contract.md --content-type doc
python3 tools/validate_frontmatter.py docs/world/demographics_contract.md --content-type doc
```

Do **not** run `python3 tools/validate_frontmatter.py docs/` (whole-tree) as the AC-passing claim —
per the investigation's Risk #1, `docs/simulation/domains/social_memory_contract.md` (outside this
ticket's 12-file scope) already fails whole-tree validation today with a pre-existing `layer: social`
violation; a whole-tree run will report a failure that is not this ticket's to fix, and would produce a
misleading "AC #3 failed" signal. Run the 12 explicit per-file commands above instead, matching AC #3's
literal per-file wording.

## Anti-Drift Test Guards

- **`test_forbidden_terminology` scans all of `docs/engine/*.md`, not just the 6 Group A files** — this
  is a built-in guard against any of the new frontmatter blocks (or the implementer accidentally editing
  body text) introducing a forbidden term. No new test needed; just ensure it's in the scoped run.
- **`test_document_structural_compliance`/`test_doc_header_compliance` guard against accidental header
  rewording** — if the implementer "cleans up" a file's headings while adding frontmatter (out of
  scope per the ticket's "Content changes... beyond adding/correcting frontmatter" restriction), these
  tests catch it immediately.
- **The synthetic `tests/tools/test_generate_registry.py` suite must keep passing unmodified** — if an
  implementer is tempted to "fix" `collect_docs()`'s error-vs-warning asymmetry (docs hard-error,
  tickets soft-warn) as part of this ticket, `test_ticket_missing_frontmatter_emits_warning_not_error`
  and `test_registry_exits_nonzero_on_missing_doc_frontmatter` would both need to change — that is
  explicitly out of scope (ticket's UQ-1: assume current hard-error behavior is correct). Any diff to
  `tools/generate_registry.py` itself in this ticket's changeset is a signal of scope creep.
- **A future doc added under `docs/` without frontmatter should still trip `make docs-registry`** —
  the new `test_registry_exits_zero_on_real_docs_tree` test (New Tests Required #1) only pins the
  *current* clean state; it does not by itself prevent regression on a *newly added* file lacking
  frontmatter (that protection already exists via the hard-error path in `collect_docs()`/
  `generate_registry()`, unchanged by this ticket) — listed here so implementers don't mistake the new
  test as a substitute for that existing enforcement.
- **`docs/REGISTRY.yaml` regeneration is not itself a "test" but must be re-run and committed** at the
  end of implementation (per the Definition of Done's "no known material gap left unstated") — if the
  implementer forgets, `make docs-registry`'s AC-required "exits 0" will pass locally but
  `docs/REGISTRY.yaml` in the commit will still show the 12 files as absent (stale registry state),
  silently reintroducing the exact discovery gap that motivated this ticket
  (`TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC` found this because the registry didn't reflect a new file).

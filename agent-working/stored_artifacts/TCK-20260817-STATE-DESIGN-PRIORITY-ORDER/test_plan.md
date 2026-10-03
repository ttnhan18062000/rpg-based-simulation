---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260817-STATE-DESIGN-PRIORITY-ORDER
artifact_type: test_plan
tags: [documentation, architecture]
---

# Test Plan — TCK-20260817-STATE-DESIGN-PRIORITY-ORDER

## Regression Surface

Documentation-only change (no `src/` edits expected) touching `docs/engine/project_lawbook_m10.md`
and, per the "Docs Requiring Update" finding, `docs/architecture/kernel_concurrency_design_
philosophy.md`. Existing tests that must keep passing:

- **unit / doc-integrity**:
  - `tests/docs/test_doc_integrity.py::test_manifest_file_existence` — mandatory docs from
    `docs/engine/manifest.json` must still exist.
  - `tests/docs/test_doc_integrity.py::test_document_structural_compliance` — `project_lawbook_m10.md`
    must still contain `## Purpose`, `## Architectural Pillars`, `## Table of Contents` headers
    exactly (manifest requires these 3; do not rename or remove any of them when inserting the
    precedence content between the pillar list and the ToC).
  - `tests/docs/test_doc_integrity.py::test_release_target_binding` — lawbook must still mention
    `class_b` (unaffected by this edit, but must not be accidentally removed).
  - `tests/docs/test_doc_integrity.py::test_link_integrity` — any new cross-link added to
    `project_lawbook_m10.md` or `kernel_concurrency_design_philosophy.md` must resolve if written
    as a `[label](path)` markdown link; safest is to match the doc's existing plain-backtick-path
    convention (see `## Purpose`'s "See `project_lawbook.md`..." and the ToC's
    "- Architecture overview: `docs/engine/architecture.md`"), which this regex-based check does
    not parse as a link at all.
  - `tests/docs/test_doc_integrity.py::test_terminology_alignment` — unaffected (RuntimeMode/
    HardwareClass/FailureKind enums, not pillar text), but keep passing as a smoke check that the
    manifest itself hasn't been touched.
  - `tests/docs/test_doc_path_existence.py` — any new path referenced must exist (relevant if the
    cross-link to `docs/architecture/kernel_concurrency_design_philosophy.md` is added).
  - `tests/docs/test_kernel_phase_names_consistent.py` — unrelated to pillar precedence but lives in
    the same `tests/docs/` module family; run alongside as a fast regression net for
    doc-consistency infrastructure.
  - `tests/docs/test_contributor_guardrails.py` — general doc-guardrail suite, cheap to include.
  - `tests/tools/test_validate_frontmatter.py` — both edited docs already have valid frontmatter
    (`status: active`, `authority: P1`, etc.); must remain valid after edits (no frontmatter fields
    should be touched by this ticket, but the validator is the authoritative check).

- **integration**: none expected — no code path touches these doc files at runtime; `manifest.json`
  is the only machine-read artifact referencing them, covered above.

## New Tests Required

Given the ticket's acceptance criteria are about *documentation content*, not runtime behavior, new
tests are documentation-assertion tests (Python `pytest` reading the `.md` files as text), matching
this repo's existing pattern in `tests/docs/test_doc_integrity.py` and
`tests/docs/test_kernel_phase_names_consistent.py`.

- **Test name**: `test_lawbook_states_pillar_precedence_order`
  **Category**: unit / doc-consistency
  **Verifies**: `docs/engine/project_lawbook_m10.md` contains an explicit precedence/trade-off
  statement in or immediately after "Architectural Pillars" — not just the 5 enumerated pillar
  names. Concretely: assert the doc contains the 4 order terms ("Determinism", "Resource-Safety",
  "Performance", "Auditability") in that relative order (e.g. via successive `.index()` calls or a
  single regex spanning all 4 in sequence), and that "Performance" appears as a named, ranked term
  — not only as a word inside "Hardware-Class Honesty" or "Bounded Resources" prose.
  **Location**: `tests/docs/test_doc_integrity.py` (new function) or a new
  `tests/docs/test_lawbook_pillar_precedence.py`, whichever the implementer's Plan prefers — prefer
  extending `test_doc_integrity.py` since it already owns lawbook-content assertions
  (`test_release_target_binding`).

- **Test name**: `test_lawbook_precedence_matches_design_philosophy_verbatim`
  **Category**: unit / doc-consistency (anti-drift guard)
  **Verifies**: the 4 order terms as they appear in `project_lawbook_m10.md` are character-identical
  to the 4 order-term strings used in `docs/architecture/kernel_concurrency_design_philosophy.md`
  Part 1 (prose and/or mermaid `flowchart LR` labels) — guards directly against AC4's "matches
  verbatim" requirement drifting apart on a future edit to either file.
  **Location**: `tests/docs/test_doc_integrity.py` or the same new file as above.

- **Test name**: `test_lawbook_cross_links_design_philosophy_doc`
  **Category**: unit / doc-consistency
  **Verifies**: `project_lawbook_m10.md` contains a reference (path string, whichever convention is
  chosen) to `docs/architecture/kernel_concurrency_design_philosophy.md`, confirming the SSOT
  cross-link this ticket's scope requires rather than an independently-drafted duplicate.
  **Location**: same file as above.

- **Test name**: `test_design_philosophy_part1_not_stale_after_lawbook_states_order`
  **Category**: unit / doc-consistency (regression guard for the specific staleness this
  investigation identified)
  **Verifies**: `kernel_concurrency_design_philosophy.md` Part 1 no longer contains the now-false
  claim that the order "is not stated as a rule anywhere" (i.e. asserts that exact phrase — or
  whatever replaces it — is absent, or that a corrected phrase referencing `project_lawbook_m10.md`
  is present). Only meaningful if the investigation's recommended reading of the Out-of-Scope
  parenthetical is confirmed by the plan; if the plan decides not to touch
  `kernel_concurrency_design_philosophy.md` at all, this test should instead assert the ticket's
  Assumptions/Open-Questions section documents the resulting staleness explicitly rather than
  silently leaving it — do not skip covering this outcome either way.
  **Location**: same file as above.

## Scoped Pytest Commands

```
pytest tests/docs/ -v
pytest tests/tools/test_validate_frontmatter.py -v
```

Both are fast, fully-offline, no `-m "not slow"` filtering needed (no slow-marked tests in
`tests/docs/`). Do not run `pytest tests/` — scope is the doc-integrity/tools domain only, per
Testing Rule.

## Anti-Drift Test Guards

- The 4 new/extended assertions above collectively guard against the exact failure mode this
  ticket's own investigation flagged: independently-drafted, near-duplicate precedence prose that
  silently diverges from `kernel_concurrency_design_philosophy.md` Part 1 on a future edit to either
  file (the same drift class `TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT` and C8 already found twice in
  this doc area).
- `test_document_structural_compliance` (existing) already guards against accidentally renaming or
  removing the `## Architectural Pillars` / `## Table of Contents` headers while inserting new
  content between them — no new test needed for that, just confirm it still passes.
- Do **not** add any test asserting `docs/engine/project_lawbook.md`'s pillar list matches
  `project_lawbook_m10.md`'s — that would encode the pre-existing, deliberately-unfixed drift as if
  reconciling it were this ticket's job, which it explicitly is not (see investigation's Anti-Drift
  Hazards). If a future ticket fixes that drift, it should add its own test then.
- If the plan chooses to edit `harness_architecture.md` to add "Performance" (contrary to this
  investigation's recommendation), a reviewer should treat that as scope creep flagged by this test
  plan, not something to silently accept — no test is written for it here on purpose, since it
  should not happen.

---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC
artifact_type: test_plan
tags: [architecture, engine, documentation]
---

# Test Plan — TCK-20260817-KERNEL-CONCURRENCY-DESIGN-DOC

This is a **docs-only** ticket (new file under `docs/architecture/`, cross-link edits to 4 existing
docs, no `src/` or `tests/` changes). There is no unit/integration/arena-combat regression surface
in the usual sense — the regression surface here is the doc-integrity/frontmatter/registry test
suite plus the two acceptance-criteria commands (`make docs-registry`, `make knowledge-index-update`).

## Regression Surface

**Unit / doc-integrity:**
- `tests/docs/test_doc_integrity.py` — `test_manifest_file_existence`,
  `test_document_structural_compliance` (must not break `worker_contract.md`'s required headers
  `Purpose` / `Backpressure & Fallback Law` when inserting its cross-link),
  `test_terminology_alignment`.
- `tests/docs/test_doc_path_existence.py::test_doc_path_citations_exist` — scans
  `docs/engine`, `docs/architecture`, `docs/performance` for path citations; carries a
  `pytest.mark.xfail(strict=True)` pinned to 12 known-dead citations. The new doc's `##
  References` section must not add citations beyond that pinned set.
- `tests/docs/test_kernel_phase_names_consistent.py` — unrelated to this ticket's content, but
  lives in the same scanned directory tree; must stay green (already un-xfailed by the phase-count
  fix ticket).
- `tests/tools/test_validate_frontmatter.py` — validates the `STATUS_VALUES = {"authoritative",
  "active", "historical", "archive"}` constraint the new doc's frontmatter must satisfy, and the
  `authoritative` → `last_verified`-required rule (relevant if `authority`/`status` choice is
  revisited).
- `tests/tools/test_generate_registry.py` — the `docs-registry` Make target's underlying script;
  must index the new doc without error.
- `tests/unit/docs/test_doc_archive.py` — sanity check that this new doc (status `active`, not
  `archive`) is not miscategorized by path-prefix rules.

**Tools/registry:**
- `tests/tools/test_registry_query.py` — if the new doc needs to be discoverable via
  `related_code_areas`/`tags` filtering for future investigations (per this agent's own "Finding
  Prior Work" registry-query mechanism).
- `tests/tools/test_layer_registry.py`, `tests/tools/test_tag_registry.py` — confirm `layer:
  architecture` and `tags: [architecture, engine, documentation]` (or whichever set Plan settles
  on) remain registry-valid; no new layer/tag registration is expected for this ticket.

## New Tests Required

Given this ticket produces no new runtime behavior, no new unit/integration tests are required by
the acceptance criteria themselves — the acceptance criteria are satisfied by grep-verifiable
content and passing the existing doc-integrity suite. However, two acceptance criteria are
explicitly grep-checks that should be verified as literal commands (not just eyeballed) before
claiming DONE:

- **Cross-link presence check** — Category: architecture guard (manual/scripted grep, not a new
  pytest test). What it verifies: `docs/engine/kernel.md` and all three of
  `bounded_concurrency_contract.md`, `worker_contract.md`, `concurrent_integrity_contract.md`
  contain a resolvable reference to the new doc's path. Where: run as a one-off verification
  command during Verify, e.g.
  `grep -rn "kernel_concurrency_design_philosophy" docs/engine/kernel.md docs/engine/contracts/bounded_concurrency_contract.md docs/engine/contracts/worker_contract.md docs/engine/contracts/concurrent_integrity_contract.md`
  — must return exactly 4 matches (one per file). This directly operationalizes this ticket's own
  acceptance criteria ("grep-verifiable cross-link").
- **New-doc frontmatter legality check** — Category: unit (via existing validator, not a new
  test file). What it verifies: `python3 tools/validate_frontmatter.py docs/architecture/kernel_concurrency_design_philosophy.md --content-type doc`
  exits 0. Where: run directly during Verify; covered indirectly by
  `tests/tools/test_validate_frontmatter.py`'s existing parametrized coverage if that suite
  globs `docs/**/*.md`, otherwise run standalone.
- **Mermaid diagram presence check** — Category: architecture guard. What it verifies: if Plan
  resolves the blocking mermaid-diagram gap (see investigation.md Risks #1) by authoring or
  recovering the diagrams, confirm the landed doc actually contains 2
  ` ```mermaid ` fenced blocks (`grep -c '^```mermaid' docs/architecture/kernel_concurrency_design_philosophy.md`
  should return `2`), since the source Appendix A text contained zero and this is easy to silently
  under-deliver.

## Scoped Pytest Commands

```
python3 -m pytest tests/docs/ tests/unit/docs/ -m "not slow" -q
python3 -m pytest tests/tools/test_validate_frontmatter.py tests/tools/test_generate_registry.py tests/tools/test_registry_query.py tests/tools/test_layer_registry.py tests/tools/test_tag_registry.py -q
```

Never `pytest tests/` — scoped to the docs-integrity and registry-tooling domains this ticket
actually touches.

## Anti-Drift Test Guards

- `tests/docs/test_doc_path_existence.py::test_doc_path_citations_exist`'s `xfail(strict=True)`
  is itself the guard against silently adding new dead path citations in the new doc's References
  section — if the new doc introduces a 13th dead citation, this test's failure will no longer
  match its pinned reason text even though it still nominally "passes" as an xfail; treat any
  citation in the new doc that isn't independently verified to exist as a real regression, not
  something the xfail marker absorbs for free.
- `tests/docs/test_doc_integrity.py::test_document_structural_compliance` is the concrete guard
  against `worker_contract.md`'s cross-link edit accidentally reflowing/renaming its two
  manifest-required headers (`Purpose`, `Backpressure & Fallback Law`).
- No test currently asserts Appendix A's "Known documentation drift" section content or the
  `concurrency_limit`/RNG open-question pointer wording — these are prose-only judgment calls
  (see investigation.md Risks) that no automated guard will catch if left stale; Verify must check
  them by direct read, not by test pass/fail.
- `make knowledge-index-update` (acceptance criterion: `search_docs` for "kernel concurrency
  design philosophy fork-join" surfaces the new doc) is **known to fail in this sandbox** due to a
  network block on `huggingface.co`, confirmed by repeated direct attempts earlier in this same
  session. This is an environment limitation, not something this ticket's content can fix. Plan
  and Implement must record the actual exit status/output of this command when run — never mark
  this acceptance criterion as passed without a real, current run showing success, and never
  silently substitute a claim that it "should work" for evidence that it did.

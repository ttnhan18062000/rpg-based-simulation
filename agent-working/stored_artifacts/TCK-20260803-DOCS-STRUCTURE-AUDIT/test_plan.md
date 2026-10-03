---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260803-DOCS-STRUCTURE-AUDIT
artifact_type: test_plan
tags: [documentation, registry]
---

# Test Plan — TCK-20260803-DOCS-STRUCTURE-AUDIT

## Regression Surface

Unit (doc-tooling):
- `tests/tools/test_generate_registry.py` — full file. In particular:
  - `TestDocEntryGeneration::test_doc_entry_skips_archive_subdir` (line 90) and
    `::test_doc_entry_skips_parity_ledger_subdir` (line 103) — must keep passing unchanged;
    this ticket does not touch `archive`/`parity_ledger` exclusion behavior.
  - `TestRealDocsTree::test_registry_exits_zero_on_real_docs_tree` (line ~529) and
    `::test_check_flag_detects_no_drift_against_real_registry` (line ~534) — run against the
    real `docs/` tree; must still exit 0 / report no drift after this audit, since the
    audit's conclusion is "no functional change to `_SKIP_DOC_SUBDIRS`."
  - `TestRealDocsTree::test_skip_doc_subdirs_exist_on_disk` (line 539-550) — must keep
    passing as-is (all four entries — `archive`, `parity_ledger`, `scenarios`, `entity` —
    remain real on-disk directories; no entries added or removed by this ticket's
    conclusions).

Integration (docsite/registry build, indirect):
- None directly exercised by source changes in this ticket, since no `docs/*.md` content is
  modified and `_SKIP_DOC_SUBDIRS` is unchanged. `make docs-registry` / `make docs-build`
  are not expected to be run as part of verifying this ticket, but would be unaffected if run.

Arena-combat: not applicable — no combat-domain code or docs touched.

## New Tests Required

Per this ticket's acceptance criteria, the only state changes possible are (a) a `git rm` of
a genuinely-dead folder — **investigation found none qualify**, so no test is needed for that
branch — and (b) documentation of the `scenarios`/`entity` no-op rationale via an in-code
comment next to `_SKIP_DOC_SUBDIRS` — a comment has no runtime behavior to test.
Consequently, **no new test is strictly required** by the investigation's conclusions.
However, one guard is recommended to close a real gap the investigation surfaced (that the
existing regression test cannot distinguish "excludes real doc content" from
"currently-inert no-op"):

- **Test name**: `test_skip_doc_subdirs_inert_entries_documented` (or fold into
  `test_skip_doc_subdirs_exist_on_disk` as an additional assertion)
- **Category**: unit / architecture guard
- **What it verifies**: for each entry in `_SKIP_DOC_SUBDIRS` that currently contains zero
  `.md` files under `docs/<entry>/` (i.e., `scenarios`, `entity` as of this audit), assert
  that `tools/generate_registry.py`'s module docstring or an inline comment adjacent to
  `_SKIP_DOC_SUBDIRS` mentions that entry by name — preventing a future silent addition of an
  inert entry with no documented rationale, and catching drift if one of these entries
  someday gains real `.md` content (at which point the "inert" framing would need updating).
  This is optional scope — only required if the Plan phase decides to add the clarifying
  comment recommended in the investigation; if the Plan phase decides "no comment needed,"
  this test is not required either.
- **Where it should live**: `tests/tools/test_generate_registry.py`, in the existing
  `TestRealDocsTree` class, next to `test_skip_doc_subdirs_exist_on_disk`.

If the Plan phase instead concludes truly nothing changes (no comment added either), then
correspondingly **zero new tests** are required — the AC's testing bar
(`pytest tests/tools/test_generate_registry.py -q` passes) is satisfied by the existing suite
already passing today, since nothing in `tools/generate_registry.py` changes.

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/tools/test_generate_registry.py -q
```

No other domain is touched (no `src/` changes, no `tests/unit/strategic/` changes — the
`test_scenario_runner.py` reference check was read-only verification, not a modification), so
no additional scoped command is needed. If `docs/scenarios/phase1/*.yaml` had turned out to
be dead and were removed, `tests/unit/strategic/test_scenario_runner.py` would also need to
run — it does not, since those files are kept.

## Anti-Drift Test Guards

- `test_doc_entry_skips_archive_subdir` and `test_doc_entry_skips_parity_ledger_subdir`
  passing unchanged is itself the guard against accidentally touching those two
  out-of-scope, already-confirmed-correct exclusions.
- `test_registry_exits_zero_on_real_docs_tree` and
  `test_check_flag_detects_no_drift_against_real_registry` running against the *real*
  `docs/` tree (not a fixture) are the guards against any accidental structural change (a
  folder deletion, a `_SKIP_DOC_SUBDIRS` edit) silently changing the registry's shape or
  entry count — if this ticket's implementation removes a folder or edits the skip set
  without updating expectations, one of these two tests will fail against the live tree.
- If `tests/unit/strategic/test_scenario_runner.py` is ever run as part of this ticket's
  verification (it should not need to be, since `docs/scenarios/` is being kept), a failure
  there would be the direct signal that the "keep `scenarios/` — it's actively referenced"
  conclusion in the investigation was acted against.
- No test should assert on the `docs/archive/` file count (`452`/`439`) as a fixed value —
  that count is expected to keep growing over time as more work is archived, and the
  investigation explicitly flags the "146" figure in the ticket's own scoping text as already
  stale. A future ticket adding a brittle exact-count assertion against `docs/archive/` would
  itself become a maintenance hazard.

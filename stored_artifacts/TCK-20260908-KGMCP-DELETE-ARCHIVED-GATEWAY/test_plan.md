---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY
artifact_type: test_plan
tags: [ai, mcp, governance]
---

# Test Plan — TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY

## Regression Surface

**Unit / integration — must keep passing unmodified (zero real behavior change, only import/config
surface):**
- `tests/tools/test_write_path_guard.py` — the live, extracted write-path-guard module's own test
  suite (54 tests per `docs/parity_ledger/infrastructure.yaml` INFRA-342's `v2_evidence`). Confirmed
  to import only `tools.write_path_guard`, never anything under `tools/archive/`.
- `tests/tools/test_retrieval_cache.py` — large, actively-extended suite; its 3 classes cited by
  INFRA-343 (`TestProviderResultCache`, `TestMigration003`, `TestProviderResultCacheStats`) plus
  `TestLevel2Migrations` (INFRA-346), `TestMigration004`/`TestContextPacketCache`/
  `TestContextPacketCacheStats` (INFRA-349) must all still pass — confirmed to import
  `tools.write_path_guard`, not any archived module.
- `tests/docs/test_redaction_retention_policy_doc.py` — imports `tools.write_path_guard as kgr`
  (already updated by the predecessor ticket); must keep passing, in particular
  `test_payload_size_cap_doc_matches_live_module_constant`.
- `tests/tools/test_mcp_json_registration.py` — asserts `.mcp.json` has exactly
  `{"knowledge-search", "github"}`; unaffected by this ticket (already true today), but must be
  re-run to confirm no accidental `.mcp.json` edit.
- `tests/tools/test_wave1_agent_tools_frontmatter.py` — asserts `done-checker.md`/`test-scoper.md`
  no longer grant `mcp__knowledge-gateway__*`; unaffected by this ticket, re-run as a pure
  regression guard.
- `tests/docs/test_phase4_direct_tool_comparison_doc.py`,
  `tests/docs/test_phase4_workflow_recommendation_doc.py`,
  `tests/docs/test_phase5_repeated_demand_measurement_doc.py` — confirmed zero dependency on any
  archived module (predecessor's own Review Round 1 finding); must still collect and pass, proving
  they were not accidentally swept into this ticket's delete.
- `tests/tools/test_evidence_cache_identity_contract.py` — confirmed independent (reads
  `retrieval_cache.py` via `ast.parse()` only); regression guard that this ticket's delete does not
  touch it.
- `tests/tools/test_generate_retro.py` — large suite covering `tools/agent-monitoring/generate_retro.py`,
  including its `compute_kgmcp_cache_efficiency_metrics()` function; confirmed to import only
  `retrieval_cache.py`, never any archived module. Must pass unmodified.
- `tests/tools/test_ci_workflow_test_coverage.py` — **regression surface with a known, required
  change** (see New Tests Required below); the suite as a whole must still pass, but two of its
  existing tests need their assertions updated to match post-delete reality, not left red.

**Architecture-guard tests:**
- `tests/tools/test_knowledge_gateway_archival.py` — **regression surface with a known, required
  change** (see New Tests Required below); `test_write_path_guard_exists_and_is_not_archived` must
  keep passing unmodified; the other two tests need updating (see below) since their subject files
  no longer exist anywhere.
- `tests/tools/test_scope_coverage_static.py` — its comment citing archived test filenames
  (`test_knowledge_gateway_cache.py`, `test_knowledge_gateway_redaction.py`) is prose only, not a
  live assertion against file existence; confirm via full-file read before Implement that no
  assertion in it depends on `tests/archive/`'s contents.

**Nothing under `tests/archive/` itself is a regression-surface item** — those 15 files are being
deleted, not preserved; they are excluded from default collection today via `norecursedirs` and
will simply cease to exist.

## New Tests Required

This ticket is pure deletion/cleanup, so no ticket Acceptance Criterion calls for new *behavioral*
coverage. However, two existing test files require **updates that are themselves new test-scoped
work**, uncovered by this investigation and not named in the ticket's own Related Code Areas:

- **Update `tests/tools/test_knowledge_gateway_archival.py`**
  - Category: architecture guard
  - What it verifies today: that the 6 gateway source files were archived (moved) from `tools/` to
    `tools/archive/`. Post-delete, "archived and present at `tools/archive/`" is no longer true —
    the correct post-condition is "absent from both the old `tools/` paths AND `tools/archive/`."
  - Required change: replace `test_gateway_modules_exist_at_archive_location()` with a test
    asserting the archived filenames are absent from `tools/archive/` too (or delete this whole
    file if `test_write_path_guard_exists_and_is_not_archived()`'s coverage is fully subsumed by a
    new, more direct "gateway package no longer exists anywhere in the repo" test). Keep
    `test_write_path_guard_exists_and_is_not_archived()` (still valid, still needed) either way.
  - Where it lives: `tests/tools/test_knowledge_gateway_archival.py` (existing file, in-place edit).

- **Update `tests/tools/test_ci_workflow_test_coverage.py`**
  - Category: architecture guard / static config guard
  - What it verifies today: `test_pytest_norecursedirs_reads_real_pyproject_toml()` asserts
    `"archive" in norecursedirs` against the real `pyproject.toml`;
    `test_check_against_real_repo_state_recognizes_tests_archive_as_norecursedirs_excluded()`
    asserts `by_condition["ci_test_dir_covered:tests/archive"]["status"] == "PASS"` against the
    real repo tree. Both assumptions become false once `"archive"` is removed from
    `norecursedirs` and `tests/archive/` is deleted.
  - Required change: remove or rewrite `test_pytest_norecursedirs_reads_real_pyproject_toml()`'s
    `"archive" in norecursedirs` assertion (drop it, or invert it to assert absence, per whatever
    the implementer determines is the correct post-delete invariant for this shared config file —
    note other `norecursedirs` entries like `"stored_artifacts"` must NOT be affected by this
    change). Remove or rewrite
    `test_check_against_real_repo_state_recognizes_tests_archive_as_norecursedirs_excluded()` since
    its subject directory no longer exists — do not leave a test indexing a dict key that may no
    longer be produced by the checker, which would raise `KeyError` rather than fail cleanly.
    `test_directory_is_excluded_from_pytest_collection_matches_any_path_segment()` (L442-445) and
    `test_fixture_norecursedirs_excluded_directory_passes_instead_of_failing()` (L452-477) use
    synthetic fixture data (`{"archive", "scratch"}`, `{"orphan"}`), not the real repo state — these
    stay valid and must NOT be touched.
  - Where it lives: `tests/tools/test_ci_workflow_test_coverage.py` (existing file, in-place edit,
    L432-485 region only).

No net-new test file is required by this ticket's own Acceptance Criteria; the two updates above
are corrective edits to existing regression coverage that this ticket's own action (the delete)
would otherwise leave silently red or silently pointing at nonexistent files.

## Scoped Pytest Commands

Primary regression command, per the ticket's own AC:
```
pytest tests/tools/ tests/docs/ -v
```

Narrower, faster pre-check before the full command above (fast-fail on the files most directly
affected):
```
pytest tests/tools/test_write_path_guard.py tests/tools/test_retrieval_cache.py \
       tests/tools/test_knowledge_gateway_archival.py tests/tools/test_ci_workflow_test_coverage.py \
       tests/tools/test_mcp_json_registration.py tests/tools/test_wave1_agent_tools_frontmatter.py \
       tests/docs/test_redaction_retention_policy_doc.py \
       tests/docs/test_phase4_direct_tool_comparison_doc.py \
       tests/docs/test_phase4_workflow_recommendation_doc.py \
       tests/docs/test_phase5_repeated_demand_measurement_doc.py -v
```

Collection-only sanity check (before and after the delete) to prove zero collection errors and
zero leftover references to the deleted `tests/archive/` files:
```
pytest tests/tools/ tests/docs/ -v --co
```

Never: `pytest tests/` (unscoped, forbidden by CLAUDE.md's Testing Rule) and never
`pytest tests/archive/` after the delete lands (the directory will no longer exist).

## Anti-Drift Test Guards

- **Zero-import guard**: before deleting, re-run
  `grep -rln "knowledge_gateway" tools/ src/ tests/ .claude/ docs/ | grep -v '^tools/archive/\|^tests/archive/'`
  one final time immediately pre-delete (not trusted from any prior run, per the ticket's own
  Verification-evidence framing) — must show only the expected doc-prose/comment/test-name hits
  enumerated in investigation.md, zero new live call sites.
- **`tools/write_path_guard.py` / `tools/retrieval_cache.py` untouched guard**: `git diff --stat
  tools/write_path_guard.py tools/retrieval_cache.py` must show zero changes as part of this
  ticket's diff (the ticket's own Out of Scope forbids touching either).
- **No accidental `tests/docs/` sweep guard**: `pytest tests/docs/test_phase4_direct_tool_comparison_doc.py
  tests/docs/test_phase4_workflow_recommendation_doc.py tests/docs/test_phase5_repeated_demand_measurement_doc.py -v --co`
  must still show all 3 files collected after the delete — proves they were not accidentally caught
  up in the `tests/archive/` removal.
- **`dashboard-frontend`/`generate_retro.py` untouched guard**: `git diff --stat
  tools/agent-monitoring/generate_retro.py tools/agent-monitoring/kgmcp_baseline_runner.py
  tools/agent-monitoring/kgmcp_baseline_corpus.py dashboard-frontend/` must show zero changes — these
  are confirmed live and confirmed independent of the deleted files; any diff here would be
  unrelated scope creep.
- **`pyproject.toml` scoped-edit guard**: `git diff pyproject.toml` must show exactly one line
  removed (`"archive",` from `norecursedirs`) and nothing else — not `markers`, not any other
  `[tool.pytest.ini_options]` key.
- **Parity ledger single-writer-path guard**: `git diff docs/parity_ledger/infrastructure.yaml`
  must show only field-level changes to the 21 named entries (`status`/`v2_evidence`/
  `divergence_note`), produced via `tools/parity_ledger_writer.py` — never a raw multi-line `Edit`
  diff touching surrounding entries' formatting/whitespace, which would indicate a raw-edit
  corruption risk rather than the sanctioned per-entry writer tool being used.
- **Test-file-count guard**: before closing this ticket, `find tests/archive -type f -name '*.py' 2>/dev/null | wc -l`
  must return nothing (directory gone) and `git log --diff-filter=D --name-only <this-ticket-commit>
  -- tests/archive/` must show exactly the 15 files enumerated in investigation.md — not 20, and
  not a different count — closing the loop on this investigation's central finding.

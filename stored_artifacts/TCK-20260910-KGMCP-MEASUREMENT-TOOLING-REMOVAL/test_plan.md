---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL
artifact_type: test_plan
tags: [agent-monitoring, mcp]
---

# Test Plan — TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL

## Regression Surface

This is a pure-deletion ticket with zero live import of the 3 modules being removed (confirmed in
investigation.md), so the regression surface is narrow: confirm nothing outside the deleted files
was depending on them, and confirm the 2 retained fixtures' real consumers still pass.

**unit / tools**
- `tests/tools/test_write_path_guard.py` — must keep passing unmodified; confirms
  `MAX_PAYLOAD_BYTES`/`check_size_cap()` behavior is untouched by the (optional) comment-only edit
  at `tools/write_path_guard.py:61`.
- `tests/tools/test_knowledge_gateway_archival.py` — must keep passing unmodified; unrelated
  architecture guard (gateway modules only), confirms this ticket does not regress it.
- `tests/tools/test_generate_registry.py`, `tests/tools/test_validate_frontmatter.py` — must keep
  passing after `docs/agent-monitoring/README.md` and the `INFRA-334` parity entry are edited and
  `docs/REGISTRY.yaml` is regenerated.
- `tests/tools/test_parity_ledger_writer.py` (if present) or equivalent parity-ledger schema
  validation — must keep passing after `INFRA-334`'s `v2_evidence` field is rewritten via
  `tools/parity_ledger_writer.py::write_entry()`.

**integration / docs**
- `tests/docs/test_phase4_direct_tool_comparison_doc.py` — must keep passing; reads the **retained**
  `tests/tools/fixtures/kgmcp_phase4_direct_tool_comparison_results.json` directly via
  `json.loads()`, no runner import. This is the primary anti-regression check that the 7 deletions
  didn't reach a file this test needs.
- `tests/docs/test_phase5_repeated_demand_measurement_doc.py` — must keep passing; reads the
  **retained** `tests/tools/fixtures/kgmcp_phase5_repeated_demand_measurement_results.json`
  directly via `json.loads()`, no runner import. Same anti-regression purpose.
- `tests/docs/test_redaction_retention_policy_doc.py` — must keep passing; confirms the
  `MAX_PAYLOAD_BYTES` doc-vs-constant cross-check is unaffected by the `write_path_guard.py:61`
  comment edit (that test only checks the constant value against doc text, never the comment).

There is no `arena-combat` surface — this ticket touches no simulation/combat code.

## New Tests Required

No new test files are required by the acceptance criteria — this is a subtractive/cleanup ticket
whose correctness is proven by the *absence* of consumers and the continued passing of existing
tests, not by new behavior. Two lightweight guard additions are still worth adding to lock the
outcome and prevent silent re-introduction:

- **Test name:** `test_kgmcp_measurement_modules_no_longer_exist`
  **Category:** architecture guard
  **Verifies:** `tools/agent-monitoring/kgmcp_baseline_corpus.py`,
  `tools/agent-monitoring/kgmcp_baseline_runner.py`, and
  `tools/agent-monitoring/kgmcp_phase5_repeated_demand_measurement_runner.py` do not exist as
  files, mirroring `test_knowledge_gateway_archival.py`'s own pattern for the gateway modules so a
  future accidental re-add of dead measurement tooling is caught immediately.
  **Location:** extend `tests/tools/test_knowledge_gateway_archival.py` with these 3 filenames
  appended to a new list (do not add them to `_ARCHIVED_FILENAMES`, which is specifically the
  gateway-package set per that file's own docstring — use a second, clearly-named list/test
  function instead, to avoid conflating "gateway package" with "measurement tooling").

- **Test name:** `test_orphaned_kgmcp_fixtures_removed_retained_fixtures_present`
  **Category:** architecture guard
  **Verifies:** the exact 7 named fixtures no longer exist under `tests/tools/fixtures/`, and the
  2 retained fixtures (`kgmcp_phase4_direct_tool_comparison_results.json`,
  `kgmcp_phase5_repeated_demand_measurement_results.json`) still do — a single assertion sweep so a
  future accidental fixture re-add or accidental deletion of a still-needed fixture both fail
  loudly instead of silently breaking a `tests/docs/` test at collection time.
  **Location:** same file (`tests/tools/test_knowledge_gateway_archival.py`), or a new
  `tests/tools/test_kgmcp_measurement_tooling_removed.py` if the implementer prefers not to widen
  the existing gateway-scoped file's stated purpose — either is acceptable, record which was
  chosen.

## Scoped Pytest Commands

```
pytest tests/tools/test_write_path_guard.py tests/tools/test_knowledge_gateway_archival.py -v
pytest tests/docs/test_phase4_direct_tool_comparison_doc.py tests/docs/test_phase5_repeated_demand_measurement_doc.py tests/docs/test_redaction_retention_policy_doc.py -v
pytest tests/tools/ -k "registry or frontmatter or parity" -v
```

If the new architecture guards above are added:
```
pytest tests/tools/test_knowledge_gateway_archival.py -v
```
(or the new standalone file, if that path is chosen instead)

Never `pytest tests/` — scope to `tests/tools/` and `tests/docs/` as above, per this repo's
Testing Rule.

## Anti-Drift Test Guards

- `tests/docs/test_phase4_direct_tool_comparison_doc.py` and
  `tests/docs/test_phase5_repeated_demand_measurement_doc.py` passing unmodified is itself the
  strongest anti-drift guard available: both read their fixture directly, so if the implementer
  ever accidentally deletes one of the 2 retained fixtures, these tests fail immediately at
  collection/run time (`FileNotFoundError` from `Path.read_text()`), not silently.
- `test_knowledge_gateway_archival.py`'s existing 3 tests act as a boundary guard — they prove this
  ticket's deletions stayed inside the measurement-tooling family and never touched the already-
  hard-deleted gateway package's own file set (no accidental double-delete of a nonexistent path,
  no accidental re-scope into `TCK-20260908`'s already-closed territory).
- `test_write_path_guard.py`'s `MAX_PAYLOAD_BYTES == 65536` and `check_size_cap()` assertions guard
  against the optional comment-only edit at `write_path_guard.py:61` silently turning into (or
  masking) a real logic change — a `git diff` limited to `#`-prefixed lines plus this test suite
  passing unmodified is the required proof the edit stayed comment-only.
- `test_generate_registry.py`/`test_validate_frontmatter.py` guard the `docs/agent-monitoring/
  README.md` edit and the `INFRA-334` parity-ledger edit against introducing a frontmatter or
  registry-shape violation while removing the stale section/evidence text.

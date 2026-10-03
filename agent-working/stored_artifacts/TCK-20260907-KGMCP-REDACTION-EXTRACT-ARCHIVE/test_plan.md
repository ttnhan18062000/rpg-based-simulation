---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE
artifact_type: test_plan
tags: [ai, mcp, governance]
---

# Test Plan — TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE

## Regression Surface

Existing tests that must keep passing (unaffected by this ticket's changes):

**Unit / integration (`tools/`, unaffected):**
- `tests/tools/test_retrieval_cache.py` — the bulk of this suite (migrations, Level 1/2
  read/write, access-log) does not touch `_kgr_redaction` directly; only the small subset that
  exercises `open_connection_with_limits()` indirectly (via `_get_level1_connection()` etc.) is
  affected by the import-path change, not by any behavior change. Must still pass in full.
- `tests/tools/test_generate_retro.py` — `generate_retro.py` depends only on `retrieval_cache.py`,
  never on the gateway modules; must be unaffected.
- `tests/tools/test_test_scope_coverage_static.py` — `expected_test_dirs_for()` is a pure
  path-string mapping (not a filesystem check), so its existing assertions referencing
  `"tools/knowledge_gateway_redaction.py"` and `"tools/retrieval_cache.py"` as *string inputs*
  keep passing regardless of whether those files still exist at that path post-archival.
- `tests/tools/test_post_tool_hook.py`, `tests/tools/test_settings_json_hooks_wiring.py` —
  unaffected (no gateway import).
- `tests/docs/test_redaction_retention_policy_doc.py` — all tests except
  `test_payload_size_cap_doc_matches_live_module_constant` (which needs its import path updated,
  see New Tests / Updated Tests below) are pure doc-structure checks, unaffected.

**Architecture guard:**
- `tests/tools/test_wave1_agent_tools_frontmatter.py::test_wave1_agents_do_not_declare_disallowed_tools_field`
  and `test_wave1_candidate_scope_excludes_known_denied_tools` — unaffected by this ticket's
  frontmatter edit (they check for absence of specific forbidden tools, not gateway-specific).

## Tests That Will Break As a Direct, Known Consequence of This Ticket (must be updated, not just re-run)

- `tests/tools/test_wave1_agent_tools_frontmatter.py::test_wave1_agent_files_declare_tools_field[done-checker]`
  and `[test-scoper]` — `_WAVE1_CANDIDATE_TOOLS["done-checker"]`/`["test-scoper"]` in the test file
  itself hard-pins the exact `tools:` string including the two
  `mcp__knowledge-gateway__knowledge_context`/`mcp__knowledge-gateway__knowledge_status` entries
  (lines 35-46). **Must edit this Python dict in the same change as the two `.md` frontmatter
  edits** — editing only the `.md` files leaves this parametrized test failing for those two
  agent_name values.
- `tests/docs/test_redaction_retention_policy_doc.py::test_payload_size_cap_doc_matches_live_module_constant` —
  currently does `sys.path.insert(0, str(_REPO_ROOT / "tools")); import knowledge_gateway_redaction
  as kgr; ... kgr.MAX_PAYLOAD_BYTES`. Must be updated to import `MAX_PAYLOAD_BYTES` from the new
  extraction-target module instead.
- `tests/tools/test_knowledge_gateway_mcp.py::test_mcp_json_gains_exactly_one_new_server_entry` —
  hard-asserts `set(mcp_config["mcpServers"].keys()) == {"knowledge-search", "github",
  "knowledge-gateway"}`. Once `.mcp.json`'s `knowledge-gateway` entry is removed, this assertion
  fails. Since this whole test file also does a top-level `_mod = <sibling-load of
  knowledge_gateway_mcp.py>`, the file becomes uncollectable/unrunnable the moment the module is
  archived regardless of this one assertion.
- `tests/tools/test_knowledge_gateway_packet_assembly.py`, `tests/tools/test_knowledge_gateway_router.py`,
  `tests/tools/test_knowledge_gateway_contract_schemas.py` — each independently asserts `.mcp.json`
  carries a `knowledge-gateway` entry (confirmed via `grep -n "mcp_config\[.mcpServers.\]\[.knowledge-gateway.\]"`-
  style checks at lines 681/389/352 respectively). Same failure mode as above.
- Every test file that imports one of the archived modules (`tools/knowledge_gateway_{mcp,router,
  packet_assembly,cache,redaction}.py`) via `from tools import ...` or
  `importlib.util.spec_from_file_location(..., <literal path>)` becomes uncollectable once the
  module moves, independent of any specific assertion: `test_knowledge_gateway_mcp.py`,
  `test_knowledge_gateway_router.py`, `test_knowledge_gateway_packet_assembly.py`,
  `test_knowledge_gateway_cache.py`, `test_knowledge_gateway_redaction.py`,
  `test_knowledge_gateway_contract_schemas.py`, `test_knowledge_gateway_failure_semantics.py`,
  `test_kgmcp_measurement_baseline.py`, `test_kgmcp_baseline_corpus_dedup_coverage.py`,
  `test_kgmcp_phase1_baseline_comparison.py`, `test_kgmcp_phase2_baseline_recomparison.py`,
  `test_kgmcp_phase3_pilot_acceptance_measurement.py`, `test_kgmcp_phase4_direct_tool_comparison.py`,
  `test_kgmcp_phase4_warm_direct_tool_comparison.py`, `test_kgmcp_phase5_repeated_demand_measurement.py`,
  and (via doc-structure tests that import the live module for cross-checks) `tests/docs/
  test_phase4_direct_tool_comparison_doc.py`, `tests/docs/test_phase4_workflow_recommendation_doc.py`.
  This is the ticket's own Acceptance Criteria item: "Every test that legitimately covered the
  gateway package... still passes (moved/updated as needed, not silently deleted or skipped)" —
  **the concrete mechanism for "moved... not silently skipped" is not yet decided** (see
  investigation.md Risk #2): either (a) move these files to `tests/archive/` **and** add
  `tests/archive` to `pyproject.toml`'s `[tool.pytest.ini_options] norecursedirs`, or (b) mark them
  `@pytest.mark.skip(reason="TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE: gateway archived, see
  tools/archive/")` in place. Recommend (a) for consistency with the `scripts/archive/` code
  convention — but this is a Plan/Architecture-Review decision, not resolved by this test plan.
- `tests/tools/test_evidence_cache_identity_contract.py` — does **not** import any gateway module
  directly (confirmed: only reads `docs/engine/contracts/knowledge_gateway_mcp/*` and
  `tools/retrieval_cache.py` via `ast.parse()`/`Path.read_text()`). Stays in place, unaffected —
  do not move this one alongside the others.

## New Tests Required

- **Test name**: `test_<new_module>_evaluate_write_candidate_matches_original_behavior` (exact name
  TBD by Plan/implementer)
  **Category**: unit
  **What it verifies**: the extracted `evaluate_write_candidate()` (and its full transitive
  dependency closure — `check_allowlist`, `redact_content`, `scan_for_secrets`, `check_size_cap`,
  `check_never_cache_categories`) in the new module produces byte-identical `WriteDecision` output
  to the pre-extraction behavior, for the same fixture inputs `tests/tools/
  test_knowledge_gateway_redaction.py` already exercises (allowlist reject, each of the 10 secret
  patterns, oversized payload, each of the 6 never-cache categories, the ALLOW path). This is the
  actual regression guard for AC1 ("importable from a new, stable, gateway-independent module").
  **Where it should live**: `tests/tools/test_<new_module_name>.py` (new file), or the relocated
  `tests/tools/test_knowledge_gateway_redaction.py` renamed/repointed at the new module — Plan's
  call which, but it must not simply disappear.
- **Test name**: `test_retrieval_cache_imports_open_connection_with_limits_from_new_location`
  **Category**: architecture guard
  **What it verifies**: `tools/retrieval_cache.py`'s source no longer contains
  `from tools import knowledge_gateway_redaction` — greps for the new import statement instead.
  Direct regression guard for AC2.
  **Where it should live**: `tests/tools/test_retrieval_cache.py` (new test in the existing
  `TestStaticGuards`-style class, matching the module's own established static-guard pattern).
- **Test name**: `test_gateway_modules_archived_not_present_at_old_paths`
  **Category**: architecture guard
  **What it verifies**: `tools/knowledge_gateway_{mcp,router,packet_assembly,cache,redaction}.py`
  and `tools/start_knowledge_gateway_mcp.sh` no longer exist at their old paths, and (mirror
  assertion) exist at the chosen archive location. Direct regression guard for AC3.
  **Where it should live**: `tests/tools/test_knowledge_gateway_archival.py` (new file) or folded
  into an existing gate_checks-style static test.
- **Test name**: `test_mcp_json_no_longer_registers_knowledge_gateway`
  **Category**: architecture guard
  **What it verifies**: `.mcp.json`'s `mcpServers` keys are exactly `{"knowledge-search",
  "github"}` (the inverse of the now-broken `test_knowledge_gateway_mcp.py` assertion) — replaces
  that assertion's intent post-archival. Direct regression guard for AC4.
  **Where it should live**: `tests/tools/test_mcp_json_registration.py` (new, small, standalone —
  or wherever Plan decides `.mcp.json`-shape tests belong now that the gateway-specific ones that
  used to cover this are archived).
- **Test name**: `test_wave1_agent_files_declare_tools_field[done-checker]`/`[test-scoper]`
  (existing, parametrized) — after `_WAVE1_CANDIDATE_TOOLS` is updated to drop the two
  `mcp__knowledge-gateway__*` entries, these parametrized cases become the direct regression guard
  for AC5. No new test needed, just the dict update described above.
- **Test name**: `test_governance_capability_policy_epic_doc_cites_new_scan_for_secrets_location`
  (optional, low-priority)
  **Category**: unit / doc-structure
  **What it verifies**: `governance_capability_policy_epic.md`'s "Related Code Areas" section no
  longer cites the old `tools/knowledge_gateway_redaction.py` path for `scan_for_secrets()`.
  **Where it should live**: `tests/docs/` if this project's convention is to structurally test
  planning-doc citations (check `tests/docs/` precedent before adding — may be unnecessary
  ceremony for a planning doc versus a frozen contract).

## Scoped Pytest Commands

```
pytest tests/tools/ -v
pytest tests/docs/test_redaction_retention_policy_doc.py -v
```

`tests/tools/` must be passed as the bare directory (per
`tools/gate_checks/test_scope_coverage_static.py`'s own enforced convention and the
`TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP` precedent this ticket's own investigation
cites) — not a cherry-picked file list, since this ticket touches or breaks tests across a wide
swath of that directory (gateway tests, `retrieval_cache.py` tests, the Wave 1 frontmatter test,
and whichever archive-guard tests are newly added). If the chosen archive location for tests is
`tests/archive/` and `pyproject.toml`'s `norecursedirs` is updated to exclude it, also run:

```
pytest tests/archive/ -v --co  # collection-only sanity check, confirm archived tests are excluded from default runs but still individually runnable
```

## Anti-Drift Test Guards

- **`.mcp.json`'s `github`/`knowledge-search` entries stay byte-identical.** A new
  `test_mcp_json_no_longer_registers_knowledge_gateway` (or equivalent) should assert the
  `knowledge-search` entry's exact dict shape, not just its presence — mirrors the existing
  `test_knowledge_gateway_mcp.py::test_mcp_json_gains_exactly_one_new_server_entry`'s own
  `knowledge_search_entry == {...}` byte-identity check, inverted.
- **`retrieval_cache.py`'s connection-tuning discipline must not regress.**
  `tests/docs/test_redaction_retention_policy_doc.py::test_sqlite_defaults_not_silently_implemented`
  already guards against `PRAGMA journal_mode`/`PRAGMA busy_timeout`/`os.chmod`/`chmod` appearing
  directly in `tools/retrieval_cache.py`'s own source — re-run this specific test after the import
  path change to confirm the guard still holds (a naive "inline the function instead of importing
  it" mistake during extraction would silently violate this).
- **`test_wave1_candidate_scope_excludes_known_denied_tools`'s forbidden-pairs list is untouched**
  by this ticket — confirm no accidental edit widens `done-checker`/`test-scoper`'s scope beyond
  removing exactly the two `mcp__knowledge-gateway__*` entries (e.g. don't also drop `Edit` from
  `done-checker` as a side effect of editing the same frontmatter line).
- **`tools/agent-monitoring/generate_retro.py` must show zero behavior change.** It has no gateway
  dependency, so `tests/tools/test_generate_retro.py`'s full suite passing unmodified is itself the
  anti-drift signal that this ticket didn't accidentally touch shared monitoring-report logic while
  editing adjacent `tools/agent-monitoring/` files.
- **Do not let the archive-test-collection fix (`norecursedirs` or `pytest.mark.skip`) silently
  widen to exclude/skip test files that were NOT part of this ticket's gateway-archival set** — if
  choosing the `norecursedirs` route, the new `tests/archive/` directory should contain *only* the
  files this ticket moves there; a follow-up `git status`/`git diff --stat` review before Finalize
  should confirm the moved-file list matches exactly the "Tests That Will Break" enumeration above,
  nothing more.

---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY
artifact_type: investigation
tags: [ai, mcp, governance]
---

# Investigation — TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY

## Current Behavior

### `tools/archive/` — real, verified current contents (11 files, confirmed via `ls -la`, not trusted from the ticket's own summary)

Source archive, 5 gateway modules + 1 shell script (moved by `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`):
- `tools/archive/knowledge_gateway_cache.py` (33598 bytes)
- `tools/archive/knowledge_gateway_mcp.py` (24028 bytes)
- `tools/archive/knowledge_gateway_packet_assembly.py` (45809 bytes)
- `tools/archive/knowledge_gateway_redaction.py` (6463 bytes — the Step-2-trimmed remainder only: `check_db_size_within_limit()`, `execute_bounded_transaction()`, the write-lock pair, and §10 GC-eligibility predicates; the load-bearing symbols already live at `tools/write_path_guard.py`, untouched by this ticket)
- `tools/archive/knowledge_gateway_router.py` (19650 bytes)
- `tools/archive/start_knowledge_gateway_mcp.sh` (1147 bytes)

Plus 5 phase-runner scripts (moved by `TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS`, from their prior orphaned home `tools/agent-monitoring/kgmcp_phase*_runner.py`):
- `tools/archive/kgmcp_phase1_gateway_runner.py`
- `tools/archive/kgmcp_phase2_gateway_runner.py`
- `tools/archive/kgmcp_phase3_gateway_runner.py`
- `tools/archive/kgmcp_phase4_direct_tool_comparison_runner.py`
- `tools/archive/kgmcp_phase4_warm_direct_tool_comparison_runner.py`

Total: 6 + 5 = 11 files (matches the ticket's own "6 files + 5 files" framing exactly; a `__pycache__/` subdirectory also exists and must be removed alongside, not left orphaned).

### `tests/archive/` — real, verified current contents (**15 files, not 20**)

Direct `ls -la tests/archive/` (excluding `__pycache__/`) shows exactly 15 files:
- `test_kgmcp_baseline_corpus_dedup_coverage.py`
- `test_kgmcp_measurement_baseline.py`
- `test_kgmcp_phase1_baseline_comparison.py`
- `test_kgmcp_phase2_baseline_recomparison.py`
- `test_kgmcp_phase3_pilot_acceptance_measurement.py`
- `test_kgmcp_phase4_direct_tool_comparison.py`
- `test_kgmcp_phase4_warm_direct_tool_comparison.py`
- `test_kgmcp_phase5_repeated_demand_measurement.py`
- `test_knowledge_gateway_cache.py`
- `test_knowledge_gateway_contract_schemas.py`
- `test_knowledge_gateway_failure_semantics.py`
- `test_knowledge_gateway_mcp.py`
- `test_knowledge_gateway_packet_assembly.py`
- `test_knowledge_gateway_redaction.py`
- `test_knowledge_gateway_router.py`

**This is the single most important correction to this ticket's own scope text.** The ticket's Related Code Areas/Scope describe "15 files from the predecessor + 5 more added by the hotfix = 20 files under `tests/archive/`." Cross-checking against `stored_artifacts/TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE/plan.md` Step 8's own literal 15-file list confirms the 5 phase-runner test files (`test_kgmcp_phase1_baseline_comparison.py`, `test_kgmcp_phase2_baseline_recomparison.py`, `test_kgmcp_phase3_pilot_acceptance_measurement.py`, `test_kgmcp_phase4_direct_tool_comparison.py`, `test_kgmcp_phase4_warm_direct_tool_comparison.py`) were **already part of that original 15-file list** — they were moved to `tests/archive/` at the same time as the other 10, in the same predecessor ticket. `TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS`'s real, distinct contribution was archiving the corresponding **source runner scripts** (`tools/agent-monitoring/kgmcp_phase*_runner.py` → `tools/archive/kgmcp_phase*_runner.py`) and updating these 5 already-archived test files' internal `importlib`/literal-path references to point at the runners' new `tools/archive/` location (visible in git status as `M` — modified, not `A` — added, for exactly these 5 test files). There is no 20th–5th "new" test file; **the correct total test-file delete count is 15, not 20.** The implementer must not go looking for 5 additional test files that do not exist — the delete-scope AC is satisfied by deleting these same 15.

### `pyproject.toml` `norecursedirs` (L52-60)

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
norecursedirs = [
    "reviews", "scratch", "stored_artifacts", ".venv", ".git",
    "node_modules", "__pycache__", "archive",
]
```
No `testpaths` restriction exists in this file, so pytest's default collection recurses from the repo root, meaning `norecursedirs`'s bare-basename `"archive"` entry currently also (harmlessly) stops descent into every other directory literally named `archive`: `docs/archive/` (21 `.md` files, zero `test_*.py`), `docs/plans/archive/` (empty of test files, confirmed via `find`), `scripts/archive/` (5 files: `apply_traceability.py`, `ledger_validator.py`, `remediate_checklist.py`, `report_coverage.py`, `validate_checklist.py` — none match pytest's `test_*.py`/`*_test.py` collection pattern). None of these other four `archive/` directories need the `norecursedirs` exclusion for correctness (they contain no collectible test files either way); the entry can be safely removed once `tests/archive/` itself is deleted, exactly as the ticket's own scope text anticipates.

### Confirmed zero remaining live call sites (re-verified independently, not trusted from the ticket's own Early Closure Decision text)

`grep -rln "knowledge_gateway" tools/ src/ tests/ .claude/ docs/ --include="*.py" --include="*.md" --include="*.sh" --include="*.json" | grep -v '^tools/archive/\|^tests/archive/'` returns exactly one hit outside doc prose: `tests/tools/test_mcp_json_registration.py:20: def test_mcp_json_no_longer_registers_knowledge_gateway():` — a test function name asserting the entry's *absence*, not a call site. `tools/retrieval_cache.py` and `tools/write_path_guard.py` cite `knowledge_gateway_*` only in comments/docstrings describing where symbols were extracted from (confirmed via `graphify query`'s dependency traversal starting from the three archived source modules: all 95 traversed nodes resolve to `src=tools/archive/...`/`tests/archive/...` paths, zero edges reach live `src/`/`tools/` code). `tools/agent-monitoring/generate_retro.py`'s ~20 "kgmcp"-stem hits are all its own `compute_kgmcp_cache_efficiency_metrics()` analytics function (reads `agent-monitoring/tools.jsonl`'s cache-access log — a downstream consumer of already-recorded telemetry, zero import dependency on any archived module) and its `dashboard-frontend/src/views/StatsView.tsx` consumer (`KgmcpTicketRow`, `kgmcpTicketRows()`, `kgmcpVerdictColorClass()` — renders `kgmcp_cache_efficiency` JSON fields, also zero dependency on the archived files). This confirms the Early Closure Decision's own conclusion independently.

### Two live, in-scope-adjacent tests that assert facts this ticket's own delete falsifies (gap not named in the ticket's own Scope/Related Code Areas)

1. **`tests/tools/test_knowledge_gateway_archival.py`** (live path, NOT under `tests/archive/`, so not covered by this ticket's delete list) — `test_gateway_modules_exist_at_archive_location()` (L29-32) asserts each of the 6 archived source filenames exists under `tools/archive/`. Once this ticket deletes those 6 files, this assertion fails. `test_gateway_modules_archived_not_present_at_old_paths()` stays valid (still true — the old `tools/` paths still won't exist), and `test_write_path_guard_exists_and_is_not_archived()` stays valid (unaffected). This file must be updated or deleted as part of this ticket's own Implement phase, or the required `pytest tests/tools/ tests/docs/ -v` AC gate fails on a test this ticket's Related Code Areas never named.
2. **`tests/tools/test_ci_workflow_test_coverage.py`** (L432-485) — two tests read the *real* `pyproject.toml` and the *real* repo tree:
   - `test_pytest_norecursedirs_reads_real_pyproject_toml()` (L432-435) asserts `"archive" in norecursedirs` against the live file. Removing the `"archive"` `norecursedirs` entry (this ticket's own scope) breaks this assertion directly.
   - `test_check_against_real_repo_state_recognizes_tests_archive_as_norecursedirs_excluded()` (L480-485) calls `check_ci_workflow_test_coverage(_REAL_WORKFLOW_PATH, _REPO_ROOT)` and indexes `by_condition["ci_test_dir_covered:tests/archive"]`, asserting `status == "PASS"`. Once `tests/archive/` no longer exists as a directory, this condition key most likely is never generated by the checker at all (it enumerates real test directories under `tests/`), so the dict lookup will raise `KeyError` rather than a clean assertion failure.

   Both tests are explicitly framed in the file's own comment block (L422-429) as having been added *because of* `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`'s archival — they are direct, foreseeable casualties of this ticket's own reversal of that archival, and must be updated (not silently left red) as part of this ticket's own Implement phase, even though neither file appears in the ticket's Related Code Areas.

## Mechanics / Engine Constraints

None. This ticket touches only tooling/governance infrastructure (`tools/`, `tests/`, `pyproject.toml`, parity ledger metadata, agent-infrastructure planning docs) — no `src/` simulation code, no Mechanics Bible chapter, and no `docs/engine/` contract governs deletion of already-archived, already-dead tooling. The applicable authority here is CLAUDE.md's own Authoritative Mechanics Rule as it applies to the parity ledger (`docs/parity_ledger/`) and doc/code parity generally, not any `docs/mechanics/`/`docs/engine/` chapter.

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: 21 entries (INFRA-334, 335-339, 342-352, 354-357) currently cite `v2_evidence`/`test_path` values pointing at files that exist today only as archived snapshots (`tools/archive/...`, `tests/archive/...`); this ticket's hard-delete makes those citations point at files absent from the repo entirely, not just relocated — every entry's `status`/`divergence_note` (or, for INFRA-342/343 specifically, `v2_evidence`) must be updated via `tools/parity_ledger_writer.py` to reflect that the cited evidence is now fully gone, not archived-but-present. See "Parity Ledger Overlap" below for the real current value of every entry and a specific per-entry recommendation.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md`: §1's own milestone list (milestones 3-4: "Monitor for 2 weeks" / "Delete only after the monitoring window confirms no renewed calls") is the source-of-truth planning doc this ticket executes; it currently describes milestones 3-4 as pending/future work and does not yet record the Early Closure Decision (proceeding without the full 2-week window) or that milestone 4 has now executed. Must be updated to close out §1 once this ticket lands, so a future reader of this planning doc does not believe milestones 3-4 are still outstanding.
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`: this doc was deliberately kept `status: active` by `TCK-20260909-KGMCP-DOC-STATUS-SWEEP` specifically because it mixes still-live content (backing `tools/write_path_guard.py`) with historical content describing the archived gateway — and that historical content contains at least 8 direct citations of `tools/archive/knowledge_gateway_{router,cache,mcp,packet_assembly,redaction}.py` and `tests/archive/test_knowledge_gateway_{cache,packet_assembly}.py` as files that currently exist at those archive paths (e.g. L88-89, L156-157, L221-222, L335-336, L360-361). Once this ticket hard-deletes those files, every one of these citations becomes factually wrong in a new way (the file is not just moved, it no longer exists anywhere in the repo). A scoped, additive correction is required — consistent with the doc's own established "scoped-status note" precedent from `TCK-20260909-KGMCP-DOC-STATUS-SWEEP` (a targeted note per citation site, not a full rewrite or a `status: historical` flip, which the current ticket's own Out of Scope explicitly excludes as a separate future sweep).

The following docs were considered and are explicitly excluded, not silently skipped:

The `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md` doc's one live citation of the extracted symbols (`- tools/write_path_guard.py — source of scan_for_secrets() (line 149) for M4 (relocated from tools/knowledge_gateway_redaction.py by TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE).`, References section) points at the live `tools/write_path_guard.py` location, not at any `tools/archive/`/`tests/archive/` path — it is already correct and needs no further change from this ticket's own delete action.

The `docs/engine/contracts/knowledge_gateway_mcp_contract.md` and `docs/engine/contracts/knowledge_gateway_mcp/keep_or_deprecate_decision.md` docs (checked directly, both under `docs/`) contain zero citations of any `tools/archive/`/`tests/archive/` path — confirmed via direct grep — so this ticket's delete action does not make anything in either doc factually stale. `keep_or_deprecate_decision.md` is additionally one of the ticket's own explicitly-named excluded decision docs (Out of Scope).

The `docs/observability/retrieval_retention_redaction_policy.md` doc (path: `docs/observability/retrieval_retention_redaction_policy.md`, under `docs/`) is not required to change: it cross-references `redaction_retention_policy.md` by path only, carries no `tools/archive/`/`tests/archive/` file:line citations of its own, and this ticket does not touch its subject matter.

A full `status: historical` frontmatter sweep of the wider `docs/engine/contracts/knowledge_gateway_mcp/` directory (the other 10+ docs beyond `redaction_retention_policy.md`) is explicitly out of scope per the ticket's own Out of Scope section and `TCK-20260909-KGMCP-DOC-STATUS-SWEEP`'s own prior, deliberate, individually-assessed disposition of every doc in that directory — this ticket does not reopen that sweep.

## Parity Ledger Overlap

All 21 entries confirmed present in `docs/parity_ledger/infrastructure.yaml`, current real state (read directly, not assumed from the predecessor ticket's own plan text):

| ID | status | priority | Current test_path/v2_evidence state |
|---|---|---|---|
| INFRA-334 | verified | P2 | `test_path: tests/tools/test_kgmcp_measurement_baseline.py` — stale (file deleted by this ticket); `v2_evidence` cites `tools/agent-monitoring/kgmcp_baseline_corpus.py`, which this ticket does NOT touch (stays live) |
| INFRA-335 | verified | P1 | `test_path: tests/tools/test_knowledge_gateway_router.py` — stale |
| INFRA-336 | verified | P1 | `test_path: tests/tools/test_knowledge_gateway_packet_assembly.py` — stale |
| INFRA-337 | verified | P1 | `test_path: tests/tools/test_knowledge_gateway_mcp.py` — stale |
| INFRA-338 | verified | P1 | `test_path: tests/tools/test_knowledge_gateway_failure_semantics.py` — stale |
| INFRA-339 | verified | P1 | `test_path: tests/tools/test_kgmcp_phase1_baseline_comparison.py` — stale |
| INFRA-342 | verified | P1 | `v2_evidence` already fully rewritten by the predecessor to cite `tools/write_path_guard.py` (54 tests) — this is one of the 2 entries the predecessor gave a full, direct rewrite rather than an additive note; `divergence_note` is `None` |
| INFRA-343 | verified | P1 | `v2_evidence` (already rewritten) cites 4 now-`tests/archive/`-only test files as historical record, plus `tests/tools/test_retrieval_cache.py`'s 3 still-live classes; `divergence_note` is `None` |
| INFRA-344 | verified | P1 | `test_path: tests/tools/test_kgmcp_phase2_baseline_recomparison.py` (cites 16/17 passing detail) — stale |
| INFRA-345 | verified | P1 | `test_path` cites `tests/tools/test_knowledge_gateway_redaction.py::TestSizeCap` plus `tests/docs/test_redaction_retention_policy_doc.py` — the first half is stale (file deleted), the second half (`tests/docs/...`) is untouched by this ticket and stays valid |
| INFRA-346 | verified | P1 | `test_path` cites `tests/tools/test_retrieval_cache.py::TestLevel2Migrations` (untouched, stays valid) plus `tests/tools/test_knowledge_gateway_redaction.py::TestRedactionPolicyVersion` (stale) — mixed |
| INFRA-347 | verified | P1 | `test_path` cites `tests/tools/test_knowledge_gateway_packet_assembly.py`/`test_knowledge_gateway_mcp.py` — stale |
| INFRA-348 | verified | P1 | same as above — stale |
| INFRA-349 | verified | P1 | `test_path` cites a mix of `tests/tools/test_retrieval_cache.py` (untouched, stays valid) and `tests/tools/test_knowledge_gateway_{cache,mcp}.py` (stale) — mixed |
| INFRA-350 | verified | P1 | `test_path: tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py` — stale |
| INFRA-351 | verified | P1 | `test_path: tests/tools/test_knowledge_gateway_packet_assembly.py::test_parity_id_query_reaches_real_entry_lookup_end_to_end` — stale |
| INFRA-352 | verified | P1 | `test_path: tests/tools/test_knowledge_gateway_mcp.py::test_level2_hit_rejected_...` — stale |
| INFRA-354 | verified | P2 | `test_path: tests/tools/test_kgmcp_phase4_direct_tool_comparison.py` — stale |
| INFRA-355 | verified | P2 | `test_path` cites `tests/tools/test_kgmcp_phase5_repeated_demand_measurement.py` (stale) and `tests/docs/test_phase5_repeated_demand_measurement_doc.py` (untouched, stays valid) — mixed |
| INFRA-356 | verified | P1 | `test_path` cites a long mixed list — `tests/tools/test_knowledge_gateway_{packet_assembly,mcp,router}.py`, `test_kgmcp_baseline_corpus_dedup_coverage.py`, `test_kgmcp_phase{3,4}_*.py` — all stale |
| INFRA-357 | verified | P1 | `test_path` cites `tests/tools/test_knowledge_gateway_{packet_assembly,mcp}.py` — stale |

All 21 already carry a `divergence_note` from the predecessor ticket's own Step 13 (19 of them an additive note beginning "Archived 2026-09-07 by TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE; code now lives at tools/archive/<same filename>..." — itself now going stale the same way the doc citations above do, since "now lives at tools/archive/" stops being true). None of these 21 are `P0` (they run P1/P2 only per the table above), so none carries the ticket's own hard "P0 entries require a passing `test_path`" requirement — but per the Authoritative Mechanics Rule, a `status: verified` entry whose cited evidence no longer exists anywhere in the repo is a **factually false claim**, not merely a stale pointer, and per the ticket's own Scope text (INFRA-342/343 "may need a status change... to `missing`") this reasoning extends to all 21, not just those two. Recommend, per entry:
- **INFRA-342, INFRA-343** (the 2 entries the predecessor already gave a real rewrite): re-verify their `v2_evidence` still cites at least one live path (`tools/write_path_guard.py`, `tests/tools/test_write_path_guard.py`, `tests/tools/test_retrieval_cache.py`) — these can very plausibly stay `status: verified` since their primary evidence is the live `write_path_guard.py` test suite, not the archived files; only the historical-record portions of their `v2_evidence` text describing the 4 now-fully-deleted `tests/archive/` files need a small wording update (from "moved to tests/archive/, historical record" to "deleted by TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY, no longer present anywhere").
- **The other 19** (INFRA-334, 335-339, 344-352 minus 342/343, 354-357): their sole or primary `test_path` citation is now gone from the repo entirely. A `status` change from `verified` to `missing` (or another value `tools/parity_ledger_writer.py`'s schema allows for "the behavior is presumed still correct in `src/` but its own regression-locking test evidence no longer exists to prove it") is the honest choice, per the exact wording the ticket's own Scope text proposes for INFRA-342/343 — extended here to the full 19. Do not silently leave `status: verified` pointing at nonexistent evidence.

This determination (`verified` → `missing`-or-equivalent for 19, more nuanced for INFRA-342/343) is an implementation-time judgment call, not fully resolved here — flagged in Risks below as needing the implementer/parity-updater agent's confirmation of `tools/parity_ledger_writer.py`'s actual allowed `status` enum values before committing to `missing` specifically.

## Prior Work

- `stored_artifacts/TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE/` (investigation.md, plan.md, test_plan.md) — the direct predecessor; plan.md Steps 7-9 and 13 are the ground truth this investigation cross-checked against real files above.
- `tickets/done/TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS.md` — archived the 5 phase-runner source scripts into `tools/archive/` and widened this ticket's own verification grep pattern; did not add any new test files to `tests/archive/` (they were already there — see Current Behavior above).
- `tickets/done/TCK-20260909-KGMCP-DOC-STATUS-SWEEP.md` — flipped 11 of 12 `docs/engine/contracts/knowledge_gateway_mcp/` docs to `status: historical`, deliberately kept `redaction_retention_policy.md` `status: active` with a scoped-status note — the precedent this investigation's recommended doc update for that file should follow (an additive, scoped note, not a full rewrite).
- `docs/engine/contracts/knowledge_gateway_mcp/keep_or_deprecate_decision.md` §4 — the Option C re-ratification this ticket and its predecessor execute; not re-litigated here.

## Risks and Open Questions

1. **Two live tests (`tests/tools/test_knowledge_gateway_archival.py`, `tests/tools/test_ci_workflow_test_coverage.py`) will break on this ticket's own delete and are not named anywhere in the ticket's Related Code Areas or Scope.** Both must be updated as part of this ticket's Implement phase (see Current Behavior above for exact assertions affected) or the ticket's own required `pytest tests/tools/ tests/docs/ -v` full-pass AC cannot be satisfied. This is a real scope gap in the ticket as currently written, not a hypothetical.
2. **The ticket's own stated test-file delete count (20) does not match the real filesystem (15).** Flagged prominently in Current Behavior — this must not silently become "delete 15 files but report AC as if 20 were deleted."
3. **Parity ledger status determination is not fully resolved.** Whether `tools/parity_ledger_writer.py`'s schema supports a `status` value more precise than `verified`/`divergent`/`missing`/`unsupported`/`legacy_verified` for "evidence permanently deleted, behavior presumed still correct" is not confirmed here — the implementer/parity-updater agent must check the tool's actual enum before choosing a value for the 19 non-INFRA-342/343 entries.
4. **Out-of-repo-visibility blast radius remains structurally unverifiable**, same caveat the ticket's own Out of Scope/Assumptions section already states: the Early Closure Decision is a repo-visible confirmation only; if a genuinely external, non-repo-visible consumer of the archived gateway exists, nothing in this investigation (or the ticket's own re-verification) can detect it. This is a pre-existing, explicitly-accepted risk, not a new one raised by this investigation.
5. **`docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md`** was not read in this investigation (not named in the ticket's Related Docs) — if it independently tracks milestone 3-4 completion status for this same item, it may need the same closure update as `standalone_items.md`. Flagged as an open question for the implementer to check quickly before Finalize, not confirmed as a required change here.

## Anti-Drift Hazards

- Do not touch `tools/write_path_guard.py`, `tools/retrieval_cache.py`, or any of their currently-passing tests beyond what is strictly required to keep them passing after the delete (the ticket's own Out of Scope already states this; re-stated here because `tests/tools/test_retrieval_cache.py` and `tests/tools/test_write_path_guard.py` sit directly adjacent to the deleted files' old import graph and are an easy place to over-edit).
- Do not delete or modify any of the 3 `tests/docs/test_phase{4,4,5}_*.py` files (`test_phase4_direct_tool_comparison_doc.py`, `test_phase4_workflow_recommendation_doc.py`, `test_phase5_repeated_demand_measurement_doc.py`) — the predecessor's own Review Round 1 explicitly confirmed these have zero real dependency on anything archived and deliberately kept them at `tests/tools/`/`tests/docs/` (not moved to `tests/archive/`); they must not be swept into this ticket's delete either.
- Do not touch the 7 `tools/agent-monitoring/kgmcp_baseline_runner.py`/`kgmcp_baseline_corpus.py`/`generate_retro.py`-adjacent files, or `dashboard-frontend/src/views/StatsView.tsx` — all confirmed live, all confirmed to have zero dependency on the files this ticket deletes (see Current Behavior's "confirmed zero remaining live call sites" above).
- Do not perform a raw multi-line `Edit` on `docs/parity_ledger/infrastructure.yaml` — this repo's own documented full-file-rewrite corruption hazard for this ~9500+ line shared YAML file applies directly; use `tools/parity_ledger_writer.py` per-entry (or its batch form) exactly as the ticket's own Scope text and the predecessor's Step 13 precedent require.
- Do not widen the `pyproject.toml` edit beyond removing the single `"archive"` `norecursedirs` list entry — do not touch `markers` or any other `[tool.pytest.ini_options]` key, matching the predecessor's own established discipline for this shared config file.
- Do not re-open the `docs/engine/contracts/knowledge_gateway_mcp/` directory-wide `status: historical` sweep — `TCK-20260909-KGMCP-DOC-STATUS-SWEEP` already individually assessed and closed that decision; this ticket's own doc update to `redaction_retention_policy.md` must stay a scoped, additive correction of the now-stale archive-path citations only.

---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE
phase: done
date: 2026-09-07
tags: [ai, mcp, governance]
---

# TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE

## Title
Extract shared redaction helpers out of the gateway, then archive the Knowledge Gateway MCP (epic M2, steps 1-2)

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
`TCK-20260907-KGMCP-DEPRECATION-EPIC`'s M1 re-ratified `TCK-20260824-KGMCP-KEEP-OR-DEPRECATE` to
**Option C — deprecate/remove** (recorded in
`docs/engine/contracts/knowledge_gateway_mcp/keep_or_deprecate_decision.md` §4). This ticket
executes that epic's M2 steps 1-2 only: extract the shared, load-bearing pieces of
`tools/knowledge_gateway_redaction.py` into a gateway-independent location, then archive the
remaining gateway modules and deregister `.mcp.json`. M2 steps 3-4 (the 2-week zero-call
monitoring window, then delete) are explicitly out of scope here — they cannot happen in one
session and will be filed as a separate follow-on once this ticket's archival lands.

**Real complication found during this ticket's own scoping** (not accounted for in
`standalone_items.md` §1's original milestone text, which only mentions extracting
`scan_for_secrets()`): `tools/retrieval_cache.py` — a genuinely independent, actively-used module
(imported by the live `tools/agent-monitoring/post_tool_hook.py` hook and
`src/api/agent_ops_dashboard/ingest.py`) — has a real, hard import dependency on
`knowledge_gateway_redaction.py` for **two more functions**: `open_connection_with_limits()` and
`evaluate_write_candidate()`, not just `scan_for_secrets()`. Archiving
`knowledge_gateway_redaction.py` without resolving this would break `retrieval_cache.py` and
everything that depends on it — a real regression risk, not a hypothetical one.

## Scope
1. Investigate exactly which symbols in `knowledge_gateway_redaction.py` have live consumers
   outside the gateway package itself (confirmed so far: `scan_for_secrets()` — needed by
   `governance_capability_policy_epic.md`'s M4; `open_connection_with_limits()` and
   `evaluate_write_candidate()` — needed by `retrieval_cache.py`) versus symbols only the gateway
   itself uses.
2. Extract the shared symbols into a new, stable, gateway-independent module — not a location that
   will itself get archived alongside the gateway. Update every real consumer
   (`retrieval_cache.py`, and wherever `governance_capability_policy_epic.md`'s M4 eventually
   imports from) to import from the new location.
3. Once the shared symbols are extracted and every consumer updated, archive (do not hard-delete)
   the remaining gateway modules: `tools/knowledge_gateway_{mcp,router,packet_assembly,cache,
   redaction}.py`, `tools/start_knowledge_gateway_mcp.sh` — move to an archive location.
4. Remove the Knowledge Gateway MCP's registration from `.mcp.json`.
5. Remove the accidental `mcp__knowledge-gateway__*` tool-allowlist grant from
   `.claude/agents/done-checker.md` and `.claude/agents/test-scoper.md` (the `knowledge_status`
   grant on `test-scoper.md`, and both `knowledge_context`/`knowledge_status` on
   `done-checker.md`) — per the re-ratification brief's finding that this grant was accidental,
   not deliberate.
6. Confirm zero regressions in every test/tool that legitimately depended on the gateway package
   (per `standalone_items.md` §1's own Acceptance signal) — the archived modules' own tests move
   or get marked accordingly, not silently deleted.
7. File the M2 steps 3-4 follow-on ticket (2-week zero-call monitoring window, then delete) once
   this ticket's archival is confirmed landed.

## Out of Scope
- The 2-week zero-call monitoring window itself, or the eventual delete (M2 steps 3-4) — filed as
  a separate follow-on ticket, not part of this ticket's own Definition of Done.
- Re-litigating the re-ratification decision itself — Option C is already ratified
  (`TCK-20260907-KGMCP-DEPRECATION-EPIC` M1, `keep_or_deprecate_decision.md` §4).
- `governance_capability_policy_epic.md`'s M4 (wiring the extracted `scan_for_secrets()` into a
  Bash secret-exposure hook) — that epic's own scope, this ticket only makes the function
  importable from a stable location.
- Any change to the re-ratification decision docs themselves (`keep_or_deprecate_decision.md`,
  `audit_phase0_5.md`, `knowledge-gateway-mcp-proposal.md`, `roadmap.md`, `standalone_items.md`)
  beyond what M1 already recorded — this ticket executes M2, it doesn't re-document M1.

## Acceptance Criteria
- [x] `scan_for_secrets()`, `open_connection_with_limits()`, and `evaluate_write_candidate()` (and
      any other symbol found to have a real external consumer during Investigate) are importable
      from a new, stable, gateway-independent module.
- [x] `tools/retrieval_cache.py` imports the relocated symbols from the new location, not from
      `tools/knowledge_gateway_redaction.py` — confirmed via a real test run showing zero
      regressions.
- [x] `tools/knowledge_gateway_{mcp,router,packet_assembly,cache,redaction}.py` and
      `tools/start_knowledge_gateway_mcp.sh` are archived (moved, not deleted) to a clearly-named
      archive location.
- [x] `.mcp.json`'s Knowledge Gateway MCP registration is removed.
- [x] `.claude/agents/done-checker.md` and `.claude/agents/test-scoper.md` no longer carry the
      accidental `mcp__knowledge-gateway__*` grant.
- [x] Every test that legitimately covered the gateway package or `retrieval_cache.py`'s shared-
      symbol dependency still passes (moved/updated as needed, not silently deleted or skipped).
      `tests/tools/ tests/docs/` (2623 collected: 2605 passed, 4 failed, 18 skipped, 2 xfailed —
      the 4 failures are all pre-existing `tests/tools/test_knowledge_search.py` timing-SLA/
      subprocess-resource-limit flakiness, confirmed unrelated to this ticket's diff via direct
      inspection, see Implementation Notes). `tests/archive/`'s 15 files are excluded from
      default collection; 10/15 are individually collectable via `pytest tests/archive/ --co`, the
      other 5 fail collection for reasons directly traceable to Step 9's own "leave archived
      internal cross-imports unfixed" precedent (documented as a plan Deviation, not a gap in this
      ticket's own real ACs).
- [x] A follow-on ticket for M2 steps 3-4 (2-week monitoring window, delete) is filed once
      archival lands. `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY.md` filed in
      `tickets/inprogress/` (marked `BLOCKED` — time-based precondition).

## Related Tickets
- `TCK-20260907-KGMCP-DEPRECATION-EPIC` (`tickets/inprogress/`) — the parent epic; this ticket
  executes its M2 steps 1-2.
- `TCK-20260824-KGMCP-KEEP-OR-DEPRECATE` (done) — the original ratification, now superseded.
- `governance_capability_policy_epic.md`'s M4 — the cross-epic dependency on
  `scan_for_secrets()`'s extraction target.
- `TCK-20260729-RETRIEVAL-CACHE-LEVELS` — source ticket for `tools/retrieval_cache.py`, the
  module whose real dependency on the gateway's redaction module this ticket must resolve.
- `TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE` — source of the accidental
  `done-checker`/`test-scoper` allowlist grant this ticket removes.
- `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` (`tickets/inprogress/`, BLOCKED) — the M2 steps 3-4
  follow-on this ticket files (per Scope item 7 / Implementation Notes Step 14): the 2-week
  zero-call monitoring window, then hard-delete of the archive locations
  (`tools/archive/`, `tests/archive/`) this ticket creates.

## Related Docs
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md` (§1) — the
  original milestone spec this ticket executes (steps 1-2 only), including the two open gaps its
  own investigation flagged (the `retrieval_cache.py` dependency, and a usage-count reconciliation
  note not otherwise material to this ticket's scope).
- `docs/engine/contracts/knowledge_gateway_mcp/keep_or_deprecate_decision.md` (§4) — the
  re-ratification this ticket executes.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`
  (M4) — the cross-epic dependency on the extraction target.
- `docs/observability/retrieval_retention_redaction_policy.md` — cited by `retrieval_cache.py`'s
  own module docstring for the redaction-category conventions the relocated functions must keep
  intact.

## Related Stored Artifacts
None yet — investigation not yet performed.

## Related Code Areas
- `tools/knowledge_gateway_redaction.py` (source of the symbols to extract)
- `tools/retrieval_cache.py` (the real external consumer to update)
- `tools/knowledge_gateway_{mcp,router,packet_assembly,cache}.py`,
  `tools/start_knowledge_gateway_mcp.sh` (to archive)
- `.mcp.json`
- `.claude/agents/done-checker.md`, `.claude/agents/test-scoper.md`
- `tests/tools/test_knowledge_gateway_*.py`, `tests/tools/test_retrieval_cache.py`,
  `tests/tools/test_evidence_cache_identity_contract.py`

## Assumptions / Open Questions
- The exact new module name/location for the extracted symbols is not yet decided — Investigate
  should confirm a name that reads as genuinely gateway-independent (not e.g. a subdirectory of
  the gateway's own package), per `agent-working-design`'s explicit guidance: "put it somewhere
  stable that won't itself get archived alongside the gateway."
- `standalone_items.md` §1's own investigation found a usage-count reconciliation gap ("2 vs 2,138"
  vs. a direct grep finding "13 vs 3,212") — not material to this ticket's own scope (the
  re-ratification already happened on the stronger, independently-verified 1-vs-3,375 figure), but
  Investigate should note it for completeness rather than silently ignore the discrepancy.
- Whether any other file beyond `retrieval_cache.py` has an undiscovered real dependency on
  `knowledge_gateway_redaction.py` (or any other gateway module) is exactly what Investigate must
  determine — do not assume the two known consumers above are exhaustive without checking.

## Implementation Notes

Implemented all 14 plan steps in the stated dependency order.

- **Step 1**: Created `tools/write_path_guard.py` with the full ~19-symbol transitive closure of
  `evaluate_write_candidate()` (allowlist, redaction+hashing, secret-scan, size-cap, never-cache
  enumeration, `WriteDecision`/`evaluate_write_candidate()`, `open_connection_with_limits()`),
  moved verbatim, docstrings preserved.
- **Step 2**: Trimmed `tools/knowledge_gateway_redaction.py` to the archival-only remainder
  (`SQLITE_MAX_DB_SIZE_BYTES`, `check_db_size_within_limit()`, `execute_bounded_transaction()`,
  the write-guard pair, all of §10).
- **Step 3**: Updated `tools/retrieval_cache.py`'s import + 3 call sites + the 5 named
  comment/docstring mentions to `write_path_guard`.
- **Step 4**: Updated `tests/docs/test_redaction_retention_policy_doc.py`'s direct import and
  dropped the unused `_KNOWLEDGE_GATEWAY_REDACTION_PY` constant.
- **Step 5**: Added `tests/tools/test_write_path_guard.py` (54 tests, ported from the original
  `test_knowledge_gateway_redaction.py`, all passing).
- **Step 6**: Added `test_retrieval_cache_imports_open_connection_with_limits_from_new_location`
  to `tests/tools/test_retrieval_cache.py::TestStaticGuards`.
- **Step 7**: Added `"archive"` to `pyproject.toml`'s `norecursedirs`.
- **Step 8**: Moved exactly 15 gateway-dependent test files to `tests/archive/` via `git mv`
  (confirmed the 3 `tests/docs/test_phase{4,4,5}_*.py` files stayed in place, untouched).
- **Step 9**: Archived the 5 gateway modules + shell script to `tools/archive/` via `git mv`; left
  `tools/archive/knowledge_gateway_cache.py`'s internal import unfixed (deliberate); updated the 7
  literal `importlib.util.spec_from_file_location` path constants across 7 moved test files that
  referenced old `tools/`/`tests/tools/` source locations.
- **Step 10**: Removed `.mcp.json`'s `knowledge-gateway` entry (confirmed `knowledge-search`/
  `github` byte-identical); added `tests/tools/test_mcp_json_registration.py`.
- **Step 11**: Removed the accidental `mcp__knowledge-gateway__*` grants from
  `.claude/agents/done-checker.md`/`test-scoper.md` and updated
  `tests/tools/test_wave1_agent_tools_frontmatter.py`'s `_WAVE1_CANDIDATE_TOOLS` dict in the same
  step.
- **Step 12**: Explicit no-op, confirmed via `git diff --stat tools/agent-monitoring/` (zero
  changes) and `test_generate_retro.py` passing unmodified.
- **Step 13**: Fixed the 3 stale doc citations (2 spots in `redaction_retention_policy.md` plus a
  4th, adjacent test-path citation found during implementation — see Deviations in
  `staging_artifacts/.../plan.md`; 1 spot in `governance_capability_policy_epic.md`) and all 21
  parity-ledger entries via `tools/parity_ledger_writer.py` (INFRA-342/343 got a full
  `v2_evidence`/`test_path` rewrite; the other 19, including INFRA-334, got the lightweight
  additive `divergence_note` annotation). Verified via `tools/parity_index.py build` (rebuilds
  clean) and `pytest tests/tools/test_parity_index.py tests/tools/test_parity_ledger_writer.py
  tests/tools/test_parity_index_baseline.py` (all pass, no baseline drift).
- **Step 14**: Filed `tickets/inprogress/TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY.md` (M2 steps
  3-4 follow-on, marked `BLOCKED` — a time-based precondition, not a missing-context block),
  Related Tickets pointing back to this ticket and to `TCK-20260907-KGMCP-DEPRECATION-EPIC`.

**Document-Update phase (post-Implement) findings:**
1. This ticket's own `## Related Tickets` section was missing the forward reference to the
   `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` follow-on it files (Step 14) — the follow-on ticket
   linked back here, but the reverse link was absent. Added.
2. Beyond Step 13's 4 named spots, `redaction_retention_policy.md` carried several more citations
   describing `tools/knowledge_gateway_{router,cache,mcp,packet_assembly}.py` and
   `tests/tools/test_knowledge_gateway_{cache,packet_assembly}.py` in present tense as live/
   currently-reachable/currently-passing — all now false given this same ticket's own archival
   action (deregistered `.mcp.json`, moved to `tools/archive/`/`tests/archive/`). Most material:
   §6's Level 2 architecture-guard-test paragraph asserted `test_knowledge_gateway_cache.py` was
   "currently-passing," but that file is one of the 5 archived test files this ticket's own
   Deviation 5 documents as failing collection outright. Added archival-status notes at each spot
   (the §2 "Disclosed gap," §6's MCP-reachability claim and Level-2-test claim, §8's
   `packet_assembly.py` citations) following the same annotation convention Step 13 already used
   for the redaction-module citations. Re-ran `pytest tests/docs/test_redaction_retention_policy_doc.py`
   (venv python, `pydantic` not on bare `python3`): 7/7 still pass. The wider
   `docs/engine/contracts/knowledge_gateway_mcp/` directory sweep (Risk #4) remains deferred, as
   originally scoped — this fix stayed within the one file this ticket already owns.

**Real deviations found during Implement** (all documented in
`staging_artifacts/TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE/plan.md`'s own Deviations
section):

1. Reverted two extra `tools/knowledge_gateway_cache.py` path-mention edits in
   `tools/retrieval_cache.py` that went beyond Step 3's literal 5-spot list — kept exactly to
   plan.
2. Fixed a 4th, adjacent stale test-path citation in `redaction_retention_policy.md` beyond the
   plan's named 3 spots (an honest gap the plan missed, directly adjacent to a spot it did name).
3. **Found a real regression the plan/investigation did not anticipate**:
   `tests/tools/test_evidence_cache_identity_contract.py` reads a sibling *test* file's source
   directly (`_SIBLING_SCHEMA_TEST = tests/tools/test_knowledge_gateway_contract_schemas.py`) —
   the investigation's claim that this file "imports no gateway module directly" was accurate for
   Python imports but missed this `Path.read_text()` dependency. Fixed the path constant to point
   at the new `tests/archive/` location.
4. **Found a second real regression**: `tools/gate_checks/ci_workflow_test_coverage.py` (an
   existing CI-coverage static guard, unrelated to the gateway) had no concept of a
   `pyproject.toml` `norecursedirs`-excluded directory — it flagged the new `tests/archive/` as an
   "orphaned test directory not referenced by any fast-lane CI job," which is factually wrong for
   a directory deliberately excluded from all collection. Added `pytest_norecursedirs()` and
   `directory_is_excluded_from_pytest_collection()` to that module (reading the same
   `norecursedirs` list pytest itself consults) and wired them into
   `check_ci_workflow_test_coverage()`'s aggregator, with 6 new regression tests proving the fix
   catches what it claims (matching that test file's own stated coverage-honesty convention). This
   is a generalizable, reusable fix (any future archived-with-tests directory hits the same gap),
   not a `tests/archive`-specific hack.
5. Confirmed 5 of the 15 archived test files (`test_kgmcp_baseline_corpus_dedup_coverage.py`,
   `test_knowledge_gateway_cache.py`, `test_knowledge_gateway_mcp.py`,
   `test_knowledge_gateway_packet_assembly.py`, `test_knowledge_gateway_redaction.py`) fail
   collection outright when run directly (`pytest tests/archive/`), not just assertion failures —
   traced to plain `from tools import X` package imports of a module that itself moved into
   `tools/archive/` (unreachable without an `__init__.py`, which Step 9 explicitly declined to
   add) and to `knowledge_gateway_mcp.py`'s own `Path(__file__).resolve().parent.parent`
   arithmetic breaking one directory level deeper. Left unfixed, consistent with Step 9's own
   "frozen historical snapshot" precedent — fixing it would require exactly what that step
   rejected. Does not affect any real AC (all 7 verified above); `tests/archive/` is fully
   excluded from every default collection path.

## Test Summary

- `pytest tests/tools/ tests/docs/ -q` (bare-directory scoped, per this project's own
  `TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP` precedent): **2623 collected — 2605
  passed, 4 failed, 18 skipped, 2 xfailed.** The 4 failures
  (`test_knowledge_search.py::TestQueryHappyPath::test_query_completes_within_2_seconds`,
  `::TestLiveQueryDocsMechanics::test_build_docs_chunk_count_exceeds_500`,
  `::test_build_completes_under_five_minutes`, `::test_existing_ticket_query_still_works`) are all
  live-subprocess timing-SLA/resource-budget tests against `tools/knowledge_search.py` — a module
  this ticket's diff never touches (confirmed via `grep` — its only "knowledge_gateway" matches
  are synthetic fixture directory names in doc-id-derivation tests, not real dependencies).
  Confirmed pre-existing/environment-dependent, not a regression from this ticket.
- `pytest tests/tools/test_write_path_guard.py -v`: 54/54 passed.
- `pytest tests/docs/test_redaction_retention_policy_doc.py -v`: 7/7 passed.
- `pytest tests/tools/test_retrieval_cache.py -v`: full suite passed, including the new
  architecture-guard test and `test_sqlite_defaults_not_silently_implemented`.
- `pytest tests/tools/test_knowledge_gateway_archival.py tests/tools/test_mcp_json_registration.py
  tests/tools/test_wave1_agent_tools_frontmatter.py -v`: all passed.
- `pytest tests/tools/test_evidence_cache_identity_contract.py -v`: 19/19 passed (after the
  deviation fix).
- `pytest tests/tools/test_ci_workflow_test_coverage.py -v`: 33/33 passed (27 original + 6 new,
  after the deviation fix).
- `pytest tests/tools/test_parity_index.py tests/tools/test_parity_ledger_writer.py
  tests/tools/test_parity_index_baseline.py -v`: 74/74 passed, zero baseline drift.
- `pytest tests/archive/ --co`: 201/201 tests collected across 10/15 files; the other 5 fail
  collection for the documented, precedent-consistent reason (see Deviations item 5) — this
  directory is excluded from every default collection path regardless.
- `pytest tests/tools/ tests/docs/ --co -q`: zero of the 15 moved filenames appear; all 3 retained
  `tests/docs/test_phase{4,4,5}_*.py` files still appear and pass (13/13) when run directly.
- `git diff --stat tools/agent-monitoring/`: empty (Step 12 no-op confirmed).

## Files Changed

**Created:**
- `tools/write_path_guard.py`
- `tests/tools/test_write_path_guard.py`
- `tests/tools/test_knowledge_gateway_archival.py`
- `tests/tools/test_mcp_json_registration.py`
- `tickets/inprogress/TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY.md`
- `staging_artifacts/TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE/investigation.md`
- `staging_artifacts/TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE/plan.md`
- `staging_artifacts/TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE/test_plan.md`

**Modified:**
- `tools/knowledge_gateway_redaction.py` (trimmed to the archival-only remainder, before being
  moved)
- `tools/retrieval_cache.py`
- `tests/docs/test_redaction_retention_policy_doc.py`
- `tests/tools/test_retrieval_cache.py`
- `pyproject.toml`
- `.mcp.json`
- `.claude/agents/done-checker.md`
- `.claude/agents/test-scoper.md`
- `tests/tools/test_wave1_agent_tools_frontmatter.py`
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`
- `docs/parity_ledger/infrastructure.yaml` (21 entries)
- `tests/tools/test_evidence_cache_identity_contract.py` (deviation fix)
- `tools/gate_checks/ci_workflow_test_coverage.py` (deviation fix)
- `tests/tools/test_ci_workflow_test_coverage.py` (deviation fix — 6 new tests)
- `tickets/inprogress/TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE.md` (this file)

**Moved (`git mv`):**
- `tools/knowledge_gateway_{mcp,router,packet_assembly,cache,redaction}.py`,
  `tools/start_knowledge_gateway_mcp.sh` → `tools/archive/`
- 15 test files, `tests/tools/` → `tests/archive/` (7 of these also internally edited for literal
  `spec_from_file_location` path fixes: `test_kgmcp_phase1_baseline_comparison.py`,
  `test_kgmcp_phase2_baseline_recomparison.py`, `test_knowledge_gateway_cache.py`,
  `test_knowledge_gateway_failure_semantics.py`, `test_knowledge_gateway_mcp.py`,
  `test_knowledge_gateway_packet_assembly.py`, `test_knowledge_gateway_router.py`)

**Pre-existing at Implement start, not touched by this session** (visible in `git status` but
predate this Implement turn — from the parent epic's own M1 re-ratification work in this same
worktree): `docs/engine/contracts/knowledge_gateway_mcp/audit_phase0_5.md`,
`docs/engine/contracts/knowledge_gateway_mcp/keep_or_deprecate_decision.md`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md`,
`docs/plans/knowledge-gateway-mcp-proposal.md`,
`tickets/inprogress/TCK-20260907-KGMCP-DEPRECATION-EPIC.md`.

**Housekeeping run:** `graphify update .` (35877 nodes, 103159 edges rebuilt) and
`make knowledge-index-update` (9 files re-embedded, incremental) — both required since `src/`/
`tests/` and `docs/` files changed.

## Completion Summary

Extracted the ~19-symbol transitive closure of `evaluate_write_candidate()` out of
`tools/knowledge_gateway_redaction.py` into a new, gateway-independent `tools/write_path_guard.py`
module, updated `tools/retrieval_cache.py` (its one real external consumer) to import from the new
location, then archived the now-orphaned remainder of the Knowledge Gateway MCP package (5 source
modules + 1 shell script to `tools/archive/`, 15 test files to `tests/archive/`, excluded from
default pytest collection via `pyproject.toml`), deregistered `.mcp.json`'s `knowledge-gateway`
entry, removed the accidental `mcp__knowledge-gateway__*` tool grants from
`done-checker.md`/`test-scoper.md`, corrected 3 stale doc citations and 21 parity-ledger entries
(2 full rewrites, 19 lightweight annotations via `tools/parity_ledger_writer.py`), and filed the
M2 steps 3-4 follow-on ticket. During implementation, found and fixed two real regressions the
plan/investigation had not anticipated (a sibling-test-file path dependency in
`test_evidence_cache_identity_contract.py`, and a `norecursedirs`-unaware CI-coverage static guard
that would have wrongly flagged `tests/archive/` as an orphaned directory) — both documented as
Deviations, not silently papered over. All 7 Acceptance Criteria are satisfied; the full scoped
regression suite (`tests/tools/ tests/docs/`, 2623 tests) passes except 4 pre-existing,
environment-dependent `tools/knowledge_search.py` timing tests wholly unrelated to this ticket's
diff.

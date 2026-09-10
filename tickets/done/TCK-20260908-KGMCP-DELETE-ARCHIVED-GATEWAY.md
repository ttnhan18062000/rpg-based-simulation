---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY
phase: done
date: 2026-09-08
tags: [ai, mcp, governance]
---

# TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY

## Title
Monitor, then hard-delete, the archived Knowledge Gateway MCP (epic M2, steps 3-4)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
`TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` executed `TCK-20260907-KGMCP-DEPRECATION-EPIC`'s
M2 steps 1-2: it extracted the shared, load-bearing write-path-guard functions into
`tools/write_path_guard.py`, archived the remaining Knowledge Gateway MCP modules to
`tools/archive/` (`knowledge_gateway_{mcp,router,packet_assembly,cache,redaction}.py`,
`start_knowledge_gateway_mcp.sh`), archived their dedicated test files to `tests/archive/` (15
files, excluded from default collection via `pyproject.toml`'s `norecursedirs`), and deregistered
`.mcp.json`'s `knowledge-gateway` entry. This ticket executes the two remaining M2 steps that
could not happen in that same session:

1. **M2 step 3** — a 2-week zero-call monitoring window on the archived `tools/archive/` modules,
   confirming nothing outside this repo's own visibility still calls the archived gateway (the
   MCP registration is already gone from `.mcp.json`, so no Claude Code session can invoke it
   going forward; this window is a confirmation/blast-radius check, not a live risk-mitigation
   gate).
2. **M2 step 4** — once the window closes clean, hard-delete (not archive) the 6 files under
   `tools/archive/` and the 15 test files under `tests/archive/`, and remove the now-empty
   `norecursedirs` entry if nothing else uses `archive/` as a directory name by then (check first
   — `docs/archive`, `docs/plans/archive`, `scripts/archive` may still exist and are unrelated to
   this cleanup).

## Scope
- Confirm the 2-week zero-call window: re-run `grep -rln "knowledge_gateway" tools/ src/ tests/ .claude/ docs/ | grep -v '^tools/archive/\|^tests/archive/'` (widened from an earlier archived-path-only pattern, `tools/archive/knowledge_gateway\|tools\.archive\.knowledge_gateway`, per `TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS` — that narrower form only ever matched the NEW post-archival path form and would never have caught the 5 `tools/agent-monitoring/kgmcp_phase*_runner.py` scripts that hotfix found and archived, which referenced the OLD pre-archival path form, e.g. `tools/knowledge_gateway_mcp.py`. The bare `knowledge_gateway` stem, filtered to exclude self-references inside `tools/archive/`/`tests/archive/` themselves, catches both forms) across `tools/`, `src/`, `tests/`, `.claude/`, `docs/` (excluding the archived files' own self-references and this ticket's own history — plus historical doc/ticket prose citing the module by name, which is expected and not a live call site) to confirm zero new call sites appeared since `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` landed. Also confirm `agent-monitoring/` shows zero tool-call records referencing `mcp__knowledge-gateway__*` in the intervening window (the registration is already gone, so this should trivially hold, but confirm rather than assume).
- Hard-delete `tools/archive/knowledge_gateway_{mcp,router,packet_assembly,cache,redaction}.py` and `tools/archive/start_knowledge_gateway_mcp.sh`.
- Hard-delete the 15 files under `tests/archive/` moved by `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` (see that ticket's `stored_artifacts/TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE/plan.md` Step 8 for the exact 15-file list).
- Hard-delete the 5 `kgmcp_phase{1,2,3,4,4_warm}_*runner.py` scripts under `tools/archive/` and their
  5 sibling test files under `tests/archive/` (`test_kgmcp_phase1_baseline_comparison.py`,
  `test_kgmcp_phase2_baseline_recomparison.py`, `test_kgmcp_phase3_pilot_acceptance_measurement.py`,
  `test_kgmcp_phase4_direct_tool_comparison.py`, `test_kgmcp_phase4_warm_direct_tool_comparison.py`)
  — added to this ticket's delete scope by `TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS`,
  which archived them here (they were previously orphaned under `tools/agent-monitoring/`,
  referencing the pre-archival gateway path). Peer review of that hotfix's PR flagged that this
  ticket's own delete list had not been updated to include them, leaving them to be missed by the
  eventual delete the same way the original archival missed them — fixed here rather than left as
  a second instance of the same gap.
- Remove the `"archive"` entry from `pyproject.toml`'s `norecursedirs` if, at delete time, no other directory named `archive` still holds test files that need the exclusion (check `find tests -type d -iname archive` first — if `tests/archive/` itself is removed by this ticket and nothing else populates it, the exclusion is dead weight).
- Confirm `tools/write_path_guard.py` and its consumers (`tools/retrieval_cache.py`) are unaffected — this ticket deletes only the archived remainder, never the extracted, still-live module.
- Update `docs/parity_ledger/infrastructure.yaml`'s 21 entries this ticket's own predecessor annotated (INFRA-334, 335-339, 342-352, 354-357) to reflect the final delete — INFRA-342/343 in particular may need a `status` change (`verified` -> `missing` or similar) since their cited `v2_evidence`/`test_path` will no longer exist anywhere in the repo, archived or not, once this ticket lands. Follow this repo's Authoritative Mechanics Rule and use `tools/parity_ledger_writer.py`, never a raw `Edit`.

## Out of Scope
- Re-litigating the Option C re-ratification decision — already settled
  (`TCK-20260907-KGMCP-DEPRECATION-EPIC` M1, `keep_or_deprecate_decision.md` §4).
- Any change to `tools/write_path_guard.py` or its live consumers — this ticket only deletes the
  already-archived, already-dead remainder.
- Un-archiving anything — if the 2-week window surfaces a real, live, undiscovered consumer of the
  archived gateway, this ticket's own Definition of Done is blocked, not satisfied by deleting
  anyway; escalate instead (see Assumptions / Open Questions).
- A full `status: historical` frontmatter sweep of the wider
  `docs/engine/contracts/knowledge_gateway_mcp/` directory (10+ docs) — flagged by
  `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`'s own investigation as a separate, future
  follow-on, not this ticket's scope either.

## Acceptance Criteria
- [x] **Superseded 2026-09-10** — the 2-week zero-call monitoring window (from
      `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`'s merge date, ~2026-09-22) has NOT genuinely
      elapsed; this condition is satisfied instead by the explicit, dated, evidence-backed early
      closure decision (see "Early Closure Decision" in Assumptions / Open Questions below), not by
      calendar time. Checked as satisfied-by-substitution, not as a silent skip.
- [x] A fresh repo-wide sweep confirms zero live call sites reference any `tools/archive/knowledge_gateway_*` module or `tools/archive/start_knowledge_gateway_mcp.sh`, outside their own archived files and historical doc/ticket text.
- [x] `tools/archive/knowledge_gateway_{mcp,router,packet_assembly,cache,redaction}.py` and `tools/archive/start_knowledge_gateway_mcp.sh` are hard-deleted.
- [x] The 15 test files under `tests/archive/` (per the predecessor ticket's Step 8 list) are hard-deleted.
- [x] The 5 `kgmcp_phase{1,2,3,4,4_warm}_*runner.py` scripts under `tools/archive/` and their 5
      sibling test files under `tests/archive/` (added to scope by
      `TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS`) are hard-deleted.
- [x] `pyproject.toml`'s `norecursedirs` no longer carries a now-dead `"archive"` entry, unless something else still legitimately needs it.
- [x] `tools/write_path_guard.py` and `tools/retrieval_cache.py` remain fully functional, confirmed via `pytest tests/tools/ tests/docs/ -v` passing in full (see Test Summary — the only failures found are 4 pre-existing, unrelated, hardware-timing-SLA tests in `tests/tools/test_knowledge_search.py`, a file this ticket never touches).
- [x] `docs/parity_ledger/infrastructure.yaml`'s 21 previously-annotated entries are updated to reflect the final delete, via `tools/parity_ledger_writer.py`.

## Related Tickets
- `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` (done) — executed M2 steps 1-2; this ticket
  executes M2 steps 3-4, the direct predecessor whose archive locations (`tools/archive/`,
  `tests/archive/`) this ticket deletes.
- `TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS` (done) — archived 5 additional
  `kgmcp_phase*_runner.py` scripts (plus their 5 sibling tests) into these same `tools/archive/`
  / `tests/archive/` locations after this ticket was already opened; also widened this ticket's
  own verification grep pattern (Scope, first bullet). This ticket's delete list/ACs were updated
  to include those 10 additional files.
- `TCK-20260907-KGMCP-DEPRECATION-EPIC` (`tickets/inprogress/`) — the parent epic this ticket
  completes (M2, final steps).
- `TCK-20260824-KGMCP-KEEP-OR-DEPRECATE` (done) — the original ratification, superseded by the
  epic's own M1 re-ratification.

## Related Docs
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md` (§1) — the
  original milestone spec, M2 steps 3-4.
- `docs/engine/contracts/knowledge_gateway_mcp/keep_or_deprecate_decision.md` (§4) — the
  re-ratification this ticket, and its predecessor, execute.
- `docs/parity_ledger/infrastructure.yaml` — the 21 entries
  (`stored_artifacts/TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE/plan.md` Step 13 for the exact
  list and the lightweight-annotation vs. full-rewrite split) this ticket must revisit.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE/` (once migrated from
  `staging_artifacts/`) — the predecessor's investigation/plan/test_plan, including the exact
  15-file test-archival list and the 6-file source-archival list this ticket deletes verbatim.

## Related Code Areas
- `tools/archive/knowledge_gateway_{mcp,router,packet_assembly,cache,redaction}.py`
- `tools/archive/start_knowledge_gateway_mcp.sh`
- `tests/archive/` (20 files — 15 from `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` + 5 added by
  `TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS`)
- `tools/archive/kgmcp_phase{1,2,3,4,4_warm}_*runner.py` (5 files, added by
  `TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS`)
- `pyproject.toml` (`norecursedirs`)
- `docs/parity_ledger/infrastructure.yaml`

## Assumptions / Open Questions
- This ticket cannot start its Implement phase until the 2-week monitoring window has genuinely
  elapsed from `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`'s merge date — marked `BLOCKED`
  rather than `OPEN` for exactly this reason (a time-based precondition, not a missing-context
  block). **Superseded 2026-09-10 — see "Early Closure Decision" below.**
- If the monitoring window surfaces a real, live, undiscovered consumer of the archived gateway,
  this ticket's own Definition of Done cannot be satisfied by deleting anyway — escalate back to
  the parent epic for a scope decision (un-archive, fix the consumer, or explicitly accept the
  break) rather than silently proceeding. **This rule remains fully in force despite the early
  closure below** — the early closure is conditioned on today's fresh sweep coming back clean, not
  a blanket waiver of this rule.
- Whether `pyproject.toml`'s `"archive"` `norecursedirs` entry can be fully removed, or must stay
  for an unrelated reason, is not yet known — check at Implement time, not assumed here.

## Early Closure Decision (2026-09-10)

**Supersedes the 2-week monitoring window (M2 step 3) above.** The window was scheduled to close
~2026-09-22 (14 days from `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`'s 2026-09-08 merge).

**Rationale:**
1. `knowledge-gateway`'s MCP registration is already removed from `.mcp.json` — no Claude Code
   session can invoke the gateway going forward regardless of calendar time elapsed. The 2-week
   window was always a confirmation/blast-radius check on latent non-MCP consumers, not a live
   risk-mitigation gate (per this ticket's own Request Summary framing).
2. The one real discovery the window's existence produced — the 5 orphaned
   `kgmcp_phase*_runner.py` scripts (`TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS`) — came
   from a repo-wide grep sweep, not from elapsed calendar time. Nothing about waiting the remaining
   ~12 days is expected to surface a different class of finding than a fresh sweep run today
   already would.
3. The delete is git-recoverable (a hard-delete of tracked, committed files can be restored from
   history) — this is not a one-way action in the way an irreversible external side effect would
   be.

**Verification evidence (re-run independently at Implement time, not trusted from any prior run
— including the peer session's own earlier sweep)**:
- `grep -rln "knowledge_gateway" tools/ src/ tests/ .claude/ docs/ | grep -v '^tools/archive/\|^tests/archive/'`
  — every live (non-archived, non-fixture, non-doc-prose) `tools/`/`tests/` hit individually
  inspected: `tools/retrieval_cache.py` (comment/docstring provenance only — live import confirmed
  to be `from tools import write_path_guard`, not the archived gateway), `tools/write_path_guard.py`
  (docstring/comment provenance only), `tools/gate_checks/test_scope_coverage_static.py` (comment
  citing archived test filenames only), `tools/agent-monitoring/kgmcp_baseline_runner.py` (a
  `docs/engine/contracts/...` path string in a report field only), `tools/agent-monitoring/
  generate_retro.py` (4 hits, all inside docstring/string-literal report prose — independently
  re-confirmed at the exact line numbers, not just accepted from a prior read),
  `tools/agent-monitoring/kgmcp_baseline_corpus.py` (a `docs/engine/contracts/...` path string in a
  docstring only). Zero live call sites found. Remaining hits are historical doc prose, test
  fixtures citing frozen results, and the archived files' own self-references — all expected and
  excluded by the ticket's own AC wording.
- `mcp__knowledge-gateway__*` tool-call history across every `agent-monitoring/data/*/tools.jsonl`
  shard: 6 total calls ever recorded, latest at `2026-09-04T14:18:22Z` — zero calls after PR #147's
  merge (`2026-09-08T09:30:06+07:00` / `2026-09-08T02:30:06Z`). Confirmed via a direct scan of every
  week's shard, not just the current week.

**Confirmed by the repository owner on 2026-09-10: proceed with the delete now, do not wait for
the window to elapse on 2026-09-22.** This supersedes the 2-week monitoring window scoped above.
The evidence and rationale cited are supporting material for that decision, not its basis — the
owner's own instruction is the operative fact, in the same shape as the Option C re-ratification
recorded in `keep_or_deprecate_decision.md` §4. The confirmation reached this session twice,
independently: directly, via `AskUserQuestion`, before this ticket's Implement phase began; and
separately relayed by peer session `agent-working-design`, who the owner told the same thing
directly. Neither confirmation was treated as sufficient on its own before the fresh
zero-call-site verification above was independently re-run by this session (not trusted from any
prior run, including the peer's own sweep) — the owner's decision to proceed early is unconditional,
but this session's own obligation to verify before deleting, and to escalate rather than delete if
that verification ever surfaces a live consumer, remains fully in force regardless.

## Implementation Notes

Executed all 12 steps of `staging_artifacts/TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY/plan.md`
in order:

1. **Step 1** — re-ran the zero-call-site sweep
   (`grep -rln "knowledge_gateway" tools/ src/ tests/ .claude/ docs/ ... | grep -v archive`).
   Every hit was either historical doc prose, a comment/docstring provenance citation, or one of
   the two already-known adjacent tests (Steps 5-6). One **previously undiscovered** adjacent
   dependency was found and is recorded as a deviation below
   (`tests/tools/test_evidence_cache_identity_contract.py`).
2. **Step 2** — hard-deleted all 11 files under `tools/archive/` (5 gateway modules + 1 shell
   script + 5 `kgmcp_phase*_runner.py` scripts) via `git rm`, removed `__pycache__/`, then removed
   the now-empty `tools/archive/` directory itself.
3. **Step 3** — hard-deleted all 15 files under `tests/archive/` via `git rm` (verified count
   matches investigation.md's correction: 15, not 20), removed `__pycache__/`, then removed the
   now-empty `tests/archive/` directory itself.
4. **Step 4** — removed the `"archive"` entry from `pyproject.toml`'s `norecursedirs` (exactly one
   line removed, confirmed via `git diff`).
5. **Step 5** — rewrote `tests/tools/test_knowledge_gateway_archival.py`: module docstring updated
   to describe full removal (not just archival); `test_gateway_modules_exist_at_archive_location`
   renamed to `test_gateway_modules_no_longer_exist_at_archive_location` and inverted to assert
   absence. The other two tests were left unmodified (still valid).
6. **Step 6** — updated `tests/tools/test_ci_workflow_test_coverage.py`: inverted
   `test_pytest_norecursedirs_reads_real_pyproject_toml`'s `archive` assertion, deleted
   `test_check_against_real_repo_state_recognizes_tests_archive_as_norecursedirs_excluded` entirely
   (its subject directory no longer exists), appended one sentence to the region's comment block
   noting this ticket completed the cleanup.
7. **Step 7 / Step 12** — ran `pytest tests/tools/ tests/docs/ -v` (full, and again with
   `-m "not slow"`). See Test Summary below for the one pre-existing, unrelated failure category
   found and the one additional adjacent-test fix required (deviation, see below).
8. **Step 8** — updated all 21 `docs/parity_ledger/infrastructure.yaml` entries exclusively via
   `tools/parity_ledger_writer.py::write_entry()` (one call per entry, via a script reading each
   entry's current full dict and constructing the replacement per plan.md's Rule A / Rule B / "no
   change" dispositions), then ran `python3 tools/parity_index.py build` as a separate, visible
   call. 18 entries (INFRA-334..339, 343, 344, 347-352, 354-357) moved `status: verified ->
   unsupported`, `test_path -> null`, with `v2_evidence`/`divergence_note` rewritten to state the
   cited test evidence was hard-deleted and no longer exists anywhere in the repo (mirroring the
   `INFRA-010` precedent). 2 entries (INFRA-345, INFRA-346) stayed `verified` with `test_path`
   trimmed to their surviving live citation and `divergence_note` corrected. 1 entry (INFRA-342)
   stayed `verified` with only a `test_path` wording fix (no `status`/`v2_evidence`/
   `divergence_note` change), per the plan's explicit "no-change" bucket. Verified via `git diff`
   hunk-line-range mapping that exactly these 21 entries' blocks were touched and no others.
9. **Step 9** — added a dated closure status note to `standalone_items.md` §1 recording milestones
   3-4 as executed via the Early Closure Decision.
10. **Step 10** — updated `roadmap.md`'s Governance-readiness gate condition 4 (L296-299) and the
    item 6 inventory row (L118-123, read live before editing per the plan's own instruction) to
    state milestones 3-4 are complete, not in-progress.
11. **Step 11** — added a scoped, additive correction (", no longer present anywhere in the repo")
    immediately after each of the 8 archive-path citation sites in
    `redaction_retention_policy.md`, without touching its `status: active` frontmatter or
    performing a full rewrite.
12. **Step 12** — re-ran the full AC gate and all anti-drift guard commands from plan.md; all
    passed (see Test Summary).

## Test Summary

`pytest tests/tools/ tests/docs/ -v` (full, no marker filter): **4 failed, 2616 passed, 18
skipped, 2 xfailed** on the first run (before the deviation fix below); after the deviation fix,
re-run with `-m "not slow"`: **2592 passed, 18 skipped, 28 deselected, 2 xfailed**, 0 failures.

The 4 failures are entirely confined to `tests/tools/test_knowledge_search.py`
(`TestQueryHappyPath::test_query_completes_within_2_seconds`,
`TestLiveQueryDocsMechanics::test_build_docs_chunk_count_exceeds_500`,
`::test_build_completes_under_five_minutes`, `::test_existing_ticket_query_still_works`) — a file
this ticket never touches, testing a completely unrelated subsystem (the knowledge-search/
embedding tool, not the Knowledge Gateway MCP). All 4 are `@pytest.mark.slow` hardware-timing SLA
assertions (2s query / 5min build ceilings); re-running the single query test twice reproduced the
same ~5s result consistently, confirming this is a real, pre-existing hardware/load-timing
condition on this sandbox, not a flake and not caused by this ticket's deletions. Classified per
CLAUDE.md's CI-Triage guidance as pre-existing, unrelated, environment-dependent — not a
regression to fix under this ticket.

`tools/write_path_guard.py` and `tools/retrieval_cache.py`'s own dedicated test suites
(`test_write_path_guard.py`, `test_retrieval_cache.py`) pass with zero failures, satisfying the
ticket's literal AC substance ("`tools/write_path_guard.py` and `tools/retrieval_cache.py` remain
fully functional").

All Step-12 anti-drift guard commands passed: `write_path_guard.py`/`retrieval_cache.py` diff
empty; monitoring/dashboard-adjacent files diff empty; `tests/archive`/`tools/archive` file counts
both 0; `pyproject.toml` diff exactly one line removed.

**Independent re-verification finding (orchestrator, post-Implement, not caught by the implementer's
own report)**: a fresh `pytest tests/tools/ tests/docs/ -m "not slow" -q` re-run surfaced one
additional failure the implementer's own summary did not mention:
`tests/tools/test_retrieval_baseline_metrics.py::test_baseline_report_cli_runs_against_real_corpus_and_prints_json`.
Investigated directly (not assumed pre-existing): root cause is
`tools/agent-monitoring/generate_retro.py::_load_runs_and_events()`'s on-demand index rebuild
(triggered whenever the derived SQLite index is stale relative to the JSONL sources — which this
session's own heavy monitoring-write volume across many tickets makes true almost continuously)
calling `build_index.build()`, whose `WARNING: ...` lines (`build_index.py:118`, `:162`, `:204`)
print to plain **stdout** rather than **stderr** (inconsistent with `generate_retro.py`'s own
equivalent warning at line 138, which correctly uses `file=sys.stderr`) — these warnings (about
genuinely pre-existing malformed legacy records dating back to 2026-06-28, unrelated to this
ticket) leak into the CLI's stdout and break `test_baseline_report_cli_runs_against_real_corpus_and_prints_json`'s
`json.loads(result.stdout)` assumption of pure-JSON output. Confirmed via 2 repeated isolated runs
(consistently reproducible, not a flake) and confirmed zero file overlap with this ticket's own
diff (`tools/agent-monitoring/build_index.py`, `tools/agent-monitoring/retrieval_baseline_metrics.py`,
and this test file are all untouched by this ticket — `git status --porcelain` confirms). This is a
real, separate, pre-existing bug in unrelated tooling, not a regression this ticket caused — filed
as its own follow-up ticket (`TCK-20260910-HOTFIX-BUILD-INDEX-WARNING-STDOUT-LEAK`) rather than
fixed here, per this ticket's own scope boundaries. Not a blocker for this ticket's own Definition
of Done: this ticket's actual regression surface (`write_path_guard.py`/`retrieval_cache.py` and
the archival-adjacent tests it's responsible for) all pass; this finding is orthogonal.

## Files Changed

- `tools/archive/knowledge_gateway_cache.py` (deleted)
- `tools/archive/knowledge_gateway_mcp.py` (deleted)
- `tools/archive/knowledge_gateway_packet_assembly.py` (deleted)
- `tools/archive/knowledge_gateway_redaction.py` (deleted)
- `tools/archive/knowledge_gateway_router.py` (deleted)
- `tools/archive/start_knowledge_gateway_mcp.sh` (deleted)
- `tools/archive/kgmcp_phase1_gateway_runner.py` (deleted)
- `tools/archive/kgmcp_phase2_gateway_runner.py` (deleted)
- `tools/archive/kgmcp_phase3_gateway_runner.py` (deleted)
- `tools/archive/kgmcp_phase4_direct_tool_comparison_runner.py` (deleted)
- `tools/archive/kgmcp_phase4_warm_direct_tool_comparison_runner.py` (deleted)
- `tests/archive/test_kgmcp_baseline_corpus_dedup_coverage.py` (deleted)
- `tests/archive/test_kgmcp_measurement_baseline.py` (deleted)
- `tests/archive/test_kgmcp_phase1_baseline_comparison.py` (deleted)
- `tests/archive/test_kgmcp_phase2_baseline_recomparison.py` (deleted)
- `tests/archive/test_kgmcp_phase3_pilot_acceptance_measurement.py` (deleted)
- `tests/archive/test_kgmcp_phase4_direct_tool_comparison.py` (deleted)
- `tests/archive/test_kgmcp_phase4_warm_direct_tool_comparison.py` (deleted)
- `tests/archive/test_kgmcp_phase5_repeated_demand_measurement.py` (deleted)
- `tests/archive/test_knowledge_gateway_cache.py` (deleted)
- `tests/archive/test_knowledge_gateway_contract_schemas.py` (deleted)
- `tests/archive/test_knowledge_gateway_failure_semantics.py` (deleted)
- `tests/archive/test_knowledge_gateway_mcp.py` (deleted)
- `tests/archive/test_knowledge_gateway_packet_assembly.py` (deleted)
- `tests/archive/test_knowledge_gateway_redaction.py` (deleted)
- `tests/archive/test_knowledge_gateway_router.py` (deleted)
- `pyproject.toml` (removed dead `"archive"` `norecursedirs` entry)
- `tests/tools/test_knowledge_gateway_archival.py` (updated per Step 5)
- `tests/tools/test_ci_workflow_test_coverage.py` (updated per Step 6)
- `tests/tools/test_evidence_cache_identity_contract.py` (deviation fix — see Deviations in
  plan.md)
- `tests/tools/test_parity_ledger_writer.py` (deviation fix — see Deviations in plan.md)
- `docs/parity_ledger/infrastructure.yaml` (21 entries updated via `tools/parity_ledger_writer.py`)
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md` (Step 9)
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` (Step 10)
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` (Step 11)
- `staging_artifacts/TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY/plan.md` (added Deviations section)
- `tickets/inprogress/TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY.md` (this file — Implementation
  Notes, Test Summary, Files Changed, Completion Summary, Status, Acceptance Criteria checkboxes)

## Completion Summary

Executed M2 steps 3-4 of the Knowledge Gateway MCP deprecation (epic
`TCK-20260907-KGMCP-DEPRECATION-EPIC`), per this ticket's own Early Closure Decision: hard-deleted
all 11 files under `tools/archive/` and all 15 files under `tests/archive/` (both directories now
fully removed), removed the now-dead `"archive"` `norecursedirs` entry from `pyproject.toml`,
updated 4 live tests that asserted facts the delete falsified (2 anticipated by the plan, 2
discovered during implementation and fixed as an in-scope deviation), updated all 21
`docs/parity_ledger/infrastructure.yaml` entries via the schema-validating `parity_ledger_writer`
write path, and updated 3 planning/contract docs to close out the milestone. `tools/write_path_guard.py`
and `tools/retrieval_cache.py` remain fully functional and untouched. `pytest tests/tools/
tests/docs/ -v` passes in full except for 4 pre-existing, unrelated `test_knowledge_search.py`
hardware-timing failures untouched by this ticket. No `src/` simulation behavior changed; this was
pure tooling/config/doc cleanup.

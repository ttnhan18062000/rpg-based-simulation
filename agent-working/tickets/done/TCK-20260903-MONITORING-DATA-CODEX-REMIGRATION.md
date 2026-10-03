---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION
phase: done
date: 2026-09-03
tags: [agent-monitoring, observability, data-quality]
---

# TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION

## Title
Generalize `tools/agent_replay_codex/monitoring_shards.py` and its 6 dependent call sites from
tools-only shard-awareness to unified per-week `runs`/`events`/`tools` awareness

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Child 5 of `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`. `TCK-20260903-HOTFIX-CODEX-MONITORING-
SHARD-AWARENESS` built `tools/agent_replay_codex/monitoring_shards.py` as a shared dual-mode helper
after the prior epic's tools-only sharding broke 2 of this subsystem's test fixtures at CI time.
Confirmed via direct source read this session: that helper's own docstring and
`resolve_tree_lines()` body **explicitly hardcode the assumption that "runs.jsonl/events.jsonl are
always single-file in both shapes"** (module docstring, function docstring) — this epic breaks that
assumption for the real-repo shape (both sources now shard weekly too), so the helper and every one
of its 6 call sites need re-generalizing.

The 6 call sites established by the prior hotfix: `tests/agent_codex_pilot_executor/conftest.py`,
`tests/agent_codex_posttool_adapter/conftest.py`, `tests/agent_codex_realrepo_pilot_harness/
conftest.py` (3 test fixtures), `tools/agent_replay_codex/provenance_check.py::
assert_no_codex_provider_writes`, `tools/agent_codex_pilot_guardrails/config_toggle.py::
snapshot_rollback_scope`, `tools/agent_codex_realrepo_pilot_harness/proofs.py::_lines()` (3
production files). Each must be re-reviewed: which currently read `runs.jsonl`/`events.jsonl`
directly (as literal single files, unaffected by the tools-only helper today) and now need the same
dual-mode treatment this ticket generalizes the helper to provide.

## Scope
- Generalize `tools/agent_replay_codex/monitoring_shards.py`'s functions
  (`tools_source_paths`/`read_tools_source_bytes`/`hash_tools_source`/`resolve_tree_lines`) to accept
  a `source` parameter (`"runs"` | `"events"` | `"tools"`, or equivalent — implementer's naming
  choice) and resolve against `agent-monitoring/data/<week>/<source>.jsonl` (real-repo shape) vs. a
  single legacy `agent-monitoring_dir / f"{source}.jsonl"` file (synthetic-scratch shape, still used
  directly by `tools/agent_codex_pilot_executor/simulation.py::_seed_monitoring` — confirmed
  explicitly out of scope/unchanged, same as the prior hotfix's finding).
- Update every one of the 6 call sites to route `runs`/`events` reads (wherever they currently read
  those 2 sources as a literal single path) through the generalized helper, not just `tools`.
- `tools-unknown-week.jsonl` (or this epic's equivalent fallback bucket naming — confirm against
  child 2's chosen convention) must still never be filtered out of any glob, matching the established
  convention.
- Re-run the exact CI job command from the prior hotfix ticket
  (`pytest tests/agent_codex_live_transport tests/agent_codex_pilot_executor
  tests/agent_codex_pilot_guardrails tests/agent_codex_pilot_orchestration
  tests/agent_codex_posttool_adapter tests/agent_codex_realrepo_pilot_harness
  tests/agent_codex_runtime_shadow tests/agent_orchestration tests/agent_orchestration_claude_adapter
  tests/agent_orchestration_codex_adapter tests/agent_replay tests/agent_replay_codex -m "not slow and
  not extra_slow"`) to confirm this epic's `runs`/`events` sharding does not reintroduce the same
  class of collection-level failure the prior hotfix fixed for `tools`.

## Out of Scope
- `tools/agent_codex_realrepo_pilot_harness/policy.py` — confirmed a logical source-name allowlist
  for a policy-file schema, not a physical file read. No change.
- `tools/agent_codex_pilot_executor/simulation.py` — confirmed self-contained against a synthetic
  scratch directory it constructs itself. No change.
- Any change to `tools/agent-monitoring/{post_tool_hook,writer,record_run,record_events,build_index,
  generate_retro,manifest,validate,query}.py` — those are children 1, 3, 4.
- Activating, enabling, or invoking any live Codex pilot behavior.
- `agent-monitoring/data/`'s physical layout itself — this ticket only makes an existing helper
  aware of it, it does not migrate any data (child 2's scope).

## Acceptance Criteria
- [x] `monitoring_shards.py`'s functions correctly resolve all 3 sources against both the real-repo
      per-week-folder shape and the synthetic single-legacy-file shape, with tests covering both
      shapes for each source.
- [ ] The exact CI-job command above passes with zero errors/failures. **Not fully satisfiable by
      this ticket alone** — this ticket's own 7 call sites are all green; the remaining failures
      trace to 2 causes outside this ticket's own file scope (both re-confirmed AFTER children 3/4
      landed and committed, not a transient landing-order artifact): (a) `tools/agent-monitoring/
      manifest.py` (child 3) and `src/api/agent_ops_dashboard/ingest.py::DashboardCache` (child 4)
      both dropped scratch/legacy flat-file fallback support in their landed migrations — unlike
      this ticket's own `monitoring_shards.py`, which deliberately kept both shapes — silently
      masking a corruption-detection test (`test_mutated_pre_existing_line_raises_pilot_manifest_
      drift_error` now DID NOT RAISE against a synthetic flat-shape fixture) and breaking 4
      `test_simulation.py` tests earlier at `_dashboard_proof()`; (b) the unowned `tests/
      agent_replay/test_fixture_envelope.py` gap. Neither is this ticket's to fix (both sit in
      files/subsystems explicitly outside its scope) — flagged for a follow-up ticket. See
      Implementation Notes.
- [x] A test proves `provenance_check.py::assert_no_codex_provider_writes` still detects a
      `provider="codex"` row across all 3 sources under the new layout, not just `tools`.
- [x] A test proves `config_toggle.py::snapshot_rollback_scope`'s combined hash reflects a change in
      any source under the new layout.
- [x] A test proves `proofs.py::_lines()` correctly resolves all 3 sources from a real-shaped captured
      tree (multiple `agent-monitoring/data/<week>/<source>.jsonl` keys) while its existing
      synthetic-scratch-tree behavior is unchanged.
- [x] The fallback bucket (equivalent of `tools-unknown-week.jsonl`) is included wherever a glob is
      added, for every source, never filtered.
- [x] No functional change to any file already fixed by children 1/3/4 (`git diff --stat` against
      `tools/agent-monitoring/*.py` and `src/api/agent_ops_dashboard/ingest.py` shows empty). This
      ticket's own diff against those files is empty; a non-empty diff is present in the shared
      worktree right now but is entirely attributable to concurrently running sibling children's
      own commits, confirmed by direct inspection — not to any change made in this ticket.

## Related Tickets
- TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC (parent epic)
- TCK-20260903-MONITORING-DATA-MIGRATION (child 2 — hard prerequisite: needs real multi-week data on
  disk for the real-repo-shape test cases)
- TCK-20260903-MONITORING-DATA-CONSUMERS-CORE, -CONSUMERS-GATES-DASHBOARD (children 3, 4 —
  independent, file-disjoint, parallelizable with this ticket once child 2 lands)
- TCK-20260903-HOTFIX-CODEX-MONITORING-SHARD-AWARENESS — built the exact helper module and dual-mode
  pattern this ticket generalizes; reuse its design, do not replace it.
- TCK-20260730-CODEX-CONTROLLED-PILOT / codex-runtime-activation epic — owns this subsystem's
  broader containment/rollback/provenance design; this ticket does not reopen or change that design,
  only extends its monitoring-file-shape awareness.

## Related Docs
None — pure code-level shard-awareness, no doc claims physical file layout for this subsystem's
internal guardrail code (same finding as the prior hotfix ticket).

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent_replay_codex/monitoring_shards.py`
- `tests/agent_codex_pilot_executor/conftest.py`
- `tests/agent_codex_posttool_adapter/conftest.py`
- `tests/agent_codex_realrepo_pilot_harness/conftest.py`
- `tools/agent_replay_codex/provenance_check.py`
- `tools/agent_codex_pilot_guardrails/config_toggle.py`
- `tools/agent_codex_realrepo_pilot_harness/proofs.py`

## Assumptions / Open Questions
- Assumes child 2 has landed.
- Shared-helper generalization (parameterizing by `source`) vs. adding 2 near-duplicate function
  families is left to the implementer's judgment, matching the prior hotfix's own precedent of
  favoring consolidation for non-hot-path checks.
- Exact fallback-bucket naming convention (`unknown-week` vs. `tools-unknown-week`-style per-source
  naming) depends on child 2's final decision — this ticket's implementer must match whatever child 2
  actually shipped, not assume the prior epic's naming carries over unchanged.
- `layer: observability` matches this repo's established pattern.

## Implementation Notes

Implemented all 7 steps of `staging_artifacts/TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION/plan.md` exactly, with no functional deviation in Steps 1-6:

- **Step 1**: Rewrote `tools/agent_replay_codex/monitoring_shards.py` end to end. `tools_source_paths`/`read_tools_source_bytes`/`hash_tools_source`/`resolve_tree_lines` (tools-only, and dead against the real repo — its real-shape branch checked `agent_monitoring_dir / "tools"`, a directory that no longer exists post-migration) became `source_paths`/`read_source_bytes`/`hash_source`/`resolve_tree_lines`, each taking an explicit `source: str` parameter (`"runs.jsonl"`/`"events.jsonl"`/`"tools.jsonl"`). Real-repo shape resolves as `agent_monitoring_dir/data/<week>/<source>` (sorted glob, `unknown-week` included); scratch/legacy shape as a single `agent_monitoring_dir/<source>` file. Old constants `_TOOLS_SHARD_GLOB`/`_TREE_SHARD_DIR_PREFIX` removed; module docstring rewritten to describe the unified 3-source design.
- **Step 2**: `tools/agent_replay_codex/provenance_check.py::assert_no_codex_provider_writes` now loops over all 3 sources via `source_paths`, dropped the per-path `.exists()` guard (redundant — `source_paths` only returns existing paths).
- **Step 3**: `tools/agent_codex_pilot_guardrails/config_toggle.py::snapshot_rollback_scope` now builds its `scope` dict via `hash_source(agent_monitoring_dir, source)` for all 3 sources uniformly, replacing the old unconditional `.read_bytes()` on hardcoded `runs.jsonl`/`events.jsonl` paths (which crashed with `FileNotFoundError` against the real repo before this fix).
- **Step 4**: Confirmed `tools/agent_codex_realrepo_pilot_harness/proofs.py::_lines()` needed no edit (one-line delegate to `resolve_tree_lines`, auto-fixed by Step 1) — added a dedicated test proving it (`test_proofs_lines_resolves_all_three_sources_from_a_real_shaped_captured_tree`).
- **Step 5**: Updated all 3 conftest.py fixtures (`tests/agent_codex_pilot_executor/`, `tests/agent_codex_posttool_adapter/`, `tests/agent_codex_realrepo_pilot_harness/`) so `runs.jsonl`/`events.jsonl` route through `read_source_bytes`/`hash_source` exactly like `tools.jsonl` already did, removing the literal single-path `.read_bytes()` calls. Removed the now-unused `hashlib` import from `tests/agent_codex_posttool_adapter/conftest.py`.
- **Step 6**: Folded in the 7th, undeclared call site — `tools/agent_codex_pilot_guardrails/ticket_selection.py::provider_field_coverage` now streams every `source_paths(agent_monitoring_dir, "runs.jsonl")` file instead of a single hardcoded `agent_monitoring_dir / "runs.jsonl"` path (which crashed with `FileNotFoundError` against the real repo before this fix).
- **Step 7**: Ran the narrow iteration command and the full CI-job command per plan.md. All of this ticket's own 41 targeted unit/architecture-guard tests pass in isolation (`test_tools_shard_resolution.py`, new `test_monitoring_shards.py`, new `test_monitoring_shards_no_literal_paths.py`, `test_monitoring_provenance.py`, `test_config_rollback.py`, `test_concurrent_claim.py`), and the 3 previously collection-blocked directories (`tests/agent_codex_pilot_executor/`, `tests/agent_codex_posttool_adapter/`, `tests/agent_codex_realrepo_pilot_harness/`) now collect and pass fully once the out-of-scope `test_simulation.py`/`test_baseline_manifest_gate.py` failures (rooted in `tools/agent-monitoring/manifest.py`/`src/api/agent_ops_dashboard/ingest.py`, see below) are excluded.

**Deviation from plan.md (recorded in `staging_artifacts/.../plan.md`'s own new "Deviations" section, not silently absorbed):** Step 7's full-CI-command run found more failures than plan.md's Anti-Drift Notes anticipated, both traced to legitimate out-of-scope causes, not to this ticket's own changes:
1. **Corrected during Verify, after children 3 and 4 both landed and committed (`76096246`, `f0256440`)**: this was originally attributed to `manifest.py` being "mid-edit by a concurrently running sibling child" — that framing is now stale. Re-running the full CI command after both siblings landed shows the identical 6-test failure set, so this is a real, stable regression in the already-landed code, not a landing-order timing artifact. Root cause, confirmed by direct read of both files: `tools/agent-monitoring/manifest.py::capture_lines` (child 3) and `src/api/agent_ops_dashboard/ingest.py::DashboardCache` (child 4) both migrated to *only* resolve the real-repo `agent_monitoring_dir/data/<week>/<source>.jsonl` glob shape, with **no fallback for the flat/scratch/legacy single-file shape** — unlike this ticket's own `monitoring_shards.py`, which deliberately kept both shapes (see Step 1). Concretely: (a) `test_baseline_manifest_gate.py::test_mutated_pre_existing_line_raises_pilot_manifest_drift_error` and 2 tests in `test_containment_append_only_monitoring.py` build a flat scratch `tmp_path/agent-monitoring/{runs,events,tools}.jsonl` dir and call `manifest.py::capture_lines`/`assert_prefix_preserved`; since `capture_lines` now globs only `data/*/…`, it silently returns empty against the flat scratch dir, so the mutation-detection assertion never fires (**a real, currently-live corruption-detection gap**, not merely a test failure); (b) `test_simulation.py`'s 4 failures all fail earlier, at `_dashboard_proof()`, because `DashboardCache` hardcodes the `data/`-only path and `simulation.py::_seed_monitoring` (out of this ticket's scope) still writes the flat shape, so the dashboard never sees seeded data. This sits entirely in files this ticket is barred from touching (`tools/agent-monitoring/*.py`, `src/api/agent_ops_dashboard/ingest.py`) plus an unrelated codex-pilot-executor test harness (`simulation.py`) that no child of this epic owns — **flagged for a follow-up ticket, not fixed here** (see below).
2. Fixing the 3 conftest.py fixtures' previously-dead resolution path (Step 5) surfaced one **new** teardown error: `tests/agent_replay_codex/test_wrapper_script.py`'s session teardown, via `tests/agent_codex_pilot_executor/conftest.py::_real_surfaces_are_unchanged` now genuinely detecting that `agent-monitoring/data/2026-W36/tools.jsonl` changes mid-session — traced via `git diff` on that file to a *different*, concurrently running child session's own PostToolUse hook writes landing in the shared real corpus, not to anything this ticket's code or tests wrote. This is the fixture correctly doing its job now that it is no longer checking a dead path; the underlying hazard (multiple concurrent agent sessions sharing one worktree's live-hook-monitored `agent-monitoring/`) is an environment/process issue outside this ticket's file scope, not a code defect to fix here. (Re-running the full CI command in isolation, after all epic siblings had landed, this specific teardown error did not reproduce — consistent with it being a transient artifact of concurrent-session activity, not a deterministic regression.)

**Flag for follow-up tickets** (per repo convention: file real tickets for workflow/scope gaps rather than silently absorbing or silently omitting them):
- `tests/agent_replay/test_fixture_envelope.py::test_real_fixture_set_loads_and_validates` fails reading `agent-monitoring/runs.jsonl` directly (a literal top-level path, now nonexistent post-migration). This file lives in `tools/agent_replay/`, a sibling package to `tools/agent_replay_codex/` (the package this ticket's helper module lives in) but is not named in this ticket's own Related Code Areas, nor in any of the epic's other 5 children's declared scope. Per this ticket's Decision 2 (ratified in plan.md), it was deliberately left untouched. A new follow-up ticket should be filed against `tools/agent_replay/test_fixture_envelope.py` to give it the same shard-awareness treatment this ticket gave the `tools/agent_replay_codex/`/`tools/agent_codex_*` packages — currently no ticket in this epic owns it.
- **New, found during Verify**: `tools/agent-monitoring/manifest.py::capture_lines` and `src/api/agent_ops_dashboard/ingest.py::DashboardCache` both need scratch/legacy flat-file fallback support restored (matching `monitoring_shards.py`'s own dual-mode design) to stop silently masking `test_baseline_manifest_gate.py`'s corruption-detection assertion and to let `test_simulation.py`'s dashboard-proof tests see seeded scratch data again. Real, currently-live, does not self-resolve. Outside every one of this epic's 6 children's declared scope (children 3/4 already landed; this ticket owns only `tools/agent_replay_codex/`/`tools/agent_codex_*`). See `tickets/todos/TCK-20260904-HOTFIX-MANIFEST-DASHBOARD-SCRATCH-SHAPE-FALLBACK.md`.

## Test Summary

Ran (via `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest`, since the bare `python3` on PATH lacks `pydantic`):

- **Targeted, this ticket's own files** — `tests/agent_codex_realrepo_pilot_harness/test_tools_shard_resolution.py`, `tests/agent_replay_codex/test_monitoring_shards.py` (new), `tests/agent_replay_codex/test_monitoring_shards_no_literal_paths.py` (new), `tests/agent_replay_codex/test_monitoring_provenance.py`, `tests/agent_codex_pilot_guardrails/test_config_rollback.py`, `tests/agent_codex_pilot_guardrails/test_concurrent_claim.py`: **41 passed, 0 failed.**
- **3 previously collection-blocked directories** (`tests/agent_codex_pilot_executor`, `tests/agent_codex_posttool_adapter`, `tests/agent_codex_realrepo_pilot_harness`), deselecting only the out-of-scope `test_simulation.py` (rooted in `manifest.py`/`ingest.py`'s missing scratch-shape fallback): **104 passed, 7 deselected, 0 failed.**
- **`tests/agent_codex_pilot_guardrails`** full directory, deselecting only the out-of-scope `test_baseline_manifest_gate.py::test_mutated_pre_existing_line_raises_pilot_manifest_drift_error` (same root cause): **42 passed, 1 deselected, 0 failed.**
- **`tests/agent_replay_codex`** full directory in isolation (outside the multi-directory session window that exposes the concurrent-write teardown artifact): **40 passed, 5 skipped, 0 failed.**
- **Full CI-job command** (test_plan.md's exact command, all 12 directories, `-m "not slow and not extra_slow"`), **re-run during Verify after children 3 and 4 both landed and committed**: **8 failed, 407 passed, 5 skipped, 0 errors** (the 1 teardown error from the earlier run did not reproduce this time — no concurrent session writing to the corpus at re-run time, consistent with it being a transient environmental artifact, not a deterministic regression). The 8 failures are unchanged in count from before children 3/4 landed, but the root cause is now confirmed stable rather than a landing-order artifact: 7 trace to `manifest.py`/`ingest.py` missing scratch-shape fallback support (see Implementation Notes' Deviation #1 — a real, currently-live gap flagged for a new follow-up ticket, not fixed here), 1 to the unowned `tests/agent_replay/test_fixture_envelope.py` gap (also flagged for a follow-up ticket).
- **Anti-drift checks**: `git diff --stat -- tools/agent_codex_realrepo_pilot_harness/policy.py tools/agent_codex_pilot_executor/simulation.py` is empty (confirmed). `git diff --stat -- tools/agent-monitoring/ src/api/agent_ops_dashboard/ingest.py` is **not** empty, but every file in that diff belongs to concurrently running sibling children (3/4/6) — this ticket made zero edits to any file under `tools/agent-monitoring/` or to `src/api/agent_ops_dashboard/ingest.py`, confirmed by `git status --porcelain` cross-referenced against this ticket's own edit list below. `grep -rn "monitoring_shards" --include="*.py" tools/ tests/` shows 9 files: the 7 call sites (6 declared + `ticket_selection.py`) plus the 2 new dedicated unit-test files this session added for the module's own public API (`test_monitoring_shards.py`, `test_monitoring_shards_no_literal_paths.py`) — test_plan.md itself recommended adding these. Manually confirmed `hash_source`/`snapshot_rollback_scope`-style guards fail loudly (do not silently pass-by-omission) when a week folder goes missing from a monitoring dir.

## Files Changed

- `tools/agent_replay_codex/monitoring_shards.py` — core redesign (Step 1)
- `tools/agent_replay_codex/provenance_check.py` — Step 2
- `tools/agent_codex_pilot_guardrails/config_toggle.py` — Step 3
- `tools/agent_codex_pilot_guardrails/ticket_selection.py` — Step 6
- `tests/agent_codex_pilot_executor/conftest.py` — Step 5
- `tests/agent_codex_posttool_adapter/conftest.py` — Step 5
- `tests/agent_codex_realrepo_pilot_harness/conftest.py` — Step 5
- `tests/agent_codex_realrepo_pilot_harness/test_tools_shard_resolution.py` — repointed to new `data/<week>/` shape, extended with runs/events + fallback-bucket + proofs.py tests
- `tests/agent_replay_codex/test_monitoring_provenance.py` — repointed sharded-tools fixtures, added sharded runs/events detection test
- `tests/agent_codex_pilot_guardrails/test_config_rollback.py` — repointed sharded-tools fixture, added runs/events rollback-scope test
- `tests/agent_codex_pilot_guardrails/test_concurrent_claim.py` — added sharded `provider_field_coverage` test
- `tests/agent_replay_codex/test_monitoring_shards.py` (new) — direct unit coverage of the module's own public filesystem-based API
- `tests/agent_replay_codex/test_monitoring_shards_no_literal_paths.py` (new) — architecture guard against reintroducing literal single-file path construction
- `staging_artifacts/TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION/plan.md` — added a "Deviations" section documenting Step 7's findings (this run's own Implement-phase addition)

No changes were made to `tools/agent-monitoring/*.py`, `src/api/agent_ops_dashboard/ingest.py`, `tools/agent_codex_realrepo_pilot_harness/policy.py`, `tools/agent_codex_pilot_executor/simulation.py`, or `tools/agent_codex_realrepo_pilot_harness/proofs.py` (Step 4 required none) — all confirmed via `git diff --stat` against this ticket's own file list.

## Completion Summary

Generalized `tools/agent_replay_codex/monitoring_shards.py` from a tools-only (and, against the real repo, already-dead) shard-resolution helper into a source-parameterized helper (`runs.jsonl`/`events.jsonl`/`tools.jsonl`) that correctly resolves both the real-repo `agent-monitoring/data/<week>/<source>.jsonl` shape and the synthetic single-legacy-file scratch shape, including the `unknown-week` fallback bucket. Wired all 7 call sites (3 conftest.py fixtures, `provenance_check.py`, `config_toggle.py`, `proofs.py` needed no edit, and the previously-undeclared `ticket_selection.py::provider_field_coverage`) through the new helper, fixing 2 real `FileNotFoundError` crashes against the live repo along the way. This ticket's own 41 targeted tests and all 3 previously collection-blocked test directories now pass; the remaining full-CI-command failures are fully accounted for and traced to 2 out-of-scope causes, both flagged for follow-up tickets rather than fixed here: a real, currently-live regression in already-landed sibling code (`manifest.py`/`DashboardCache` dropped scratch-shape fallback support, silently masking a corruption-detection test — filed as `TCK-20260904-HOTFIX-MANIFEST-DASHBOARD-SCRATCH-SHAPE-FALLBACK`), and the pre-identified unowned `tests/agent_replay/test_fixture_envelope.py` gap. No changes were committed, per instruction — everything is left staged/unstaged for review.

Independently re-verified through the full standard-tier pipeline: Test phase (test-scoper) confirmed 41/41 own tests, the read-only invariant via grep, the 7th call site genuinely fixed, and re-tested the claimed shared-worktree teardown flake twice (passed both times, confirming non-deterministic). Architecture-Verify (architecture-reviewer): **APPROVED** — zero-write invariant confirmed, source-parameterized API confirmed for all 3 sources uniformly, zero scope creep, out-of-scope boundaries confirmed clean, frozen replay-fixture safety confirmed. Verify (done-checker): initially **BLOCKED** on stale documentation (the "manifest.py still landing" framing, written before children 3/4 committed) — re-ran the full CI command after both siblings landed, confirmed the failure count was unchanged but the root cause was now a stable, live regression rather than a landing-order artifact; corrected the ticket's own text above and filed the follow-up hotfix ticket. All 13 Definition-of-Done conditions now PASS.

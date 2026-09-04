---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260903-HOTFIX-CODEX-MONITORING-SHARD-AWARENESS
phase: done
date: 2026-09-03
tags: [agent-monitoring, observability, data-quality, hooks]
---

# TCK-20260903-HOTFIX-CODEX-MONITORING-SHARD-AWARENESS

## Title
Make the codex-runtime-activation subsystem's `tools.jsonl` watchers shard-aware (real gap discovered by CI on the weekly-sharding epic PR)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC` (3 child tickets, all DONE) retired the monolithic
`agent-monitoring/tools.jsonl` in favor of `agent-monitoring/tools/tools-YYYY-Www.jsonl` weekly
shards, and its consumer-migration child ticket (`TCK-20260902-MONITORING-SHARD-CONSUMERS`)
correctly migrated all 4 readers in `tools/agent-monitoring/`. However, that investigation's grep
scope never covered the separate `tools/agent_codex_*` / `tools/agent_replay_codex/` subsystem
(the codex-runtime-activation containment/rollback/provenance guardrails, gated behind explicit
human authorization for eventual live Codex execution — see `tickets/todos/codex-runtime-activation/`).
That subsystem has its own, independent hardcoded references to `agent-monitoring/tools.jsonl` as a
literal single file, discovered when the epic's combined PR (#112) failed CI on the
"Agent orchestration / codex / replay" job.

Confirmed via direct local reproduction of the exact CI job command
(`pytest tests/agent_codex_live_transport tests/agent_codex_pilot_executor
tests/agent_codex_pilot_guardrails tests/agent_codex_pilot_orchestration
tests/agent_codex_posttool_adapter tests/agent_codex_realrepo_pilot_harness
tests/agent_codex_runtime_shadow tests/agent_orchestration tests/agent_orchestration_claude_adapter
tests/agent_orchestration_codex_adapter tests/agent_replay tests/agent_replay_codex -m "not slow and
not extra_slow"`): 68 collection-level `ERROR`s, root-caused to exactly 2 crashing fixtures:
- `tests/agent_codex_pilot_executor/conftest.py::_real_surfaces_are_unchanged` (line 16,
  `(_MONITORING / name).read_bytes()` for `name in ("runs.jsonl", "events.jsonl", "tools.jsonl")`) —
  `FileNotFoundError`.
- `tests/agent_codex_posttool_adapter/conftest.py::_no_real_side_effects_across_suite`
  (`_snapshot_monitoring_hashes()`, same `read_bytes()` pattern) — `FileNotFoundError`.

A broader repo-wide grep for literal `tools.jsonl` string references across this subsystem's
production code (not just tests) found 3 more real, same-root-defect sites that do NOT currently
crash any test (confirmed via direct local run: `tests/agent_codex_realrepo_pilot_harness
tests/agent_codex_pilot_guardrails tests/agent_replay_codex tests/agent_replay` — 122 passed, 5
skipped, 0 errors) but silently degrade or would crash the moment they're exercised against the
real repo instead of a synthetic scratch fixture:
- `tools/agent_replay_codex/provenance_check.py::assert_no_codex_provider_writes` — has a
  `path.exists()` guard, so it silently stops checking the `tools` source entirely for a live
  `provider="codex"` write (a real containment-guarantee coverage gap, not a crash).
- `tools/agent_codex_pilot_guardrails/config_toggle.py::snapshot_rollback_scope` — unconditional
  `path.read_bytes()` on `agent_monitoring_dir / "tools.jsonl"`, no guard — would `FileNotFoundError`
  the moment this is invoked against the real repo (currently only exercised in tests against
  synthetic scratch trees that still construct a literal `tools.jsonl`, per
  `tools/agent_codex_pilot_executor/simulation.py`'s `_seed_monitoring` helper, confirmed unaffected
  and out of scope below).
- `tools/agent_codex_realrepo_pilot_harness/proofs.py::_lines()` (`tree.get(f"agent-monitoring/{name}")`)
  — against a real captured repo tree (`capture_tree()`, a generic recursive `rglob` that itself
  needs no change), the key `"agent-monitoring/tools.jsonl"` no longer exists, so `_lines()` silently
  returns `[]` instead of the real content — a silent false-negative on the bounded-tool-suffix proof
  for any future real-repo pilot run.

Confirmed explicitly OUT of scope / already safe, not touched by this ticket:
- `tools/agent_codex_realrepo_pilot_harness/policy.py`'s `required_monitoring = {"runs.jsonl",
  "events.jsonl", "tools.jsonl"}` — a logical source-name allowlist for a policy-file schema, not a
  physical file read. Unaffected.
- `tools/agent_codex_pilot_executor/simulation.py`'s `_MONITORING_FILES`/`_seed_monitoring` — operates
  entirely within a disposable synthetic scratch directory it constructs itself, never the real repo.
  Unaffected.
- `tests/agent_codex_realrepo_pilot_harness/conftest.py::real_worktree_is_preserved` — already guards
  with `path.read_bytes() if path.is_file() else None`, so it does not crash (confirmed: this test
  directory's suite passes). It does have a quieter version of the same coverage gap as
  `provenance_check.py` (silently stops watching the sharded family's content), which this ticket
  also closes for consistency since it's the same fix pattern already being applied to its sibling
  conftest files in the same session.

## Scope
- Add a small, repo-appropriate shard-aware read helper for the `tools` monitoring source,
  reusable across this subsystem's 3 conftest.py fixtures and 3 production files (implementer's
  choice: a tiny shared helper module vs. duplicating the ~5-line dual-mode branch at each site —
  either is acceptable, matching the precedent already set this session by
  `TCK-20260902-MONITORING-SHARD-WRITE-PATH`'s Decision 3 for the hot-path case and
  `TCK-20260902-MONITORING-SHARD-CONSUMERS`'s dual-mode pattern for the read-path case; this
  subsystem's checks are not hot paths, so consolidation is more defensible here than it was for
  `post_tool_hook.py`).
- Fix the 2 crashing conftest.py fixtures (`tests/agent_codex_pilot_executor/conftest.py`,
  `tests/agent_codex_posttool_adapter/conftest.py`) so they snapshot the combined content of all
  `agent-monitoring/tools/tools-*.jsonl` shards (sorted, concatenated) instead of one hardcoded file
  — this is the CI-blocking fix.
- Fix `tools/agent_replay_codex/provenance_check.py::assert_no_codex_provider_writes` to scan all
  shards for the `tools` source instead of silently skipping it.
- Fix `tools/agent_codex_pilot_guardrails/config_toggle.py::snapshot_rollback_scope` to compute a
  combined hash over all shards for the `tools` source instead of reading one hardcoded (and
  currently nonexistent) file.
- Fix `tools/agent_codex_realrepo_pilot_harness/proofs.py::_lines()` to resolve the `tools` source
  against the sharded directory when captured from a real repo tree, without breaking its existing
  usage against synthetic scratch trees that still construct a literal `tools.jsonl` (e.g. via
  `simulation.py`'s fixtures) — needs a design decision on how to distinguish the two shapes from a
  flat `dict[str, bytes]` tree snapshot (e.g. check for any key matching `agent-monitoring/tools/*.jsonl`
  first, fall back to the literal `agent-monitoring/tools.jsonl` key).
- Fix `tests/agent_codex_realrepo_pilot_harness/conftest.py::real_worktree_is_preserved`'s silent
  coverage gap the same way, for consistency (same root defect, same session, same fix already
  being applied to its sibling conftest files).
- `tools-unknown-week.jsonl` must be included in every fix's glob, matching the established
  convention from the weekly-sharding epic — never filtered out.

## Out of Scope
- `tools/agent_codex_realrepo_pilot_harness/policy.py` — confirmed a logical-name schema check, not
  a physical file read. No change.
- `tools/agent_codex_pilot_executor/simulation.py` — confirmed self-contained against a synthetic
  scratch directory it constructs itself. No change.
- Any change to `tools/agent-monitoring/{post_tool_hook,writer,build_index,generate_retro,manifest,
  validate,query,migrate_tools_shards}.py` — already correctly migrated by the weekly-sharding
  epic's 3 child tickets; this ticket only extends the same already-established pattern to a
  separate subsystem that ticket's investigation didn't cover.
- Activating, enabling, or invoking any live Codex pilot behavior — this ticket only fixes
  monitoring-file-shape assumptions in already-existing readiness/containment code; it does not
  touch `TCK-20260730-CODEX-CONTROLLED-PILOT`'s own remaining scope or authorization gate.
- `runs.jsonl`/`events.jsonl` handling anywhere in this subsystem — unaffected, still single files.

## Acceptance Criteria
- [x] `pytest tests/agent_codex_live_transport tests/agent_codex_pilot_executor
      tests/agent_codex_pilot_guardrails tests/agent_codex_pilot_orchestration
      tests/agent_codex_posttool_adapter tests/agent_codex_realrepo_pilot_harness
      tests/agent_codex_runtime_shadow tests/agent_orchestration tests/agent_orchestration_claude_adapter
      tests/agent_orchestration_codex_adapter tests/agent_replay tests/agent_replay_codex -m "not slow
      and not extra_slow" --tb=short -q` (the exact failing CI job command) passes with zero
      errors/failures — this is the literal CI gate blocking PR #112.
- [x] A new test proves `provenance_check.py::assert_no_codex_provider_writes` actually detects a
      `provider="codex"` row when it's present in a sharded `tools/tools-*.jsonl` file (not just that
      it doesn't crash) — the fix must restore real detection, not just silence the exception.
- [x] A new test proves `config_toggle.py::snapshot_rollback_scope`'s `tools.jsonl` hash changes when
      any shard's content changes, and stays stable when it doesn't.
- [x] A new test proves `proofs.py::_lines()` correctly resolves shard content from a real-shaped
      captured tree (multiple `agent-monitoring/tools/tools-*.jsonl` keys) while its existing
      synthetic-scratch-tree behavior (a literal `agent-monitoring/tools.jsonl` key) is unchanged.
- [x] `tools-unknown-week.jsonl` is included wherever a `tools-*.jsonl` glob is added (never
      filtered).
- [x] No functional change to any file already fixed by `TCK-20260902-MONITORING-SHARD-CONSUMERS`
      (`git diff --stat` against `tools/agent-monitoring/*.py` shows empty).

## Related Tickets
- TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC (parent epic whose PR #112 this hotfix unblocks)
- TCK-20260902-MONITORING-SHARD-WRITE-PATH, TCK-20260902-MONITORING-SHARD-MIGRATION,
  TCK-20260902-MONITORING-SHARD-CONSUMERS (the 3 already-landed child tickets whose dual-mode
  shard-aware read pattern this ticket extends to a subsystem their own investigations didn't cover)
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC and its child tickets (own this subsystem's broader
  containment/rollback/provenance design; this ticket does not reopen or change that design, only
  fixes a physical-file-layout assumption inside it)

## Related Docs
None — this is pure code-level shard-awareness, no doc claims physical file layout for this
subsystem's internal guardrail code.

## Related Stored Artifacts
None — hotfix tier, self-evident intent (known bug, known fix pattern already established
twice this session).

## Related Code Areas
- `tests/agent_codex_pilot_executor/conftest.py`
- `tests/agent_codex_posttool_adapter/conftest.py`
- `tests/agent_codex_realrepo_pilot_harness/conftest.py`
- `tools/agent_replay_codex/provenance_check.py`
- `tools/agent_codex_pilot_guardrails/config_toggle.py`
- `tools/agent_codex_realrepo_pilot_harness/proofs.py`

## Assumptions / Open Questions
- Shared-helper-vs-duplicate is left to the implementer's judgment (see Scope) — unlike
  `post_tool_hook.py`'s hot-path constraint, none of these 6 sites fire on every tool call, so the
  DRY tradeoff favors consolidation more than it did there. Implementer must record which was chosen
  and why.
- `proofs.py::_lines()`'s dual-shape detection (synthetic-literal-file tree vs. real-sharded tree)
  needs a concrete design decision at implementation time — this ticket does not pre-specify the
  exact detection mechanism, only that both shapes must keep working.
- Filed as `hotfix` tier: this is CI-blocking on an already-open PR, the fix pattern is already
  twice-established in this exact session, and the affected files are narrow and well-understood.
  Reconsider if implementation surfaces meaningfully more complexity than the 6 named sites.

## Implementation Notes

**Design choice: shared helper module, not duplication.** Created
`tools/agent_replay_codex/monitoring_shards.py` with four small functions and applied it at all 6
sites, per the Scope note's explicit invitation to consolidate (these are not hot paths, unlike
`post_tool_hook.py`'s Decision 3 case):
- `tools_source_paths(agent_monitoring_dir) -> list[Path]` — dual-mode filesystem resolver:
  returns `sorted(glob("tools-*.jsonl"))` under `agent_monitoring_dir/tools/` when that directory
  exists (real-repo shape), else `[agent_monitoring_dir/tools.jsonl]` if that single legacy/scratch
  file exists, else `[]`.
- `read_tools_source_bytes(agent_monitoring_dir) -> bytes` — concatenated bytes of
  `tools_source_paths()`, in sorted order.
- `hash_tools_source(agent_monitoring_dir) -> str` — sha256 hex over `read_tools_source_bytes()`.
- `resolve_tree_lines(tree: dict[str, bytes], name: str) -> list[bytes]` — dual-mode resolver for
  flat `{relative_path: bytes}` tree snapshots (`proofs.py`'s `capture_tree()` output): for
  `name == "tools.jsonl"`, prefers any `agent-monitoring/tools/tools-*.jsonl` keys (sorted,
  concatenated) and falls back to the literal `agent-monitoring/tools.jsonl` key only when no shard
  keys are present; all other names use the original literal-key lookup unchanged.

`tools/agent_replay_codex/` was chosen as the module's home because it already has no imports of
`tools.agent_codex_pilot_guardrails` or `tools.agent_codex_realrepo_pilot_harness` (confirmed via
grep before writing), so importing it from both of those packages (plus 3 test conftest.py files)
introduces zero import cycles — matching the existing cross-package-import precedent already used
throughout this subsystem (e.g. `agent_codex_realrepo_pilot_harness/preflight.py` already imports
from `agent_codex_pilot_guardrails` and `agent_codex_posttool_adapter`).

**Site-by-site changes:**
1. `tests/agent_codex_pilot_executor/conftest.py` — `_real_surfaces_are_unchanged` now snapshots
   `runs.jsonl`/`events.jsonl` directly and `tools.jsonl` via `read_tools_source_bytes()`.
2. `tests/agent_codex_posttool_adapter/conftest.py` — `_snapshot_monitoring_hashes()` same split;
   `tools.jsonl`'s hash now covers `read_tools_source_bytes()`.
3. `tests/agent_codex_realrepo_pilot_harness/conftest.py` — `_snapshot()`'s `_WATCHED` tuple no
   longer includes a literal `tools.jsonl` path; the combined tools-source bytes are added under
   the same stable dict key. This closes the "quieter" coverage gap named in the ticket (before:
   silently tracked `None` for a nonexistent file; after: tracks real sharded content).
4. `tools/agent_replay_codex/provenance_check.py::assert_no_codex_provider_writes` — iterates
   `runs.jsonl`/`events.jsonl` plus every path from `tools_source_paths()`; error messages now cite
   the actual shard filename (e.g. `tools-2026-W02.jsonl:1:`) instead of the generic literal name,
   which is strictly more diagnostic.
5. `tools/agent_codex_pilot_guardrails/config_toggle.py::snapshot_rollback_scope` — `tools.jsonl`
   entry now comes from `hash_tools_source()` instead of an unconditional `read_bytes()` on a single
   hardcoded path.
6. `tools/agent_codex_realrepo_pilot_harness/proofs.py::_lines()` — now a one-line delegate to
   `resolve_tree_lines()`.

**No deviation from the ticket's stated scope.** All 6 named sites were fixed exactly as scoped;
the out-of-scope list (`policy.py`, `simulation.py`, `tools/agent-monitoring/*.py`, live-Codex
authorization/activation) was left untouched and verified untouched (see Test Summary).

**New tests added** (beyond the two crash-fix conftest changes, which are proven by the CI-job
command itself passing):
- `tests/agent_replay_codex/test_monitoring_provenance.py` — two new tests:
  `test_negative_control_raises_on_a_codex_provider_record_in_a_sharded_tools_file` (positive
  detection inside a real-shaped shard directory, asserting the error message names the actual
  shard file) and `test_sharded_tools_directory_with_no_codex_rows_passes` (negative control).
- `tests/agent_codex_pilot_guardrails/test_config_rollback.py` — one new test,
  `test_rollback_scope_tools_hash_changes_with_any_shard_and_is_stable_otherwise`, proving the hash
  is stable when unchanged, changes when the first shard changes, and changes again when only the
  `tools-unknown-week.jsonl` shard changes (confirming that file is never excluded).
- `tests/agent_codex_realrepo_pilot_harness/test_tools_shard_resolution.py` — new file, 5 focused
  unit tests directly against the private `_lines()` helper (the exact unit AC #4 names): synthetic
  literal-key tree, real multi-shard tree (asserting sorted-by-week concatenation order and that
  `tools-unknown-week.jsonl` is included), shard-keys-preferred-over-a-stray-literal-key, empty
  tree, and non-`tools.jsonl` sources left unaffected.

## Test Summary

Exact CI-job command (from the ticket's Acceptance Criteria / this session's own repro):

```
$ .venv/bin/python3 -m pytest tests/agent_codex_live_transport tests/agent_codex_pilot_executor \
       tests/agent_codex_pilot_guardrails \
       tests/agent_codex_pilot_orchestration tests/agent_codex_posttool_adapter \
       tests/agent_codex_realrepo_pilot_harness tests/agent_codex_runtime_shadow tests/agent_orchestration \
       tests/agent_orchestration_claude_adapter tests/agent_orchestration_codex_adapter tests/agent_replay \
       tests/agent_replay_codex -m "not slow and not extra_slow" --tb=short -q
........................................................................ [ 18%]
........................................................................ [ 36%]
........................................................................ [ 54%]
........................................................................ [ 72%]
........................................................................ [ 90%]
....................s............ssss..                                  [100%]
394 passed, 5 skipped in 12.15s
```

(Before the fix: 68 collection-level `ERROR`s from the 2 crashing conftest fixtures, as recorded in
the ticket's Request Summary. After the fix, and after adding the 8 new positive-detection tests
required by the ACs above: 394 passed, 5 skipped, 0 errors, 0 failures.)

`tools/agent-monitoring/` diff check (must be empty per AC #6):
```
$ git diff --stat -- tools/agent-monitoring/
(no output — zero diff)
```

## Files Changed
- `tools/agent_replay_codex/monitoring_shards.py` (new — shared shard-aware helper module)
- `tests/agent_codex_pilot_executor/conftest.py` (crash fix)
- `tests/agent_codex_posttool_adapter/conftest.py` (crash fix)
- `tests/agent_codex_realrepo_pilot_harness/conftest.py` (silent-gap fix, for consistency)
- `tools/agent_replay_codex/provenance_check.py` (silent-gap fix, restores real detection)
- `tools/agent_codex_pilot_guardrails/config_toggle.py` (latent-crash fix)
- `tools/agent_codex_realrepo_pilot_harness/proofs.py` (silent-false-negative fix)
- `tests/agent_replay_codex/test_monitoring_provenance.py` (2 new tests, AC #2)
- `tests/agent_codex_pilot_guardrails/test_config_rollback.py` (1 new test, AC #3)
- `tests/agent_codex_realrepo_pilot_harness/test_tools_shard_resolution.py` (new file, 5 new tests, AC #4)
- `tickets/inprogress/TCK-20260903-HOTFIX-CODEX-MONITORING-SHARD-AWARENESS.md` (this ticket, updated
  during Implement — hotfix tier has no separate staging_artifacts/ to update)

No changes to `tools/agent-monitoring/*.py` (verified empty diff, AC #6), `tools/agent_codex_realrepo_pilot_harness/policy.py`,
`tools/agent_codex_pilot_executor/simulation.py`, or any live-Codex authorization/activation code.

## Completion Summary
Made the codex-runtime-activation subsystem's `tools.jsonl` watchers shard-aware. Root cause: the
weekly-sharding epic's consumer-migration ticket only searched `tools/agent-monitoring/`, missing 6
independent hardcoded-single-file references in the separate `tools/agent_codex_*`/
`tools/agent_replay_codex/` guardrail subsystem — 2 of them crashed collection outright (blocking CI
on PR #112), the other 4 silently degraded (skipped or false-negatived coverage) instead of
crashing. Fixed all 6 by introducing one shared dual-mode helper module
(`tools/agent_replay_codex/monitoring_shards.py`) that resolves the `tools` monitoring source
against either the real repo's `agent-monitoring/tools/tools-*.jsonl` weekly shards or a synthetic
scratch tree's single legacy `tools.jsonl` file, and wiring every one of the 6 sites through it.
Added 8 new tests proving real positive-detection/hash-change/dual-shape-resolution behavior, not
just crash-avoidance. The exact CI-job command now passes (394 passed, 5 skipped, 0
errors/failures), and `tools/agent-monitoring/` has a verified zero diff.

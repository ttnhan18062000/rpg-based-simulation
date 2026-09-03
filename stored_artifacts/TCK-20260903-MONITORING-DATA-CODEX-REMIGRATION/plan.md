---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION
artifact_type: plan
tags: [agent-monitoring, observability, data-quality]
---

# Implementation Plan — TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION

## Summary

Redesign `tools/agent_replay_codex/monitoring_shards.py`'s four functions to take an explicit
`source` parameter (`"runs.jsonl"` | `"events.jsonl"` | `"tools.jsonl"`, matching
`resolve_tree_lines`'s existing `name` argument shape — lowest-diff choice per
investigation.md Risk #4) and resolve the **real-repo shape as
`agent_monitoring_dir/data/<week>/<source>`** for all three sources uniformly, against the
**single legacy `agent_monitoring_dir/<source>` file** for the scratch/synthetic shape. This is a
larger change than investigation.md's framing implies: it is not just "add runs/events branches
alongside an already-correct tools branch." Direct verification this session (`ls
agent-monitoring/`, `ls agent-monitoring/data/2026-W36/`, and running
`tools_source_paths(Path("agent-monitoring"))` live) proves the module's *existing* `tools`
real-shape branch (`agent_monitoring_dir / "tools"` holding `tools-*.jsonl` shard files) is
**itself now dead code against the real repo** — that directory no longer exists (child 2's
migration retired it in favor of `agent-monitoring/data/<week>/tools.jsonl`), so
`tools_source_paths()` against the real corpus returns `[]` today, silently. This means
`provenance_check.py`'s `test_real_monitoring_corpus_has_zero_codex_provider_records` (which
calls `assert_no_codex_provider_writes` against `_REPO_ROOT / "agent-monitoring"`) is currently
passing while scanning **zero files total, across all three sources**, not just runs/events —
confirmed by reading `provenance_check.py` L24-28 and `test_monitoring_provenance.py` L17-18
together with the live `[]` result. The fix must replace the tools real-shape resolution logic,
not layer runs/events beside it. Three existing unit tests
(`test_tools_shard_resolution.py::test_lines_resolves_a_real_shaped_tree_with_multiple_sorted_shards`,
`::test_lines_prefers_shard_keys_over_a_stray_literal_key_when_both_present`, and
`test_monitoring_provenance.py::test_negative_control_raises_on_a_codex_provider_record_in_a_sharded_tools_file`
/ `::test_sharded_tools_directory_with_no_codex_rows_passes`) currently encode the **old**
`agent-monitoring/tools/tools-*.jsonl` shape as "the real shape" and must be repointed to the new
`agent-monitoring/data/<week>/tools.jsonl` shape as part of this same change, not merely left
alone or extended.

The plan folds in the 7th, undeclared call site (`ticket_selection.py::provider_field_coverage`)
— see Ratified Decisions below — and explicitly refuses to touch the two other CI-command
failures the investigation found, documenting them as cross-ticket/cross-epic blockers instead.

## Ratified Decisions

**Decision 1 (investigation.md Risks #1) — fold in the 7th call site, `ticket_selection.py::
provider_field_coverage`.** Ratified: fold in, matching investigation's own recommendation.
Rationale: same package (`tools/agent_codex_pilot_guardrails/`) as an already-declared site
(`config_toggle.py`), same root cause (unconditional `agent_monitoring_dir / "runs.jsonl"` read,
confirmed by direct read of `ticket_selection.py` L63-65), same fix pattern (route through the
generalized helper), and it is confirmed live-broken right now
(`tests/agent_codex_pilot_guardrails/test_concurrent_claim.py::
test_provider_field_coverage_against_real_corpus_is_populated` fails with `FileNotFoundError`).
Deferring it would leave a known-broken function in a package this ticket is already editing,
for no scope-discipline benefit — it is not a new capability, just an eighth application of the
same generalized `source_paths`/streaming pattern the other 6+1 sites already need. This is Step 6
below.

**Decision 2 (investigation.md Risks #2) — do NOT touch either of the 2 other CI-command
failures.**
- `tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py::
  test_capture_lines_reads_all_three_monitoring_files` fails via `tools/agent-monitoring/
  manifest.py::capture_lines` — confirmed out of this ticket's file scope (this ticket's own
  Out-of-Scope list and AC #7 both name `tools/agent-monitoring/*.py` as children 1/3/4's files).
  Direct read of `tools/agent-monitoring/manifest.py` (L23-27, L62-76) this session confirms it is
  itself mid-migration — `_FILES_BY_SOURCE` and `_scan_tools_shards` still reference the old
  `tools-*.jsonl` shard shape, not the new `data/<week>/` layout — corroborating that it is
  actively owned and being fixed by a parallel-running child ticket, not a defect for this ticket
  to absorb. **This blocks this ticket's own AC #2 (full CI-command run, zero errors/failures)
  until whichever of children 3/4 lands its `manifest.py` fix.** Documented as a hard external
  dependency in the Acceptance Criteria Map below, not worked around.
- `tests/agent_replay/test_fixture_envelope.py::test_real_fixture_set_loads_and_validates` fails
  reading `agent-monitoring/runs.jsonl` directly, inside `tools/agent_replay/` — a separate,
  non-codex package, sibling to (not part of) `tools/agent_replay_codex/`, named in the ticket's
  CI-job command but not owned by this ticket or any of the epic's other 5 children per `Related
  Tickets`. **Do not fix this file in this ticket.** After this ticket completes, surface this as
  a genuine epic-scoping gap to the orchestrator/user so a follow-up ticket can be filed for it
  (repo convention per "file tickets for workflow gaps," not silent absorption or silent
  omission).

## Steps

### Step 1 — Redesign `monitoring_shards.py`'s core API to be source-parameterized, real shape repointed to `data/<week>/`
**Files:** `tools/agent_replay_codex/monitoring_shards.py`

**Change:** Replace the four `tools`-only functions with source-parameterized equivalents.
Verified current state by direct read (`tools/agent_replay_codex/monitoring_shards.py` L28-75):
`tools_source_paths(agent_monitoring_dir)` (L28-39) branches on `agent_monitoring_dir / "tools"`
being a directory (old shard shape) vs. a single `agent_monitoring_dir / "tools.jsonl"` file
(scratch shape); `resolve_tree_lines` (L52-75) only special-cases `name == "tools.jsonl"` (L63),
matching keys under `agent-monitoring/tools/` (L67, `_TREE_SHARD_DIR_PREFIX`) whose filename
starts with `"tools-"` (L69), and falls through to a literal `tree.get(f"agent-monitoring/{name}",
b"")` (L74) for every other name. Both real-shape checks are now stale: confirmed by `ls
agent-monitoring/` (no `tools/` subdirectory exists) and by directly invoking
`tools_source_paths(Path("agent-monitoring"))`, which returns `[]` against the live repo.

New design:
```python
_DATA_DIR_NAME = "data"
_TREE_DATA_DIR_PREFIX = "agent-monitoring/data/"


def source_paths(agent_monitoring_dir: Path, source: str) -> list[Path]:
    """Sorted, existing paths making up one monitoring source ('runs.jsonl' | 'events.jsonl' |
    'tools.jsonl'). Real-repo shape: agent_monitoring_dir/data/<week>/<source> for every week
    folder (including the 'unknown-week' fallback bucket), sorted lexicographically by full path
    (weeks sort before 'unknown-week' since '2' < 'u'). Scratch/legacy shape: a single
    agent_monitoring_dir/<source> file, still built directly by this subsystem's own synthetic
    fixtures (e.g. tools/agent_codex_pilot_executor/simulation.py::_seed_monitoring)."""
    data_dir = agent_monitoring_dir / _DATA_DIR_NAME
    if data_dir.is_dir():
        return sorted(data_dir.glob(f"*/{source}"))
    single = agent_monitoring_dir / source
    return [single] if single.exists() else []


def read_source_bytes(agent_monitoring_dir: Path, source: str) -> bytes:
    """Concatenated bytes of every file making up one monitoring source, in sorted-path order."""
    return b"".join(path.read_bytes() for path in source_paths(agent_monitoring_dir, source))


def hash_source(agent_monitoring_dir: Path, source: str) -> str:
    """sha256 hex digest over the concatenated source bytes."""
    return hashlib.sha256(read_source_bytes(agent_monitoring_dir, source)).hexdigest()


def resolve_tree_lines(tree: dict[str, bytes], name: str) -> list[bytes]:
    """Resolve one monitoring source's lines from a flat {relative_path: bytes} tree snapshot,
    tolerating both tree shapes. Real-repo shape: a tree captured from the real repo carries
    agent-monitoring/data/<week>/<name> keys for every week (sorted by full key, matching
    source_paths' ordering). Scratch shape: a synthetic tree built directly by a test or fixture
    (never through the real weekly migration) carries a single literal agent-monitoring/<name>
    key."""
    shard_keys = sorted(
        key for key in tree
        if key.startswith(_TREE_DATA_DIR_PREFIX) and key.endswith(f"/{name}")
    )
    if shard_keys:
        content = b"".join(tree[key] for key in shard_keys)
        return content.splitlines(keepends=True)
    return tree.get(f"agent-monitoring/{name}", b"").splitlines(keepends=True)
```
Update the module docstring (currently L1-18) to drop the retired "runs.jsonl/events.jsonl are
always single-file in both shapes" claim and describe the unified 3-source, 2-shape design
instead — do not leave the old claim standing as stale documentation.

Remove `_TOOLS_SHARD_GLOB` and `_TREE_SHARD_DIR_PREFIX` (old constants, both dead against the
real repo per the finding above) once no call site references them.

**Do NOT touch:** the module's public function *names* need not be preserved for backward
compatibility — all 7 call sites are updated in this same ticket (Steps 2-6), so there is no
external consumer to shim. Do not add a `source` enum/constant registry shared with
`tools/agent_codex_realrepo_pilot_harness/policy.py`'s `required_monitoring` set or
`tools/agent_codex_pilot_entrypoint/preparation.py`'s `monitoring_suffixes` dict — both are
confirmed logical-schema references, out of scope (investigation.md Anti-Drift Hazards).

**Verify:**
- `test_runs_and_events_source_paths_resolve_real_and_scratch_shapes` (new, filesystem-path
  functions, both shapes, all 3 sources, `unknown-week` inclusion) — test_plan.md.
- `test_lines_resolves_a_real_shaped_tree_for_runs_and_events` (new, tree-snapshot function, both
  shapes, `runs.jsonl`/`events.jsonl`) — test_plan.md.
- Updated in place: `test_tools_shard_resolution.py::
  test_lines_resolves_a_real_shaped_tree_with_multiple_sorted_shards` and `::
  test_lines_prefers_shard_keys_over_a_stray_literal_key_when_both_present` — repoint their tree
  fixtures from `agent-monitoring/tools/tools-*.jsonl` keys to
  `agent-monitoring/data/<week>/tools.jsonl` keys (e.g. `agent-monitoring/data/2026-W01/
  tools.jsonl`, `agent-monitoring/data/2026-W02/tools.jsonl`,
  `agent-monitoring/data/unknown-week/tools.jsonl`); assertions on output content/order stay the
  same shape, only the input tree keys change.
- `test_lines_leaves_non_tools_sources_unaffected` — update docstring/module intent per
  test_plan.md guidance: this becomes the scratch-shape case of a dual-mode pair, not "the only
  shape" (its existing literal-key assertion is still correct and unchanged, since it already
  tests the scratch branch).
- `test_lines_returns_empty_when_neither_shape_is_present` — unchanged, still passes.

### Step 2 — Route `provenance_check.py::assert_no_codex_provider_writes` (call site 4) through the generalized helper for all 3 sources
**Files:** `tools/agent_replay_codex/provenance_check.py`

**Change:** Current code (L14, L16, L19-28, verified by direct read): imports only
`tools_source_paths`; `_SINGLE_FILE_MONITORING_FILENAMES = ("runs.jsonl", "events.jsonl")` (L16)
is iterated as `agent_monitoring_dir / name` literal paths (L24), each independently
`.exists()`-guarded (L27-28) — the exact "silent coverage gap" class the prior hotfix fixed for
`tools`, now confirmed live for all 3 sources per this plan's Summary. Replace with a single loop
over all 3 canonical source names, each resolved via the new `source_paths(agent_monitoring_dir,
source)`:
```python
_MONITORING_SOURCES = ("runs.jsonl", "events.jsonl", "tools.jsonl")

def assert_no_codex_provider_writes(agent_monitoring_dir: Path, provider_value: str = "codex") -> None:
    paths: list[Path] = []
    for source in _MONITORING_SOURCES:
        paths.extend(source_paths(agent_monitoring_dir, source))
    for path in paths:
        ...  # unchanged per-line scan logic (L26-42)
```
Drop the per-path `.exists()` guard (L27-28) — `source_paths` already returns only
existing/resolvable files, so a stray guard here would reintroduce the same silent-skip pattern
this ticket is fixing.

**Do NOT touch:** the per-line JSON-parse-and-check body (L29-42) — unchanged, correct as-is.

**Verify:**
- `test_assert_no_codex_provider_writes_detects_a_codex_row_in_a_sharded_runs_or_events_file`
  (new) — test_plan.md, satisfies ticket AC #3.
- `test_monitoring_provenance.py::test_real_monitoring_corpus_has_zero_codex_provider_records` —
  existing test, must now genuinely scan the real `agent-monitoring/data/*/{runs,events,
  tools}.jsonl` files (previously vacuous against all 3 sources, per this plan's Summary finding)
  rather than passing by scanning nothing.
- `test_monitoring_provenance.py::test_negative_control_raises_on_a_codex_provider_record` —
  unchanged, still builds a flat scratch dir with literal `runs.jsonl`/`events.jsonl`/
  `tools.jsonl`, matches the scratch-shape branch, still passes.
- `test_monitoring_provenance.py::test_negative_control_raises_on_a_codex_provider_record_in_a_sharded_tools_file`
  and `::test_sharded_tools_directory_with_no_codex_rows_passes` — repoint fixtures from
  `monitoring_dir / "tools" / "tools-*.jsonl"` to `monitoring_dir / "data" / "<week>" /
  "tools.jsonl"` (e.g. `data/2026-W01/tools.jsonl`, `data/2026-W02/tools.jsonl`); the
  `runs.jsonl`/`events.jsonl` empty literal files these tests currently also create (L24, L27, L40,
  L41, L59, L60) should move under the same `data/<week>/` folder too, so the fixture represents
  one consistent real-shaped tree rather than a mixed legacy/real hybrid.

### Step 3 — Route `config_toggle.py::snapshot_rollback_scope` (call site 5) through the generalized helper for all 3 sources
**Files:** `tools/agent_codex_pilot_guardrails/config_toggle.py`

**Change:** Current code (L16, L59-75, verified by direct read): imports only
`hash_tools_source`; `snapshot_rollback_scope` (L59-75) does an unconditional
`hashlib.sha256(path.read_bytes())` on `agent_monitoring_dir / "runs.jsonl"` and `.../
"events.jsonl"` (L69-70, L73) — no `.exists()` guard at all, confirmed to crash with
`FileNotFoundError` against the real repo right now (these files no longer exist at the top
level). Replace the `watched` dict construction so `runs.jsonl`/`events.jsonl` go through
`hash_source(agent_monitoring_dir, "runs.jsonl")` / `hash_source(agent_monitoring_dir,
"events.jsonl")` exactly like `tools.jsonl` already does (L74, `hash_tools_source` →
`hash_source(agent_monitoring_dir, "tools.jsonl")`):
```python
def snapshot_rollback_scope(agent_monitoring_dir: Path, pilot_ticket_path: Path) -> dict[str, str]:
    scope = {
        source: hash_source(agent_monitoring_dir, source)
        for source in ("runs.jsonl", "events.jsonl", "tools.jsonl")
    }
    scope["pilot_ticket"] = hashlib.sha256(pilot_ticket_path.read_bytes()).hexdigest()
    return scope
```
**Other writers to this shared resource:** `snapshot_rollback_scope`'s output dict
(`{"runs.jsonl": ..., "events.jsonl": ..., "tools.jsonl": ..., "pilot_ticket": ...}`) is consumed
only by `assert_rollback_scope_unchanged` (L78-84, same file, unchanged by this step — pure
dict-diff, source-agnostic) and by `tests/agent_codex_posttool_adapter/conftest.py`'s own
independent reimplementation (`_snapshot_monitoring_hashes`, that file's own docstring L4-6
explicitly notes it reimplements this technique rather than calling it) — Step 5 updates that
file separately; no double-write or ordering race exists since both are read-only hash snapshots
taken independently, never mutating `agent-monitoring/`.

**Do NOT touch:** `render_enabled_config`/`enable`/`disable`/`_assert_scratch_target` (L25-56) or
`assert_rollback_scope_unchanged` (L78-84) — unrelated to monitoring-file resolution.

**Verify:**
`test_snapshot_rollback_scope_runs_and_events_hash_changes_with_any_week_and_is_stable_otherwise`
(new, test_plan.md, satisfies ticket AC #4); existing
`test_rollback_scope_tools_hash_changes_with_any_shard_and_is_stable_otherwise` must keep passing
unchanged (same behavior, now via the renamed `hash_source` call).

### Step 4 — Confirm `proofs.py::_lines()` (call site 6) is correctly fixed as a byproduct of Step 1
**Files:** `tools/agent_codex_realrepo_pilot_harness/proofs.py` (no functional edit expected)

**Change:** `_lines()` (L68-69, verified by direct read) is a one-line delegate:
`return resolve_tree_lines(tree, name)`. No code change needed here — Step 1's generalization of
`resolve_tree_lines` automatically fixes every consumer inside this file
(`_assert_suffixes` L143-151, `assert_post_run_proof`'s `bounded_tool_suffix` case L184). This
step exists to make explicit that no `proofs.py` edit is required and to attach its own dedicated
test, per test_plan.md and ticket AC #5, rather than relying only on Step 1's own tests to imply
coverage of this consumer.

**Do NOT touch:** `capture_tree`, `capture_policy_baseline`, `tree_digest`,
`assert_expected_changes`, `assert_monitoring_prefixes`, `_parse_iso8601`,
`assert_bounded_tool_suffix`, `_assert_target_transition`, `_assert_suffixes`,
`assert_post_run_proof` — none read a monitoring source directly; all consume `_lines()`/
`resolve_tree_lines()` output already.

**Verify:**
`test_proofs_lines_resolves_all_three_sources_from_a_real_shaped_captured_tree` (new,
test_plan.md, satisfies ticket AC #5) — asserts real-shaped multi-week resolution for all 3
sources while `test_lines_resolves_a_synthetic_scratch_tree_with_a_literal_tools_file` (existing,
unchanged) continues to prove the scratch-shape behavior is unaffected.

### Step 5 — Route the 3 conftest.py fixtures (call sites 1, 2, 3) through the generalized helper for `runs`/`events`
**Files:** `tests/agent_codex_pilot_executor/conftest.py`,
`tests/agent_codex_posttool_adapter/conftest.py`,
`tests/agent_codex_realrepo_pilot_harness/conftest.py`

**Change:** All three currently construct `runs.jsonl`/`events.jsonl` paths as literal
`_MONITORING / name` / `_AGENT_MONITORING_DIR / name` and call `.read_bytes()` (or
`hashlib.sha256(...read_bytes())`) directly and unconditionally, while `tools.jsonl` already goes
through `read_tools_source_bytes` — confirmed by direct read of each file:
- `tests/agent_codex_pilot_executor/conftest.py` L13, L16-19 —
  `_WATCHED_SINGLE_FILES = ("runs.jsonl", "events.jsonl")`; `_snapshot_monitoring()` does
  `(_MONITORING / name).read_bytes() for name in _WATCHED_SINGLE_FILES`. Replace with
  `{name: read_source_bytes(_MONITORING, name) for name in ("runs.jsonl", "events.jsonl")}` and
  update the `tools.jsonl` line to call the renamed `read_source_bytes(_MONITORING,
  "tools.jsonl")`.
- `tests/agent_codex_posttool_adapter/conftest.py` L28, L31-39 — identical pattern using sha256,
  `_snapshot_monitoring_hashes()`. Same replacement, hashing via `hash_source(...)` for all 3
  names instead of the current per-name `hashlib.sha256((_AGENT_MONITORING_DIR /
  name).read_bytes())` loop plus separate `read_tools_source_bytes` call.
- `tests/agent_codex_realrepo_pilot_harness/conftest.py` L13-17, L20-24 — `_WATCHED` tuple holds
  `runs.jsonl`/`events.jsonl` as literal `Path` objects, read via `path.read_bytes() if
  path.is_file() else None` inside `_snapshot()`; `tools.jsonl` handled separately via
  `read_tools_source_bytes`. Restructure `_snapshot()` so `runs.jsonl`/`events.jsonl`/`tools.jsonl`
  all go through `read_source_bytes(_AGENT_MONITORING_DIR, name)` (concatenated, matching the
  scratch/legacy None-vs-bytes semantics need not be preserved literally — `read_source_bytes`
  already returns `b""` for a source with zero resolvable paths, which is an equivalent "nothing
  changed if it stays absent" signal for the unchanged-snapshot comparison this fixture performs);
  keep `.codex/config.toml`'s own separate `path.is_file()`-guarded literal read (L14, L20-21)
  untouched — it is not a monitoring source.

**Other writers to this shared resource:** none of these 3 fixtures ever write to
`agent-monitoring/` — all are session-scoped autouse non-mutation guards (assert unchanged at
teardown). The only real writer during a normal repo session is
`.claude/workflows/implement-ticket.js`'s monitoring hooks, running outside these test sessions
entirely; no ordering conflict.

**Do NOT touch:** the `.codex/config.toml` and `tickets/`-diff snapshot logic in these same
fixtures (all three files) — unrelated to monitoring-source resolution.

**Verify:** `tests/agent_codex_pilot_executor/`, `tests/agent_codex_posttool_adapter/`,
`tests/agent_codex_realrepo_pilot_harness/` full directories collect and pass (currently
collection-blocked by these exact fixtures per test_plan.md's Regression Surface — 68 errors);
`test_conftest_snapshot_functions_cover_all_three_sources_via_generalized_helper` (new,
architecture guard, test_plan.md) — asserts no literal `(_AGENT_MONITORING_DIR / "runs.jsonl")` /
`"events.jsonl"` path construction remains outside `monitoring_shards.py` in these 3 files plus
the other 4 production call sites.

### Step 6 — Fold in the 7th call site: `ticket_selection.py::provider_field_coverage`
**Files:** `tools/agent_codex_pilot_guardrails/ticket_selection.py`

**Change:** Current code (L52-73, verified by direct read): `provider_field_coverage` opens
`agent_monitoring_dir / "runs.jsonl"` (L63) unconditionally with `open(runs_path, "r",
encoding="utf-8")` (L65), no shard awareness, no existence guard, and does not import
`monitoring_shards` at all. Confirmed live-broken:
`tests/agent_codex_pilot_guardrails/test_concurrent_claim.py::
test_provider_field_coverage_against_real_corpus_is_populated` currently fails with
`FileNotFoundError`. Replace the single-file open with iteration over
`source_paths(agent_monitoring_dir, "runs.jsonl")`, streaming each file line-lazily (preserving
the function's own documented "line-lazy, mirroring manifest.py::_scan_file's own streaming
technique" contract, L53-54):
```python
def provider_field_coverage(agent_monitoring_dir: Path) -> int:
    count = 0
    for runs_path in source_paths(agent_monitoring_dir, "runs.jsonl"):
        with open(runs_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                record = json.loads(stripped)
                if record.get("provider") is not None:
                    count += 1
    return count
```
Add `from tools.agent_replay_codex.monitoring_shards import source_paths` to this file's imports.

**Other writers to this shared resource:** `runs.jsonl` (now `agent-monitoring/data/<week>/
runs.jsonl`) is written by `tools/agent-monitoring/record_run.py` / `writer.py` (children 1/3,
untouched by this ticket) during real ticket workflow runs, and read elsewhere in this same
package by `assert_no_concurrent_claim` (L28-49, same file) — but that function takes an
in-memory `run_records: list[dict]` parameter, never reads the file itself, so no interaction with
this step's change.

**Do NOT touch:** `select_pilot_candidate` (L14-25), `assert_no_concurrent_claim` (L28-49) —
unrelated to monitoring-source file resolution.

**Verify:**
- `tests/agent_codex_pilot_guardrails/test_concurrent_claim.py::
  test_provider_field_coverage_against_real_corpus_is_populated` — existing, currently failing,
  must pass.
- `test_provider_field_coverage_resolves_sharded_real_repo_runs_source` (new, test_plan.md) —
  synthetic multi-week positive-detection case, parity with the other 6 sites' new tests.

### Step 7 — Full CI-job command + anti-drift diff verification
**Files:** none (verification only)

**Change:** No code change. Run the exact CI-job command named in the ticket's own Scope/AC, and
the anti-drift diff checks from test_plan.md's Scoped Pytest Commands / Anti-Drift Test Guards.

**Verify:**
- Narrow iteration command (test_plan.md) — must show 0 errors/failures across all files this
  ticket touches:
  ```
  pytest tests/agent_codex_pilot_executor tests/agent_codex_posttool_adapter \
    tests/agent_codex_realrepo_pilot_harness tests/agent_codex_pilot_guardrails \
    tests/agent_replay_codex -m "not slow and not extra_slow" -v
  ```
- Full CI-job command (ticket AC #2) — expected to still show exactly 1 pre-existing failure
  (`test_capture_lines_reads_all_three_monitoring_files`, `manifest.py`, child 3) and possibly the
  unowned `tests/agent_replay/test_fixture_envelope.py` failure (Decision 2) if that ticket has
  not been filed/landed yet; both are explicitly out of scope per Decision 2. **Ticket AC #2 as
  literally written (zero errors/failures for the whole command) cannot be fully satisfied by this
  ticket alone — see Acceptance Criteria Map.**
  ```
  pytest tests/agent_codex_live_transport tests/agent_codex_pilot_executor \
    tests/agent_codex_pilot_guardrails tests/agent_codex_pilot_orchestration \
    tests/agent_codex_posttool_adapter tests/agent_codex_realrepo_pilot_harness \
    tests/agent_codex_runtime_shadow tests/agent_orchestration \
    tests/agent_orchestration_claude_adapter tests/agent_orchestration_codex_adapter \
    tests/agent_replay tests/agent_replay_codex -m "not slow and not extra_slow" --tb=short -q
  ```
- `git diff --stat -- tools/agent-monitoring/ src/api/agent_ops_dashboard/ingest.py` — must be
  empty (ticket AC #7).
- `git diff --stat -- tools/agent_codex_realrepo_pilot_harness/policy.py
  tools/agent_codex_pilot_executor/simulation.py` — must be empty (test_plan.md Anti-Drift Test
  Guards).
- `grep -rn "monitoring_shards" --include="*.py" tools/ tests/` — must show 7 files (6 declared +
  `ticket_selection.py`, per Decision 1).
- Re-run `test_config_rollback.py::test_real_committed_config_never_touched_by_this_suite` and
  `tests/agent_codex_realrepo_pilot_harness/conftest.py::real_worktree_is_preserved` — must fail
  loudly (not silently pass-by-omission) if pointed at a monitoring dir missing an expected week
  folder, per test_plan.md's explicit anti-regression instruction.

## Scope Guards

- Do not touch `tools/agent_codex_realrepo_pilot_harness/policy.py`'s `required_monitoring` set or
  `tools/agent_codex_pilot_entrypoint/preparation.py`'s `monitoring_suffixes` dict literal (L50)
  — confirmed logical source-name schema references, not physical file reads.
- Do not touch `tools/agent_codex_pilot_executor/simulation.py`'s `_MONITORING_FILES`/
  `_seed_monitoring` — confirmed self-contained scratch-directory construction; this is the
  canonical scratch shape the generalized helper must keep serving unchanged.
- Do not touch `tools/agent-monitoring/{post_tool_hook,writer,record_run,record_events,
  build_index,generate_retro,manifest,validate,query}.py` or `src/api/agent_ops_dashboard/
  ingest.py` — children 1, 3, 4's files. `manifest.py` is confirmed still mid-migration (its own
  `_scan_tools_shards` still references the old `tools-*.jsonl` shard shape) — leave it exactly as
  is; do not "fix" it opportunistically even though it is adjacent code in a related subsystem.
- Do not fix `tests/agent_replay/test_fixture_envelope.py` — unowned by any epic child, flag as a
  gap for a follow-up ticket instead (Decision 2).
- Do not activate, enable, or invoke any live Codex pilot behavior as a side effect of touching
  this subsystem's code.
- Do not add a shared `source` name registry/constant importable by
  `tools/agent_codex_realrepo_pilot_harness/policy.py` or
  `tools/agent_codex_pilot_entrypoint/preparation.py` — those stay logical-schema-only, untouched.
- Function renames in Step 1 (`tools_source_paths` → `source_paths`,
  `read_tools_source_bytes` → `read_source_bytes`, `hash_tools_source` → `hash_source`) are
  internal to this ticket's own 7 call sites; do not leave old names as unused aliases/shims —
  update every caller directly instead.

## Dependency Map

- Step 1 must land before Steps 2-6 (all of them import from the redesigned module).
- Steps 2, 3, 4, 5, 6 are mutually independent once Step 1 lands (5 distinct files, no shared
  edit surface between them).
- Step 7 (verification) depends on all of Steps 1-6 being complete.
- This entire ticket has a hard prerequisite already satisfied: child 2
  (`TCK-20260903-MONITORING-DATA-MIGRATION`) has landed — confirmed via `ls agent-monitoring/data/`
  showing weeks `2026-W23` through `2026-W36` plus `unknown-week`, each holding
  `{runs,events,tools}.jsonl`.
- This ticket's own AC #2 (full CI-command, zero errors/failures) has an **unresolved external
  dependency on child 3 or child 4 landing their `manifest.py` fix** — not blocking Steps 1-7 of
  this plan, but blocking the ticket's own final AC #2 sign-off. See Acceptance Criteria Map.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Functions resolve all 3 sources against both shapes, tests covering both shapes for each source | Step 1 | `test_runs_and_events_source_paths_resolve_real_and_scratch_shapes`, `test_lines_resolves_a_real_shaped_tree_for_runs_and_events`, updated `test_tools_shard_resolution.py` tests |
| Exact CI-job command passes with zero errors/failures | Steps 1-6 (this ticket's own files); **blocked for the whole command** by child 3/4's `manifest.py` fix and by the unowned `tools/agent_replay/test_fixture_envelope.py` gap (Decision 2) | Step 7's full CI-job command run — expect this ticket's own 7 sites all green; the 2 external failures are explicitly not this ticket's to resolve |
| `assert_no_codex_provider_writes` detects a `provider="codex"` row across all 3 sources | Step 2 | `test_assert_no_codex_provider_writes_detects_a_codex_row_in_a_sharded_runs_or_events_file` |
| `snapshot_rollback_scope`'s combined hash reflects a change in any source | Step 3 | `test_snapshot_rollback_scope_runs_and_events_hash_changes_with_any_week_and_is_stable_otherwise` |
| `proofs.py::_lines()` correctly resolves all 3 sources from a real-shaped captured tree, synthetic-scratch-tree behavior unchanged | Step 1 (implementation), Step 4 (dedicated test) | `test_proofs_lines_resolves_all_three_sources_from_a_real_shaped_captured_tree`, `test_lines_resolves_a_synthetic_scratch_tree_with_a_literal_tools_file` |
| Fallback bucket (`unknown-week`) included wherever a glob is added, for every source, never filtered | Step 1 | `test_fallback_bucket_never_filtered_for_runs_events_or_tools` |
| No functional change to files owned by children 1/3/4 | All steps (scope discipline) | `git diff --stat -- tools/agent-monitoring/ src/api/agent_ops_dashboard/ingest.py` empty |

## Anti-Drift Notes

- **The real-repo "tools" shape itself changed, not just runs/events.** Do not assume the
  existing `tools_source_paths`/`resolve_tree_lines` real-shape branches (keyed on
  `agent-monitoring/tools/tools-*.jsonl`) are still correct and only need runs/events siblings
  added — they are dead code against the live repo today (verified this session) and must be
  repointed to `agent-monitoring/data/<week>/tools.jsonl` as part of Step 1, not preserved.
- **`test_real_monitoring_corpus_has_zero_codex_provider_records` was passing vacuously before
  this ticket** (scanning zero files across all 3 sources, not just runs/events) — after Step 2,
  confirm this test is actually exercising real content by checking it would fail if a
  `provider="codex"` row were temporarily present in the real corpus (do this as a manual sanity
  check during implementation, not as a committed test against real data).
- **Preserve the `resolve_tree_lines` sorted-concatenation-order guarantee** — weeks sort
  lexicographically ahead of `unknown-week` for all 3 sources now, same rule as the old `tools`
  precedent, just generalized.
- **Preserve the "shard keys win over a stray literal key" precedent** for all 3 sources (test
  `test_lines_prefers_shard_keys_over_a_stray_literal_key_when_both_present`, updated per Step 1).
- **The 2 CI-command failures outside this ticket's scope (manifest.py / child 3, and
  `tools/agent_replay/test_fixture_envelope.py` / unowned) must not be fixed here.** Report both
  to the orchestrator/user after this ticket completes — the `manifest.py` one as a landing-order
  dependency already covered by `Related Tickets`, the `test_fixture_envelope.py` one as a genuine
  epic-scoping gap needing a new follow-up ticket filed (repo convention: file real tickets for
  workflow/scope gaps, do not silently patch around them or silently ignore them).
- **Do not widen into `tools/agent-monitoring/*.py` even opportunistically** — `manifest.py`'s
  own mid-migration state (confirmed by direct read) may look like "one small aligned fix," but it
  is explicitly children 3/4's file per this ticket's own Out-of-Scope list and AC #7's empty-diff
  requirement.

## Deviations (recorded during implementation)

Steps 1-6 were implemented exactly as specified, with no functional deviation. Step 7's
verification surfaced two findings materially different from this plan's own Step 7/Anti-Drift
Notes predictions — neither was fixed, per Decision 2 and the Scope Guards; both are recorded
here instead of silently absorbed or silently omitted:

1. **The `manifest.py`-rooted failure count is wider and less stable than "exactly 1" at any given
   instant, because `tools/agent-monitoring/manifest.py` was being actively, concurrently edited
   by another child (3 or 4) throughout this ticket's own implementation session.** At the moment
   this plan was written, the full CI-job command's only `manifest.py`-rooted failure was
   `test_capture_lines_reads_all_three_monitoring_files`. Running the identical command at Step 7
   of implementation instead showed that exact test passing, but 6 *other* tests failing instead,
   all tracing to the same `manifest.py` root cause (confirmed by direct read of each failure's
   traceback, all resolving through `baseline_manifest_gate.py`'s `capture_pilot_baseline`/
   `assert_pilot_baseline_preserved` wrappers around `manifest.py::capture_lines`/
   `assert_prefix_preserved`, or directly through
   `tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py`'s own
   direct exercise of `manifest.py`): `tests/agent_codex_pilot_executor/test_simulation.py::
   test_simulation_writes_coherent_disposable_lifecycle_and_terminalizes_claim`,
   `::test_simulation_prefix_gate_rejects_altered_deleted_or_reordered_history[<lambda>0/1/2]` (3
   cases), `tests/agent_codex_pilot_guardrails/test_baseline_manifest_gate.py::
   test_mutated_pre_existing_line_raises_pilot_manifest_drift_error`, and
   `tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py::
   test_assert_prefix_preserved_rejects_rewritten_lines` /
   `::test_assert_prefix_preserved_rejects_reordered_lines`. None of these files are in this
   ticket's Related Code Areas or touched by any of Steps 1-6; all are downstream of `manifest.py`
   itself being mid-edit, confirmed by `git diff --stat -- tools/agent-monitoring/manifest.py`
   showing an active, uncommitted, non-empty diff throughout this session (11 insertions, 22
   deletions relative to the last commit) that this ticket did not make. This is the same class of
   external dependency this plan already named in Decision 2 and the Acceptance Criteria Map — the
   *count and identity* of affected tests just isn't stable while the dependency is still landing.
   Not fixed here; still blocked on whichever of children 3/4 lands its `manifest.py` fix.

2. **Fixing the 3 conftest.py fixtures' dead-code path (Step 5) surfaces a new, previously-latent
   teardown failure — `tests/agent_replay_codex/test_wrapper_script.py::
   test_wrapper_script_runs_standalone_and_writes_result`'s session teardown, via
   `tests/agent_codex_pilot_executor/conftest.py::_real_surfaces_are_unchanged` — caused by the
   live, shared-worktree monitoring corpus genuinely changing mid-session.** Before this ticket,
   `_snapshot_monitoring()` in that conftest called the (dead-against-the-real-repo)
   `read_tools_source_bytes`, so its session-start/session-end snapshots were vacuously equal
   regardless of real content — the exact "silently passing while checking nothing" pattern this
   whole ticket exists to close. After Step 5's fix, the snapshot genuinely reads
   `agent-monitoring/data/<week>/tools.jsonl`, and this session found that file changing *during
   test execution* — confirmed by `git diff` on `agent-monitoring/data/2026-W36/tools.jsonl`
   showing newly appended rows whose own `session_id`/`run_id` belong to a different, concurrently
   running child session (`TCK-20260903-MONITORING-DATA-CONSUMERS-GATES-DASHBOARD`, agent
   `test-scoper`) — i.e. another active agent's own PostToolUse hook writes landing in the shared
   real corpus mid-test-run, not any write made by this ticket's own code or tests. This is a
   correct detection by the now-fixed guard of a real invariant violation in the current shared
   environment, not a defect introduced by this ticket's changes — reproducibly absent when the
   same test file is run in isolation (outside the session-scoped fixture's multi-directory
   window), and reproducibly present only when run alongside `tests/agent_codex_pilot_executor/`
   in the same pytest session while another agent is concurrently active in this worktree. Not
   fixed here — weakening the fixture's assertion to tolerate live concurrent writes would
   reintroduce exactly the silent-pass defect class this ticket closes, and the actual fix (some
   form of session/writer isolation for concurrent agent sessions sharing one worktree's
   `agent-monitoring/`) is outside this ticket's file scope entirely. Flagged for the
   orchestrator/user as a separate, genuine finding — likely relevant to a future ticket about
   concurrent-session isolation for this monitoring corpus, distinct from both of Decision 2's
   already-known exclusions.

---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION
artifact_type: investigation
tags: [agent-monitoring, observability, data-quality]
---

# Investigation — TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION

## Current Behavior

### `tools/agent_replay_codex/monitoring_shards.py` (full file read)
Confirmed via direct read: this module today is **`tools`-only**, exactly as the ticket's Title
frames it. It does **not** touch `runs`/`events` at all — those two sources are read as literal
single files at every call site, completely outside this helper. Four functions:
- `tools_source_paths(agent_monitoring_dir) -> list[Path]` (L28-39): dual-mode resolver —
  `sorted(glob("tools-*.jsonl"))` under `agent_monitoring_dir/tools/` if that dir exists
  (prior-epic tools-only shard shape), else `[agent_monitoring_dir/tools.jsonl]` if that single
  legacy file exists, else `[]`.
- `read_tools_source_bytes(agent_monitoring_dir) -> bytes` (L42-44): concatenates
  `tools_source_paths()` in sorted order.
- `hash_tools_source(agent_monitoring_dir) -> str` (L47-49): sha256 hex over the above.
- `resolve_tree_lines(tree: dict[str, bytes], name: str) -> list[bytes]` (L52-75): dual-mode
  resolver for a flat `{relative_path: bytes}` tree snapshot. **Only branches on
  `name == "tools.jsonl"`** (L63); every other `name` (i.e. `"runs.jsonl"`, `"events.jsonl"`) falls
  straight through to `tree.get(f"agent-monitoring/{name}", b"")` (L74) — a literal single-key
  lookup, unconditionally. The module docstring (L9-14) and this function's own docstring (L57-61)
  both state outright: *"runs.jsonl/events.jsonl are always single-file in both shapes."* That
  assumption is exactly what this epic breaks (both sources are now sharded per week too), so this
  ticket's "runs/events awareness" is a **genuinely new capability**, not a re-path of existing
  logic — confirmed, not assumed.

`tests/agent_codex_realrepo_pilot_harness/conftest.py`'s docstring on the original hotfix
(`TCK-20260903-HOTFIX-CODEX-MONITORING-SHARD-AWARENESS`, read in full from `tickets/done/`) confirms
the same design intent explicitly in its own "Out of Scope" section: *"`runs.jsonl`/`events.jsonl`
handling anywhere in this subsystem — unaffected, still single files."* No stored artifacts exist
for that hotfix (`stored_artifacts/TCK-20260903-HOTFIX-CODEX-MONITORING-SHARD-AWARENESS/` does not
exist — hotfix tier has no staging artifacts by design); its full design rationale lives in the
ticket file itself under Implementation Notes, which was read in full.

### The 6 declared call sites — verified, count confirmed accurate, plus 1 undeclared 7th site found
Grepped `monitoring_shards` repo-wide (`grep -rn "monitoring_shards" --include="*.py" .`): exactly 6
files import from it, matching the ticket's list one-for-one:
1. `tests/agent_codex_pilot_executor/conftest.py` (L8, L13, L16-19) — `_snapshot_monitoring()`
   reads `runs.jsonl`/`events.jsonl` via direct `(_MONITORING / name).read_bytes()` (module-level
   `_WATCHED_SINGLE_FILES = ("runs.jsonl", "events.jsonl")`), and `tools.jsonl` via
   `read_tools_source_bytes()`. Needs dual-mode treatment for `runs`/`events`.
2. `tests/agent_codex_posttool_adapter/conftest.py` (L24, L28, L31-39) — identical pattern,
   `_snapshot_monitoring_hashes()`, module-level `_WATCHED_SINGLE_FILE_MONITORING_FILES =
   ("runs.jsonl", "events.jsonl")`. Same fix needed.
3. `tests/agent_codex_realrepo_pilot_harness/conftest.py` (L8, L13-17, L20-34) — `_WATCHED` tuple
   holds `.codex/config.toml`, `runs.jsonl`, `events.jsonl` as literal `Path` objects read via
   `path.read_bytes() if path.is_file() else None`; `tools.jsonl` is added separately via
   `read_tools_source_bytes()`. Same fix needed.
4. `tools/agent_replay_codex/provenance_check.py::assert_no_codex_provider_writes` (L14, L16,
   L19-42) — `_SINGLE_FILE_MONITORING_FILENAMES = ("runs.jsonl", "events.jsonl")`, iterated with a
   `path.exists()` guard that **silently skips** the source if missing (matches the same "silent
   coverage gap" class the prior hotfix fixed for `tools`). Confirmed live right now:
   `tests/agent_replay_codex/test_monitoring_provenance.py::test_real_monitoring_corpus_has_zero_codex_provider_records`
   calls this against the real `agent-monitoring/` dir and currently passes only because the
   `.exists()` guard silently stops checking `runs`/`events` entirely (both no longer exist as
   top-level files) — a real, currently-live containment-coverage gap, not hypothetical.
5. `tools/agent_codex_pilot_guardrails/config_toggle.py::snapshot_rollback_scope` (L16, L59-75) —
   unconditional `hashlib.sha256(path.read_bytes())` on `agent_monitoring_dir / "runs.jsonl"` and
   `.../ "events.jsonl"`, no guard at all. **This one crashes for real right now** if invoked
   against the real repo (confirmed: `agent-monitoring/runs.jsonl` and `.../events.jsonl` no longer
   exist at the top level per child 2's migration).
6. `tools/agent_codex_realrepo_pilot_harness/proofs.py::_lines()` (L11, L68-69) — one-line delegate
   to `resolve_tree_lines()`. Consumed generically for **all three** source names inside
   `_assert_suffixes()` (L143-151, iterates `result.policy.monitoring_suffixes` which the fixture
   builders populate with `"runs.jsonl"`, `"events.jsonl"`, `"tools.jsonl"` keys — see
   `tools/agent_codex_pilot_entrypoint/preparation.py` L50 and
   `tests/agent_codex_realrepo_pilot_harness/test_preflight.py` L143) and in `assert_post_run_proof`
   (L184) for the `bounded_tool_suffix` case, which is hardcoded to `"tools.jsonl"` only. Since
   `resolve_tree_lines` only special-cases `"tools.jsonl"`, `runs`/`events` tree lookups currently
   always take the literal-key branch — correct only against a synthetic scratch tree (e.g.
   `tests/agent_codex_realrepo_pilot_harness/test_harness_context.py::_write_shape()`, confirmed by
   direct read to build a real `agent-monitoring/runs.jsonl` literal file inside a `tmp_path`
   scratch tree, never the real repo) — but wrong against a tree captured from the real repo via
   `capture_tree()` (a generic recursive `rglob`, itself needs no change), where `runs`/`events` are
   now also per-week-sharded.

**7th undeclared call site found (real, live, currently-failing) —
`tools/agent_codex_pilot_guardrails/ticket_selection.py::provider_field_coverage`** (L52-73): reads
`agent_monitoring_dir / "runs.jsonl"` via unconditional `open(runs_path, "r", ...)`, zero shard
awareness, zero existence guard, and does **not** import `monitoring_shards` at all — grep for
`monitoring_shards` correctly returned only 6 files because this site never adopted the helper in
the first place (it predates the prior hotfix and was missed by that hotfix's own grep, same root
cause as the prior hotfix's own discovery story). This is in the *same package*
(`tools/agent_codex_pilot_guardrails/`) as call site #5 (`config_toggle.py`), which the ticket does
list. Confirmed live-broken right now, not hypothetical: ran
`pytest tests/agent_codex_pilot_guardrails/test_concurrent_claim.py -q` and got
`FAILED tests/agent_codex_pilot_guardrails/test_concurrent_claim.py::test_provider_field_coverage_against_real_corpus_is_populated`
with `FileNotFoundError: .../agent-monitoring/runs.jsonl`. **This ticket's "6 call sites" framing is
short by one; a 7th genuinely in-scope site (same subsystem, same root cause, same fix pattern)
must be included or explicitly deferred with a stated reason — see Risks.**

### The codex subsystem's own purpose (confirmed via direct read, no README exists)
`tools/agent_replay_codex/invoker.py`'s module docstring: *"Invoker: wires the consent gate, entry
criterion, containment, and real `codex exec` invocation together
(TCK-20260721-CODEX-REPLAY-PARITY, Step 6)."* Combined with `provenance_check.py`'s own docstring
(*"nothing in this package ever calls tools/agent-monitoring/writer.py with provider='codex' — the
whole package only reads fixtures and writes to a scratch-dir JSON file"*) and the already-cited
`TCK-20260721-CODEX-REPLAY-PARITY` framing, this confirms: "codex replay" means containment-gated
readiness/rollback/provenance guardrails for an eventual, still-unauthorized live Codex pilot
invocation — not production monitoring-write code. **Zero of the 7 call sites (6 declared + 1
found) write to the real monitoring corpus.** All are either read-only real-corpus checks
(provenance, rollback-scope hashing, non-mutation test snapshots) or operate entirely against
synthetic `tmp_path` scratch trees. This confirms the ticket's own framing: this is read-only-path
generalization, lower risk than children 1-4's write-path/production-API work.

### Existing tests
`tests/agent_codex_realrepo_pilot_harness/test_tools_shard_resolution.py` (full file read, 51
lines, 5 tests) — all against the private `_lines()` helper (thin delegate to
`resolve_tree_lines()`): synthetic-literal-key tree, real multi-shard tree (asserts sorted-by-week
concatenation + `tools-unknown-week.jsonl` inclusion), shard-keys-preferred-over-stray-literal-key,
empty tree, and — critically — `test_lines_leaves_non_tools_sources_unaffected` (L48-51) which
**directly asserts today's non-generalized behavior**: `_lines(tree, "runs.jsonl")` on a tree with a
literal `"agent-monitoring/runs.jsonl"` key returns that key's lines unconditionally. This exact
test will need to become the *scratch-shape* case of a new dual-mode pair, not simply preserved
as-is, once `runs`/`events` also gain a real-shape shard branch — the test's docstring/module intent
must be updated to state it is testing one of two shapes, not the only shape.

Also directly exercised by real-corpus-touching tests: `test_config_rollback.py`'s
`test_rollback_scope_tools_hash_changes_with_any_shard_and_is_stable_otherwise` (scratch-only,
`tools` source only — needs `runs`/`events` sibling assertions once those become hash-sourced
through the generalized helper too, since `snapshot_rollback_scope`'s `runs.jsonl`/`events.jsonl`
entries currently come from a plain `path.read_bytes()`, not a hash function at all);
`test_monitoring_provenance.py`'s `test_real_monitoring_corpus_has_zero_codex_provider_records`
(runs against the real corpus, silently degraded per the L4 finding above);
`test_config_rollback.py`'s `test_real_committed_config_never_touched_by_this_suite` (unrelated,
`.codex/config.toml` only, no change needed).

### Determinism / replay-fixture implications
Grepped `tests/agent_codex_realrepo_pilot_harness/fixtures`, `tests/agent_codex_pilot_executor/
fixtures`, `tests/agent_replay_codex/fixtures` for any file referencing `tools.jsonl`/`runs.jsonl`/
`events.jsonl`/`agent-monitoring` — **zero matches, no fixture directories exist under those
packages carrying such content**. No frozen replay fixture hardcodes a monitoring-file-shape
assumption. The only places file-shape assumptions live are in Python test/production code itself
(the 7 sites above), all editable as part of this ticket — confirmed no additional frozen-fixture
risk beyond what's already covered by the 7 call sites and the existing
`test_tools_shard_resolution.py` unit tests.

## Mechanics / Engine Constraints
None. This subsystem is explicitly outside Mechanics Bible / engine-contract governance —
confirmed by `docs/parity_ledger/infrastructure.yaml`'s own INFRA-306 entry (below) stating
`tools/agent_codex_posttool_adapter/` is "agent-orchestration/developer-tooling only." Same applies
to `tools/agent_replay_codex/` and `tools/agent_codex_pilot_guardrails/` — no chapter or contract
constrains physical monitoring-file-shape resolution logic.

## Docs Requiring Update
None.

`docs/agent-monitoring/schema.md` (path: `docs/agent-monitoring/schema.md`) is not required to
change for this ticket: confirmed by direct read (it was already updated by child 2's own Step 10,
lines ~116-121, ~153, ~372-384) to describe the current unified
`agent-monitoring/data/<week>/{runs,events,tools}.jsonl` shape and the `unknown-week` fallback
bucket, plus `git log --follow` recovery guidance for all 3 retired legacy paths. It documents the
general write/read-index physical layout, not this internal guardrail subsystem's own snapshot/hash
helper code — this ticket changes only how `tools/agent_replay_codex/`,
`tools/agent_codex_pilot_guardrails/`, and their tests resolve that already-documented layout
internally, which is not a claim schema.md itself makes or needs to restate (same finding the prior
hotfix ticket already made for the `tools`-only case).

## Parity Ledger Overlap
`docs/parity_ledger/infrastructure.yaml` entry `INFRA-306` (`status: verified`, `priority: P2`)
documents `tools/agent_codex_posttool_adapter/` (`TCK-20260730-CODEX-POSTTOOL-ADAPTER`) — cites
`record_builder.py`, `redaction.py`, `identity.py`, `live_gate.py`, `writer_bridge.py`,
`activation_fragment.py`. **Not touched by this ticket**: none of those files read
`runs.jsonl`/`events.jsonl`/`tools.jsonl` directly (the package's own conftest.py, one of this
ticket's 6 declared call sites, is a suite-level non-mutation *test* fixture, not part of
`INFRA-306`'s described production-code surface). No `status`/`v2_evidence` change needed; P2 so no
`test_path` currency requirement either. No other parity-ledger entry references `monitoring_shards`,
`agent_replay_codex`, or `agent_codex_pilot_guardrails` by name (grepped all of
`docs/parity_ledger/*.yaml` for those terms).

## Prior Work
- `stored_artifacts/TCK-20260902-MONITORING-SHARD-CONSUMERS/` — the read-path dual-mode pattern
  this ticket's helper already reuses (per the prior hotfix's own design note).
- `tickets/done/TCK-20260903-HOTFIX-CODEX-MONITORING-SHARD-AWARENESS.md` — read in full (no
  stored_artifacts exist for it, hotfix tier). Built the exact helper and 6-site wiring this ticket
  generalizes; explicitly scoped `runs`/`events` as unaffected/out-of-scope at the time, which is
  exactly what this ticket now reopens.
- `tickets/done/TCK-20260903-MONITORING-DATA-MIGRATION.md` — hard prerequisite, confirmed landed:
  `agent-monitoring/data/<week>/{runs,events,tools}.jsonl` exists on disk for weeks `2026-W23`
  through `2026-W36` plus `agent-monitoring/data/unknown-week/{runs,events,tools}.jsonl` (verified
  via `ls`). **Fallback bucket naming resolved by direct observation**: it is the directory
  `unknown-week` (not `tools-unknown-week.jsonl`-style filename prefixing) — the assumption/open
  question in this ticket's own body ("depends on child 2's final decision") is now answered: one
  `unknown-week` folder holding all 3 sources' fallback files, matching the same
  `<week>/{runs,events,tools}.jsonl` shape as every other week.

## Risks and Open Questions

1. **Ticket's "6 call sites" is short by one — `ticket_selection.py::provider_field_coverage` is a
   7th genuinely in-scope, currently-broken site**, in the same package as an already-declared site.
   Confirmed via a real, reproduced test failure (not a hypothetical grep hit). This needs an
   explicit decision before Plan: either fold it into this ticket's scope (recommended — same
   subsystem, same root cause, same fix pattern, avoids leaving a known-broken function in a
   package this ticket is already touching) or explicitly defer it with a stated reason and a
   follow-up ticket filed. Silently leaving it out matches neither Format 1 nor Format 2 doc
   handling — it is a code gap, not a doc — but the same "don't silently drop a discovered gap"
   principle applies.

2. **The full CI-job command named in the ticket's own Scope/AC (`pytest
   tests/agent_codex_live_transport ... tests/agent_replay_codex -m "not slow and not
   extra_slow"`) currently has 2 additional failures outside this ticket's own file scope**,
   confirmed by actually running that exact command against the current worktree:
   - `tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py::test_capture_lines_reads_all_three_monitoring_files`
     — fails via `tools/agent-monitoring/manifest.py::capture_lines`, a file this ticket's own
     Out-of-Scope list explicitly assigns to children 1/3/4. **Blocks this ticket's AC #2 (exact
     command passes with zero errors/failures) until whichever of children 3/4 fixes
     `manifest.py` also lands** — a real cross-ticket sequencing dependency, not something to fix
     here.
   - `tests/agent_replay/test_fixture_envelope.py::test_real_fixture_set_loads_and_validates` —
     fails reading `agent-monitoring/runs.jsonl` directly. **This is in `tools/agent_replay/`, a
     separate, non-codex generic replay package (sibling to, not part of,
     `tools/agent_replay_codex/`)**, named in the CI-job command but not owned by this ticket, any
     of children 3/4/6, or any other epic child found in `Related Tickets`. This is an
     **undiscovered gap in the epic's own scoping** — the epic's 6 children do not cover it. Flag
     for a decision at Plan: either this ticket's scope quietly widens to include this one file
     (it is a single-file, single-test fix, same root cause), or a new gap ticket must be filed per
     this repo's established practice of filing real tickets for workflow/scope gaps rather than
     silently patching around them — do not assume either answer here.

   Both are already-failing today (pre-existing, not introduced by this ticket), confirmed by
   running the exact command before any change was made — this ticket did not cause them, but its
   own AC #2 as literally written cannot pass while either remains unfixed by someone.

3. **`resolve_tree_lines`'s "prefers shard keys over stray literal key" precedent (tested,
   `test_lines_prefers_shard_keys_over_a_stray_literal_key_when_both_present`) must be preserved
   per-source once generalized** — i.e. if a captured tree somehow carries both an
   `agent-monitoring/data/<week>/runs.jsonl` key and a legacy `agent-monitoring/runs.jsonl` key,
   the shard-shape branch should win, matching the existing `tools` precedent. Not expected in
   practice (mutually exclusive shapes) but should be an explicit test case for consistency.

4. Naming the new `source` parameter (`"runs"`/`"events"`/`"tools"` vs. filenames
   `"runs.jsonl"`/etc.) is left to the implementer per the ticket's own Assumptions — no existing
   convention forces one over the other; `resolve_tree_lines` already takes a `name` parameter
   shaped as `"tools.jsonl"` (with extension), so extending that exact shape is the lower-diff
   choice, but `tools_source_paths`/`read_tools_source_bytes`/`hash_tools_source` currently take no
   name parameter at all (single-source, hardcoded) and will need one added regardless of shape
   chosen.

## Anti-Drift Hazards
- **Do not touch `tools/agent_codex_realrepo_pilot_harness/policy.py`'s `required_monitoring`
  set** (`{"runs.jsonl", "events.jsonl", "tools.jsonl"}`, confirmed by direct read) or
  `tools/agent_codex_pilot_entrypoint/preparation.py`'s `monitoring_suffixes` dict literal (L50) —
  both are confirmed logical source-name schema references, not physical file reads; already
  explicitly out of scope per this ticket and the prior hotfix's identical finding.
- **Do not touch `tools/agent_codex_pilot_executor/simulation.py`'s `_MONITORING_FILES`/
  `_seed_monitoring`** — confirmed self-contained against a synthetic scratch directory it
  constructs itself (`_MONITORING_FILES = ("runs.jsonl", "events.jsonl", "tools.jsonl")`, all 3
  built as literal files inside a throwaway scratch tree). This is the canonical "legacy/scratch
  shape" this ticket's generalized helper must keep serving unchanged.
- **Do not widen scope into `tools/agent-monitoring/{manifest,build_index,generate_retro,validate,
  query,post_tool_hook,writer,record_run,record_events}.py`** — those are children 1/3/4's files,
  confirmed already correctly migrated or in-flight in sibling tickets; this ticket's own AC #7
  requires an empty `git diff --stat` against `tools/agent-monitoring/*.py` and
  `src/api/agent_ops_dashboard/ingest.py`.
- **Preserve the never-filter-`unknown-week` convention** — now applies to all 3 sources under the
  unified `agent-monitoring/data/unknown-week/{runs,events,tools}.jsonl` shape, not a per-source
  filename-prefixed fallback file. Any new glob this ticket adds for `runs`/`events` must include
  the `unknown-week` folder the same way `tools` shard globs already include
  `tools-unknown-week.jsonl` today.
- **`resolve_tree_lines`'s sorted-concatenation-order guarantee must extend identically to
  `runs`/`events`** — the existing `tools` tests assert weeks are sorted lexicographically
  (`2026-W01` before `2026-W02` before `unknown-week`, since `"W01" < "W02" < "unknown-week"` as
  strings); do not silently change this ordering rule when generalizing.
- Do not activate, enable, or invoke any live Codex pilot behavior as a side effect of touching
  this subsystem's code — confirmed explicitly out of scope by the ticket and unrelated to the
  monitoring-shard generalization itself.

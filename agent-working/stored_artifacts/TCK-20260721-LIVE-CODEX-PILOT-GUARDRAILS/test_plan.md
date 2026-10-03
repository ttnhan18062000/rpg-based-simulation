---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS
artifact_type: test_plan
tags: [ai, workflows, hooks, rollback]
---

# Test Plan — TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS

## Regression Surface

Existing tests that must keep passing, by file path. No `src/` simulation code or
arena-combat suite is in this ticket's blast radius (confirmed in investigation.md's
Mechanics/Engine Constraints — not applicable).

**Unit / process-neutral (predecessor tooling this ticket consumes read-only):**
- `tests/agent_replay/test_runner_no_forbidden_calls.py`
- `tests/agent_replay/test_no_mutation_snapshot.py`
- `tests/agent_replay_codex/test_entry_criterion.py`
- `tests/agent_replay_codex/test_consent_gate.py`
- `tests/agent_replay_codex/test_containment.py`
- `tests/agent_replay_codex/test_codex_config_guard.py`
- `tests/agent_replay_codex/test_no_forbidden_calls.py`
- `tests/agent_orchestration/*` (contract core)
- `tests/agent_orchestration_claude_adapter/*` (includes
  `test_no_codex_scope_creep.py::test_no_production_hook_registered_in_codex_config` — must stay
  green; this ticket's own config/flag work must not regress it)
- `tests/agent_orchestration_codex_adapter/*` (includes
  `test_no_production_hook_enabled.py` — same invariant, Codex-adapter side)
  (known pre-existing, unrelated failure carried forward from every predecessor ticket in this
  batch: `tests/agent_orchestration/test_contract_structure.py::
  test_contract_yaml_has_versioning_field_and_documented_scheme`, `FileNotFoundError` on a stale
  `staging_artifacts/` path, tracked by the still-open
  `tickets/todos/TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH.md` — do not "fix" it here, do not
  let it be misread as a regression this ticket introduced)

**Integration (baseline-manifest + monitoring-writer tooling this ticket's rollback/snapshot logic
depends on):**
- `tests/tools/test_monitoring_writer.py`
- `tests/tools/test_monitoring_writer_lockfile_candidate.py`
- `tests/tools/test_post_tool_hook.py`
- `tests/tools/test_record_run.py`
- `tests/tools/test_record_events.py`
- `tests/tools/test_agent_ops_dashboard_ingest.py` (provider/execution_id/ticket_id
  read-side fields this ticket's own signal-availability gap, investigation.md Risk #3, is
  scoped around — must not regress, not itself modified by this ticket)

**Ticket/field-validation tooling (only if Plan's Risk #2 decision extends the ticket template):**
- `tests/tools/test_ticket_field_values.py` (or equivalent — exact file name depends on how
  `tools/ticket_field_values.py`'s own test suite is organized; verify the real path during
  Implement before assuming this exact name)
- `tools/validate_frontmatter.py`'s own test suite, if Plan's chosen "human owner"/"rollback plan"
  field shape touches frontmatter validation at all (unlikely — these are body fields per the
  existing `## Tier`/`## Status` precedent — but must be checked, not assumed, once Plan decides
  Risk #2)

**Arena-combat / simulation:** none.

## New Tests Required

Per the ticket's 7 acceptance criteria. Exact test names/module layout are Plan-phase decisions
(investigation.md's Risks #1/#2/#3/#5) — this lists what each new test must verify, not its final
shape or package name.

1. **Ticket-selection rejects missing human owner / missing rollback plan**
   - Category: unit / architecture guard
   - Verifies: given a candidate ticket lacking Plan's chosen structured owner/rollback-plan
     representation (investigation.md Risk #2), the selection step returns/raises a named rejection
     result — not a silent pass, not a generic exception. Must include both a positive case
     (candidate with both fields present → accepted) and two independent negative cases (owner
     present but rollback plan absent; rollback plan present but owner absent) — a single combined
     negative case would not prove the two checks are independently enforced.
   - Location: new package's own test file, e.g. `test_ticket_selection.py` (package name TBD by
     Plan, following the batch's established `tools/<concern>/` per-ticket convention).

2. **Ticket-selection rejects concurrent same-work claim by both providers**
   - Category: unit / architecture guard
   - Verifies: given synthetic run-state input shaped like two providers claiming the same
     `ticket_id` concurrently, the selection step rejects it. Because investigation.md Risk #3
     confirms no real `agent-monitoring/runs.jsonl` record carries a `provider` field today, this
     test's fixture data must be **explicitly synthetic/constructed**, not read from the real
     corpus — and the test (or an adjacent one) must assert this limitation directly: e.g. a
     companion test confirming that scanning the real, current `agent-monitoring/runs.jsonl`
     produces zero `provider`-bearing records, so a reviewer can see the gap is acknowledged rather
     than silently assumed away. Do not let this test's green pass be mistaken for proof the check
     works against real historical data.
   - Location: same new package, e.g. `test_ticket_selection.py` or `test_concurrent_claim.py`.

3. **Enabled hook/writer set is a subset of Phase-2/Phase-3 evidence**
   - Category: architecture guard
   - Verifies AC #3 literally: the pilot's own enabled-hook-event set is `⊆ {"PostToolUse"}` and
     its enabled-writer-function set is `⊆ {write_line, write_lines}` from
     `tools/agent-monitoring/writer.py` — sourced either from a new constant this ticket defines or
     from `agent-orchestration/hook-events.yaml` (Plan must read that file first, per
     investigation.md Risk #5, before deciding which). Must fail if a future edit widens the
     enabled set beyond what Phase 2/3 evidenced (e.g. adding `PreToolUse` or a raw
     `open(..., "a")` bypass of `writer.py`) without updating the evidence basis too — i.e. this is
     a real subset-assertion test, not a hardcoded equality check that would pass trivially.
   - Location: same new package, e.g. `test_enabled_surface.py`.

4. **Pre/post baseline-manifest diff fails closed on any pre-existing line change**
   - Category: integration
   - Verifies: reuses `tools/agent-monitoring/manifest.py::capture_lines`/
     `assert_prefix_preserved` unmodified (per investigation.md's explicit "consume, not rebuild"
     finding) around a simulated pilot run. Must include a **negative control**: deliberately
     mutate one pre-existing line in a `tmp_path` copy of the manifest data between the pre and
     post snapshot, and assert the pilot workflow's own wrapper around
     `assert_prefix_preserved` surfaces this as a fail-closed rejection (not merely that
     `assert_prefix_preserved` itself raises — the pilot workflow's own gate-check wrapper must be
     what's under test, matching investigation.md Risk #4's "hash changes" vocabulary reconciliation
     — state explicitly whether this test targets the prefix-check, the whole-file-hash check from
     `build_manifest()`, or both).
   - Location: same new package, e.g. `test_baseline_manifest_gate.py`.

5. **Codex-adapter rollback is a single config/flag flip; zero-byte-diff proof**
   - Category: integration
   - Verifies AC #2 literally: performing the rollback (disable) action leaves
     `agent-monitoring/{runs,events,tools}.jsonl` and the pilot ticket file byte-for-byte unchanged
     — i.e. the rollback action itself touches only the config/flag artifact, never the monitoring
     corpus or ticket file. Must run against a `tmp_path`/scratch copy of the config artifact, never
     the real committed `.codex/config.toml` (per investigation.md's Anti-Drift Hazards — this
     ticket must not leave a hook-enabled state committed). Must include the "enable → verify pilot
     surface is live-capable in the toggle's own model → rollback → assert zero diff" full round
     trip, not merely the disable half in isolation, so the test actually proves rollback recovers
     from an enabled state rather than trivially passing from an already-disabled one.
   - Location: same new package, e.g. `test_config_rollback.py`.

6. **Human sign-off gate refuses to proceed without it, distinct from and later than ticket
   designation**
   - Category: unit / architecture guard
   - Verifies AC #5: the pilot-execution entry point (not the ticket-selection step from tests
     1-2 above) refuses to proceed (raises a named exception, never silently defaults to
     "proceed") when the sign-off mechanism Plan designs is absent — and, critically, that
     ticket-selection succeeding does NOT itself satisfy this later gate (i.e. two independent
     checks, not one check reused twice). Mirror
     `tools/agent_replay_codex/consent_gate.py::require_live_consent()`'s strict, non-coercive
     equality pattern (no truthy coercion) if Plan chooses an env-var-shaped mechanism, or an
     equivalent strict check if Plan chooses a token-file mechanism instead.
   - Location: same new package, e.g. `test_signoff_gate.py`.

7. **This ticket's own scope-boundary self-assertion (AC #7)**
   - Category: unit / architecture guard
   - Verifies: no code path anywhere in this ticket's own new package can, even when every gate
     above is satisfied, actually invoke a real `codex exec`/production hook against a real ticket
     — i.e. this ticket's own deliverable has no "execute now" entry point at all, only
     selection/rollback/manifest/sign-off *tooling*. A reasonable mechanical proxy: an AST or
     import-graph scan (mirroring `tests/agent_orchestration/test_validator_no_network_calls.py`'s
     existing `_SCOPE_CREEP_MARKERS` pattern) asserting this ticket's new package never imports
     `tools.agent_replay_codex.invoker` or calls `subprocess.run(["codex", ...])` directly — the
     guardrail tooling checks preconditions and flips configuration; it does not itself drive Codex.
   - Location: same new package, e.g. `test_no_live_execution_path.py`.

## Scoped Pytest Commands

Never `pytest tests/`. Scoped to the affected domain(s):

```
# The new package this ticket adds (exact path is a Plan decision)
pytest tests/agent_codex_pilot_guardrails/ -v   # placeholder name — confirm real path at Implement

# Predecessor tooling this ticket consumes read-only — must stay green
pytest tests/agent_replay/ -v
pytest tests/agent_replay_codex/ -v
pytest tests/agent_orchestration/ tests/agent_orchestration_claude_adapter/ tests/agent_orchestration_codex_adapter/ -v

# Monitoring-writer + baseline-manifest regression (this ticket's manifest-diff/rollback logic depends on these)
pytest tests/tools/test_monitoring_writer.py tests/tools/test_monitoring_writer_lockfile_candidate.py tests/tools/test_post_tool_hook.py tests/tools/test_record_run.py tests/tools/test_record_events.py -v

# Dashboard read-side regression (provider/execution_id fields this ticket's Risk #3 gap concerns)
pytest tests/tools/test_agent_ops_dashboard_ingest.py -v
```

If Plan's Risk #2 decision extends the ticket-field validation surface
(`tools/ticket_field_values.py` or `tools/validate_frontmatter.py`), add that module's own test
file to the command list explicitly once its real path is confirmed — do not assume the name here.

## Anti-Drift Test Guards

- **No test in this ticket's new package may ever flip the real, committed `.codex/config.toml`
  to a hook-enabled state and leave it that way.** Every rollback/enable-disable test (New Test #5)
  must operate on a `tmp_path` copy; a final assertion (or a session-scoped fixture teardown check)
  should confirm the real committed file is still byte-identical to its pre-suite state after the
  full test run — mirroring the batch's existing `assert_config_bytes_unchanged` pattern but
  applied at the *test-suite* level, not just inside one test.
- **The "concurrent claim by both providers" test (New Test #2) must not be allowed to quietly pass
  as a false proof of real-world coverage.** Per investigation.md Risk #3, a companion assertion
  (or an explicit skip-reason/xfail-with-comment) must make visible that this check currently only
  exercises synthetic data, since no real record has a `provider` field yet — a reviewer scanning
  green test output alone should not conclude the concurrent-claim guard is proven against live
  data.
- **A baseline-manifest fail-closed test with no negative control is not a valid guard** (New Test
  #4) — mirrors the identical anti-drift principle `CODEX-REPLAY-PARITY`'s own test plan required
  for its containment test; the same reasoning applies here: "no violation observed" on a run that
  never exercises the failure path proves nothing.
- **Guard against silently treating ticket-selection success as sign-off** (New Test #6) — a test
  asserting these are two independently-gated code paths, not one gate whose result is reused,
  directly enforces AC #5's "distinct from and later than ticket designation" wording.
- **Guard against scope creep into a real live-execution entry point** (New Test #7) — this is the
  single most important anti-drift guard in this ticket's entire suite, given this is "the only
  concern touching genuinely irreversible-risk territory" per the ticket's own Request Summary.
  Any PR/diff that adds a code path importing `tools.agent_replay_codex.invoker` or spawning a real
  `codex` subprocess from this ticket's new package should be treated as an AC #7 violation, not a
  reasonable extension.
- **Guard against accepting unstructured prose as "recorded human owner"/"rollback plan" evidence**
  (New Test #1) — the negative cases must use a candidate ticket whose free-text body *mentions*
  "owner" or "rollback" in prose (e.g. inside `## Implementation Notes`) without satisfying
  whatever structured field Plan designs, proving the check reads structured data, not keyword-greps
  the ticket body.
- **Guard the known pre-existing failure from silently multiplying**: if
  `test_contract_yaml_has_versioning_field_and_documented_scheme` is still failing when this ticket
  reaches Verify, the ticket's own Test Summary must name it explicitly as pre-existing/unrelated
  (matching every predecessor ticket's own precedent for how to report it), not silently absorbed
  into this ticket's own pass count.

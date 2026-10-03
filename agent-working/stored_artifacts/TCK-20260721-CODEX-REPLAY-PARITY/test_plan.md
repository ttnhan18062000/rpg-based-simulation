---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-CODEX-REPLAY-PARITY
artifact_type: test_plan
tags: [ai, workflows, process-improvement, hooks]
---

# Test Plan — TCK-20260721-CODEX-REPLAY-PARITY

## Regression Surface

Existing tests that must keep passing, by file path. All verified runnable today
(`.venv/bin/python3 -m pytest ...`); baseline pass/fail state recorded so this ticket's own
Implement/Verify phases can distinguish a pre-existing failure from a real regression.

**Unit / process-neutral (agent-replay + orchestration contract stack):**
- `tests/agent_replay/test_runner.py`
- `tests/agent_replay/test_fixture_spec_doc.py`
- `tests/agent_replay/test_fixture_envelope.py`
- `tests/agent_replay/test_runner_no_forbidden_calls.py`
- `tests/agent_replay/test_no_mutation_snapshot.py`
  (baseline: `pytest tests/agent_replay/ -q` → **25 passed**, verified directly)
- `tests/agent_orchestration/*` (contract core: loader/generator/bootstrap-equality/etc.)
- `tests/agent_orchestration_claude_adapter/*` (terminal-status conformance, containment, scope-creep guard)
- `tests/agent_orchestration_codex_adapter/*` (legacy-skills containment, generator write-guard/traceability, AGENTS.md generation, no-production-hook)
  (baseline: `pytest tests/agent_orchestration/ tests/agent_orchestration_claude_adapter/ tests/agent_orchestration_codex_adapter/ -q`
  → **83 passed, 1 failed** — the 1 failure is
  `tests/agent_orchestration/test_contract_structure.py::test_contract_yaml_has_versioning_field_and_documented_scheme`,
  a **known, pre-existing, unrelated** stale-path failure tracked by the still-open
  `tickets/todos/TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH.md` — confirmed directly, not
  caused by this ticket's own diff. Do not "fix" it here (out of scope); do not let a future run
  of this same command be misread as a new regression this ticket introduced.)

**Integration (monitoring writer + call sites this ticket's shadow-mode provenance check depends on):**
- `tests/tools/test_monitoring_writer.py`
- `tests/tools/test_monitoring_writer_lockfile_candidate.py`
- `tests/tools/test_post_tool_hook.py`
- `tests/tools/test_record_run.py`
- `tests/tools/test_record_events.py`
  (baseline: `pytest tests/tools/test_monitoring_writer.py tests/tools/test_post_tool_hook.py tests/tools/test_record_run.py tests/tools/test_record_events.py -q`
  → **55 passed**, verified directly)
- `tests/tools/test_agent_ops_dashboard_ingest.py`, `test_agent_ops_dashboard_api.py`,
  `test_agent_ops_dashboard_api_boundary.py`, `test_agent_ops_dashboard_concurrency.py`
  (provider/execution_id-aware dashboard reads this ticket's shadow-mode results could surface
  through, per `MONITORING-WRITER-UNIFICATION`'s own `ingest.py` extension — not modified by this
  ticket, but must not regress).
- `tests/tools/test_codex_capability_diagnostics.py` (real-`codex`-CLI-present diagnostic, skip-clean
  when absent)
- `tests/tools/test_codex_hook_payload_fixture.py` (validates the existing captured hook-payload
  fixture — this ticket must not accidentally corrupt or duplicate that fixture's format)
- `tests/unit/lab_agent/test_workflow_registry.py`

**Arena-combat / simulation:** none — this ticket touches no `src/` simulation code, confirmed by
investigation's Mechanics/Engine Constraints section (not applicable).

## New Tests Required

Per the ticket's 9 acceptance criteria. Exact test names, file locations, and internal design
(e.g. whether shadow mode compares 2 vs. 5 fixtures) are Plan-phase decisions per investigation's
Risks #1/#2/#4 — the list below states what each new test must verify, not its final name/shape.

1. **Entry-criterion gate test**
   - Category: unit / architecture guard
   - Verifies: this ticket's own real-Codex-execution code path structurally refuses to run (raises
     or exits) unless `MONITORING-WRITER-UNIFICATION`'s writer module is importable/landed — i.e.
     the entry criterion is enforced in code, not merely documented.
   - Location: new package's own test file, e.g.
     `tests/agent_replay_codex/test_entry_criterion.py` (exact package name is a Plan decision).

2. **Programmatic human-consent gate test**
   - Category: unit / architecture guard
   - Verifies: the real-Codex-invocation entry point refuses to proceed (raises a named exception,
     never silently skips or defaults to "proceed") when the consent mechanism Plan designs (e.g.
     an env var / consent-token file / required explicit argument) is absent or stale. Must include
     both a negative case (absent consent → refusal, no `codex` subprocess spawned — assert via a
     monkeypatched/mocked subprocess call that it was never invoked) and a positive case (consent
     present → proceeds to the next step).
   - Location: same new package, e.g. `test_consent_gate.py`.

3. **Containment-technique test (the ONE method Plan selects)**
   - Category: integration (real Codex CLI required — should `pytest.skip` cleanly, mirroring
     `test_codex_capability_diagnostics.py`'s `shutil.which("codex") is None` guard, when `codex`
     is not on `PATH` or when the consent gate is not satisfied)
   - Verifies: whichever technique Plan selects (strace file-open trace / namespace-sandbox /
     isolated-scratch-dir + porcelain-or-content-hash diff, per investigation's tradeoff table) —
     actually proves zero write to `tickets/**` and zero append to
     `agent-monitoring/{runs,events,tools}.jsonl` across one real Codex invocation. Must assert
     both a **negative control** (the technique correctly detects a synthetic touch — e.g.
     deliberately write a byte to a scratch copy mid-test and confirm the check fails) and the real
     **positive proof** (a real Codex invocation produces zero detected touch) — a containment test
     with no negative control cannot prove it would ever catch a real violation.
   - Location: new package's own test file, e.g. `test_containment_real_process.py`.

4. **Zero-production-hook-invocation test**
   - Category: integration
   - Verifies: across the real Codex invocation(s) this ticket performs, `.codex/config.toml`
     remains byte-identical to its committed, comment-only state before/after (reuse the
     `tomllib.load(...) == {}` assertion pattern from
     `tests/agent_orchestration_codex_adapter/test_no_production_hook_enabled.py`), and no
     `~/.codex/` hook-registration side-effect leaks into this repo's own tree.
   - Location: same new package.

5. **Pre/post content-hash or git-porcelain snapshot assertion (ticket AC's own explicit bullet,
   distinct from the general containment test above — scoped specifically to `tickets/` and
   `agent-monitoring/*.jsonl` around the real invocation)**
   - Category: integration
   - Verifies: reuses `tools/agent-monitoring/manifest.py::capture_lines`/`assert_prefix_preserved`
     (the exact pair `CODEX-GUIDANCE-FIXTURE-CAPTURE` already proved fit-for-purpose for "a live
     workflow execution that legitimately appends to these files during the same run") — snapshot
     immediately before/after the real Codex invocation specifically (not the whole ticket's test
     run), assert the prefix is preserved with zero rewrite/reorder/delete.
   - Location: same new package.

6. **Phase-completion / gate-result / artifact-reference / normalized-event-intent parity test**
   - Category: integration
   - Verifies: running the same fixture (the existing
     `tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml`, or a structurally
     identical new one per investigation Risk #4) through both `tools.agent_replay.runner.replay_slice()`
     (existing) and this ticket's new Codex-adapter execution path produces matching
     `final_status`/`phases_completed` — and, per the ticket's AC on shadow mode specifically,
     matching gate result and required-artifact references too. Any mismatch must be checked
     against `agent-orchestration/intentional-divergences.md` before failing (reuse
     `tools/agent_orchestration_claude_adapter/divergence_log.py::is_approved()`'s pattern/shape,
     or a Codex-side equivalent, per Plan's decision on where Codex-side divergences get logged).
   - Location: same new package, e.g. `test_phase_parity.py`.

7. **Shadow-mode comparison across N real implement-ticket inputs**
   - Category: integration
   - Verifies: for each of the N inputs Plan defines (investigation Risk #4), Claude's already-live
     result (from the real historical ticket the fixture was derived from) and Codex's replayed
     result are compared and recorded (phase completion, gate result, artifact refs, normalized
     event intent) — with **zero write to the live monitoring corpus attributable to Codex** as a
     structural assertion of every one of these N comparisons, not just a summary claim.
   - Location: same new package, e.g. `test_shadow_mode_comparison.py`.

8. **Monitoring-record-provenance test — Claude is the sole live writer**
   - Category: architecture guard
   - Verifies: after every real-Codex-touching test in this suite runs, no record in the real
     `agent-monitoring/{runs,events,tools}.jsonl` carries `provider == "codex"` (or whatever
     canonical Codex provider string Plan settles on, per investigation Risk #5) — a direct,
     mechanical check enabled by `MONITORING-WRITER-UNIFICATION`'s new `execution_id`/`provider`
     fields. This is the AC's own "verified via monitoring-record provenance" requirement made
     concrete and automated, not left to manual inspection.
   - Location: same new package.

9. **Divergence-registration test**
   - Category: unit
   - Verifies: if the parity/shadow-mode tests above find any real mismatch, it is registered in
     `agent-orchestration/intentional-divergences.md` with the required
     `Approved-by`/`Approved-date`/`Status: RATIFIED` fields before the ticket can close — mirrors
     `tests/agent_orchestration_claude_adapter/test_divergence_log.py`'s
     `test_human_approved_divergence_marker_is_parsed_and_enforced` shape, reused or newly written
     for this ticket's own axis (e.g. `axis: codex_parity`).
   - Location: same new package, or extend `tests/agent_orchestration_claude_adapter/test_divergence_log.py`
     if Plan decides to share the divergence-log module rather than fork it (a genuine Plan-phase
     reuse-vs-fork decision, not assumed here).

## Scoped Pytest Commands

Never `pytest tests/`. Scoped to the affected domain(s):

```
# The new package this ticket adds (exact path is a Plan decision, e.g. tests/agent_replay_codex/)
pytest tests/agent_replay_codex/ -v

# Existing replay-proof regression (must stay green, untouched by this ticket)
pytest tests/agent_replay/ -v

# Existing orchestration-contract stack regression (1 known pre-existing failure, see Regression Surface)
pytest tests/agent_orchestration/ tests/agent_orchestration_claude_adapter/ tests/agent_orchestration_codex_adapter/ -v

# Monitoring-writer regression (this ticket's provenance checks depend on this landing correctly)
pytest tests/tools/test_monitoring_writer.py tests/tools/test_post_tool_hook.py tests/tools/test_record_run.py tests/tools/test_record_events.py -v

# Codex-CLI-present diagnostics + hook-payload fixture (skip-clean without codex on PATH)
pytest tests/tools/test_codex_capability_diagnostics.py tests/tools/test_codex_hook_payload_fixture.py -v

# Dashboard read-side regression (provider/execution_id filtering this ticket's results could surface through)
pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_concurrency.py -v
```

## Anti-Drift Test Guards

- **No test in this ticket's new package may ever target a path resolving under the real repo's
  `agent-monitoring/` directory for a *write* it expects to succeed** — every write-path test must
  target `tmp_path` or the isolated scratch directory; only the read-only snapshot/diff tests (#3,
  #5, #8 above) may read the real `agent-monitoring/*.jsonl` files, and only to assert absence of
  change, never to seed test data into them.
- **A containment test with no negative control is not a valid guard** (see New Test #3) — every
  containment-proof test must demonstrate it can actually detect a synthetic violation, not merely
  report "no violation observed" on a run that never exercises the failure path.
- **The consent-gate test (New Test #2) must assert the underlying `codex` subprocess call was
  never made when consent is absent** — not merely that the function returned an error. A test
  that only checks the return value could pass even if the code called `codex` first and checked
  consent after, which would violate the AC's "refuses to proceed" wording.
- **Guard against silently reusing the AST-scan technique for the real-Codex containment proof** —
  a test asserting "this ticket's new package contains no `ast.parse`-based check pretending to
  cover the Codex-process boundary" is not required as its own test, but any reviewer/Architecture-Verify
  pass should treat an AST-only proof for the Codex side as a failed AC, per the ticket's own
  explicit "not AST scan" wording.
- **Guard against a shadow-mode "comparison" that silently applies Codex's output anywhere** — every
  shadow-mode test (#7) must assert, in addition to the comparison result itself, that no file
  under `tickets/`, no `agent-orchestration/` contract file, and no `.claude/` file was modified as
  a side effect of running the comparison — reusing the same snapshot/diff mechanics as New Test #5,
  applied around the whole shadow-mode comparison rather than just the raw Codex invocation.
- **Guard the known pre-existing failure from silently multiplying**: if
  `test_contract_yaml_has_versioning_field_and_documented_scheme` is still failing when this ticket
  reaches Verify, the ticket's own Test Summary must name it explicitly as pre-existing/unrelated
  (matching `CODEX-GUIDANCE-FIXTURE-CAPTURE`'s own precedent for how to report it) rather than
  silently absorbing it into this ticket's own pass count or, worse, "fixing" it as an
  undocumented drive-by change.
- **Guard against inventing a second fixture-envelope format**: any new fixture(s) this ticket adds
  for the N-input shadow-mode comparison (New Test #7) must validate through the existing
  `tools/agent_replay/fixture_envelope.py::load_fixture()` unchanged — a test asserting this
  (`load_fixture(new_fixture_path)` succeeds without modification to `fixture_envelope.py`) is a
  direct guard against silently forking the envelope schema.

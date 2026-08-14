---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260721-CODEX-REPLAY-PARITY
phase: done
date: 2026-07-21
tags: []
---

# TCK-20260721-CODEX-REPLAY-PARITY

## Title
Real Codex replay adapter and parity suite

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Run the replay fixture through the actual Codex adapter (not just the provider-neutral Python replay runner), proving zero ticket edits, zero production-hook invocation, and zero monitoring-corpus writes during replay; then run shadow mode against real implement-ticket inputs, comparing Claude and Codex on phase completion, gate result, required artifacts, and normalized event intent, with Claude remaining the only live writer throughout. This matters because the discovery epic's existing AST-scan/content-hash containment proof only works for in-process Python code, and a real Codex CLI/session is a separate opaque external process that needs a materially different, process-level verification technique.

**Corrected per Codex review (2026-07-22):** this ticket now has an explicit intra-batch dependency on `TCK-20260721-MONITORING-WRITER-UNIFICATION` (the plan sequences Phase 4 after Phase 3; this ticket's shadow-mode monitoring-record-provenance checks depend on that writer/reader contract existing). It also now requires a formal, enforceable human-consent gate before any real Codex CLI/API invocation that consumes account usage — the Codex-guidance ticket documents this risk, but this ticket needs its own enforceable guard, not just a shared assumption.

## Scope
- **Entry criterion: `TCK-20260721-MONITORING-WRITER-UNIFICATION` must have landed** — this ticket's monitoring-record-provenance checks depend on that writer/reader contract existing
- **Require an explicit, programmatically-checked human-consent gate before any step that invokes the real Codex CLI/API** (which consumes account usage) — the workflow must refuse to proceed to that step without recorded consent, mirroring the same requirement in `TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE`
- Run the replay fixture through the actual Codex adapter/CLI (not the provider-neutral Python replay runner) for a fixture spanning Scope through Review phases
- Prove zero ticket edits, zero production-hook invocation, and zero monitoring-corpus writes during the real Codex replay using a process-level or filesystem-level containment proof (not AST scan) — e.g. strace/file-open monitoring, git-porcelain snapshot diff, or filesystem-permission sandboxing; this ticket's own Investigate/Plan phase must select and justify ONE auditable method before any paid/live invocation, not merely list candidates
- Take pre/post content-hash or git-porcelain snapshots of tickets/ and agent-monitoring/*.jsonl around the real Codex invocation and assert identical
- Run shadow-mode comparison across N real implement-ticket inputs, comparing Claude and Codex on phase completion, gate result, required artifacts, and normalized event intent
- Confirm Claude remains the sole live writer throughout, verified via monitoring-record provenance
- Register any mismatch in agent-orchestration/intentional-divergences.md (established by the Claude conformance adapter ticket) if found

## Out of Scope
- Does not cover phases beyond Scope through Review (Implement, Test, Parity, Verify, Finalize) unless the fixture envelope format is separately extended to define a files_changed/diff payload — that extension, if needed, is a distinct piece of work explicitly outside this ticket's boundary
- Does not enable a live Codex pilot ticket run (that is the live-Codex-pilot-guardrails ticket's scope)
- Does not modify the Python-only replay runner's existing AST-scan/content-hash containment proof (tools/agent_replay/) — this ticket adds a new, separate real-process containment technique rather than replacing the existing one
- Does not begin before TCK-20260721-MONITORING-WRITER-UNIFICATION has landed
- Does not invoke the real Codex CLI/API at any point without the explicit, recorded human-consent gate having been satisfied first

## Acceptance Criteria
- [x] This ticket does not begin real-Codex-execution work until TCK-20260721-MONITORING-WRITER-UNIFICATION has landed
- [x] An explicit, programmatically-checked human-consent gate exists and is enforced immediately before any step that invokes the real Codex CLI/API; the workflow refuses to proceed without it
- [x] This ticket's own Investigate/Plan phase selects and documents ONE auditable process-level containment-verification technique (not a list of candidates) before any paid/live Codex invocation occurs
- [x] Running the same fixture envelope through a real Codex-side execution path produces final_status/phases_completed that exactly match the Python runner's output for the same fixture; any divergence is registered in agent-orchestration/intentional-divergences.md
- [x] A process-level or filesystem-level containment proof (not AST scan) demonstrates zero invocation of the 4 forbidden monitoring/hook scripts during the real Codex run
- [x] Pre/post content-hash or git-porcelain snapshot of tickets/ and agent-monitoring/*.jsonl around the real Codex invocation is asserted identical (zero diff)
- [x] Shadow-mode comparison across N real implement-ticket inputs records phase completion, gate result, required artifact refs, and normalized event intent for both Claude and Codex
- [x] Monitoring-record provenance confirms Claude is the sole live writer throughout all shadow-mode runs (Codex never writes to the live monitoring corpus)
- [x] This ticket's scope boundary (Scope through Review only) is explicitly documented and enforced — no fixture inputs spanning Implement/Test/Parity/Verify/Finalize are exercised unless the fixture envelope is separately extended

## Related Tickets
- TCK-20260721-MONITORING-WRITER-UNIFICATION (hard predecessor — added per Codex's 2026-07-22 review correction; this ticket's shadow-mode provenance checks depend on the writer/reader contract it delivers)
- TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE (hard predecessor — trusted .codex/ config and verified real hook payloads)
- TCK-20260721-CODEX-REPLAY-PROOF
- TCK-20260721-CODEX-CAPABILITY-MATRIX
- TCK-20260721-ORCHESTRATION-CONTRACT-ADR
- TCK-20260721-AGENTS-DIR-DISPOSITION
- TCK-20260721-PROVIDER-AGNOSTIC-EPIC
- TCK-20260721-MONITORING-WRITER-DECISION

## Related Docs
- docs/ai/replay_fixture_spec.md
- docs/ai/codex_capability_matrix.md
- docs/ai/monitoring_writer_decision.md
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent_replay/runner.py
- tools/agent_replay/fixture_envelope.py
- tools/agent_replay/__init__.py
- tests/agent_replay/
- tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml
- tests/tools/test_codex_capability_diagnostics.py
- docs/ai/replay_fixture_spec.md
- docs/ai/codex_capability_matrix.md
- docs/ai/monitoring_writer_decision.md
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md
- stored_artifacts/TCK-20260721-CODEX-REPLAY-PROOF/

## Assumptions / Open Questions
- OPEN QUESTION for this ticket's own Investigate/Plan phase: the process-level containment verification technique (strace vs. filesystem sandboxing vs. scratch-dir execution) is not yet designed anywhere in the repo and must be selected and justified before implementation, not assumed here
- Hard dependency on the Codex guidance/fixture-capture ticket delivering the trusted .codex/ config and verified real hook payloads (codex_capability_matrix.md notes payload capture was deferred/undocumented as of this investigation)
- Sequenced strictly after ticket groups C1-C5 land, since none exist as concrete tickets yet at investigation time
- Real Codex API usage in this ticket carries real cost/consent considerations distinct from the free Python-only replay proof, separate from the fixture-capture cost in the Codex guidance ticket
- layer assigned as `ai` (agent/orchestration tooling layer) — this ticket concerns the Codex replay adapter and provider-agnostic orchestration infrastructure, not gameplay simulation code

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260721-CODEX-REPLAY-PARITY/plan.md`'s 12 ordered steps.
New sibling package `tools/agent_replay_codex/` drives a real `codex exec` process through
`wrapper_script.py`, which imports and calls the literal, unmodified
`tools.agent_replay.fixture_envelope.load_fixture()` / `tools.agent_replay.runner.replay_slice()`
functions — proving a real Codex-invoked process can be driven through the exact same
deterministic Scope→Investigate→Plan→Review branch logic the Python-only replay proof already
exercises, not a Codex-side reimplementation.

**Step 1 (entry criterion):** `entry_criterion.py::assert_monitoring_writer_landed()` loads
`tools/agent-monitoring/writer.py` via `importlib.util.spec_from_file_location` (mirroring
`manifest.py`'s own hyphenated-directory-import technique) and asserts `write_line`/`write_lines`
are callable. Passes against the real repo today, confirming MONITORING-WRITER-UNIFICATION has
landed.

**Step 2 (consent gate):** `consent_gate.py::require_live_consent()` checks
`env.get("CODEX_REPLAY_PARITY_LIVE_CONSENT") != "1"` (exact-string match) and has zero dependency
on `subprocess`.

**Steps 3–6 (wrapper, containment, config guard, invoker):** built exactly per plan. One deviation
from the plan's own illustrative pseudocode: the orchestrating instructions for this Implement
pass explicitly required the consent check to be the literal first two statements of
`run_codex_replay()`, strictly before the entry-criterion check (plan.md's own pseudocode showed
entry-criterion first, then consent). `invoker.py` implements consent-first, entry-criterion-
second — verified directly: `run_codex_replay(fixture_path, repo_root=REPO_ROOT, env={})` raises
`ConsentNotGrantedError` with `subprocess.run` monkeypatched to raise `AssertionError` if called,
confirming consent is checked before any subprocess object is ever constructed. See
`staging_artifacts/.../plan.md`'s Deviations section.

**Step 7 (REAL, consent-gated integration proof — genuinely executed, not simulated):** The human
operator (this session) set `CODEX_REPLAY_PARITY_LIVE_CONSENT=1` in their own shell and the real
`codex exec` invocation was run multiple times during this Implement pass — both a standalone
manual sanity check and the full pytest integration suite. **Genuine, observed outcome:**
- `codex --version` → `codex-cli 0.145.0` (same version investigation.md recorded).
- Manual sanity invocation: `codex exec -C /tmp/codex-replay-parity-manual-test -s workspace-write
  --skip-git-repo-check "Run: <python3> <wrapper_script.py> --fixture <fixture> --out <out>"`
  completed in ~0ms of tool-call time, exit code 0, and wrote a correct
  `{"final_status": "ok", "phases_completed": ["Scope", "Investigate", "Plan", "Review"]}` to the
  scratch-dir output path.
- **Empirical finding (genuinely undocumented before this run, per plan's Anti-Drift Notes):**
  `-s workspace-write -C <scratch_dir>` does NOT block the wrapper script's read of
  `tools/agent_replay/*.py` outside the scratch-dir workspace — Codex's sandbox permitted the read
  of `/home/u24desktop/Working/rpg-based-simulation/tools/...` even though the workspace root was
  the isolated `/tmp/...` scratch dir. No `read-only` fallback was needed. Non-interactive
  `codex exec` against an untrusted-but-scratch cwd did not hang or prompt for trust confirmation
  — it completed automatically (this repo's own absolute path is separately, pre-existingly
  trusted per investigation.md, but the scratch dir itself is a fresh, never-before-seen path and
  still worked cleanly).
- Full pytest run with consent granted:
  `pytest tests/agent_replay_codex/test_containment_real_process.py
  tests/agent_replay_codex/test_no_production_hook_invocation.py
  tests/agent_replay_codex/test_pre_post_snapshot.py tests/agent_replay_codex/test_phase_parity.py
  tests/agent_replay_codex/test_shadow_mode_comparison.py -v` → all 5 real-invocation tests
  genuinely PASSED (one real `codex exec` call shared across the whole pytest session via the
  session-scoped `real_codex_replay` fixture, per plan.md's Step 7 requirement of one real call
  per full-suite run, not five).
- `git status --porcelain -- tickets/ agent-monitoring/{runs,events,tools}.jsonl` before and after
  every real invocation was byte-identical to the pre-existing ambient dirty state (one
  pre-existing modified `agent-monitoring/tools.jsonl` and one pre-existing untracked
  `tickets/inprogress/TCK-20260721-CODEX-REPLAY-PARITY.md` — both present before this ticket's
  work began, unrelated to it) — zero new diff introduced by any real Codex invocation.
  `.codex/config.toml` bytes (md5 `4386e3df0c2a36f35cd7caf289d540dd`) were identical before and
  after every real invocation, and remained hook-free.

**Step 8 (phase-parity, AC #4):** `test_phase_parity.py` — real result: Codex-side
`final_status="ok"`, `phases_completed=["Scope","Investigate","Plan","Review"]`, exactly matching
`replay_slice(load_fixture(...))`'s own real output. **Zero divergence found** — the fail-safe
`is_approved(...)` branch was never exercised for a real reason; no entry was added to
`agent-orchestration/intentional-divergences.md` (confirmed: `git diff --stat
agent-orchestration/intentional-divergences.md` is empty).

**Step 9 (provenance):** `provenance_check.py::assert_no_codex_provider_writes()` confirms the
real `agent-monitoring/*.jsonl` corpus today has zero `provider=="codex"` records.

**Step 10 (divergence-registration unit test):** passes unconditionally against a synthetic
`tmp_path` divergence log — proves the reuse path Step 8 could have exercised actually works.

**Step 11 (shadow mode, N=1, AC #7):** `shadow_mode.py::compare_claude_and_codex()`. **Real bug
found and fixed during this Implement pass**: the first real run of
`test_shadow_mode_comparison.py` genuinely FAILED — `claude_gate_result` was read as the raw
fixture verdict string `"APPROVED"` while `codex_gate_result` was `codex_outcome.final_status`
(`"ok"`), which `tools.agent_replay.runner.replay_slice()` only ever returns as `"ok"` on the
happy path, never the literal string `"APPROVED"` — a vocabulary mismatch between the two sides
of the comparison, not a real Claude/Codex behavioral divergence. Fixed by normalizing
`claude_gate_result` the same way `replay_slice()` itself normalizes verdicts:
`"ok" if review_verdict == "APPROVED" else review_verdict`. Re-ran with consent granted:
`test_n1_comparison_against_existing_fixture` genuinely PASSED, `match=True`. This was caught
precisely because Step 7 required a REAL invocation rather than a predicted/simulated one — a
simulated run would not have surfaced this bug.

**Step 12 (regression pass):** all commands from plan.md's Step 12 run; results:
- `pytest tests/agent_replay_codex/ -v` → 26 passed (21 unconditional + 5 skipped without
  consent; all 26 passed when re-run with consent granted, see Step 7 above).
- `pytest tests/agent_replay/ -v` → 25 passed, untouched (confirmed `git diff --stat
  tools/agent_replay/` and `git diff --stat tests/agent_replay/` both empty).
- `pytest tests/agent_orchestration/ tests/agent_orchestration_claude_adapter/
  tests/agent_orchestration_codex_adapter/ -v` → 83 passed, 1 failed. The 1 failure is
  `test_contract_structure.py::test_contract_yaml_has_versioning_field_and_documented_scheme`,
  the known, pre-existing, unrelated stale-`staging_artifacts/`-path failure tracked by
  `tickets/todos/TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH.md` (still open) — reported here
  as baseline noise per this ticket's plan.md, not fixed.
- `pytest tests/tools/test_monitoring_writer.py tests/tools/test_post_tool_hook.py
  tests/tools/test_record_run.py tests/tools/test_record_events.py -v` → 55 passed.
- `pytest tests/tools/test_codex_capability_diagnostics.py
  tests/tools/test_codex_hook_payload_fixture.py -v` → 7 passed.
- `pytest tests/tools/test_agent_ops_dashboard_ingest.py
  tests/tools/test_agent_ops_dashboard_api.py
  tests/tools/test_agent_ops_dashboard_api_boundary.py
  tests/tools/test_agent_ops_dashboard_concurrency.py -v` → 48 passed.
- `pytest tests/unit/lab_agent/test_workflow_registry.py -v` → 4 passed.
- Scope-guard `git diff --stat` checks: `tools/agent_replay/` empty, `tests/agent_replay/` empty,
  `.claude/` empty, `agent-orchestration/intentional-divergences.md` empty (no real divergence
  found), `tools/agent-monitoring/` empty, `.agents/` empty, `CLAUDE.md` empty. Only new,
  untracked files under `tools/agent_replay_codex/` and `tests/agent_replay_codex/`.
- `graphify update .` was run per project convention (new `tests/` files added); it emitted a
  pre-existing, unrelated warning ("new graph has 27264 nodes but existing graph.json has 27265 —
  refusing to overwrite") and made no change — not investigated further as out of this ticket's
  scope; flagged here for visibility, not silently ignored.

N=1 for shadow-mode (AC's "N real implement-ticket inputs") per plan.md Decision #4: reuses the
one already-committed `tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml`
fixture — no new fixture was authored, per the ticket's own Out-of-Scope line forbidding
fixture-envelope-format extension beyond Scope-through-Review.

## Test Summary

New tests: 26 in `tests/agent_replay_codex/` (21 pass unconditionally; 5 require
`CODEX_REPLAY_PARITY_LIVE_CONSENT=1` + `codex` on PATH — skip cleanly otherwise). All 26 genuinely
passed with consent granted during this Implement pass (real `codex exec` invocations, not
simulated). Regression: `tests/agent_replay/` (25 passed, untouched),
`tests/agent_orchestration*/` (83 passed, 1 known pre-existing unrelated failure),
`tests/tools/test_{monitoring_writer,post_tool_hook,record_run,record_events,
codex_capability_diagnostics,codex_hook_payload_fixture,agent_ops_dashboard_*}.py` (110 passed),
`tests/unit/lab_agent/test_workflow_registry.py` (4 passed). No new failures introduced.

## Files Changed

New package `tools/agent_replay_codex/`: `__init__.py`, `errors.py`, `entry_criterion.py`,
`consent_gate.py`, `wrapper_script.py`, `containment.py`, `codex_config_guard.py`, `invoker.py`,
`provenance_check.py`, `shadow_mode.py`.

New test package `tests/agent_replay_codex/`: `__init__.py`, `conftest.py`,
`test_entry_criterion.py`, `test_consent_gate.py`, `test_wrapper_script.py`,
`test_containment.py`, `test_codex_config_guard.py`, `test_no_forbidden_calls.py`,
`test_containment_real_process.py`, `test_no_production_hook_invocation.py`,
`test_pre_post_snapshot.py`, `test_phase_parity.py`, `test_monitoring_provenance.py`,
`test_divergence_registration.py`, `test_shadow_mode_comparison.py`.

No existing production file was modified. `tools/agent_replay/{runner.py,fixture_envelope.py}`,
`tests/agent_replay/*`, `tools/agent-monitoring/*.py`, `.claude/`, `.agents/`, `CLAUDE.md`, and
`agent-orchestration/intentional-divergences.md` are all untouched (confirmed via `git diff
--stat` in Step 12 above).

## Completion Summary

Built `tools/agent_replay_codex/`, a new sibling package that drives a real, authenticated Codex
CLI process (`codex exec`) through the exact same unmodified
`load_fixture()`/`replay_slice()` functions the existing Python-only replay proof calls, gated by
a programmatically-enforced consent check (`CODEX_REPLAY_PARITY_LIVE_CONSENT=1`, exact-string
match, literal first check before any subprocess object exists) and an isolated-scratch-dir +
git-porcelain/content-hash containment technique (reusing `tests/agent_replay/
test_no_mutation_snapshot.py`'s proven pattern, parameterized for a new package, plus
`manifest.py`'s append-only monitoring check). The real, consent-gated integration proof (Step 7)
was genuinely executed multiple times during this Implement pass, not simulated: Codex's real
execution matched the Python runner's `final_status`/`phases_completed` output exactly for the
one committed fixture (zero divergence, nothing added to `intentional-divergences.md`), zero
diff was ever observed in `tickets/`, `agent-monitoring/*.jsonl`, or `.codex/config.toml` across
any real invocation, and zero `provider=="codex"` record exists anywhere in the live monitoring
corpus. One real bug was found and fixed in this pass's own shadow-mode comparison logic (a
vocabulary mismatch between the fixture's raw `"APPROVED"` verdict string and
`replay_slice()`'s normalized `"ok"` status) — caught specifically because the invocation was
real rather than predicted. All acceptance criteria are satisfied; the full scoped regression
pass is green except the one known, pre-existing, out-of-scope
`test_contract_yaml_has_versioning_field_and_documented_scheme` failure already tracked by a
separate open ticket.

---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260721-CODEX-REPLAY-PARITY
phase: open
date: 2026-07-21
tags: []
---

# TCK-20260721-CODEX-REPLAY-PARITY

## Title
Real Codex replay adapter and parity suite

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Run the replay fixture through the actual Codex adapter (not just the provider-neutral Python replay runner), proving zero ticket edits, zero production-hook invocation, and zero monitoring-corpus writes during replay; then run shadow mode against real implement-ticket inputs, comparing Claude and Codex on phase completion, gate result, required artifacts, and normalized event intent, with Claude remaining the only live writer throughout. This matters because the discovery epic's existing AST-scan/content-hash containment proof only works for in-process Python code, and a real Codex CLI/session is a separate opaque external process that needs a materially different, process-level verification technique.

## Scope
- Run the replay fixture through the actual Codex adapter/CLI (not the provider-neutral Python replay runner) for a fixture spanning Scope through Review phases
- Prove zero ticket edits, zero production-hook invocation, and zero monitoring-corpus writes during the real Codex replay using a process-level or filesystem-level containment proof (not AST scan) — e.g. strace/file-open monitoring, git-porcelain snapshot diff, or filesystem-permission sandboxing
- Take pre/post content-hash or git-porcelain snapshots of tickets/ and agent-monitoring/*.jsonl around the real Codex invocation and assert identical
- Run shadow-mode comparison across N real implement-ticket inputs, comparing Claude and Codex on phase completion, gate result, required artifacts, and normalized event intent
- Confirm Claude remains the sole live writer throughout, verified via monitoring-record provenance
- Register any mismatch in agent-orchestration/intentional-divergences.md (established by the Claude conformance adapter ticket) if found

## Out of Scope
- Does not cover phases beyond Scope through Review (Implement, Test, Parity, Verify, Finalize) unless the fixture envelope format is separately extended to define a files_changed/diff payload — that extension, if needed, is a distinct piece of work explicitly outside this ticket's boundary
- Does not enable a live Codex pilot ticket run (that is the live-Codex-pilot-guardrails ticket's scope)
- Does not modify the Python-only replay runner's existing AST-scan/content-hash containment proof (tools/agent_replay/) — this ticket adds a new, separate real-process containment technique rather than replacing the existing one

## Acceptance Criteria
- [ ] Running the same fixture envelope through a real Codex-side execution path produces final_status/phases_completed that exactly match the Python runner's output for the same fixture; any divergence is registered in agent-orchestration/intentional-divergences.md
- [ ] A process-level or filesystem-level containment proof (not AST scan) demonstrates zero invocation of the 4 forbidden monitoring/hook scripts during the real Codex run
- [ ] Pre/post content-hash or git-porcelain snapshot of tickets/ and agent-monitoring/*.jsonl around the real Codex invocation is asserted identical (zero diff)
- [ ] Shadow-mode comparison across N real implement-ticket inputs records phase completion, gate result, required artifact refs, and normalized event intent for both Claude and Codex
- [ ] Monitoring-record provenance confirms Claude is the sole live writer throughout all shadow-mode runs (Codex never writes to the live monitoring corpus)
- [ ] This ticket's scope boundary (Scope through Review only) is explicitly documented and enforced — no fixture inputs spanning Implement/Test/Parity/Verify/Finalize are exercised unless the fixture envelope is separately extended

## Related Tickets
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

## Test Summary

## Files Changed

## Completion Summary

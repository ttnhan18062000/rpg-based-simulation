---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260721-PROVIDER-AGNOSTIC-EPIC
phase: done
date: 2026-07-21
tags: [ai, workflows, process-improvement]
---

# TCK-20260721-PROVIDER-AGNOSTIC-EPIC

## Title
Provider-agnostic agent orchestration discovery epic

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
One parent epic ticket to scope and track the discovery work needed before Claude Code and Codex can share one agent-orchestration system. The epic itself must be scope-only (no direct implementation) and must not authorize any production runtime, hook, or monitoring-writer change. It stays blocked from spawning a follow-on implementation epic until all five discovery outputs (from the five child tickets) are complete, evidence-backed, and explicitly approved.

## Scope
- Scope-only epic: create and track the five child discovery tickets (.agents/ disposition audit, Codex capability matrix, monitoring writer decision, orchestration contract ADR, replay-only proof).
- Mirror the scope-only wording precedent set by TCK-20260708-AGENT-INFRA-HARDENING-EPIC: "Track and sequence the child tickets. No direct implementation."
- Record the five-output exit gate (from the source plan's "Approval model and exit gate" section) as this epic's completion condition.
- Reference finding_01_claude.md's confirmation that .agents/workflows and .agents/skills are live-parsed by src/lab/registry.py's WorkflowRegistry (test_real_registry_contracts currently passing) so child TCK-20260721-AGENTS-DIR-DISPOSITION does not silently drop this.

## Out of Scope
- No direct implementation work of any kind — this ticket only scopes and tracks child tickets.
- No production Claude/Codex runtime, hook, or monitoring-writer change is authorized by this epic.
- No follow-on implementation epic may be scoped until all five discovery outputs are complete, evidence-backed, and explicitly approved.
- Creating any provider-runtime implementation ticket — blocked until all 5 discovery outputs are complete, evidence-backed, and explicitly approved (see this same epic).

## Acceptance Criteria
- [x] .agents/ disposition report and active-location map is delivered (per child ticket TCK-20260721-AGENTS-DIR-DISPOSITION) classifying every path in .agents/ and naming one approved future active Codex instruction/skill location.
- [x] Provider-neutral orchestration contract-format ADR is delivered (per child ticket TCK-20260721-ORCHESTRATION-CONTRACT-ADR) deciding contract representation, source ownership, versioning, provider-adapter boundary, execution identity, and conformance mechanism.
- [x] Execution-identity/monitoring-writer ADR is delivered with portability and concurrency evidence (per child ticket TCK-20260721-MONITORING-WRITER-DECISION), including a stress-tested cross-platform concurrent-write strategy.
- [x] Codex capability matrix is delivered (per child ticket TCK-20260721-CODEX-CAPABILITY-MATRIX) verifying current Codex capabilities, trust behavior, lifecycle hook events, role/delegation model, skills/config surfaces, and payload/fixture gaps against official docs and fixture experiments.
- [x] Replay-fixture spec and proof is delivered (per child ticket TCK-20260721-CODEX-REPLAY-PROOF) demonstrating a Codex slice executes against recorded fixtures with proof of zero ticket edits, zero production hook invocations, and zero monitoring-corpus writes.
- [x] No follow-on implementation epic or provider-runtime implementation ticket is opened/scoped until all five discovery outputs above are complete, evidence-backed, and explicitly approved.
- [x] Parent epic ## Scope states only that it tracks/sequences the five child discovery tickets, with no direct implementation work claimed for the parent itself.
- [x] Parent epic ## Out of Scope explicitly excludes any production Claude/Codex runtime, hook, or monitoring-writer change, and excludes creating provider-runtime implementation tickets now.

## Related Tickets
- TCK-20260721-AGENTS-DIR-DISPOSITION
- TCK-20260721-CODEX-CAPABILITY-MATRIX
- TCK-20260721-MONITORING-WRITER-DECISION
- TCK-20260721-ORCHESTRATION-CONTRACT-ADR
- TCK-20260721-CODEX-REPLAY-PROOF
- TCK-20260708-AGENT-INFRA-HARDENING-EPIC
- TCK-20260711-EPIC-SCOPE-ORPHAN-FIX

## Related Docs
- docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md
- docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_ticket_handoff_codex.md
- docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_finding_01_claude.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/lab/registry.py
- tests/unit/lab_agent/test_workflow_registry.py

## Assumptions / Open Questions
- finding_01_claude.md (not yet folded into the main plan/handoff) shows .agents/ is not pure dead scaffolding — src/lab/registry.py's WorkflowRegistry parses .agents/workflows/*.md and .agents/skills/*/SKILL.md, and test_real_registry_contracts currently passes against that real content; child TCK-20260721-AGENTS-DIR-DISPOSITION must not silently drop this.
- The handoff's "all five Discovery-Epic Acceptance Criteria" phrase refers to the 5 numbered exit-gate outputs in the source plan's "Approval model and exit gate" section, not the 4-bullet "## Discovery-Epic Acceptance Criteria" section — this epic's AC is built from the 5 numbered outputs.
- No existing ticket or REGISTRY.yaml/working_log.csv entry covers this scope — confirmed non-duplicate.
- Epic-tier tickets run scope-only, return EPIC_SCOPED status; no staging_artifacts/plan.md/investigation.md/test_plan.md required for the parent itself.

## Implementation Notes
All 5 child discovery tickets implemented via `implement-epic` (folder mode, then epic_id mode after this ticket's own Scope-only `EPIC_SCOPED` exit) in SEQUENCE.md order: `TCK-20260721-AGENTS-DIR-DISPOSITION`, `TCK-20260721-CODEX-CAPABILITY-MATRIX`, `TCK-20260721-MONITORING-WRITER-DECISION`, `TCK-20260721-ORCHESTRATION-CONTRACT-ADR`, `TCK-20260721-CODEX-REPLAY-PROOF` (all `DONE`, `tickets/done/provider-agnostic-discovery/`).

Post-implementation, a 5-round Claude↔Codex review chain (`docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_*.md`) found and closed 2 real defects in the delivered outputs before Codex's final approval:
1. `docs/ai/agents_dir_disposition.md` falsely claimed `.claude/` was a shared Codex/Claude location — corrected via `TCK-20260721-AGENTS-DISPOSITION-FIX` to the accurate two-surface framing (Claude → `.claude/`; Codex → root `AGENTS.md` + `.agents/skills/`, neither built yet).
2. That same doc's follow-up wording wrongly implied zero live discoverability risk from the legacy `.agents/skills/` tree — corrected via `TCK-20260721-AGENTS-DISPOSITION-DISCOVERABILITY-FIX` to state the tree (18 `SKILL.md` files) is currently Codex-discoverable today, unapproved/stale, and named a hard containment precondition for any future Codex-delivery ticket.

Codex's final response (`idea_provider_agnostic_agent_orchestration_discovery_gate_closure_final_corrections_response_codex.md`) approved closure explicitly: *"Approved — the discovery epic may close... The provider-agnostic implementation epic may now be scoped from `provider_agnostic_orchestration/implementation_plan.md`."*

## Test Summary
(epic — see children; each child ticket's own Test Summary covers its scoped test suite. Aggregate: `TCK-20260721-AGENTS-DIR-DISPOSITION` 95/95, `TCK-20260721-CODEX-CAPABILITY-MATRIX` 111/111, `TCK-20260721-MONITORING-WRITER-DECISION` 998/998 (6 pre-existing unrelated failures independently confirmed unrelated), `TCK-20260721-ORCHESTRATION-CONTRACT-ADR` 144/144, `TCK-20260721-CODEX-REPLAY-PROOF` 67/67, `TCK-20260721-AGENTS-DISPOSITION-FIX` 133/133, `TCK-20260721-AGENTS-DISPOSITION-DISCOVERABILITY-FIX` 133/133 — all passing at each ticket's own close.)

## Files Changed
(epic — see children for source/test changes; no `src/` file was touched by any child, per the batch's unconditional containment rule)
- `docs/ai/agents_dir_disposition.md` (`TCK-20260721-AGENTS-DIR-DISPOSITION`, corrected twice post-review)
- `docs/ai/codex_capability_matrix.md` (`TCK-20260721-CODEX-CAPABILITY-MATRIX`)
- `docs/ai/monitoring_writer_decision.md` + `tests/tools/test_monitoring_writer_lockfile_candidate.py` (`TCK-20260721-MONITORING-WRITER-DECISION`)
- `docs/architecture/agent_orchestration_contract.md` (`TCK-20260721-ORCHESTRATION-CONTRACT-ADR`)
- `docs/ai/replay_fixture_spec.md` + `tools/agent_replay/` + `tests/agent_replay/` (`TCK-20260721-CODEX-REPLAY-PROOF`)
- `docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_*.md` (5-round review chain, this epic-closure pass)
- This ticket itself, closed directly (epic tier has no automated Finalize phase — followed the `TCK-20260708-AGENT-INFRA-HARDENING-EPIC` closure precedent)

## Completion Summary
All 5 discovery outputs delivered, evidence-backed, and explicitly approved by Codex after a 5-round review chain that surfaced and closed 2 real cross-document defects (both in `TCK-20260721-AGENTS-DIR-DISPOSITION`'s deliverable). All 8 epic ACs satisfied: the five per-output ACs are each backed by a `DONE` child ticket; no follow-on implementation epic or provider-runtime ticket was opened during discovery; the epic's own Scope/Out-of-Scope sections correctly stayed track-only with no direct implementation claimed.

Per the source plan's exit gate, this closure unblocks scoping a follow-on implementation epic from `docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md` (authored by Codex, reviewed by Claude, no blocking issues found). That implementation epic carries forward, as named preconditions rather than assumptions: Linux-only evidence for the monitoring writer (Windows/macOS explicitly `NOT APPROVED / BLOCKED`), an unspecified conformance mechanism needing its own design pass, unverified Codex hook payload shape (existence verified, payload not captured), and — per Codex's final response — a hard containment requirement that the first Codex-delivery ticket quarantine or atomically replace the legacy `.agents/skills/` tree (preserving an archived, reviewable copy, no historical monitoring data rewritten) before enabling root `AGENTS.md` or project Codex configuration.

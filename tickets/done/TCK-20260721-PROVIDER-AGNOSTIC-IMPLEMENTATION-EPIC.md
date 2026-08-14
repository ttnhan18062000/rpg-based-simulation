---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC
phase: done
date: 2026-07-21
tags: [ai, workflows, process-improvement]
---

# TCK-20260721-PROVIDER-AGNOSTIC-IMPLEMENTATION-EPIC

## Title
Provider-agnostic agent orchestration implementation epic

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
Direct successor to the closed discovery epic (`TCK-20260721-PROVIDER-AGNOSTIC-EPIC`). Scope-only epic tracking the follow-on implementation of provider-agnostic agent orchestration (Claude Code + Codex sharing one semantic working process), per the implementation blueprint at `docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md` (authored by Codex, reviewed by Claude with no blocking issues per `idea_provider_agnostic_agent_orchestration_discovery_gate_closure_corrections_claude.md`'s "Separately reviewed" section). This epic records the plan's own preconditions, non-negotiable data-safety rules, and proposed ticket groups as its own entry gate and scope description; it creates no child tickets itself and authorizes no direct implementation.

## Scope
- Scope-only epic: track and sequence child implementation tickets to be created by a follow-on `/create-tickets` run against `docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md`. No direct implementation work by this ticket itself (mirrors `TCK-20260708-AGENT-INFRA-HARDENING-EPIC`'s and `TCK-20260721-PROVIDER-AGNOSTIC-EPIC`'s "Track and sequence the child tickets. No direct implementation." wording).
- Record the implementation plan's 4 stated Preconditions ("Preconditions — Must Be Recorded Before Implementation Tickets") as this epic's own entry gate, verified satisfied:
  1. **Discovery gate is corrected and closed** — satisfied: `docs/ai/agents_dir_disposition.md` no longer claims `.claude/` is a Codex skill location (corrected by `TCK-20260721-AGENTS-DISPOSITION-FIX`, DONE) and no longer implies zero live-discoverability risk from the legacy `.agents/skills/` tree (corrected by `TCK-20260721-AGENTS-DISPOSITION-DISCOVERABILITY-FIX`, DONE); Codex's final review explicitly approved discovery-epic closure and named this implementation plan as unblocked for scoping.
  2. **Scope is Linux-only for shared monitoring writes** — satisfied/carried forward: `docs/ai/monitoring_writer_decision.md` records Linux as the only **APPROVED** platform (200 concurrent-write stress test across 10 threads x 20 iterations, 0 corrupted/lost/duplicated/interleaved lines), with Windows and macOS explicitly unsupported pending platform-specific evidence.
  3. **A human owner approves the implementation epic boundary** (starts with `implement-ticket` replay/shadow behavior only; does not authorize cutover of all development/simulation workflows) — satisfied by this ticket's creation at explicit user request, scoped exactly to that boundary.
  4. **Existing Claude behavior is a protected baseline** (no phase may replace/redirect the live `.claude/workflows/*.js` pipeline until conformance/shadow tests pass) — carried forward as a standing invariant binding every child ticket, not a one-time precondition to satisfy now.
- Record the implementation plan's "Proposed Ticket Groups" section (minimum 7 groups) as this epic's own scope description / Related Tickets placeholder — the actual child tickets are created by a separate `/create-tickets` pass against the same source doc, not by this epic ticket itself:
  1. Baseline manifest and legacy compatibility fixtures.
  2. Contract core + validator for `implement-ticket`.
  3. Claude contract conformance adapter/tests (no behavior change).
  4. Codex guidance/skills arrangement plus real hook-payload fixture capture.
  5. Linux common monitoring writer + additive reader/query/dashboard support.
  6. Real Codex replay adapter and parity suite.
  7. Shadow-mode comparison and isolated live-pilot guardrails.
- Record the implementation plan's "Non-Negotiable Data-Safety Rules" table as explicit constraints every child ticket must respect: existing JSONL is immutable historical input (never rewrite/backfill/reorder/delete/compact `agent-monitoring/*.jsonl`); new schema is strictly additive (`schema_generation`, `provider`, `execution_id`, `ticket_id`, `contract_version`, legacy fields stay readable); legacy gaps are explicit (readers return `unknown`/`legacy` provenance, never infer provider/execution identity from unreliable strings except documented best-effort views); writes are atomic and append-only via the approved Linux lock-file protocol; migration is reversible and feature-flagged (disabling Codex leaves the live Claude path and historical data unchanged); verification never mutates source data (snapshots/read-only inputs/temp copies only). A read-only baseline manifest (counts, byte sizes, SHA-256 hashes, parser/validator result, legacy-warning count per JSONL file) must be captured before any writer change and re-verified equal after every writer/reader migration.
- Record the newly-added containment precondition from Codex's final review (`idea_provider_agnostic_agent_orchestration_discovery_gate_closure_final_corrections_response_codex.md`, "Implementation constraint carried forward" section) as a hard entry/exit criterion for the first Codex-delivery child ticket: it must quarantine or atomically replace the legacy `.agents/skills/` tree, preserve an archived reviewable copy outside Codex's discovery path, use a recoverable replacement strategy, and rewrite zero historical monitoring data as part of that action.
- This epic does not close until the implementation plan's own per-phase exit criteria (Phase 0 through Phase 6, "Delivery Sequence" section) are met by its children, and the plan's "Test and Evidence Matrix" and "Rollback and Incident Policy" sections are honored by each child's implementation.

## Out of Scope
- No direct implementation of any child ticket's code, contract, adapter, or writer — this ticket only scopes and tracks.
- No authorization to cut over the live Claude workflow (`.claude/workflows/*.js`) — it remains the sole authoritative execution path until Phase 4+ parity/shadow evidence exists per child tickets.
- No provider-runtime code of any kind is created by this ticket (no `agent-orchestration/` contract files, no `.codex/` configuration, no `AGENTS.md`, no writer code).
- No cross-platform (Windows/macOS) monitoring writer work — explicitly out of scope per Precondition 2 until separate platform-specific evidence exists.
- No enabling of any live Codex hook registration or production hook invocation — deferred to Phase 5 (isolated live Codex pilot) per a child ticket with its own human-owned rollback plan.
- No migration or backfill of historic `agent-monitoring/*.jsonl` records — explicitly listed as a Non-Goal in the implementation plan.
- No expansion beyond `implement-ticket` (e.g. `create-tickets`, `implement-epic`, simulation/lab workflows) — deferred to Phase 6 per the plan, and only after `implement-ticket` pilots succeed.
- No creation of the actual child implementation tickets within this ticket — that is a separate `/create-tickets` run against the same source plan.
- No re-litigation of discovery-epic findings (`.agents/` disposition, Codex capability matrix, monitoring writer decision, orchestration contract ADR, replay fixture spec) — those are closed, evidence-backed, and approved; this epic only carries their conclusions forward as constraints.

## Acceptance Criteria
- [x] Epic `## Scope` states only that it tracks/sequences child implementation tickets (to be created via a follow-on `/create-tickets` run), with no direct implementation claimed for the parent itself.
- [x] Epic `## Out of Scope` explicitly excludes live-Claude-workflow cutover, provider-runtime code creation, non-Linux writer work, live Codex hook enablement, and historical-record migration/backfill.
- [x] All 4 implementation-plan preconditions are individually verified and cited with evidence in this ticket's Scope section before the epic is considered entry-gated.
- [x] All 7 proposed ticket groups have been created as real child tickets via `/create-tickets` against the implementation plan (`tickets/todos/provider-agnostic-implementation/`, `SEQUENCE.md` encodes their dependency order) and linked in this epic's Related Tickets.
- [x] The implementation plan's Non-Negotiable Data-Safety Rules and the Codex-final-review containment precondition (legacy `.agents/skills/` quarantine/atomic-replacement) are recorded as binding constraints on every child ticket — spot-checked across `BASELINE-MONITORING-MANIFEST`, `CODEX-GUIDANCE-FIXTURE-CAPTURE`, `MONITORING-WRITER-UNIFICATION`, and `LIVE-CODEX-PILOT-GUARDRAILS`'s own Scope/Out-of-Scope text at closure review (2026-07-27); confirmed genuinely present, not just asserted at the epic level.
- [x] **AMENDED 2026-07-27** (original wording below, struck for the record): this epic closes once Phase 0-4 exit criteria are fully satisfied by children's evidence, and Phase 5 readiness/rollback/sign-off tooling is built and mechanically proven to contain no live-execution path — not once a live pilot has actually run. The original wording ("Phase 0-6...satisfied by its children") literally required a *completed* live Codex pilot with human-approved scope-widening before this epic could close, which directly conflicts with this same ticket's own Precondition 3 ("starts with `implement-ticket` replay/shadow behavior only; does not authorize cutover of all development or simulation workflows") and the source plan's Non-Goals section ("Enabling all agent workflows, simulation workflows, or autonomous Codex dispatch in the first implementation epic" is explicitly out of scope). `TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS` built exactly what Precondition 3 authorized — readiness tooling, deliberately never a live run — so the original AC #6 could never have been satisfied without that ticket exceeding its own approved scope. Selecting a real pilot candidate, obtaining human sign-off, and running one is future work for a later epic. Phase 6 ("Controlled expansion and cutover review") was never in scope for this epic either way, confirmed by the plan's own Non-Goals and Delivery Sequence wording, and remains future-epic work.
  <s>This epic ticket is not moved to `tickets/done/` until the implementation plan's own per-phase exit criteria (Phase 0-6) are satisfied by its children's evidence, mirroring how the discovery epic required all 5 child outputs before closing.</s>
- [x] `docs/REGISTRY.yaml` and `tickets/working_log.csv` reflect this epic at scope-close, per the standard epic-tier "returns immediately after Scope" closure precedent (`TCK-20260708-AGENT-INFRA-HARDENING-EPIC`, `TCK-20260721-PROVIDER-AGNOSTIC-EPIC`).

## Related Tickets
- TCK-20260721-PROVIDER-AGNOSTIC-EPIC (predecessor, DONE — discovery epic; this epic is its named successor)
- TCK-20260721-AGENTS-DIR-DISPOSITION (DONE — discovery child, precondition 1 evidence)
- TCK-20260721-AGENTS-DISPOSITION-FIX (DONE — precondition 1 evidence)
- TCK-20260721-AGENTS-DISPOSITION-DISCOVERABILITY-FIX (DONE — precondition 1 evidence, names the containment precondition)
- TCK-20260721-CODEX-CAPABILITY-MATRIX (DONE — discovery child, feeds Phase 2)
- TCK-20260721-MONITORING-WRITER-DECISION (DONE — precondition 2 evidence, feeds Phase 3)
- TCK-20260721-ORCHESTRATION-CONTRACT-ADR (DONE — discovery child, feeds Phase 0/1 contract skeleton)
- TCK-20260721-CODEX-REPLAY-PROOF (DONE — discovery child, feeds Phase 4)
- TCK-20260708-AGENT-INFRA-HARDENING-EPIC (precedent for scope-only epic wording)
- TCK-20260721-BASELINE-MONITORING-MANIFEST
- TCK-20260721-ORCHESTRATION-CONTRACT-CORE
- TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER
- TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE
- TCK-20260721-MONITORING-WRITER-UNIFICATION
- TCK-20260721-CODEX-REPLAY-PARITY
- TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS

## Related Docs
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md (primary source — implementation blueprint)
- docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_corrections_claude.md ("Separately reviewed" section — Claude's review of the plan, no blocking issues)
- docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_final_corrections_response_codex.md ("Implementation constraint carried forward" section — containment precondition)
- docs/ai/agents_dir_disposition.md
- docs/ai/codex_capability_matrix.md
- docs/ai/monitoring_writer_decision.md
- docs/architecture/agent_orchestration_contract.md
- docs/ai/replay_fixture_spec.md
- docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md
- docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_ticket_handoff_codex.md
- docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_finding_01_claude.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260721-AGENTS-DIR-DISPOSITION/
- stored_artifacts/TCK-20260721-CODEX-CAPABILITY-MATRIX/
- stored_artifacts/TCK-20260721-MONITORING-WRITER-DECISION/
- stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-ADR/
- stored_artifacts/TCK-20260721-CODEX-REPLAY-PROOF/
- None yet for this epic itself (epic tier, no staging artifacts required).

## Related Code Areas
- agent-orchestration/ (does not yet exist — to be created by child ticket group 2, not this epic)
- .claude/workflows/implement-ticket.js (protected baseline per precondition 4 — must not be modified until child conformance/shadow evidence exists)
- .claude/settings.json, .claude/agents/, .claude/skills/ (Claude adapter surfaces referenced by the plan)
- .agents/skills/ (legacy tree subject to the containment precondition)
- AGENTS.md (does not yet exist — Codex durable-guidance surface, child ticket group 4)
- agent-monitoring/*.jsonl (protected historical data — writer migration is child ticket group 5)
- src/lab/registry.py (WorkflowRegistry — live-parses `.agents/workflows/*.md` and `.agents/skills/*/SKILL.md`, per discovery finding_01_claude.md; any containment action must not break `tests/unit/lab_agent/test_workflow_registry.py`)

## Assumptions / Open Questions
- Assumes the discovery epic's closure (Codex's final approval quoting "The provider-agnostic implementation epic may now be scoped from `provider_agnostic_orchestration/implementation_plan.md`") constitutes sufficient authorization to open this epic; if that approval is later disputed, this epic's entry gate is invalidated.
- Precondition 3 ("a human owner approves the implementation epic boundary") is treated as satisfied by the user's explicit request to create this ticket now, scoped exactly to `implement-ticket` replay/shadow behavior per the plan's stated boundary — if the user intended a broader boundary, this assumption is wrong and the epic's Out of Scope must be revised before child tickets are created.
- `layer: ai` is used per this repo's established convention (matches the discovery epic, the implementation plan's own frontmatter, and all 5 discovery-child tickets) — this repo's `layer:ai` denotes the Claude/Codex agent-orchestration system, not gameplay cognition.
- Assumes the follow-on `/create-tickets` run against the implementation plan will produce at least the 7 ticket groups listed here, possibly split further per the plan's "no ticket may combine writer implementation, historical-data remediation, and provider live rollout" constraint — exact ticket count/IDs are not fixed by this epic.
- No parity ledger entry applies: existing `docs/parity_ledger/infrastructure.yaml` entries covering agent-orchestration/monitoring-pipeline tooling explicitly state "no simulation behavior is involved," consistent with this epic being agent-tooling-only, outside Mechanics Bible/parity scope.
- No conflicting or duplicate in-progress/backlogged ticket was found covering this exact scope (`tickets/inprogress/`, `tickets/done/`, `tickets/backlogs/` all scanned) as of 2026-07-21.

## Implementation Notes
Scope-only epic; no direct implementation by this ticket. All 7 child tickets were implemented and closed via the standard `implement-ticket` pipeline (Scope/Investigate/Plan/Review/Implement/Architecture-Verify/Test/Parity/Verify/Finalize), each independently architecture-reviewed and done-checker-verified. One real defect was caught and fixed pre-Implement on the final child (`LIVE-CODEX-PILOT-GUARDRAILS`): its no-live-execution-path guard initially missed dynamic `importlib`-based module loading and scoped its subprocess ban to calls containing the literal string `"codex"` — both fixed before Implement began, independently re-confirmed in the actual shipped code at Architecture-Verify.

At closure review (2026-07-27), a genuine internal inconsistency was found in this epic's own original AC #6 (see the Acceptance Criteria section's amendment note) and resolved by explicit human decision: amend the AC to match Precondition 3's already-stated boundary rather than leave the epic open pending a live pilot that was never authorized in this epic's own scope. Reviewed and approved in substance by Codex per `docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_batch_closure_response_codex.md`, with one procedural condition (commit the tickets 6/7 closure diff before closing) that was satisfied prior to this closure.

## Test Summary
No tests apply to this ticket directly (epic tier, scope-only). Each of the 7 children carries its own independently-run, independently-verified test suite — see their individual Completion Summaries and `stored_artifacts/{ticket_id}/test_plan.md` files for details. Aggregate: 0 test regressions attributable to this batch; the one pre-existing, unrelated failure (`tests/agent_orchestration/test_contract_structure.py::test_contract_yaml_has_versioning_field_and_documented_scheme`) is tracked separately (`tickets/todos/TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH.md`) and predates this batch.

## Files Changed
This epic itself changes only its own ticket file. Its 7 children's combined Files Changed span: `agent-orchestration/` (contract core), `tools/agent_orchestration*/`, `tools/agent_replay_codex/`, `tools/agent_codex_pilot_guardrails/`, `tools/agent-monitoring/manifest.py` and the unified writer extraction, `AGENTS.md` + `.agents/skills/` regeneration (legacy tree quarantined to `docs/archive/legacy_agents_skills_20260722/`), `docs/architecture/agent_orchestration_contract.md`-adjacent tooling, `pilot_requests/`, and their respective `tests/` directories. No `.claude/workflows/*.js` file was modified by any child ticket (protected baseline, Precondition 4, held throughout). `.codex/config.toml` remains comment-only/hook-free in the committed repo state.

## Completion Summary
Closes the provider-agnostic agent orchestration implementation epic. All 7 child ticket groups from the implementation plan (baseline manifest, contract core, Claude conformance adapter, Codex guidance/fixture capture, unified monitoring writer, real Codex replay parity, live-pilot guardrails) are DONE with independently-verified evidence. Phase 0-4 exit criteria (per `implementation_plan.md`'s Delivery Sequence) are fully satisfied. Phase 5 delivers readiness/rollback/sign-off tooling only, by design — no live Codex pilot has been run or authorized; that remains explicit future work for a later epic, consistent with this epic's own Precondition 3 and the source plan's Non-Goals. Phase 6 (controlled expansion beyond `implement-ticket`) was never in this epic's scope. The headline proof this epic delivers: a real, consent-gated, paid Codex CLI invocation was genuinely run against a real fixture and produced output that exactly matched the existing Claude-side replay proof — the first concrete evidence in this repo that Claude and Codex can execute the same deterministic workflow slice through independently-built adapters reading one shared semantic contract.

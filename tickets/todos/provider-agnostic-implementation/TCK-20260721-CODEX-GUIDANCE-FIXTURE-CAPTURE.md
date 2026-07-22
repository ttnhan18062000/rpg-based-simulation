---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE
phase: open
date: 2026-07-21
tags: []
---

# TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE

## Title
Codex guidance/skills arrangement and real hook-payload fixture capture

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Add the corrected root AGENTS.md and regenerate .agents/skills/ generated from the validated shared contract (not merely "reviewed canonical material" — never reactivating stale legacy .agents content), then add minimal trusted .codex/ configuration only after isolated scratch-directory fixture experiments confirm project trust, matcher behavior, and the real hook-payload schema/timing for each event the first slice needs — without enabling any production hook yet. This matters because the live repo currently has 18 legacy SKILL.md files still auto-discoverable with no containment decision, and no Codex pilot may be authorized until that is quarantined or atomically replaced with a preserved reviewable copy.

**Corrected per Codex review (2026-07-22):** this ticket now has an explicit intra-batch dependency on `TCK-20260721-ORCHESTRATION-CONTRACT-CORE` — the plan's approved architecture treats the shared contract as the sole canonical semantic source, so a manually curated Codex delivery catalog produced before that contract exists would create a second semantic authority. Legacy-skill containment stays inside this ticket (Codex confirmed no separate ticket is needed), but the atomic replacement must now produce the catalog from the validated contract, not merely from "reviewed material."

## Scope
- **Entry criterion: `TCK-20260721-ORCHESTRATION-CONTRACT-CORE` must have landed** — the validated `agent-orchestration/` contract is this ticket's source for AGENTS.md/skills content, not an independently curated set
- Quarantine or atomically replace the legacy .agents/skills/ tree (18 SKILL.md files) BEFORE any new AGENTS.md/skills go live, preserving a byte-identical reviewable copy and leaving agent-monitoring/*.jsonl unchanged
- Add a corrected root AGENTS.md generated from the validated contract, verifiably not a copy of the stale .agents/rules/AGENTS.md draft (which has confirmed 17-phase vs real 32-phase pipeline drift)
- Regenerate .agents/skills/ content generated from the validated contract's skills.yaml (not from independently human-curated material once the contract exists — human review applies to the contract's own skills.yaml, not to a second, parallel AGENTS.md/skills curation pass)
- Run isolated scratch-directory Codex CLI fixture experiments to confirm project trust behavior, matcher behavior, and capture the real hook-payload JSON schema/timing for each event needed by the first slice
- Add minimal trusted .codex/ configuration only after fixture experiments confirm behavior — with no production hook enabled

## Out of Scope
- Does not enable a working live Codex pilot (that is the live-Codex-pilot-guardrails ticket's scope)
- Does not build the contract's own code-generation tooling (owned by TCK-20260721-ORCHESTRATION-CONTRACT-CORE) — this ticket consumes the contract's generation command, it does not build it
- Does not enable any production hook as a result of this ticket's work
- Does not begin AGENTS.md/skills generation before TCK-20260721-ORCHESTRATION-CONTRACT-CORE has landed

## Acceptance Criteria
- [ ] This ticket's AGENTS.md/skills generation work does not begin until TCK-20260721-ORCHESTRATION-CONTRACT-CORE has landed and its validator/generator is available to consume
- [ ] Legacy .agents/skills/ tree (18 SKILL.md files) is quarantined/archived with a preserved byte-identical copy, OR atomically replaced, BEFORE the new AGENTS.md/skills content goes live — verified by a test asserting no stale SKILL.md remains on Codex's auto-discovery path while the archived copy still exists
- [ ] The replacement AGENTS.md/skills catalog is generated from the validated `agent-orchestration/` contract (via its explicit generation command), not independently hand-curated — verified by tracing the generated content back to contract source fields, not merely asserting human review occurred
- [ ] Root AGENTS.md exists and is verifiably NOT a copy of the stale .agents/rules/AGENTS.md draft (e.g. does not repeat the confirmed 17-phase pipeline drift; documents the real 32-phase pipeline)
- [ ] Committed fixture record(s) capture the real hook-payload JSON schema/matcher/timing via an isolated scratch-directory Codex CLI invocation (distinct from prior documentation-citation-only evidence)
- [ ] No production hook is enabled as a result of this ticket's work (verified by explicit check of .codex/ config state at ticket close)
- [ ] agent-monitoring/*.jsonl is unchanged (append-only diff, i.e. zero rewritten/reordered/deleted lines) after the containment action
- [ ] The containment action (quarantine/replace of legacy .agents/skills/) is sequenced first within this ticket's own execution, as a hard entry criterion, before AGENTS.md/skills regeneration proceeds

## Related Tickets
- TCK-20260721-ORCHESTRATION-CONTRACT-CORE (hard predecessor — validated contract is this ticket's generation source, added per Codex's 2026-07-22 review correction)
- TCK-20260721-AGENTS-DIR-DISPOSITION
- TCK-20260721-CODEX-CAPABILITY-MATRIX
- TCK-20260721-AGENTS-DISPOSITION-FIX
- TCK-20260721-AGENTS-DISPOSITION-DISCOVERABILITY-FIX
- TCK-20260721-CODEX-REPLAY-PROOF
- TCK-20260721-ORCHESTRATION-CONTRACT-ADR
- TCK-20260721-PROVIDER-AGNOSTIC-EPIC

## Related Docs
- docs/ai/agents_dir_disposition.md
- docs/ai/codex_capability_matrix.md
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md
- docs/ai/replay_fixture_spec.md
- docs/architecture/agent_orchestration_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/ai/agents_dir_disposition.md
- docs/ai/codex_capability_matrix.md
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md
- docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_final_corrections_response_codex.md
- docs/ai/replay_fixture_spec.md
- docs/architecture/agent_orchestration_contract.md
- tests/tools/test_codex_capability_diagnostics.py
- tests/tools/test_post_tool_hook.py
- .agents/rules/AGENTS.md
- tickets/done/provider-agnostic-discovery/SEQUENCE.md

## Assumptions / Open Questions
- Real hook-payload capture consumes real API usage under the user's authenticated account — must be flagged to the ticket owner before running, consent to be obtained during Plan/Implement
- WebFetch is blocked in this sandbox — live doc re-verification for canonical AGENTS.md material may need WebSearch or cached sources as fallback
- Per Codex's 2026-07-22 review correction, "reviewed canonical material" is superseded: the AGENTS.md/skills catalog must be generated from the validated `agent-orchestration/` contract via its explicit generation command, once TCK-20260721-ORCHESTRATION-CONTRACT-CORE lands — human review applies at the contract's own skills.yaml authoring stage (that ticket's scope), not as a second independent curation pass in this ticket

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

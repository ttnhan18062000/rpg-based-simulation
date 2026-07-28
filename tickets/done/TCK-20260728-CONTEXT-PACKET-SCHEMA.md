---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260728-CONTEXT-PACKET-SCHEMA
phase: done
date: 2026-07-28
tags: [ai, registry, schema]
---

# TCK-20260728-CONTEXT-PACKET-SCHEMA

## Title
Define Context-Packet Schema and Authority/Freshness Field Contract

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
The author wants a decision document that specifies the fields of a provider-neutral ContextPacket (and its ContextRequest) — packet_id, corpus_generation, retrieval_version, budget_requested/returned, included[] entries with source_id/kind/path/heading_or_symbol/hash/authority/freshness/score/inclusion_reason/excerpt_budget, excluded_summary[], and expansion_policy. This should resolve Open Decision 3 (which authority/freshness metadata is mandatory on a packet source, and how conflicting active documents are represented) and build on the existing docs/REGISTRY.yaml authority/status primitive rather than replacing it. This matters because Phase 3+ retrieval/cache work will build directly against whatever schema this doc fixes, so it needs to be settled before any implementation lands.

## Scope
- Author docs/engine/contracts/context_packet_contract.md (new) specifying ContextRequest fields (task_ref/ticket_id/free-text intent, provider, agent_role, workflow, phase, risk_tier, changed_paths, scenario, token_budget) and ContextPacket fields (packet_id, corpus_generation, retrieval_version, budget_requested, budget_returned, included[] with source_id/kind/path/heading_or_symbol/hash/authority/freshness/score/inclusion_reason/excerpt_budget, excluded_summary[], expansion_policy), verbatim from the idea doc's Proposed Architecture section 1.
- Resolve Open Decision 3 (mandatory authority/freshness metadata; representation of conflicting active documents) with a cited answer that builds on docs/REGISTRY.yaml's existing status/authority enums rather than inventing a parallel system.
- Give the doc frontmatter that passes tools/validate_frontmatter.py with a registered layer and pre-registered tags.
- Link the new contract doc from TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC as a Phase 2 deliverable.

## Out of Scope
- Any src/ or tools/ implementation of ContextPacket construction/serialization code.
- Phase 3 retrieval/cache implementation.
- Phase 4 observability events/dashboard work.
- Phase 5-6 shadow packets or workflow adoption.
- Force-resolving Open Decisions 1, 2, 4, 5, or 6.
- Replacing or modifying docs/REGISTRY.yaml's existing status/authority enum values.

## Acceptance Criteria
- [ ] New doc (expected: docs/engine/contracts/context_packet_contract.md) exists with frontmatter that passes tools/validate_frontmatter.py using a registered layer/tags.
- [ ] Doc documents ContextRequest fields and ContextPacket fields (as listed in scope) verbatim from the idea doc's Proposed Architecture section 1.
- [ ] Doc explicitly resolves Open Decision 3 with a cited answer building on REGISTRY.yaml's status/authority enums rather than inventing a parallel system.
- [ ] Ticket's Out of Scope excludes any src/tools/ implementation, retrieval/cache code (Phase 3), observability events (Phase 4), and workflow adoption (Phase 5-6).

## Related Tickets
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
- TCK-20260728-PHASE0-PREREQ-CONFIRMATION
- TCK-20260728-RETRIEVAL-BASELINE-METRICS
- TCK-20260728-EVAL-FIXTURE-REPAIR
- TCK-20260721-MONITORING-WRITER-DECISION

## Related Docs
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase2.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure.md
- docs/parity_ledger/schema.json
- docs/engine/contracts/task_result_update_substrate_contract.md
- docs/ai/monitoring_writer_decision.md
- docs/REGISTRY.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase2.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure.md
- docs/parity_ledger/schema.json
- docs/engine/contracts/task_result_update_substrate_contract.md
- docs/ai/monitoring_writer_decision.md
- docs/REGISTRY.yaml
- tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md
- tickets/todos/context-efficient-retrieval/SEQUENCE.md
- expected: docs/engine/contracts/context_packet_contract.md

## Assumptions / Open Questions
- No existing REGISTRY.yaml mechanism represents 'conflicting active documents' today; the doc must propose a doc-only resolution or explicitly flag this as an unresolved gap rather than silently inventing new registry machinery.
- The parent epic (TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC) remains open and covers Phase 0-1 only; this ticket is a Phase 2 child, not an epic-closing change.
- Open Decisions 5 and 6 are explicitly deferred to later phases and must not be force-resolved here.
- Tier is standard rather than hotfix because this doc establishes a durable schema/contract that Phase 3+ will build against, which is architecture-review-worthy even though the deliverable is doc-only.

## Implementation Notes

Authored `docs/engine/contracts/context_packet_contract.md` (new) per `staging_artifacts/TCK-20260728-CONTEXT-PACKET-SCHEMA/plan.md`'s 8 steps, followed exactly, no deviations:

- **Frontmatter/placement (Step 1, Decision C):** `status: active, layer: ai, authority: P1, audience: agent, tags: [ai, registry, schema]`, mirroring `task_result_update_substrate_contract.md`'s field shape (adjusted `layer`/`tags`/`audience` to this ticket's registered values — the precedent doc uses `layer: engine, audience: developer` with no tags; this doc uses `layer: ai, audience: agent` per this ticket's own frontmatter, keeping `authority: P1` consistent). Opening disclaimer states the doc decides nothing in code and gives the contract-vs-decision-record placement rationale (`docs/engine/contracts/` vs `docs/ai/`). Idea doc's load-bearing constraint sentence (lines 108-110, "The packet is a retrieval artifact, not a new source of truth...") preserved verbatim. The maturity-banner constraint sentence (no new mandatory workflow gate/writer change/external retrieval service) is restated in the opening section per the epic's existing banner.
- **§1 ContextRequest (Step 2):** all 9 fields from idea doc lines 93-95 listed verbatim by name, one-line original prose per field, closing with the "→ classify and retrieve" disposition line. No invented fields.
- **§2 ContextPacket (Step 3):** all top-level fields plus all 10 `included[]` sub-fields and all 4 `excluded_summary[]` sub-fields listed verbatim by name. Decision A's non-registry-backed fallback text is embedded inline in the `authority`/`freshness` sub-field bullets themselves (describing the verbatim fields' semantics, not adding a new field), per the plan's explicit instruction.
- **§3 Open Decision 3 Resolution (Step 4):** opens with the exact Open Decision 3 blockquote from the epic ticket. Core answer cites `tools/validate_frontmatter.py:54` (`AUTHORITY_VALUES`) and `:44` (`STATUS_VALUES`) by exact enum value sets. Two clearly-labeled extension subsections: (a) non-registry-backed source fallback — `authority`/`freshness: unrated` sentinel for `code_symbol`/`test`/`graphify_node`/`tickets/inprogress/` kinds, and the separate parity-ledger `priority`/`status` proxy (`docs/parity_ledger/schema.json:16-23`) for `parity_ledger_entry` kind, explicitly flagged as a second, differently-shaped vocabulary; (b) conflicting-active-documents advisory tie-break — include both, rank by authority then `last_verified` recency, flag the lower-ranked entry's `inclusion_reason` as superseded, explicitly labeled as advisory guidance and not a REGISTRY.yaml schema change. Closing paragraph states REGISTRY.yaml's generator/schema/enums are untouched.
- **§4 Verification Path (Step 5):** cites the idea doc's exact section as the field list's source of truth, cites §3 of this doc as Open Decision 3's answer, and states explicitly that no code enforces the contract yet (future Phase 3 work) and that no parity-ledger entry is needed (agent-orchestration tooling, not simulation logic — same posture as `docs/parity_ledger/infrastructure.yaml` INFRA-281–292).
- **Step 6:** Epic ticket's OPEN DECISION 3 line replaced with a `**RESOLVED**` block in the exact style of the existing OPEN DECISION 2 resolution entry (date, ticket ref, one-paragraph answer, citation to this doc). This ticket was already present in the epic's `## Related Tickets` list, so no addition was needed there. Decisions 1/4/5/6 and the epic's `## Status`/`## Tier` were left untouched (confirmed via diff).
- **Step 7:** This section plus Test Summary/Files Changed/Completion Summary filled in now. `## Scope`, `## Out of Scope`, `## Acceptance Criteria` left untouched per the plan's explicit instruction.

No deviations from `staging_artifacts/TCK-20260728-CONTEXT-PACKET-SCHEMA/plan.md`.

## Test Summary

- `python3 tools/validate_frontmatter.py docs/engine/contracts/context_packet_contract.md` — exits 0, "OK: 1 file(s) checked — no violations" (AC1).
- Verbatim field inventory (AC2): manually diffed every `ContextRequest`/`ContextPacket` field name (including all 10 `included[]` sub-fields and 4 `excluded_summary[]` sub-fields) against idea doc lines 91-106 — all present, none renamed or dropped, no invented fields added to either verbatim section.
- Open Decision 3 citation check (AC3): §3 names `STATUS_VALUES`/`AUTHORITY_VALUES` by their exact enum value sets with file:line citations (`tools/validate_frontmatter.py:44,54`) and does not invent a parallel enum space; the `unrated` sentinel and parity-ledger proxy are both explicitly flagged as non-REGISTRY vocabularies, not silently coerced.
- Out of Scope boundary re-check (AC4): confirmed this ticket's `## Out of Scope` (unedited) still excludes src/tools implementation, Phase 3/4/5-6, force-resolving Decisions 1/2/4/5/6, and REGISTRY.yaml enum changes — all honored by the actual doc content.
- Scoped regression: `pytest tests/tools/test_validate_frontmatter.py tests/tools/test_generate_registry.py tests/tools/test_registry_query.py -v` — 135 passed, 1 failed. The one failure, `TestRealDocsTree::test_check_flag_detects_no_drift_against_real_registry`, reports that `docs/REGISTRY.yaml` is now stale because the new doc was added (`+ docs/engine/contracts/context_packet_contract.md`) and `docs/REGISTRY.yaml` has not yet been regenerated. This is expected drift, not a regression caused by this ticket's content — per `CLAUDE.md`, `docs/REGISTRY.yaml` is regenerated unconditionally by Finalize's post-migration self-check, not during Implement. No other test in the three files failed, confirming this doc's frontmatter and shape don't break frontmatter validation or registry generation logic itself.

## Files Changed

- `docs/engine/contracts/context_packet_contract.md` (new)
- `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md` (OPEN DECISION 3 marked RESOLVED)
- `tickets/inprogress/TCK-20260728-CONTEXT-PACKET-SCHEMA.md` (this file — Implementation Notes/Test Summary/Files Changed/Completion Summary)

## Completion Summary

Authored `docs/engine/contracts/context_packet_contract.md`, a doc-only Engine Contract that specifies the `ContextRequest`/`ContextPacket` field shapes verbatim from the idea doc's Proposed Architecture §1, and resolves Open Decision 3 by mapping packet `authority`/`freshness` directly onto `docs/REGISTRY.yaml`'s existing `status`/`authority` enums, with two explicitly-labeled extensions (a non-registry-backed source `unrated` fallback plus a separate parity-ledger proxy, and an advisory conflicting-active-documents tie-break rule) — neither of which touches REGISTRY.yaml's schema or enum values. The epic ticket's OPEN DECISION 3 line is marked RESOLVED citing this doc, in the same style as the sibling OPEN DECISION 2 resolution. No `src/`/`tools/` code was written; no `docs/REGISTRY.yaml` schema change was made. Frontmatter validates cleanly; the one pytest failure in the scoped regression run is expected `docs/REGISTRY.yaml` drift, resolved automatically at Finalize, not a content regression.

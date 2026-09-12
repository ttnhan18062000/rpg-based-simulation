---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION
phase: open
date: 2026-09-12
tags: [architecture, api-design]
---

# TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION

## Title
Two live public API endpoints read a registry that nothing populates in a real server — every real request returns empty/404, always

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Surfaced while investigating `TCK-20260911-CAMPAIGN-CHRONICLE-REGISTRY-UNREGISTER-DEAD` (C4):
checking whether `register_campaign()`/`register_chronicle()` had any real production caller
before deleting the dead `unregister_X()` half. They don't.

`src/api/routes/campaigns.py`'s own module-level comment claimed *"In production,
CampaignOrchestrator calls register_campaign() after creation."* Grepped every real caller of
`register_campaign()` in `src/`: none exists outside `campaigns.py` itself and its own test file
(`tests/api/test_campaign_history_api.py`). `CampaignOrchestrator` does not call it — the comment
was false, not aspirational-but-eventually-true. Corrected in this same commit (see Files Changed).

Same shape for chronicle: `register_chronicle()` has zero real callers outside `chronicle.py`
itself and `tests/api/test_chronicle_api.py`. Its own upstream producer, `ChronicleCompiler`, is
never instantiated anywhere except its own module and two test files — the entire
compile→register→serve chain is unexercised in production, not just the register step.

Two live API endpoints read these registries directly:
- `get_campaign_history()` (`src/api/routes/campaigns.py:82-112`, via `_CAMPAIGN_REGISTRY.get(campaign_id)`)
- `get_settlement_personality()` (`src/api/routes/campaigns.py:153-169`, same registry)
- The chronicle route's equivalent endpoints (`src/api/routes/chronicle.py`), same shape via
  `_CHRONICLE_REGISTRY.get(campaign_id)`.

Since nothing populates either registry in a real running server, every real request against these
endpoints returns empty/404, always, by construction — not intermittently, not only in an edge
case. This is the "inert end to end" shape this whole audit arc has found repeatedly (the
knowledge/investigation layer, `KnowledgeFact`), but at higher stakes: those were internal
decision-time mechanisms with no observable player-facing gap; this is a **public API surface** —
a caller who asks for a campaign's history or chronicle gets nothing, every time, in any real
deployment.

## Scope
- Determine which of two real dispositions applies — **this is the open question, not pre-judged
  here**:
  1. **A wiring gap**: the registries are meant to be populated by `CampaignOrchestrator`/
     `ChronicleCompiler` as the (now-corrected) comments implied, and something never got wired —
     find the real intended call site (episode completion? campaign creation? chronicle compile
     completion?) and wire it.
  2. **Test-only scaffolding exposed as production API**: these endpoints were built to be
     exercised by tests injecting state directly, and were never meant to be live in a real
     deployment without a real population path — in which case the question becomes whether they
     should be gated, removed, or given a real backing store.
- Check whether any other real path (not `CampaignOrchestrator`/`ChronicleCompiler` directly)
  legitimately populates these registries that the initial grep might have missed — e.g. a
  background worker, a startup hook, or a different orchestration layer.
- Check whether these endpoints are actually reachable/advertised in the real, deployed API surface
  (are they documented, used by the frontend, referenced by any real client code?) — this bears on
  how urgent disposition #1 vs #2 is.

## Out of Scope
- `TCK-20260911-CAMPAIGN-CHRONICLE-REGISTRY-UNREGISTER-DEAD` (C4) — already closed on its own
  narrower claim (the dead `unregister_X()` half); not reopened here.
- Actually implementing either disposition without a peer-routed decision first — this ticket's
  own Scope is explicitly to determine which disposition applies, not to build either outcome
  unilaterally.

## Acceptance Criteria
- [ ] Real evidence (not assumption) on whether any real production code path populates either
      registry — confirmed exhaustively, not just the initial grep.
- [ ] Real evidence on whether these endpoints are actually reachable in a real deployment (frontend
      usage, documentation, any real client).
- [ ] A peer-routed determination: wiring gap (implement the real population path) vs. test-only
      scaffolding (gate/remove/redesign) — obtained before implementing either.
- [ ] If a fix is implemented: real evidence (an integration test hitting the real endpoint against
      a real populated registry, not just a direct-injection unit test) that the endpoint returns
      real data in a real deployment shape.

## Related Tickets
- `TCK-20260911-CAMPAIGN-CHRONICLE-REGISTRY-UNREGISTER-DEAD` (origin — found while investigating
  C4's own leak-risk question)
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (the parent audit both tickets trace back to)
- `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION`,
  `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS` (same "inert end to end"
  finding shape, internal rather than public-API-facing)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/api/routes/campaigns.py` (`_CAMPAIGN_REGISTRY`, `register_campaign()`,
  `get_campaign_history()`, `get_settlement_personality()` — line numbers as of this filing, post-
  C4's own deletion of `unregister_campaign()`)
- `src/api/routes/chronicle.py` (`_CHRONICLE_REGISTRY`, `register_chronicle()`, its own read
  endpoints)
- `src/domains/campaigns/orchestrator.py` (`CampaignOrchestrator` — confirmed does NOT call
  `register_campaign()`)
- `src/domains/chronicle/compiler.py` (`ChronicleCompiler` — confirmed never instantiated outside
  its own module and tests)

## Assumptions / Open Questions
- Whether disposition #1 or #2 applies is the entire point of this ticket — deliberately not
  pre-judged. Both are plausible from the evidence gathered so far and the answer changes the fix
  entirely (implement real wiring vs. remove/gate a surface that shouldn't be exposed as-is).

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_

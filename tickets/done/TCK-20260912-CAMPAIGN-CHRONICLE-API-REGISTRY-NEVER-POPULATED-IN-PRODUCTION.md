---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION
phase: done
date: 2026-09-12
tags: [architecture, api-design]
---

# TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION

## Title
Two live public API endpoints read a registry that nothing populates in a real server — every real request returns empty/404, always

## Status
DONE

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
- [x] Real evidence (not assumption) on whether any real production code path populates either
      registry — confirmed exhaustively (`register_campaign`/`register_chronicle`/
      `ChronicleCompiler(`: zero production call sites beyond their own modules and test files).
- [x] Real evidence on whether these endpoints are actually reachable in a real deployment: zero
      frontend references; both API test files call the handlers directly, never through
      `create_v2_app()`.
- [x] A peer-routed (and user-routed, for this genuine architecture/product decision) determination:
      gate — stop exposing by default, keep the implementation. Neither wired nor removed.
- [x] Real test evidence the gate itself works: `tests/api/test_inert_route_gating.py` — disabled
      by default (real 404), reachable when explicitly enabled (real domain-level 404 for an
      unregistered campaign, distinguishable from the route-not-mounted 404).

## Related Tickets
- `TCK-20260911-CAMPAIGN-CHRONICLE-REGISTRY-UNREGISTER-DEAD` (origin — found while investigating
  C4's own leak-risk question)
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (the parent audit both tickets trace back to)
- `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION`,
  `TCK-20260912-KNOWLEDGE-INVESTIGATION-LAYER-INERT-NO-FACTS-NO-LEADS` (same "inert end to end"
  finding shape, internal rather than public-API-facing)
- `TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT` (the second instance of this
  exact shape in the same batch — 7 API endpoints, a different subsystem, same "store nothing
  populates" cause. Two instances in one batch suggests this may be systematic in this codebase,
  not isolated — whoever picks up either ticket should check for a third before assuming these are
  the only two, and should treat them as possibly one problem with two faces)
- `TCK-20260913-WAREHOUSE-INGESTION-NEVER-AUTOMATED-SEARCH-API-EMPTY-IN-PRACTICE` (the "check for a
  third instance" search this ticket and its sibling both called for — found `search.py`, confirmed
  it is NOT a third instance of this pattern: its empty state is a normal, correctable one, a real
  CLI ingestion path exists and works when invoked, just never automated. Filed separately per that
  distinction, not folded in)

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
  **Resolved by user decision: gate — disposition #2, keep the implementation.**

## Implementation Notes
Full investigation recorded in `stored_artifacts/TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-
NEVER-POPULATED-IN-PRODUCTION/investigation.md`.

Added `RuntimeProfile.enable_campaign_chronicle_api: bool = False` (`src/config/profiles.py`),
shared by both `campaigns.router` and `chronicle.router` (one flag, since both share the same
disposition and cause). `src/api/server.py::create_v2_app()` now only registers either router when
the flag is `True`. Confirmed `campaigns.py` and `chronicle.py` each contain exactly the 2 affected
endpoints and nothing else before gating.

Corrected two now-stale parity ledger entries that claimed unconditional router registration —
`INFRA-219` (`docs/parity_ledger/infrastructure.yaml`) and `SOC-CHRON-005`
(`docs/parity_ledger/social_narrative.yaml`) — via `tools/parity_ledger_writer.py` (the sanctioned,
schema-validating write path, per standing practice for big/structural parity ledger edits).
`SOC-CHRON-005`'s own `test_path` field was independently already invalid (a raw shell-command
string, not a structured citation) — fixed to real citations while touching the entry, since the
writer's validation rejects the whole entry otherwise.

Third-instance check surfaced `search.py`; filed as its own ticket per peer confirmation it's a
different problem shape, not folded in — see this ticket's own Related Tickets.

## Test Summary
New tests in `tests/api/test_inert_route_gating.py` (shared with the sibling ticket, 6 tests, all
pass): disabled by default (real 404 for both routes), reachable when enabled (real domain-level
404, distinguishable from route-not-mounted). Full `tests/api/` regression sweep (153 passed)
confirms `test_campaign_history_api.py`/`test_chronicle_api.py` (direct-handler-call tests)
unaffected. Full parity-tooling sweep (`test_parity_index.py`, `test_parity_index_baseline.py`,
`test_parity_ledger_scan.py`, `test_parity_ledger_writer.py` — 97 passed) confirms both ledger
corrections are schema-valid and the derived index rebuilds cleanly.

## Files Changed
- `src/config/profiles.py` — `RuntimeProfile.enable_campaign_chronicle_api` field added.
- `src/api/server.py` — `campaigns.router`/`chronicle.router` registration gated behind the new
  flag.
- `tests/api/test_inert_route_gating.py` — new, shared with the sibling ticket.
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-219` updated (conditional registration).
- `docs/parity_ledger/social_narrative.yaml` — `SOC-CHRON-005` updated (conditional registration;
  also fixed its own pre-existing invalid `test_path` format).
- `tickets/todos/TCK-20260913-WAREHOUSE-INGESTION-NEVER-AUTOMATED-SEARCH-API-EMPTY-IN-PRACTICE.md` —
  new ticket, the third-instance check's own real finding.

## Completion Summary
Disposition (gate) was the user's own decision, routed via peer, not picked here. Both required
pre-checks (nothing real depends on these routes; the gating mechanism follows an existing
`api_key_hashes` precedent) confirmed before implementing. The required "check for a third
instance" (shared with the sibling ticket) surfaced `search.py` as a genuinely different problem
shape, filed separately rather than folded in. Corrected two parity ledger entries whose
"unconditionally registered" claims are now stale, using the sanctioned writer tool, and fixed an
unrelated pre-existing format defect found while touching one of them. No known material gap left
unstated.

## Completion Summary
_(pending)_

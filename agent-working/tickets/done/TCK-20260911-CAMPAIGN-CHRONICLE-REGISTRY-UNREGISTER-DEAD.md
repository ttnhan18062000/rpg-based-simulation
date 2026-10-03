---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260911-CAMPAIGN-CHRONICLE-REGISTRY-UNREGISTER-DEAD
phase: done
date: 2026-09-11
tags: [architecture]
---

# TCK-20260911-CAMPAIGN-CHRONICLE-REGISTRY-UNREGISTER-DEAD

## Title
`unregister_campaign()`/`unregister_chronicle()` are dead — the cleanup half of a register/
unregister pair, never called anywhere, including their own tests

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found during `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (`docs/audits/
unreachable_code_inventory.md`, Cluster C4). `src/api/routes/campaigns.py` and `src/api/routes/
chronicle.py` each declare an in-memory dict registry (`_CAMPAIGN_REGISTRY`, `_CHRONICLE_REGISTRY`)
with a `register_X()`/`unregister_X()` function pair. `register_campaign()`/`register_chronicle()`
are genuinely called — from `tests/api/test_campaign_history_api.py` and `tests/api/
test_chronicle_api.py`, injecting state for API tests. `unregister_campaign()` (`campaigns.py:56`)
and `unregister_chronicle()` (`chronicle.py:52`) have **zero call sites anywhere** — not in `src/`,
not in either test file, not anywhere in `tools/`. Confirmed directly: both test files' own
docstrings say cleanup uses a separate `_clear_registry()` function instead
(`"Inject CampaignState via register_campaign() / _clear_registry()."`).

Fully verified, narrow, and low-risk — this is the cleanup half of a register/unregister pair that
was written but never wired to any real teardown path, in production or in tests.

## Scope
- Confirm `_clear_registry()` (or its per-file equivalent) genuinely covers the same cleanup need
  `unregister_campaign()`/`unregister_chronicle()` were presumably meant to serve, before deciding
  disposition.
- If `_clear_registry()` fully covers it: delete `unregister_campaign()`/`unregister_chronicle()`
  as confirmed-redundant dead code.
- If there's a real gap `_clear_registry()` doesn't cover (e.g. per-campaign/per-chronicle
  selective cleanup, as opposed to a full registry wipe): wire the existing `unregister_X()`
  functions into whatever real call site should be using them instead of deleting them.

## Out of Scope
- Any other cluster from the same audit — each has, or will have, its own ticket.
- `register_campaign()`/`register_chronicle()` themselves — already confirmed live via test usage,
  not part of this finding.

## Acceptance Criteria
- [x] `_clear_registry()`'s own real cleanup scope is confirmed (full-wipe vs. selective) before
      deciding disposition. Confirmed full-wipe (`.clear()`), used by both test files' own
      `@pytest.fixture(autouse=True)` before AND after every test.
- [x] `unregister_campaign()`/`unregister_chronicle()` are either deleted (confirmed redundant) or
      wired into a real call site (confirmed genuine gap), with rationale recorded either way.
      **Deleted, confirmed redundant** — but only after an explicit leak check peer review
      requested: verified `register_campaign()`/`register_chronicle()` have zero real production
      callers (nothing ever registers in a real server, so nothing can leak) and that both test
      files' autouse fixtures fully bound test-time registrations. No scenario exists where
      something registers and isn't cleaned up.
- [x] No regression in `tests/api/test_campaign_history_api.py`, `tests/api/test_chronicle_api.py`.
      17 passed.

## Related Tickets
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (origin — Cluster C4)
- `TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION` (new, filed from
  this ticket's own leak check — the bigger finding: nothing populates either registry in a real
  server, so two live public API endpoints return empty/404 for every real request)

## Related Docs
- `docs/audits/unreachable_code_inventory.md` (Cluster C4's own writeup)

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/api/routes/campaigns.py` (`register_campaign()`, `unregister_campaign()`,
  `_CAMPAIGN_REGISTRY`)
- `src/api/routes/chronicle.py` (`register_chronicle()`, `unregister_chronicle()`,
  `_CHRONICLE_REGISTRY`)
- `tests/api/test_campaign_history_api.py`, `tests/api/test_chronicle_api.py` (both reference
  `_clear_registry()` in their own docstrings as the real cleanup mechanism)

## Assumptions / Open Questions
None — scope is a straightforward, well-evidenced hotfix once picked up.

## Implementation Notes
Confirmed `_clear_registry()`'s real scope before deciding, per this ticket's own Scope
requirement: a full `.clear()`, used by both test files' `@pytest.fixture(autouse=True)` before and
after every test.

Before deleting, peer review asked for an explicit check the ticket's own Scope hadn't required:
whether anything registers without a corresponding unregister path in a way that could leak in a
long-running server — a dead `unregister` can mean "abandoned" or "the missing half of a real
leak," and the two read oppositely. Checked: `register_campaign()`/`register_chronicle()` have zero
real production callers anywhere in `src/` (only their own route module and own test file reference
them) — nothing ever registers in a real server, so nothing can leak there. In tests, the only place
registration happens, both files' autouse fixtures wipe the registry before AND after every test —
fully bounded, no accumulation. Confirmed abandoned, not a symptom of a real leak. Reported this
finding to peer review before deleting, and got confirmation to proceed.

That same check surfaced a materially bigger finding, reported and confirmed: the module-level
comment in `campaigns.py` claiming "In production, CampaignOrchestrator calls register_campaign()
after creation" was false — `CampaignOrchestrator` never calls it. Same shape for chronicle:
`ChronicleCompiler`, the intended upstream producer, is never instantiated anywhere outside its own
module and two test files. So two live API endpoints (`get_campaign_history()`,
`get_settlement_personality()`, and chronicle's equivalent) read a registry that nothing populates
in any real deployment — every real request returns empty/404, always. Corrected both false/
misleading comments in this same commit and filed the bigger finding as its own ticket
(`TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION`), framed as an open
disposition question (wiring gap vs. test-only scaffolding) rather than pre-judged here, per
standing "no building without declared intent" discipline.

Deleted `unregister_campaign()` (`campaigns.py`) and `unregister_chronicle()` (`chronicle.py`).
Confirmed zero remaining references anywhere in the codebase via grep after deletion.

## Test Summary
`tests/api/test_campaign_history_api.py`, `tests/api/test_chronicle_api.py` — 17 passed, no
regression. Grep confirms zero remaining references to `unregister_campaign`/`unregister_chronicle`
anywhere in `src/` or `tests/` after deletion.

## Files Changed
- `src/api/routes/campaigns.py` — deleted `unregister_campaign()`; corrected the false "In
  production, CampaignOrchestrator calls register_campaign()" comment to state the real, verified
  fact and point to the new ticket.
- `src/api/routes/chronicle.py` — deleted `unregister_chronicle()`; corrected the equivalent
  misleading comment the same way.
- `tickets/todos/TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION.md` —
  new, filed as the bigger finding surfaced by this ticket's own leak check.
- `tickets/done/TCK-20260911-CAMPAIGN-CHRONICLE-REGISTRY-UNREGISTER-DEAD.md` — this file, closed.

## Completion Summary
Deleted `unregister_campaign()`/`unregister_chronicle()` as confirmed-redundant dead code — the
originating audit's finding held, and an explicit leak check (requested by peer review, not
originally part of this ticket's own Scope) confirmed both registries are fully bounded in every
place registration actually occurs, so there was no real leak `unregister_X()` was the missing tool
for. That same check surfaced a bigger, higher-stakes finding: nothing populates either registry in
a real server at all, so two live public API endpoints return empty/404 for every real request,
always — filed as its own standard-tier ticket rather than resolved here, since this ticket's own
scope was strictly the dead cleanup-half finding. Corrected two confidently-false module-level
comments in the same commit, regardless of which way that new ticket's disposition eventually goes.

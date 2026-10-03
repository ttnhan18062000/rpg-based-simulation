# Plan — TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION

## Mechanism

Same mechanism as the sibling `TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-STARTED-API-INERT`:
`RuntimeProfile.enable_campaign_chronicle_api: bool = False` (`src/config/profiles.py`), checked in
`create_v2_app()` before registering BOTH `campaigns.router` and `chronicle.router` together (one
flag, two routers — they share the same disposition and the same "test-only scaffolding" cause,
not two independent decisions).

Confirmed both route modules contain only the affected endpoints before gating the whole router:
`campaigns.py` has exactly 2 (`get_campaign_history`, `get_settlement_personality`), `chronicle.py`
has exactly 2 (`get_chronicle`, `get_era_summary`) — gating the entire router hides nothing
unrelated.

## Not doing

- Not changing the route handlers' own empty-state responses.
- Not touching `search.py`.
- Parity ledger corrections (`INFRA-219`, `SOC-CHRON-005`) are part of this ticket's own Files
  Changed, per the Authoritative Mechanics Rule (a real logic change — conditional registration —
  requires updating any parity entry that made an unconditional-registration claim).

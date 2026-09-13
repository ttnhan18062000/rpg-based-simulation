# Investigation — TCK-20260912-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-PRODUCTION

## Disposition: gate (user decision, routed via peer)

Same disposition and reasoning as the sibling `TCK-20260912-BEHAVIOR-ANALYTICS-PIPELINE-NEVER-
STARTED-API-INERT`: both subsystems are fully built and tested with no real production data
source; gate registration rather than remove or wire, since the wire-vs-defer question stays open
for both.

## Exhaustive production-writer check

`grep -rn "register_campaign(\|register_chronicle(" src/ tests/`: only the route modules' own
definitions and test-file call sites (`tests/api/test_campaign_history_api.py`,
`tests/api/test_chronicle_api.py`) — zero production callers.
`grep -rn "ChronicleCompiler(" src/ tests/`: only its own module (`compiler.py`'s own internal
reference) and test files (`tests/unit/domains/chronicle/test_faction_chronicle.py`,
`tests/integration/scenarios/test_campaign_chronicle.py`) — zero production construction.
Both confirmed exhaustively, not just the origin ticket's own initial grep.

## Reachability in a real deployment

Zero frontend references anywhere. Both `tests/api/test_campaign_history_api.py` and
`tests/api/test_chronicle_api.py` explicitly document "Call the route handler[s] directly (no HTTP
layer needed for unit tests)" — they never construct `create_v2_app()` or a `TestClient`; gating
registration breaks neither. `tests/integration/scenarios/test_campaign_chronicle.py` and
`tests/integration/campaigns/test_nemesis_relation_and_chronicle_fidelity_campaign.py` (the
integration tests that look adjacent) exercise `ChronicleCompiler`/chronicle fidelity directly, not
the HTTP layer — confirmed via grep for `TestClient`/`create_v2_app`/`api/v1`, zero matches.

## Check for a third instance

Same check as the sibling ticket, same result: `search.py` found, confirmed a different problem
shape (a real, tested, CLI-invocable ingestion path that's simply never automated — not "nothing
can ever populate it"). Filed separately as
`TCK-20260913-WAREHOUSE-INGESTION-NEVER-AUTOMATED-SEARCH-API-EMPTY-IN-PRACTICE`, not folded in.

## Parity ledger correction

Both `INFRA-219` (`docs/parity_ledger/infrastructure.yaml`) and `SOC-CHRON-005`
(`docs/parity_ledger/social_narrative.yaml`) previously stated unconditional router registration
("Router registered in create_v2_app() with prefix='/api/v1'") — now stale given the gate. Updated
both via `tools/parity_ledger_writer.py` (the sanctioned, schema-validating write path) to record
the new conditional registration and cross-reference this ticket. `SOC-CHRON-005`'s own `test_path`
field was, independently, already in a pre-existing invalid format (a raw shell command string
rather than a structured citation) — fixed to real citations
(`tests/api/test_chronicle_api.py::test_*`) while touching the entry anyway, since the writer's own
validation rejects writes with an invalid `test_path` regardless of which field changed.

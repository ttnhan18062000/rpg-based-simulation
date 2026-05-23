# test_plan.md - API & CLI Tests

## Milestone 64: Evidence and Report Tests
- `tests/unit/observability/cognition/test_cognition_evidence_pack_builder.py`:
  - Assert that the evidence pack builder correctly aggregates before and after snapshots, diffs, and compressed feature summaries.
  - Assert that if many entities are affected, an `affected_entities_cognition_summary.json` is successfully outputted.
  - Assert that the evidence pack does not claim absolute cognition root cause, and instead uses the designated anti-misdirection phrasing (`likely related to unresolved blocker`).
- `tests/integration/observability/test_cognition_report_section.py`:
  - Run the `RunReportGenerator` and confirm that when cognition data exists, a formatted "Strategic Cognition Evidence" markdown section is generated.
  - Verify that if cognition files are missing, the generator finishes cleanly and inserts a clear "cognition data missing" notice.

## Milestone 65: API & CLI Tests
- `tests/api/test_cognition_history_api.py`:
  - Verify `GET /observability/history/runs/{run_id}/cognition/entities/{entity_id}/snapshots` successfully paginates snapshots and excludes the full node/edge arrays unless `full_graph=true` is provided.
  - Verify diffs, features, and patterns routes return correct schemas and status codes.
  - Assert path traversal checks block arbitrary query/path strings (e.g. `../` or invalid run IDs) and return 400 Bad Request.
  - Assert that missing files return clean developer-friendly JSON error payloads.
- `tests/cli/test_cognition_cli.py`:
  - Verify cli execution of `rpg-observe cognition snapshot`, `diff`, `features`, and `patterns`.
  - Verify that invalid arguments or missing run folders terminate cleanly with appropriate exit codes and error logs (no stack traces).
  - Verify path traversal checks block input (e.g., using `..` in run/entity identifiers).

---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260523-COGNITION-REPORTS-API
artifact_type: plan
tags: [cognition, reports, api]
---

# plan.md - Reports, CLI & API Plan

Integrate cognition evidence in reports/packs, and implement API/CLI endpoints.

## Key Actions
1. **Report Generation**: Update `RunReportGenerator` inside `src/observability/reporting/run_report.py` to aggregate and render strategic cognition sections (current project, active blockers, leads, concerns, potential patterns, recent changes) if cognition JSONL/JSON files are present. Show a clean missing data message if not.
2. **Evidence Packs**: Update `EvidencePackBuilder` inside `src/observability/mining/evidence.py` to package before/after entity snapshots, incremental diffs, and compressed feature/pattern summaries on anomaly triggers. Limit huge raw graphs by default.
3. **Verdict Phrasing**: Maintain strict anti-misdirection compliance inside `AIAgentInvestigationRunner` (`src/observability/mining/orchestrator.py`) by describing cognition findings as strategic context/evidence (`likely related to unresolved blocker`), not absolute root causes.
4. **History API**: Register `/observability/history/runs/{run_id}/cognition/` routes under `src/api/routes/history.py` for snapshots, diffs, features, and patterns. Secure them using alphanumeric `sanitize_id` filters and add pagination support.
5. **Live API**: Register live entity inspection route `/api/v1/observability/live/entities/{entity_id}/cognition` under `src/api/server.py` to query active in-memory actor status safely.
6. **CLI Commands**: Wire argparse-based subcommands inside `src/cli/entry.py` under the `cognition` subcommand matching `snapshot`, `diff`, `features`, and `patterns`. Block arbitrary path access and format responses cleanly.

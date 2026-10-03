---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260523-COGNITION-REPORTS-API
artifact_type: investigation
tags: [cognition, reports, api]
---

# investigation.md - API/CLI Subsystems

- **API Subsystem**: FastAPI routing lives under `src/api/routes/history.py` for historical data and `src/api/server.py` for the app setup. New read-only endpoints must follow the repository query service pattern and apply `sanitize_id` validation.
- **CLI Subsystem**: The primary command-line tool entrypoint lives in `src/cli/entry.py` (which implements the `rpg-observe` CLI). Subcommands are parsed via `argparse`, so we will integrate `rpg-observe cognition` under this framework while ensuring semantic parity with Click-style command interfaces.
- **Cognition Storage**: Snapshot data is generated in individual run folders (e.g. `data/runs/<run_id>/`) as `cognition_graph_snapshots.jsonl` (raw snaps), `cognition_graph_diffs.jsonl` (incremental diffs), `cognition_features.jsonl` (aggregated metrics), and `cognition_patterns.json` (threshold patterns).

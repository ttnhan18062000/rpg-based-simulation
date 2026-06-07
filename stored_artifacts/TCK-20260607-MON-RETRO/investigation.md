# Investigation — TCK-20260607-MON-RETRO

## Current Behavior
No retro tooling. events.jsonl and runs.jsonl exist (from MON-SCHEMA) but no way to process them into a report.

## Mechanics / Engine Constraints
None — tooling only.

## Parity Ledger Overlap
None.

## Prior Work
TCK-20260607-MON-SCHEMA: created the JSONL files and stub tools.
TCK-20260607-MON-CAPTURE: populated the JSONL files with real data from workflow runs.

## Risks and Open Questions
- ISO week format: Python uses `%G-W%V` for ISO week numbers — tested and correct.
- `RETRO-ALL.md` vs `RETRO-<week>.md`: naming convention chosen for easy identification.
- Index file at `agent-monitoring/retro/index.md` auto-regenerated on every retro run.
- Makefile `ARGS` passthrough for query target: `make agent-monitoring-query ARGS="--status failed"`.

## Anti-Drift Hazards
- generate_retro.py must be run from repo root (not from agent-monitoring/).
- The retro/ directory must exist before writing reports (mkdir -p handled in script).

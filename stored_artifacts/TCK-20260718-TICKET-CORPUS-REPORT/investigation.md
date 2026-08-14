---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260718-TICKET-CORPUS-REPORT
artifact_type: investigation
tags: []
---

# Investigation — TCK-20260718-TICKET-CORPUS-REPORT

## Current Behavior (file:line refs)

`tools/tag_report.py` (read in full) is the exact precedent: `collect_completed_tickets(root)`
walks `tickets/done/` recursively, applies 3 skip rules (SEQUENCE.md, unparseable/missing
frontmatter, pre-taxonomy/legacy ticket_id — **this last rule does not apply to this new tool**,
since Tier/Type/Priority/Layer distribution is not tag-taxonomy-gated), `build_tag_rows()`
computes, `print_report()`/`build_json_report()` render the same computation two ways,
`main()` wires argparse + `--json`/`--list-skipped` flags.

`docs/REGISTRY.yaml` (checked directly): ticket entries have `tier`, `ticket_type`, `tags`,
`date`, `related_code_areas`, `artifact_files` — but **no `layer`, no `priority`, no body
`## Status`**. Confirms the dashboard's own origin idea doc's finding: "its ticket-type rows
omit status/layer/priority entirely" — `docs/REGISTRY.yaml` is not a sufficient data source
alone; this tool must parse ticket files directly (frontmatter for `layer`, body sections for
`Tier`/`Priority` via `tools/generate_registry.py::parse_body_section`), same as
`tools/ticket_field_values.py`/`ingest.py` already do for the dashboard's row-level views.

`tickets/working_log.csv` columns confirmed: `timestamp,ticket_id,title,status,summary,
artifacts_path` — sufficient for velocity/throughput (group `timestamp` by day/week).

`tools/layer_registry.py::layer_values()` and `tools/ticket_field_values.py`'s
`TIER_VALUES`/`PRIORITY_VALUES` (from today's earlier canonical-field-enums epic) give this tool
canonical value sets to validate/cross-tab against, for free.

## Mechanics/Engine Constraints

None — reporting tooling.

## Parity Ledger Overlap

The new `/api/stats/tickets` backend endpoint touches `src/api/agent_ops_dashboard/` — same
`INFRA-275` entry as the sibling AGENTOPS-STATS-API ticket. The standalone `tools/*.py` report
script itself is not dashboard code — no parity entry needed for the tool in isolation (mirrors
`tag_report.py`, which has none).

## Prior Work

`tag_report.py` — direct precedent, described above. `tools/ticket_field_values.py`,
`tools/layer_registry.py` — canonical value sources.

## Risks and Open Questions

- Scope to `tickets/done/` only (matching `tag_report.py`'s own scope choice), not
  `tickets/inprogress/`/`tickets/todos/` — velocity/distribution stats over *completed* work is
  the natural reading of "reporting," and keeps this tool's scope consistent with its direct
  precedent rather than inventing a different corpus-scope convention.
- Artifact completeness only applies to `standard`/`epic` tickets (hotfix tickets have no
  `stored_artifacts/` requirement per `CLAUDE.md`'s own Workflow Rule).
- Tool filename: `tools/ticket_stats_report.py`, mirroring `tag_report.py`'s `<domain>_report.py`
  convention.

## Anti-Drift Hazards

- Must not duplicate `tools/ticket_field_values.py`'s `TIER_VALUES`/`PRIORITY_VALUES` or
  `tools/layer_registry.py`'s `layer_values()` — import and use them directly for canonical
  cross-referencing.
- Must not re-derive tag-registry logic — this tool doesn't touch tags at all (that's
  `tag_report.py`'s own domain, untouched).

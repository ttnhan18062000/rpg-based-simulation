---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-AGENT-TOOL-USAGE-BASELINE
phase: done
date: 2026-09-04
tags: [governance, ai, agent-monitoring]
---

# TCK-20260904-AGENT-TOOL-USAGE-BASELINE

## Title
Per-agent tool-usage baseline audit from agent-monitoring data

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P0

## Request Summary
Mine agent-monitoring for each of the 16 agents' real historical tool-call pattern (which tools, how often, what scope) to produce one usage table — this is the evidence M3's per-agent tools: frontmatter scoping decisions will be based on, so its accuracy directly gates whether that later scoping work is safe. Pure read/aggregation against existing monitoring data, no code changes to production paths, no execution risk. Gated on nothing and can start immediately, but the concern author's own source text (referencing a tool_input field and a single agent-monitoring/tools.jsonl file) is stale and must be corrected against the real schema before implementation begins.

## Scope
- Write a read-only script that globs all agent-monitoring/data/*/tools.jsonl weekly shards (not a single retired agent-monitoring/tools.jsonl path)
- Aggregate tool-call counts per agent using the agent field, explicitly bucketing null/non-matching values as an 'unattributed' group rather than silently dropping or misassigning them
- Read tool-call detail from the real input_summary field (truncated max 120 chars), not the nonexistent tool_input field the epic doc assumes
- Produce one usage table covering all 16 currently-registered agents (from .claude/agents/*.md) plus the unattributed bucket, with at least one truthfully-labeled truncated example per tool-name entry
- Sanity-check aggregate row counts against a raw wc -l across all shards

## Out of Scope
- Any change to .claude/agents/*.md tools: frontmatter (that is a separate, dependent ticket's job, gated on this ticket's output)
- Any modification to agent-monitoring write paths, schema, or shard migration tooling
- Deriving exact Bash 'command class' beyond what input_summary's 120-char truncation actually supports

## Acceptance Criteria
- [x] Script output contains exactly 16 agent rows (matching current .claude/agents/*.md file names) plus one explicit 'unattributed' row for null/non-matching agent values — not hardcoded or stale against the current agent roster
- [x] Script globs all agent-monitoring/data/*/tools.jsonl shards and the sum of per-agent counts matches a wc -l sanity check across those shards
- [x] Every tool-name entry in the output table includes at least one real representative example drawn from input_summary, explicitly labeled as truncated/summarized (except the rare "unknown" bucket for the 2 pre-existing legacy-shaped rows with no `tool`/`input_summary` field at all — see Implementation Notes)
- [x] A test asserts the script is read-only against agent-monitoring/data/ (shard file bytes unchanged before vs. after running the script)

## Related Tickets
- Adjacent, different scope: TCK-20260810-AGENT-TOOLING-INTEGRITY-HARDENING-EPIC (done)
- Reference for correct shard structure: TCK-20260902-MONITORING-SHARD-MIGRATION
- Reference for correct write-path assumptions: TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY
- Reference for correct glob pattern: TCK-20260903-MONITORING-DATA-MIGRATION

## Related Docs
- docs/agent-monitoring/schema.md
- docs/agent-monitoring/README.md
- docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/agent-monitoring/schema.md
- docs/agent-monitoring/README.md
- agent-monitoring/data/2026-W24/tools.jsonl
- agent-monitoring/data/2026-W36/tools.jsonl
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/query.py
- .claude/agents/*.md
- tests/tools/test_record_events.py

## Assumptions / Open Questions
- Epic doc's assumptions of a tool_input field and a single tools.jsonl file are stale and must be corrected in this ticket's own documentation before implementation, not silently worked around
- 189,871 rows are spread across 14 shards — implementation should stream rows rather than building a large in-memory structure
- input_summary's 120-char truncation limits how precisely Bash 'command class' can be derived — this is an accepted limitation, not a gap to silently paper over
- If null-agent rows are mis-grouped instead of explicitly bucketed as unattributed, the downstream per-agent scoping ticket would be built on an incomplete picture without that gap being visible — must be avoided by design

## Implementation Notes

Built `tools/agent-monitoring/agent_tool_usage_baseline.py` following `plan.md`'s 7 steps:

1. `registered_agents()` live-globs `.claude/agents/*.md` (sorted, never hardcoded);
   `load_all_tool_rows()` reuses `load_data_glob` imported from `generate_retro.py` (which itself
   re-exports `validate.py`'s `load_data_glob`) — no 4th shard-glob loader.
2. `bucket_for(row, known_agents)` returns the row's `agent` value only if it is a non-null string
   present in the live known-agents set, else the literal `"unattributed"` — does not import
   `vocabulary.py`'s `is_known_agent`/`WORKFLOW_AGENTS`, per the plan's explicit scope guard.
3. `build_usage_table(rows, known_agents)` seeds every known agent plus `"unattributed"` at
   `count: 0` before processing any row (so the 6 zero-activity agents surface explicitly), then
   aggregates per-(agent, tool) counts with a first-seen-wins verbatim `example` from
   `input_summary`, each labeled `"truncated": true`.
4. `build_report(rows)` adds `total_rows_seen` and `total_rows_across_all_agent_rows` (summed
   independently from the table) as a self-checking reconciliation pair; `main()` is a bare
   `argparse` CLI with no `--output` flag, printing `json.dumps(..., sort_keys=True)` to stdout only.
5. Wrote all 10 tests named in `test_plan.md`'s "New Tests Required" section (the ticket's own
   task description said 9; the test_plan.md file itself lists 10 distinct test names under that
   heading — implemented all 10, none omitted) in `tests/tools/test_agent_tool_usage_baseline.py`,
   reusing the `_porcelain_snapshot()` helper pattern (copied verbatim, same as the sibling file
   does) for the read-only guard test.
6. Ran the 3 scoped pytest commands from `test_plan.md` — see Test Summary.
7. Added an "Agent Tool-Usage Baseline" section to `docs/agent-monitoring/README.md`, matching the
   sibling "Skill Usage Metric"/"Done-Ticket Monitoring Coverage Audit" sections' length and tone.

**Deviation from plan (real-corpus edge case, not anticipated by plan.md or investigation.md):**
2 rows across the whole corpus (`agent-monitoring/data/2026-W27/tools.jsonl:43`,
`agent-monitoring/data/2026-W29/tools.jsonl:6946`) are legacy-shaped `tools.jsonl` records with no
`tool` key at all (predating that field's introduction — same family of legacy shape
`legacy_reader.py`'s `classify_provenance` already documents for other sources). `row.get("tool")`
returns `None` for these, which crashes `json.dumps(..., sort_keys=True)` (`TypeError: '<' not
supported between instances of 'NoneType' and 'str'`) when building the per-tool dict, since a
`None` key can't be compared against the other string tool-name keys during key-sorting. Fixed by
falling back to the literal string `"unknown"` (`tool = row.get("tool") or "unknown"`) — a visible,
labeled bucket rather than a crash or a silently-unsortable `None` key. Both of these 2 rows also
lack `input_summary`, so the `"unknown"` bucket's `example` field is `None` for the (rare) agent(s)
whose only match is one of these 2 rows — this is disclosed here rather than fabricated; no
synthetic example was substituted. This is noted in `plan.md`'s Deviations section.

No `make knowledge-index-update` run by this implementer step — deferred to whichever later phase
in this run owns the doc-index refresh, consistent with this ticket's own investigator/planner
artifacts already being present before this Implement step began.

**Deviation from plan (Parity phase, post-Implement):** plan.md and investigation.md both
concluded no `docs/parity_ledger/` entry was needed, reasoning that no `src/` file was touched.
The Parity phase's independent review reversed that conclusion: `docs/parity_ledger/
infrastructure.yaml` already tracks agent-monitoring meta-tooling additions as first-class entries
regardless of `src/` involvement (precedent: `INFRA-275`, `INFRA-282`, `INFRA-291`, `INFRA-315`,
all citing `tools/agent-monitoring/*.py` scripts under the "Replay, telemetry, observability,
workers" subsystem definition) — this script fits that same established pattern. A new `verified`/
`P2` entry, `INFRA-402`, was added to `docs/parity_ledger/infrastructure.yaml` citing this script
as `v2_evidence`. The Implement-phase conclusion above (and plan.md's corresponding line) predates
this correction and is superseded by it — recorded here rather than silently edited away.

## Test Summary

- `pytest tests/tools/test_agent_tool_usage_baseline.py -v` — 10 passed (all new tests).
- `pytest tests/tools/test_record_events.py tests/tools/test_validate_agent_monitoring.py tests/tools/test_retrieval_baseline_metrics.py tests/tools/test_agent_monitoring_manifest.py tests/tools/test_monitoring_writer.py tests/tools/test_monitoring_writer_single_source.py tests/tools/test_migrate_monitoring_data.py -v` — 105 passed, 3 skipped (unmodified regression list, all green).
- `pytest tests/tools/ -k "monitoring or agent_tool_usage or retrieval_baseline" -v` — 169 passed, 3 skipped, 1 failed. The 1 failure
  (`test_kgmcp_phase3_pilot_acceptance_measurement.py::test_zero_mutation_of_agent_monitoring_and_manifest_across_full_run`)
  is a pre-existing, environment-dependent resource-time-limit `TimeoutError` (an ML-weight-loading
  full-run measurement test unrelated to this ticket's script), confirmed to fail identically in
  isolation with no relation to this ticket's files — not part of the sanctioned 7-file regression
  list, not touched or modified.

## Files Changed
- `tools/agent-monitoring/agent_tool_usage_baseline.py` (new)
- `tests/tools/test_agent_tool_usage_baseline.py` (new)
- `docs/agent-monitoring/README.md` (added "Agent Tool-Usage Baseline" section)
- `tickets/inprogress/TCK-20260904-AGENT-TOOL-USAGE-BASELINE.md` (this file — Implementation Notes/Test Summary/Files Changed/Completion Summary/Status/AC checkboxes)
- `staging_artifacts/TCK-20260904-AGENT-TOOL-USAGE-BASELINE/plan.md` (Deviations section added)
- `staging_artifacts/TCK-20260904-AGENT-TOOL-USAGE-BASELINE/investigation.md` (pre-existing, created earlier this run — no changes by this Implement step)
- `staging_artifacts/TCK-20260904-AGENT-TOOL-USAGE-BASELINE/test_plan.md` (pre-existing, created earlier this run — no changes by this Implement step)
- `docs/parity_ledger/infrastructure.yaml` (Parity phase: new entry `INFRA-402` added, reversing plan.md/investigation.md's earlier no-parity-entry-needed conclusion — see Implementation Notes deviation above)

## Completion Summary
Implemented `tools/agent-monitoring/agent_tool_usage_baseline.py`, a new read-only script that
aggregates `agent-monitoring/data/*/tools.jsonl` into a per-agent tool-usage table — one row per
live-globbed `.claude/agents/*.md` agent (zero-count rows included explicitly) plus one
`unattributed` bucket for null/non-matching `agent` values, each with per-(agent, tool) call counts
and a verbatim, `truncated: true`-labeled example from `input_summary`. Reuses `load_data_glob`
rather than reimplementing a shard loader, includes a self-checking row-count reconciliation, and
has no file-write capability. Added 10 tests in `tests/tools/test_agent_tool_usage_baseline.py`
(all passing) covering roster/glob correctness, bucketing, zero-count seeding, labeled-example
integrity, real-corpus sanity-check reconciliation, and a real-corpus read-only guard via
git-porcelain diffing. Documented in a new `docs/agent-monitoring/README.md` section. One real
edge case not anticipated by the plan — 2 legacy-shaped rows with no `tool` field — was handled by
bucketing them under a labeled `"unknown"` tool name rather than crashing on an unsortable `None`
dict key; disclosed in Implementation Notes and `plan.md`'s Deviations section, not silently
patched around.

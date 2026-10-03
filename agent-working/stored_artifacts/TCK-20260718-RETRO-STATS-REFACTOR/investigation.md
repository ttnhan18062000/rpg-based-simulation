---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260718-RETRO-STATS-REFACTOR
artifact_type: investigation
tags: []
---

# Investigation — TCK-20260718-RETRO-STATS-REFACTOR

## Current Behavior (file:line refs)

`tools/agent-monitoring/generate_retro.py::generate(runs, events, label, week_str=None, tickets_root=None)`
(L168-434) is a single function that:

1. Computes derived data (L168-232): `ticket_tag_map`, `registry`, `events_by_run`, `total`,
   `done_count`, `gate_fails`, `durations`/`avg_dur`, `agent_counts`/`avg_agents`,
   `gate_counter`, `reason_counter`, `subsystem_tag_runs`/`skill_tag_runs` (via
   `categorize_tag()`), `tier_counts`/`tier_done`/`tier_scoped`.
2. Computes more derived data (L232-241): `agent_stats` (nested Counter by agent/status),
   `legacy_events`/`current_events`/`empty_summaries_current`/`legacy_event_count`/
   `long_summaries`, `slow_runs` (duration_s > 1800).
3. Builds a `lines: list[str]` and appends Markdown section-by-section (L242-434): Run Summary,
   Gate Failure Breakdown, Reason Codes (conditional), Tag Breakdown — Subsystem/Topic
   (conditional), Tag Breakdown — Process/Skill-signal (conditional), Tier Distribution, Agent
   Status Distribution, Spend Proxy — By Phase (conditional on `scored_events`), Spend Proxy —
   By Agent (conditional), Summary Quality, Slow Runs (> 30 min), Notes (static placeholder
   text). Returns `"\n".join(lines)`.

`main()` (L436-471) reads `agent-monitoring/{runs,events}.jsonl`, filters by period
(`--all`/`--days N`/`--week`), calls `generate()`, writes the result to
`agent-monitoring/retro/RETRO-*.md`, calls `_update_index()`.

The `agent-monitoring-retro` skill (`.claude/skills/agent-monitoring-retro/`) invokes this CLI —
did not need to change for this refactor since the CLI's own behavior is preserved unchanged.

## Existing tests (must all continue passing unmodified)

`tests/tools/test_generate_retro.py` — 15 tests, all calling `generate(runs, events, label, ...)`
directly and asserting on substrings/section-ordering of the returned Markdown string. This is
the primary regression guard for this refactor: since these tests pin `generate()`'s exact
observable behavior (not its internals), a refactor that preserves `generate()`'s signature and
output automatically keeps all 15 passing with zero test changes needed. Test names cover:
reason-code section presence/tallying/null-handling, tag breakdown (subsystem + skill,
security cross-reference, non-security no-gate-column, omission when no run_id resolves,
epic/folder/create-tickets/legacy-id exclusion, pre-taxonomy/untagged exclusion, real-registry
proof), spend-proxy by phase/agent (rendering, omission-when-no-score, section-ordering
relative to tag breakdown), reason-code workflow-agnosticism.

## Mechanics/Engine Constraints

None — this is dashboard/reporting tooling, not simulation behavior. No Mechanics Bible chapter
applies.

## Parity Ledger Overlap

None found — `docs/parity_ledger/infrastructure.yaml` has no entry referencing
`generate_retro.py` specifically (grepped). This ticket does not touch `src/` simulation code and
`behavior_changed` should resolve to false for the CLI's own output (byte-identical), so no new
parity entry is expected — the sibling ticket TCK-20260718-AGENTOPS-STATS-API is the one that
adds genuinely new consumable behavior (a JSON API), which may warrant its own entry.

## Prior Work

`tools/tag_report.py::build_json_report()`/`print_report()` (grepped, read in full) is the direct
precedent for this exact "same computation, two output shapes" split — `build_json_report()`
returns a plain dict, `print_report()` renders it to stdout text, both consume the same
`build_tag_rows()` computation. Follow this shape.

## Risks and Open Questions

- Dataclass vs TypedDict for the structured result: `generate_retro.py` and sibling
  `tools/agent-monitoring/*.py` modules use plain dicts/Counters throughout, no existing
  dataclass/TypedDict precedent in this specific module. `tag_report.py`'s
  `build_json_report()` returns a plain `dict`. Decision: follow that precedent — return a plain
  `dict` (JSON-serializable directly, matches this codebase's established reporting-tool
  convention) rather than introducing a new dataclass/TypedDict pattern this module doesn't
  already use. The consuming ticket (AGENTOPS-STATS-API) will convert this dict into a typed
  Pydantic model at the API boundary — that boundary is where typing is enforced in this
  codebase (`models.py`), not inside `tools/`.
- The `## Notes` section's static placeholder text ("_Fill in after reviewing..._") is
  human-authored prose, not computed data — it stays in the Markdown-rendering function, not the
  computation function, since there's nothing to extract.
- `_update_index()` (L479-505) is untouched — it reads `runs.jsonl` independently and writes
  `agent-monitoring/retro/index.md`, unrelated to `generate()`'s own computation.

## Anti-Drift Hazards

- Must not change `fmt_pct()`'s integer-percent rounding behavior (`100 * n // total`) — several
  existing tests assert exact percentage strings (e.g. `"50%"`).
- Must not reorder Markdown sections — `test_retro_spend_breakdown_placement_does_not_disturb_tag_breakdown_sections`
  asserts a specific section ordering via `report.index(...)` comparisons.
- The conditional-render pattern (sections only appear when there's data, e.g. Reason Codes,
  Tag Breakdowns, Spend Proxy) must be preserved exactly — several tests assert section
  *absence* under empty-data conditions, not just presence under populated conditions.

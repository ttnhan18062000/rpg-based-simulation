---
status: active
layer: observability
authority: P1
audience: developer
tags: [agent-monitoring, observability]
---

# Agent Monitoring

Observability layer for the Claude Code AI agent workflow. Tracks workflow runs and per-agent actions for weekly retrospectives.

**Scope:** Claude Code agents only (implement-ticket workflow, etc.). Not the RPG simulation engine's Grafana/Loki/Prometheus stack.

## What It Captures

- Which workflow ran and what its outcome was (`runs.jsonl`)
- Which agents were called, in which phase, and what each did in one sentence (`events.jsonl`)
- Every individual tool call during a session: tool name, input summary, status, duration (`tools/tools-YYYY-Www.jsonl`, one shard file per UTC ISO week)
- Per-agent tool call counts derived from `tools.jsonl`, stored as `tool_call_count` on each event
- A monotonic cost-proxy score per agent event, derived from `tools.jsonl` (Bash duration + Agent spawn count + edit-tool call count), stored as `cost_proxy_score` — an explicit proxy, not real token/dollar cost (see schema.md)
- Weekly retro reports derived from the above

## What It Does NOT Capture

- **Token counts** — the workflow `agent()` call returns the agent's output content only; the underlying API usage (`input_tokens`, `output_tokens`) is consumed by the Claude Code runtime and never forwarded to the workflow script. There is no workaround short of a platform change from Anthropic.
- Agent internal reasoning or chain-of-thought
- Simulation engine telemetry

**2026-07-19 — `cost_proxy_score` calibration finding.** The platform-blocked gap above was
reconfirmed independently against this machine's own local session transcripts (33 files, 26,911
assistant turns with a real `usage` block — `isSidechain` is `false` on every one of them, meaning
zero subagent-turn transcripts exist locally either). A regression fit at the correct grain (one
turn's tokens against that same turn's own tool calls) found no usable signal (R²≈0.0000); a fit at
session-aggregate grain found a strong but domain-mismatched signal (R²=0.93, `edit_count` the
dominant single predictor at r=0.91) — not adopted, since it measures the orchestrator's whole
session, not the per-subagent/per-phase footprint `compute_cost_proxy_score()` actually scores.
Net: `edit_count` is a weak, unconfirmed prior for `W_EDIT` being under-weighted relative to
`W_AGENT` in the shipped formula — not adopted as a weight change. Recalibration remains blocked on
better ground-truth data at the right grain, not on missing investigation. Full evidence trail:
`experiments/cost_proxy_calibration/RESULTS.md`.

**`tools/agent-monitoring/weight_sensitivity_check.py`** (promoted from the experiment above by
`TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE`) is the **required check before ever proposing a
`cost_proxy.py` weight change** — it recomputes `cost_proxy_score` for every real `(run_id, seq)`
group under two weight sets and compares the resulting spend-by-phase/spend-by-agent rank order,
so a candidate reweighting's real impact is measured before it ships, not discovered after. See
`make agent-monitoring-weight-check` below.

## Baseline Metrics Snapshot (one-off)

`tools/agent-monitoring/retrieval_baseline_metrics.py` is a separate, one-off/periodic
read-only baseline-snapshot script (distinct from the recurring weekly retro above) that prints a
JSON report over the same `runs.jsonl`/`events.jsonl`/`tools/tools-YYYY-Www.jsonl` sources. Report sections:
`context_tokens`, `search_count`, `raw_investigation_count`, `duration`, `gate_outcome`,
`review_rework`, `legacy_schema_notes`. Every derived/proxy section states its own computation and
limits inline via a `derivation`/`disclosure`/`reason` field — never a silent number. See
`docs/parity_ledger/infrastructure.yaml`'s `INFRA-292` entry for exact source line-range
provenance of each section.

## Knowledge Gateway MCP Phase 0 Measurement Baseline (one-time, separate from both cadences)

`tools/agent-monitoring/kgmcp_baseline_corpus.py` defines a fixed, versioned 7-entry
representative-query corpus for the Knowledge Gateway MCP proposal's Phase 0 measurement baseline
(`docs/plans/knowledge-gateway-mcp-proposal.md` §18/§20). The real, recorded-from-a-real-run
direct-tool baseline (Context Search + Graphify latency, tool-call counts, sources recalled,
serialized-token estimate per query) is committed at
`tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json`, produced once by
`tools/agent-monitoring/kgmcp_baseline_runner.py`. This is a **one-time Phase-0 recording**,
distinct from both `retrieval_baseline_metrics.py`'s periodic snapshot and `generate_retro.py`'s
recurring weekly cadence above — it must never be described as feeding either of those. See
`docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` for the 5 latency
measurement-point definitions, the fixture-derived promotion thresholds, and the repeated-demand
estimation design.

**2026-08-14 — `search_count`/`raw_investigation_count` now also feed the recurring cadence**
(`TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`). `SEARCH_TOOL_NAMES`,
`build_search_count_section`, and `build_raw_investigation_count_section` were relocated into
`generate_retro.py` (this module now re-imports them) to resolve a circular-import constraint and
let `generate()` render a new `## Search & Investigation Effort` section plus per-week Search
Calls / Read Calls trend columns on `agent-monitoring/retro/index.md` — see
`docs/guides/agent_monitoring.md`'s Report Sections table. This shares the underlying *numbers*
between the two tools; it does not merge the two *cadences* — `retrieval_baseline_metrics.py` still
never writes into `agent-monitoring/retro/`, and remains the one-off JSON snapshot described above.

## Security Gate Firing Check

`tools/agent-monitoring/security_gate_firing_check.py` is a separate, read-only pass/fail check
(distinct from `compute_retro_metrics()`'s aggregate `tag_breakdown_skill` count above) that
classifies every `security`-tagged ticket into `missed` (a `DONE` run with no `Security-Review`
event ever recorded — the gate should have fired and didn't), `clean` (a `DONE` run with a
`Security-Review` event or `SECURITY_BLOCKED` status somewhere in its history), or `pending` (not
yet reached `DONE`, not evaluable). Exits `1` if `missed` is non-empty. Built by
`TCK-20260805-SECURITY-GATE-FIRING-MONITOR` after `TCK-20260731-GATE-BYPASS-HARDENING` proved that
a gate's code being structurally correct does not guarantee it fired on a real historical run.

## Skill Usage Metric

`tools/agent-monitoring/skill_usage_metric.py` is a separate, read-only per-skill invocation-count
tool (distinct from `compute_retro_metrics()`'s `tag_breakdown_skill` above, which counts
tag-driven gate hits, not raw invocations) that answers "how many times was each skill actually
invoked" by filtering `tools.jsonl` to `tool == 'Skill'` and extracting the skill name from
`input_summary` via regex (that field is a Python dict-repr string, not JSON — `json.loads()` on
it raises). Reports `per_skill`, `per_skill_per_run`, and an `unparseable` count for any record the
regex can't match. Built by `TCK-20260805-SKILL-USAGE-METRIC` after this session's own skill-usage
audit found this question previously required ad hoc regex against raw `tools.jsonl` every time.

**2026-08-15 — `build_skill_usage_section` now also feeds the recurring cadence**
(`TCK-20260810-SKILL-USAGE-RETRO-TRACKING`). `build_skill_usage_section` was relocated into
`generate_retro.py` (this module now re-imports it) to resolve the same circular-import constraint
as the `search_count`/`raw_investigation_count` precedent above. `generate()` now renders a
`## Skill Usage` section with two subsections of distinct scope: a period-scoped per-skill
invocation count (trended report-over-report via `agent-monitoring/retro/index.md`'s new Skill
Invocations column) and an all-time, two-bucket zero-invocation flag
(`compute_zero_invocation_skill_flags` — `flagged_stale` for skills with a real `date_added` past
a 14-day grace period, `flagged_unknown_age` for skills with no recorded `date_added`, fail-open by
design so a skill like `backend-testing`'s real pre-`TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED`
state would have been correctly flaggable). The flag subsection is only computed/rendered when the
caller explicitly passes `all_tools` to `generate()` — never inferred from the period-scoped
`tools` argument, so ordinary `--week`/`--days` callers cannot accidentally trigger a real
`.claude/skills/` filesystem scan. Visibility only — no skill is auto-invoked or auto-deprecated
based on this flag.

## Done-Ticket Monitoring Coverage Audit

`tools/agent-monitoring/done_ticket_monitoring_coverage.py` is a separate, read-only audit
checking whether every ticket under `tickets/done/` has at least one matching `run_id` record in
`runs.jsonl`. Reports `covered`/`missing`/`unparseable` ticket lists. Deliberately reads
`runs.jsonl` directly rather than through `generate_retro`'s SQLite-index path — even after
`TCK-20260811-AGENT-MONITORING-INDEX-SILENT-STALENESS` taught that path to rebuild on staleness
(any source JSONL newer than the index's own mtime), a mtime-comparison rebuild is still only
as fresh as the last time something happened to call `_load_runs_and_events()`, not truly
up-to-the-second, and this audit's whole purpose (catching a just-closed ticket with no
monitoring record) needs the direct-read guarantee regardless. Built by
`TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT` after
`TCK-20260805-CODEX-EVENT-TRACE-GAP-INVESTIGATION` found 2 `DONE` tickets with zero monitoring
records. The full audit found 719 of 1,303 tickets missing coverage, but this is **not** an
ongoing systemic bug — the earliest real `runs.jsonl` record is dated 2026-06-07 (the
`TCK-20260607-MON-CAPTURE` ticket that built agent-monitoring capture itself), so every ticket
dated before that structurally cannot have a record; bucketing the remainder by month shows a
clean rollout-adoption curve (124 missing in the June 2026 rollout month, 24 in July, converging
to a single isolated miss in August) rather than a flat ongoing rate.

## Navigation

| Doc | Contents |
|---|---|
| [schema.md](schema.md) | Full field reference for the `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` per-week layout |
| [../guides/agent_monitoring.md](../guides/agent_monitoring.md) | How to run the weekly retro loop |
| [agent-monitoring/README.md](../../agent-monitoring/README.md) | Quick-reference schema and data files |

## Quick Start

```bash
# Build the derived SQLite index (required by query.py/validate.py; generate_retro.py
# builds it on demand if missing or stale — see schema.md's "Derived SQLite Index" section):
make agent-monitoring-index

# After some workflow runs have completed:
make agent-monitoring-retro         # generate this week's report
open agent-monitoring/retro/RETRO-$(date +%Y-W%V).md

# Validate integrity
make agent-monitoring-validate

# Query events
make agent-monitoring-query ARGS="--agent investigator --days 7"

# Before proposing any cost_proxy.py weight change:
make agent-monitoring-weight-check ARGS='--candidate-weights "{\"bash\": 0.01, \"agent\": 100, \"edit\": 10}"'
```

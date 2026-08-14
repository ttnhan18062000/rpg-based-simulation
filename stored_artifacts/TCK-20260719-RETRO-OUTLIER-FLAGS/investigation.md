---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260719-RETRO-OUTLIER-FLAGS
artifact_type: investigation
tags: []
---

# Investigation — TCK-20260719-RETRO-OUTLIER-FLAGS

## Current Behavior

`generate_retro.py::compute_retro_metrics()`'s return dict has no outlier-flagging of any kind
before this ticket. `slow_runs` exists (a fixed 1800s absolute threshold on `duration_s`) but
answers a different question ("was this literally a long time") than the proposal's request
("was this way more than similar runs typically take"). D25 (`experiments/audit_expansion/PROPOSAL.md`,
F2/F3) directly measured real production data and found a ~2000x `duration_s` spread (25s to
~14h) and a >10x `cost_proxy_score` spread within the same phase/agent pair, both with "zero
recorded investigation" — nothing currently flags either.

`runs.jsonl` schema confirmed (via `docs/agent-monitoring/schema.md` + direct field read): no
`phase` field on a run record, only `tier`. The proposal's literal wording ("duration_s > 3x the
phase median") does not map onto the real schema — a genuine Plan-phase decision, not assumable.

`src/api/agent_ops_dashboard/ingest.py::get_agent_monitoring_stats()` (read directly): builds
`AgentMonitoringStats` via `RunSummaryStats(**metrics["run_summary"])`,
`GateFailureBreakdown` etc. — explicit, per-field typed submodel construction, never
`AgentMonitoringStats(**metrics)`. A new top-level `outliers` key added to `compute_retro_metrics()`'s
return dict is silently invisible to the dashboard unless `models.py`/`ingest.py` are separately
updated. Confirmed by reading both files directly, not assumed from the ticket body alone.

## Mechanics/Engine Constraints

None — agent-monitoring is orchestration/observability tooling, not simulation gameplay.

## Parity Ledger Overlap

None pre-existing. This is a real, observable behavior change (new report section, new API output
key) with no `src/` file touched — same category as `INFRA-281`/`282`/`283` (the three immediately-
preceding tickets in this same batch), which is the direct precedent for adding a
`docs/parity_ledger/infrastructure.yaml` entry despite no Mechanics Bible chapter applying.

## Prior Work

`TCK-20260718-RETRO-STATS-REFACTOR` extracted `compute_retro_metrics()` as a pure, typed-JSON-
returning function — this ticket extends its return shape, following that same pattern (plain
dict, no Markdown formatting inside the computation function). `TCK-20260719-PHASE-AGENT-CASE-FOLD`
(immediately preceding ticket in this batch) added `_normalize_phase()`/`_normalize_agent()` — this
ticket directly reuses `_normalize_phase()` for cost_proxy_score's phase-grouping, a deliberate
synergy (a casing-fragmented phase would otherwise silently split one real outlier-detection group
into several too-small groups). `experiments/audit_expansion/PROPOSAL.md`'s D25 dimension is the
original source of the "zero recorded investigation" framing and the exact 34,837 cost_proxy_score
example this ticket's fix, once implemented, automatically re-surfaced as a live 444.1x outlier —
confirmed by direct end-to-end run against the real corpus.

## Risks and Open Questions

None outstanding — both Plan-phase decisions the ticket explicitly required (median basis;
relationship to `slow_runs`) are made and documented in `plan.md`/the ticket's Implementation
Notes.

**Found but explicitly out of scope**: running `generate_retro.py --days N` crashes on a
`runs.jsonl` record with a non-string `start_ts` — confirmed pre-existing via `git stash` (crashes
identically with this ticket's changes removed). Not fixed here; worth a future ticket.

## Anti-Drift Hazards

- Outlier detection must exclude `None`/missing values from BOTH the flagging candidate set AND
  the median basis — never coerce to 0 (would corrupt every group's median and could produce
  false-positive or false-negative flags).
- A group below `_OUTLIER_MIN_GROUP_SIZE` must be skipped entirely, not flagged against a
  near-arbitrary 1-2-point "median."
- `cost_proxy_score` grouping must use the *normalized* phase (reusing
  `TCK-20260719-PHASE-AGENT-CASE-FOLD`'s helper), never the raw un-normalized value — otherwise
  casing fragmentation directly undermines the outlier groups' own sample sizes.
- Must not modify `src/api/agent_ops_dashboard/models.py` or `ingest.py` — explicitly out of scope
  per the ticket's own Out of Scope section; the new key stays dashboard-invisible until a
  separate, deliberate future ticket wires it through.

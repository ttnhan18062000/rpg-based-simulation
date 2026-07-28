---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, agent-monitoring]
---

# Default Packet Scenario Criteria Decision — TCK-20260728-DEFAULT-PACKET-CRITERIA

Resolves **Open Decision 1** from
`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`
(tracked by epic `TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC`):

> Which scenarios and phases justify a default context packet, and what are
> their initial token budgets?

This document **decides and evidences**. It implements nothing — no packet builder, retrieval
code, or workflow phase change is created or modified as part of landing it. All claims below are
grounded in the real, freshly-run output of `tools/agent-monitoring/retrieval_baseline_metrics.py`
(TCK-20260728-RETRIEVAL-BASELINE-METRICS) over the live `agent-monitoring/*.jsonl` corpus, not a
fresh guess.

---

## 1. What the idea doc's Scenario table proposed

The idea doc's Working-Process Change section (`idea_context_efficient_agent_retrieval_observability.md`,
"This phase must be **scenario-aware**" table) names 5 scenarios, each with a *proposed* default
packet content, but assigns no verdict on whether a default packet is justified at all, and no
budget:

| Scenario | Idea doc's proposed default packet contents |
|---|---|
| Small bugfix | Ticket/issue, affected symbols, nearest tests, active local contract |
| Ticket implementation | Ticket ACs, scoped design/ADR, affected symbols/tests, relevant prior ticket |
| Code review | Diff/changed paths, relevant contract, paired tests, risk checklist |
| Architecture/planning | Active plans/ADRs, registry entries, Graphify path/community evidence |
| Incident/monitoring investigation | Incident/ticket, derived monitoring query results, relevant writer/reader code |

This decision resolves the missing verdict + budget-tier gap.

---

## 2. Per-Scenario Verdict Table

Every citation below is a literal field from `retrieval_baseline_metrics.py`'s real output,
captured by running `python3 tools/agent-monitoring/retrieval_baseline_metrics.py` against the
live corpus on 2026-07-29 (721 `runs.jsonl` records; 118 distinct `run_id`s with at least one
qualifying search call, `search_count.total = 1694`).

| Scenario | Justifies default packet? | Citation (real field) | Rationale |
|---|---|---|---|
| Small bugfix | **Yes** | `search_count.per_run` — hotfix-shaped tickets consistently cluster at the low end: `TCK-20260627-P0A-ADVENTURE-FLAG: 2`, `TCK-20260627-P1A-REJECTION-BACKOFF: 2`, `TCK-20260627-P1E-DOMAIN-INVENTORY: 2`, `TCK-20260614-ARTIFACT-BUDGET-REG: 1`, `TCK-20260614-WORLDSCEN-PERSPECTIVES: 1`. 53 of 118 ticket-scoped runs (45%) sit at ≤2 qualifying searches. | A scenario whose observed follow-up-search burden is already this low is exactly the case a small, cheap default packet can satisfy without measurable loss — there is little search volume left to "save" by under-provisioning, and little risk of over-provisioning since so few runs need more. |
| Ticket implementation | **Yes** | `gate_outcome.status_breakdown` — `DONE: 622` out of 721 total `runs.jsonl` records is overwhelmingly the dominant terminal state, and the corpus-wide median of `search_count.per_run` (excluding the `unattributed` interactive bucket) is 3. | This is the modal scenario in the entire corpus — the standard `implement-ticket` workflow accounts for the large majority of recorded runs (`DONE: 622`), so a default packet tuned to its typical (median = 3) search burden benefits the most work by volume. |
| Code review | **Deferred** | `duration.rows[].flag` — all 167 `duration` rows carry `"flag": "pause-contaminated"`, meaning no clean per-phase cost signal exists to isolate Review-phase behavior specifically. | `gate_outcome.status_breakdown` shows Review/Architecture-Verify-triggered gate fails are rare in aggregate (`NEEDS_CHANGES: 4`, `BLOCKED: 1`), but this tool has no way to attribute search volume or duration to the Review phase in isolation — see §3 Scoped Limitation. Deferring avoids fabricating a review-specific budget from data that cannot actually isolate the review phase. |
| Architecture-planning | **Yes** | `search_count.per_run` — the highest-volume outliers in the ticket-scoped corpus are architecture/refactor-shaped work: `TCK-20260614-WORLDMOD-PARAMS: 143`, `TCK-20260623-FIX-WORLDASSEMBLY: 69`, `TCK-20260630-SIMQ-WIRE-KERNEL: 38`, `TCK-20260619-E41A-GROUP-LIFECYCLE: 34`, `TCK-20260626-FIX-DESIGN-PATTERNS: 34`, `TCK-20260628-E-LONGRUN-REGRESSION: 32`. | Architecture/planning-shaped tickets show search volume an order of magnitude above the median (3) and above the small-bugfix cluster (1-2) — this scenario justifies a default packet, but scaled to a materially larger budget than the other two "yes" scenarios (see §3). |
| Incident-monitoring investigation | **Deferred** | `gate_outcome.status_breakdown` — the breakdown has no dedicated status value or workflow tag for incident/monitoring-investigation runs; they are indistinguishable from other `implement-ticket`/ad hoc runs in this coarse aggregate. | Combined with `duration.rows[].flag`'s corpus-wide `pause-contaminated` caveat, there is no reliable way today to isolate which historical runs were actually incident-investigation-shaped versus ordinary ticket work, so no scenario-specific proxy basis can be cited without inventing an attribution this tool does not provide. Deferred pending a scenario-tagging mechanism — see §3. |

---

## 3. Token Budgets Are Directional, Not Measured — and a Scoped Limitation

### 3.1 `context_tokens` is confirmed unavailable

`retrieval_baseline_metrics.py`'s own `build_context_tokens_section()` returns:

```json
{
  "status": "unavailable",
  "reason": "Real token/context-size telemetry is platform-blocked and is not recorded anywhere in agent-monitoring/*.jsonl.",
  "citation": "docs/agent-monitoring/schema.md — 'What is not recorded' section"
}
```

This matches `docs/agent-monitoring/schema.md`'s own "What is not recorded" section verbatim:

> **Token counts** are not recorded. The workflow `agent()` call returns the agent's structured
> output only; API usage metadata (`input_tokens`, `output_tokens`) is consumed internally by the
> Claude Code runtime and is not forwarded to the workflow script. There is no field for it and no
> workaround within the current platform.

Three independent confirmations now exist (schema.md, the baseline tool's own output,
`cost_proxy.py`'s docstring per the prior investigation) that no measured token count exists in
this corpus. Accordingly, **no numeric token-budget figure is asserted anywhere in this document**
— any such figure would be fabricated. Budgets below are stated as directional/relative **tiers**
(small / medium / large), each named against the specific proxy signal that grounds it.

### 3.2 Initial budget tiers (directional, proxy-grounded — not measured tokens)

| Scenario | Tier | Proxy basis |
|---|---|---|
| Small bugfix | **Small** | `search_count.per_run` volume — observed cluster at 1-2 qualifying searches for hotfix-shaped tickets. |
| Ticket implementation | **Medium** | `search_count.per_run` corpus median (3) combined with `gate_outcome.status_breakdown`'s dominant `DONE: 622` share — the modal scenario gets a moderately larger allowance than the small-bugfix floor, sized to its typical (not outlier) observed search burden. |
| Architecture-planning | **Large** | `search_count.per_run` high-volume outliers (32-143 qualifying searches) — an order of magnitude above the medium tier's median, justifying the idea doc's own allowance ("Larger budget allowed, but still cited and deduplicated") for this scenario. |
| Code review | *(deferred — no tier assigned)* | Not assigned pending the Scoped Limitation below. |
| Incident-monitoring investigation | *(deferred — no tier assigned)* | Not assigned pending the Scoped Limitation below. |

These tiers describe *relative* packet size ordering (small < medium < large) grounded in
proxy search-volume behavior actually observed in the corpus — they are a starting allocation for
Phase 5 shadow-packet calibration, not a performance guarantee, and must not be read as a token
count.

### 3.3 Scoped Limitation — no per-phase aggregation exists today

`agent-monitoring/events.jsonl` records do carry both `phase` and `ts` fields per event (confirmed
directly, e.g. `{"run_id":"TCK-20260728-CONTEXT-PACKET-SCHEMA","seq":6,"phase":"Architecture-Verify", ...,"ts":"2026-07-28T17:25:33Z"}`
from the live file). However, **no function in `retrieval_baseline_metrics.py` aggregates
`events.jsonl`'s `phase`+`ts` fields into a per-phase (as opposed to per-run) breakdown** —
`build_search_count_section()` groups by `run_id` only (via `tools.jsonl`'s `run_id` field, itself
threaded from the sidecar, not `events.jsonl`'s `phase`), and `build_duration_section()` reports
one row per `run_id` using `runs.jsonl`'s whole-run `duration_s`, not a per-event or per-phase
duration derived from `events.jsonl`'s `ts` deltas.

**This gap directly blocks two parts of the per-scenario verdict above**: the Code Review and
Incident-monitoring-investigation scenarios were both marked **Deferred**, specifically *because*
no tool today can isolate a phase-scoped (Review-phase-only, or investigation-workflow-only)
search/duration signal from the corpus — everything currently reported is run-scoped. It does
**not** block the Small bugfix, Ticket implementation, or Architecture-planning verdicts above,
since those verdicts rely on whole-run `search_count.per_run` values, which the tool already
computes correctly at the run granularity those three scenarios operate at (a small bugfix, a
standard ticket implementation, and an architecture-planning ticket are each themselves single
runs, not sub-phases of a run).

This gap is stated here as a scoped limitation of **this decision only** (Open Decision 1). It is
explicitly **not** used to resolve Open Decision 5 (sample-size/thresholds for promoting a scenario
from advisory to default) — that remains open, tracked separately in the epic ticket, and this
document takes no position on it.

---

## 4. Resolution

**Open Decision 1 is resolved.** Of the idea doc's 5 named scenarios:

- **Small bugfix**, **Ticket implementation**, and **Architecture-planning** justify a default
  context packet today, at **small**, **medium**, and **large** directional tiers respectively —
  each grounded in `search_count.per_run` volume patterns actually observed in the live corpus
  (never a fabricated token count, since `context_tokens` remains platform-unavailable per §3.1).
- **Code review** and **Incident-monitoring investigation** are **deferred** — not because their
  search/duration behavior was measured and found unjustified, but because no existing tool
  isolates a phase-scoped or investigation-scoped signal from the run-scoped data this corpus
  currently provides (§3.3's Scoped Limitation). Assigning either scenario a tier today would mean
  inventing a proxy basis this tool does not produce.

`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`'s
Open Decisions list is not directly edited by this ticket (mirrors the precedent set by Open
Decisions 2 and 3, both resolved via a standalone decision doc rather than an idea-doc edit) —
resolution status is instead recorded in
`tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`'s Assumptions/Open Questions
section, marking Open Decision 1 **RESOLVED** and pointing here, in the same style as that
ticket's existing Open Decision 2 / Open Decision 3 entries.

Any future ticket building a real packet builder (Phase 5, Selective workflow adoption) should:
(a) start with the Small/Medium/Large tiers above for the three "Yes" scenarios; (b) treat Code
Review and Incident-monitoring investigation as candidates requiring their own phase-aggregation
tooling first, not as scenarios to default-enable from this decision alone; and (c) re-derive
tiers from fresh `retrieval_baseline_metrics.py` output rather than treating the numbers cited here
as permanently fixed, since the corpus grows with every run.

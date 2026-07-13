---
status: historical
layer: ai
authority: P2
audience: developer
maturity: shipped
date: 2026-07-03
archived: 2026-07-13
tags: [idea, agent-infrastructure, observability, cost, tokens, model-routing]
---

# Idea: Agent Spend & Token Observability Layer

**Archived:** 2026-07-13 — Tier 1 shipped by `TCK-20260708-AGENT-COST-OBSERVABILITY`
(`tickets/done/`); Tier 2 (`self_reported_scope`) deliberately deferred as stretch-only (no ticket,
no demonstrated need yet) and Tier 3 remains platform-blocked, both by design rather than left
incomplete; this document is the historical design reference.

> **Maturity: SHIPPED (Tier 1).** Implemented by `TCK-20260708-AGENT-COST-OBSERVABILITY`
> (`tickets/done/`) under `TCK-20260708-AGENT-INFRA-HARDENING-EPIC`. `cost_proxy_score` is computed
> in `writeMonitoring`'s existing single pass over `tools.jsonl` (weighted Bash `duration_ms` +
> `Agent`-spawn count + edit-tool-call count; concrete starting weights `w_bash=0.001`, `w_agent=50`,
> `w_edit=1`, sized against real data rather than left as this doc's original placeholders), written
> additively to `events.jsonl`, documented as an explicit non-dollar proxy in
> `docs/agent-monitoring/schema.md`, and surfaced as a spend-by-phase/spend-by-agent breakdown in
> `make agent-monitoring-retro`'s report — closing this doc's own "Where it surfaces" section and the
> audit's Recommendation 2. **Tier 2 (`self_reported_scope`) was deferred, not ticketed** — the
> ticket's own Scope framed it as stretch-only, and there is no concrete retro use case yet demanding
> it; it remains available as a natural pickup once Tier 1's data has actually motivated a need for
> it in practice. Tier 3 remains platform-blocked, unchanged. The sibling idea's `verified_by` field
> (see below) landed via `gate-determinism-followups` (2026-07-05) and this idea's own vocabulary-cleanup
> precondition landed via [`idea_agent_monitoring_schema_enforcement.md`](idea_agent_monitoring_schema_enforcement.md) (archived — shipped)
> (`TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT`), both satisfied before this ticket ran.
> Originally raised directly from [`docs/ai/agent_infrastructure_audit.md`](../../../ai/agent_infrastructure_audit.md)
> (2026-07-03 score: 8.0/10 — the audit calls out lack of cost telemetry by name in both
> Strengths-adjacent gaps and Recommendation 2). Sibling idea to [`idea_agent_gate_determinism.md`](idea_agent_gate_determinism.md) (archived — shipped).

---

## Problem

`docs/agent-monitoring/schema.md` states the gap outright, in its own words:

> **Token counts are not recorded.** The workflow `agent()` call returns the agent's structured output only; API usage metadata (`input_tokens`, `output_tokens`) is consumed internally by the Claude Code runtime and is not forwarded to the workflow script. There is no field for it and no workaround within the current platform.

This isn't a documentation gap — it's a real blind spot. The pipeline that runs this project's development work fans out to 11 subagents across up to 9 gated phases per ticket, and `implement-epic` chains that across every ticket in a folder. There is currently no way to answer basic questions that matter for scaling AI-first work responsibly:

- Which phase or agent is actually expensive — is `investigator` doing proportionally more work than `ticket-scoper`, or about the same?
- Is a batched `implement-epic` run across 10 tickets worth its spend relative to running them by hand?
- Once cheap, machine-checkable gates exist (see the sibling idea's static verifiers), is it worth routing them to a smaller model instead of the primary one — and is there even a cost delta to justify the engineering effort?

Right now, `agent_count` (run-level) and `tool_call_count` (event-level, already computed from `tools.jsonl`) are the only proxies, and neither was designed to answer a cost question — they were designed to answer a complexity question.

---

## Idea

Since real token/cost data is platform-blocked today, build a **tiered proxy that degrades gracefully to real data if the platform ever forwards it** — rather than a one-off workaround that has to be thrown away later.

### Tier 1 — computed proxy, no agent cooperation required (available now)

`tools.jsonl` already has `duration_ms` per tool call and is already joined to `events.jsonl` by `run_id` + `seq`. `writeMonitoring` can compute a `cost_proxy_score` per event today, purely from existing data:

```
cost_proxy_score = w_bash · Σ(duration_ms where tool=Bash)
                 + w_agent · count(tool=Agent)      # nested spawns are the real cost multiplier
                 + w_edit  · count(tool in {Read,Edit,Write,MultiEdit})
```

Not a dollar figure — a *comparable, monotonic* ranking. Enough to answer "which phase is consistently the most expensive across tickets" in the weekly retro without waiting on Anthropic.

### Tier 2 — agent self-reported scope (available now, unverified)

Each agent's structured return value already includes a free-text `summary` (self-reported, per `events.jsonl` schema). Extend this pattern: add an optional `self_reported_scope` — e.g. `files_read: 12, files_written: 3, reasoning_depth: deep` — the same class of signal as `summary`, with the same trust ceiling. Cheap to add, useful as a second, independent axis against Tier 1's tool-count-derived proxy — if the two disagree a lot for one agent, that's itself informative (either the agent is misreporting, or the tool-count proxy is a bad fit for that agent's work).

### Tier 3 — real usage data (aspirational, blocked on Anthropic platform support)

If the Claude Code runtime ever forwards `input_tokens`/`output_tokens`/`cost_usd` to workflow scripts, it should be an **additive field** on the same `events.jsonl` record, not a schema rewrite. Designing Tiers 1–2 as an explicit proxy (not disguised as real data) makes this swap trivial later.

### Where it surfaces

The proxy is only worth building if it changes a decision. The concrete payoff: `make agent-monitoring-retro` gains a **spend-by-phase / spend-by-agent** breakdown in the generated report, alongside the existing pass/fail retrospective. That's the artifact a human actually reads to decide, e.g., "`architecture-reviewer` costs 3x `ticket-scoper` — is that proportional to the value it catches, or is its prompt bloated?"

Longer-term, once cost-by-agent-type is visible for a few weeks, it becomes the evidence base for a **model-routing policy**: route the machine-checkable half of a gate (once split out per the sibling determinism idea) to a cheaper model, keep the primary model for the judgment half. That's a genuine AI-first lever — spending model capability where it's actually needed instead of uniformly everywhere.

---

## Natural Integration Points

| Existing component | How this idea attaches |
|---|---|
| `docs/agent-monitoring/schema.md` — "What is not recorded" | This idea is the direct answer to that documented gap; the schema doc should gain a `cost_proxy_score` / `self_reported_scope` field spec once implemented |
| `agent-monitoring/README.md` — "What It Does NOT Capture" | Token counts stay listed as not captured (still platform-blocked); the proxy should be described as a proxy, not silently presented as equivalent |
| `writeMonitoring` (workflow finalize step) | Natural place to compute Tier 1 — it already reads `tools.jsonl` to derive `tool_call_count` today |
| `make agent-monitoring-retro` | Where the payoff has to show up, or this is telemetry nobody looks at |
| [`idea_agent_gate_determinism.md`](idea_agent_gate_determinism.md) (archived — shipped) | Its `verified_by` field tells you which half of a gate is static vs. LLM-judged — exactly the split needed before a model-routing decision is defensible |

---

## Open Questions

- Is a unitless proxy score actionable at all, or does it need at least a rough per-model $/call constant to make retro numbers feel real rather than abstract?
- How much should `self_reported_scope` be trusted, given it has no verification mechanism — the same open question the determinism idea raises for LLM-judged gates?
- If Anthropic ships real usage forwarding, does the proxy get deprecated immediately, or kept as a cheap sanity cross-check against the real numbers?
- Does a model-routing policy need its own quality-regression audit (comparing gate outcomes on the cheaper model against historical outcomes) before anyone trusts it in the critical path?

---

*Raised: 2026-07-03, directly from the agent infrastructure audit's Recommendation 2. Deferred pending a decision on whether Tier 1 alone is worth implementing before Tier 2.*

---
status: idea
layer: ai
authority: P2
audience: developer
maturity: idea
date: 2026-06-20
tags: [idea, cognition, observability, decision-trace, ring-buffer, strategic-ai]
---

# Idea: Intention Log as First-Class Runtime Object

> **Maturity: IDEA** — Not scheduled. Consider before or alongside E43 Social Memory.

> **Status note (2026-07-02):** the write side ("Core concept" below) shipped as E22 — `decision_trace.jsonl`, tick-index sidecar, REST endpoints (`docs/observability/decision_trace_contract.md`). Remaining live scope is the read side: ring buffer, Chronicle surprise signal, social-memory annotation, plus audit item P1-H. Before scheduling any of it, read the SimQ interaction and process-isolation constraints in `docs/plans/observability_process_isolation.md` §4 — the ring buffer is a behavior-feedback feature (durable cognitive state, anchor recalibration required). The shipped writer's hot-path IO violation is remediated by `TCK-20260702-OBSISO-TRACE-ASYNC`.

---

## Problem

The engine currently records *what* entities do (route choices written to `simulation_events.jsonl`), but has no structured representation of *why* they chose it. Decision rationale exists only as transient scoring state that vanishes after each tick. This creates three gaps:

1. **Opacity**: the Chronicle (E51) and social systems (E43) must reconstruct intent from outcome sequences — a lossy process that cannot distinguish between "chose combat because brave" and "chose combat because cornered."
2. **Debuggability**: calibrating scoring weights (E11D) requires manual inspection of tick-by-tick scoring, not a queryable trace.
3. **Strategic AI blindness**: strategy layer cannot query "what did I recently try and why did I abandon it?" — the information is not retained.

---

## Idea

Promote the per-tick decision trace to a **first-class durable object** — a typed, indexed, queryable record of intent, not just outcome.

### Core concept

At the end of each tick's route evaluation, serialize the entity's top-N scored options into a structured `IntentionSnapshot`:

```
IntentionSnapshot:
  entity_id: str
  tick: int
  candidates: List[RouteCandidate]
    route_kind: str
    score_breakdown:
      urgency: float
      benefit: float
      personality_bias: float
      confidence_bonus: float
      risk_penalty: float
      blocker_penalty: float
    selected: bool
  final_choice: str
```

Persist to `decision_trace.jsonl` with a byte-offset sidecar so strategic AI can query O(1) by tick.

### What this unlocks

| Consumer | How the intention log helps |
|---|---|
| **Strategic AI** | Ring buffer of recent snapshots (last 20 ticks) in working memory — enables "what did I just try?" without re-reading the file |
| **Chronicle (E51)** | Compiler reads intention log alongside `NarrativeLedger` — can attribute significance to *unexpected* choices, not just high-impact events |
| **Social Memory (E43)** | Relationship score updates can be annotated with the decision context: "avoided this entity because `risk_penalty` was high, not because of distrust" |
| **Calibration (E11D)** | Scoring weight adjustments become measurable against historical intention distributions, not just outcome rates |

### Runtime boundary

The **ring buffer** (last N ticks, in-memory) is hot-path compatible — bounded size, written once per entity per tick. The **file sink** (`decision_trace.jsonl`) is append-only and written outside the resolution phase, after `Persistence` phase commits.

The file is read only by: offline analysis tools, Chronicle compiler, and between-tick strategic queries. Never read mid-resolution.

---

## Relationship to Planned Tickets

### E22-DECISION-EXPLAIN (additive — partial overlap)

E22 already plans: *"store top-5 scored routes per entity per tick (route_kind, score breakdown by term: urgency/benefit/personality_bias/confidence_bonus/risk_penalty/blocker_penalty, selected=True/False); Write snapshots to `decision_trace.jsonl`; Add tick-index sidecar mapping tick → byte offset for O(1) lookup."*

**E22 covers the write side.** This idea adds the **read side**: a runtime ring buffer that makes recent snapshots queryable by strategic AI within the same session. Without the ring buffer, the trace is write-only observability — useful for post-run analysis but invisible to the running agent.

**Impact on E22**: additive. The ring buffer can be scoped as a sub-task within E22-D or a follow-on ticket. E22's write design is not changed by this idea.

### E43-SOCIAL-MEMORY (gap — context annotation missing)

E43 plans: *"SocialMemoryRecord as durable cross-episode model: entity_id, interaction_history[], reputation_events[], relationship_scores{entity_id: float}."*

Currently `relationship_scores` is a bare float. Without the intention log, the system cannot distinguish: "I distrusted this entity" from "I avoided this entity because the risk score was high independent of trust." Social memory records would be richer if they carried the decision context at the time of the interaction.

**Impact on E43**: gap. E43 should define how `IntentionSnapshot` context is optionally attached to `interaction_history` entries. Not a blocker, but skipping it means social memory loses causal fidelity.

### E51-CHRONICLE (additive — coherence signal)

E51 plans: *"ChronicleCompiler: post-run pipeline reading `NarrativeLedger` and `simulation_events.jsonl`; groups events into named episodes by significance threshold; Event significance scoring: severity + entity_reach + cascade_downstream_count."*

The Chronicle's significance scoring uses outcome severity, not decision surprise. A battle that was expected (entity had high confidence, chose combat deliberately) is less narratively interesting than a battle triggered by desperation (entity had no high-scoring alternatives). The intention log adds a **surprise signal**: `|actual_score - mean_candidate_score|` measures how forced the choice was.

**Impact on E51**: additive. Chronicle significance formula gains an optional surprise-weighted term from the intention log sidecar.

---

## Open Questions

- What is the right ring buffer size? 20 ticks × N entities may be non-trivial memory for large worlds.
- Should `IntentionSnapshot` be written only when `selected_route` changed from the prior tick? Or always?
- Does the strategic AI need intention data from *other* entities, or only self?

---

*Raised: 2026-06-20. Deferred pending E22-DECISION-EXPLAIN completion.*

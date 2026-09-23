---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260923-TASK-SUCCESS-RATE-METRIC-EXPERIMENT-SPEC
artifact_type: investigation
tags: [ai, agent-monitoring, governance]
---

# Investigation — TCK-20260923-TASK-SUCCESS-RATE-METRIC-EXPERIMENT-SPEC

## Context scan performed
`mcp__knowledge-search__search_docs` (query: "task success rate metric cost proxy before after
comparison agent prompt changes") and `graphify query` run before file reads, per CLAUDE.md's
Context Scan rule (shared scan turn covering this ticket and its sibling). Top hits:
`bucket_c_future_options.md`'s item-19 entry (direct source) and `docs/agent-monitoring/schema.md`'s
`cost_proxy_score` section (formula/interpretation background).

## Prerequisite status (confirmed, not re-derived)
Same as the sibling ticket: `agent_evaluation_foundation_experiment.md` (item 13) completed
2026-09-07 with all 3 Exit Criteria MET. `bucket_c_future_options.md`'s own text: "Blocked on:
`agent_evaluation_foundation_experiment.md`'s scoring approach proving repeatable — this metric
would extend that scoring, not invent its own. When it clears: extend
`tools/agent-monitoring/cost_proxy.py`'s existing before/after comparison pattern (already used for
cost-proxy weight changes) to agent-prompt changes generally."

## Reading the actual existing pattern (required before writing the spec — not assumed from the
## doc's own summary)
Read `tools/agent-monitoring/weight_sensitivity_check.py` in full (promoted from
`experiments/cost_proxy_calibration/validate_rank_order.py`, `TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE`).
Its real mechanism, precisely:
1. Reads real `(run_id, seq)` tool-call groups from `agent-monitoring/data/*/tools.jsonl`, joined
   to `phase`/`agent` from the matching `events.jsonl` record.
2. Computes `cost_proxy_score` for every group under TWO weight sets: the currently-shipped weights
   (read live from `cost_proxy.py`'s own module constants, never a second hardcoded copy) and a
   candidate set supplied on the CLI (`--candidate-weights`, no default — must always be supplied
   explicitly).
3. Buckets scores by `phase` and separately by `agent`, computes the mean score per bucket under
   each weight set, ranks buckets by mean (baseline ranking, candidate ranking).
4. Compares the two rank orders via closed-form Spearman rank correlation (`_spearman_rank_correlation`)
   — a candidate weight set that doesn't materially reorder spend rankings isn't worth the churn of
   changing; one that does needs that reordering to be a deliberate, reviewed decision.
5. Read-only against `agent-monitoring/*.jsonl`; never modifies `cost_proxy.py` — informs a
   decision, does not make one.

**Key structural fact for this spec's Method**: the pattern compares RANK ORDER across buckets
(phase/agent), not an absolute before/after score directly, because `cost_proxy_score` has no
ground-truth absolute value to compare — it's a unitless proxy (confirmed:
`docs/agent-monitoring/schema.md`'s own `cost_proxy_score` section states this explicitly, "a
monotonic, unitless proxy for relative comparison... not a dollar-denominated cost figure").
Task-success-rate is different: it has a real absolute value (pass/fail, gate-outcome match rate),
so this spec's Method should note the pattern this ticket extends is the STRUCTURE (baseline vs.
candidate comparison over the same real event data, bucketed and reported per phase/agent) rather
than the rank-correlation statistic specifically — a direct before/after rate comparison is the
right extension for a metric that does have ground truth, not a literal reuse of Spearman
correlation.

## Vocabulary to extend from (item 13's own metric definitions)
`agent_evaluation_foundation_experiment.md`'s Metrics section already defines the vocabulary a
task-success-rate metric would extend: gate-failure rate (from `agent-monitoring/*/runs.jsonl`'s
terminal statuses — DOD_BLOCKED, NEEDS_HUMAN_INPUT, NEEDS_CHANGES, CONFLICTS_DETECTED,
TESTS_FAILED), and the 2 known recurring defect-class flag rates
(`tools/agent_replay/defect_detectors.py`'s `detect_m2_doc_update_gap()`/`detect_m3_background_hang()`).
This spec's own metric should be built from this same vocabulary, not a third, incompatible
definition of "success."

## What "extending to agent-prompt changes generally" means concretely
`cost_proxy.py`'s weight-change pattern compares two WEIGHT SETS over the SAME real historical
tool-call data (no re-execution needed — weights are just a different lens on already-recorded
`tools.jsonl` rows). An agent-PROMPT change is different: the prompt text itself changes what the
agent produces, so there is no way to re-score already-recorded output under a new prompt without
re-running the agent. This spec's Method must therefore describe re-running (replaying) the sample
under both the current and changed prompt — reusing item 13's own replay infrastructure
(`tools/agent_replay/`) for that re-execution, since `weight_sensitivity_check.py`'s own re-scoring
trick (no re-execution) does not transfer directly to a prompt-change comparison.

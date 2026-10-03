---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260805-SKILL-USAGE-METRIC
artifact_type: investigation
tags: [skills, agent-monitoring]
---

# Investigation — TCK-20260805-SKILL-USAGE-METRIC

## Confirmed: no existing per-skill invocation-count metric
Grepped `tools/agent-monitoring/*.py` and `tools/*.py` for `tool == 'Skill'` / `'Skill'` filtering
— none exists. `generate_retro.py`'s `tag_breakdown_skill` (built by `RETRO-TAG-BREAKDOWN`) answers
a different question (tag-driven gate-hit counts), not raw per-skill invocation counts — it cannot
answer "was `/api-design-principles` ever invoked" for any tag with no gate.

## Real data pull (live corpus, not a fixture)
Independently derived via a direct regex pass over `agent-monitoring/tools.jsonl` (not through the
function under construction — a genuinely separate derivation, so the test built on this can
detect real bugs in the function, not just confirm the function agrees with itself):

```
total Skill invocations: 207
  71  implement-ticket        26  create-tickets       9  agent-monitoring-retro
  67  graphify                12  implement-epic       5  simq-audit
   3  dataviz     3  brainstorming     3  claude-in-chrome
   2  update-config   2  fewer-permission-prompts   2  run
   1  artifact-design   1  claude-api
```
Zero unparseable `input_summary` values in the current corpus — every `Skill`-tool record matched
`re.search(r"'skill':\s*'([^']*)'", input_summary)` cleanly.

## Decision: standalone script, not a `generate_retro.py` section
Same reasoning as this session's earlier `TCK-20260805-SECURITY-GATE-FIRING-MONITOR`: this is a
one-off/periodic lookup tool (mirrors `retrieval_baseline_metrics.py`'s own shape), not part of the
weekly retro's recurring narrative. `generate_retro.py`'s own `tag_breakdown_skill` section is left
completely untouched, per Out of Scope.

## Test-design note (avoiding a stale hardcoded fixture)
The ticket's AC5 example ("re-derive today's 71/66/26/11/9/5/3 figures as a regression fixture")
would go stale immediately — the corpus grows every session (already drifted to 71/67/26/12/9/5/3
between when that AC was written and this investigation). The correct, non-brittle interpretation:
the test independently re-derives the same counts via its own regex pass (as done above) and
asserts equality with the new function's output — a genuine cross-check of the *logic*, not a
frozen snapshot of *today's numbers*. This matches `test_retrieval_baseline_metrics.py`'s own
established precedent of asserting against live real data.

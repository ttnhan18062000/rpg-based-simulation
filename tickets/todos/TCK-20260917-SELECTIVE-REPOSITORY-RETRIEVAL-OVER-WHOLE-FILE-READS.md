---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-WHOLE-FILE-READS
phase: open
date: 2026-09-17
tags: [ai, workflows, process-improvement, optimization]
---

# TCK-20260917-SELECTIVE-REPOSITORY-RETRIEVAL-OVER-WHOLE-FILE-READS

## Title
Prefer targeted line-range and symbol retrieval over whole-file reads — the cheapest token lever
available, with no dependency, no license, and no third-party state

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
From an external AI review of this account's Claude usage, supplied by the user 2026-09-17
(`/home/u24desktop/Working/tmp/token-usage-review.md`, §8). **Reviewed rather than adopted** — its
arithmetic was checked and holds, but several of its other recommendations are not executable here
(see Assumptions).

**The observation that motivates it.** Direct user input across all recorded usage is ~363.9K tokens
against ~48.8B cache-read tokens — a ratio of roughly 134,000:1. Prompt wording is therefore not the
lever. Essentially all consumption is *context*: repeated repository reads, tool output, accumulated
history. Of the review's recommendations, targeted retrieval is the one that is **entirely ours** —
no vendor, no license, no machine-wide state, no proxy in the API path — and it is independent of
`TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC`'s outcome.

The inefficient pattern it names: search → read several entire files → inspect imports → read
related files → repeat later in the same task. The efficient one: search → identify exact symbols →
retrieve narrow line ranges → expand only when genuinely required.

## Scope
- Establish a retrieval preference order for agent work, and record it where agents will actually
  follow it: symbol/reference search first, then targeted line ranges, then dependency inspection,
  with **full-file reads as an explicit fallback rather than the default**.
- Define when a full-file read *is* correct, so the guidance does not become a blanket prohibition —
  reviewing an unfamiliar module end-to-end, auditing a file for a corpus-wide property, and reading
  a file short enough that ranged reads cost more calls than they save are all legitimate.
- Measure the change with data this repo actually has (see below).

## Out of Scope
- **Any blocking gate, ratchet, or threshold on read behaviour.** Guidance and measurement only.
  Agent monitoring is a side effect of how work happens, not a simulation feature.
- **Weakening CLAUDE.md's mandatory Context Scan.** `search_docs` → `graphify query` → registry
  before grep/read is a Hard Rule and deliberately front-loads retrieval. This ticket refines what
  happens *after* that scan narrows the target; it does not reduce the scan itself. If implementing
  this appears to require relaxing the Hard Rule, stop and report rather than routing around it.
- A token-based success metric. Not available — see Assumptions.
- Any change to `CLAUDE.md` without the user's own direct authorization.

## Acceptance Criteria
- [ ] A retrieval preference order exists in a place agents actually consult, with the legitimate
      full-file cases named explicitly.
- [ ] A measured before/after on **`Read`-tool call counts and full-file versus ranged reads**,
      derived from `agent-monitoring/data/YYYY-Www/tools.jsonl`, which records every `Read` call with
      its `input_summary`. This is the substitute for the token metric that is unavailable.
- [ ] The baseline window and its population counts are recorded, so the comparison window can be
      matched rather than eyeballed.
- [ ] No gate, ratchet, or blocking check is introduced.
- [ ] Nothing under `agent-monitoring/data/` is mutated; any derivation is read-time only, following
      `TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT`'s precedent.

## Related Tickets
- `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` — the vendor-dependent sibling. This ticket is
  deliberately independent of its outcome and should not be blocked on it.
- `TCK-20260708-AGENT-COST-OBSERVABILITY` (done) — established that real token data is
  platform-blocked, which is why this ticket measures read behaviour instead.
- `TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT` (done) — read-time-only derived-metric precedent.

## Related Docs
- `docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`
  — the existing in-repo plan for this problem space. Its governing principle applies directly:
  *"A context-budget reduction is successful only when correctness signals hold or improve."*
- `docs/agent-monitoring/schema.md` — "What is not recorded"
- `/home/u24desktop/Working/tmp/token-usage-review.md` — the external review this derives from
  (external, unversioned; treat as a source, not as authority)

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `agent-monitoring/data/YYYY-Www/tools.jsonl` (`tool`, `input_summary` — the measurement source)
- `tools/agent-monitoring/retrieval_baseline_metrics.py`
- `.claude/agents/*.md` and `.claude/skills/*` — the plausible homes for the preference order

## Assumptions / Open Questions
- **The review's own §14 metric program is largely not executable here**, and this ticket
  deliberately does not inherit it. It asks for uncached-input, cache-read, cache-write, output and
  tool-result token counts; `docs/agent-monitoring/schema.md` states token counts are "consumed
  internally by the Claude Code runtime… There is no field for it and no workaround within the
  current platform." Read-call counts are the honest substitute.
- **A real risk of this change is under-context, not over-cost.** The same source plan names it:
  *"under-context: missing an active constraint, paired test, contract, or prior decision and
  producing incorrect work."* Ranged reads make that more likely, not less. This session has twice
  reached wrong conclusions from truncated output. Whatever guidance lands must say plainly that a
  ranged read which turns out to be insufficient should be widened immediately, and that concluding
  from a partial read is the failure mode being traded against.
- Where the preference order belongs is undecided — agent role files, a skill, or CLAUDE.md. The
  first two need no special authorization; CLAUDE.md does.
- Whether `input_summary` is granular enough to classify a read as ranged versus whole-file is
  **unverified**. Check before relying on it; if it is not, the measurement needs a different source
  and that finding should be recorded rather than worked around.

## Implementation Notes
Cheapest item in this family and independent of every vendor question, so it can proceed regardless
of what the Headroom trial concludes.

Resist expanding this into a retrieval-architecture project. The in-repo plan
(`idea_context_efficient_agent_retrieval_observability.md`) already covers that design space and is
sequenced after provider-agnostic orchestration; this ticket is the small behavioural slice that can
be done now without waiting for it.

## Test Summary
_To be completed by the implementer._

## Files Changed
_To be completed by the implementer._

## Completion Summary
_Open._

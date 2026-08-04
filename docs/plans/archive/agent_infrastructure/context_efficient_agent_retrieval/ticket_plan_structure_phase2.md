---
status: historical
layer: ai
authority: P2
audience: developer
maturity: shipped
date: 2026-07-28
archived: 2026-08-04
tags: [ai, workflows, process-improvement]
---

# Ticket Plan Structure — Context-Efficient Agent Retrieval, Phase 2

Guide for `/create-tickets`'s Comprehend/Structure phases when parsing
`idea_context_efficient_agent_retrieval_observability.md`'s Phase 2 only.

This supersedes `ticket_plan_structure.md` (the Phase 0-1 structure guide, which
explicitly forbade ticketing Phase 2) for this batch only — Phase 0-1 are now
`DONE` (`TCK-20260728-PHASE0-PREREQ-CONFIRMATION`, `TCK-20260728-RETRIEVAL-BASELINE-METRICS`,
`TCK-20260728-EVAL-FIXTURE-REPAIR`), satisfying the prerequisite this phase was
gated behind.

## Scope this batch to Phase 2 of the source doc's "Sequenced Future Epic" only

Phase 2 is **"Retrieval contract and metadata inventory — decide context-packet
schema, authority/freshness rules, code/test index boundaries, retention, and
privacy controls."** This is explicitly a *decision/design* phase, not an
implementation phase — the Maturity banner still applies in full: this batch
does not authorize a new mandatory workflow gate, a production monitoring
writer change, or a new external retrieval service. Actual retrieval/cache code
is Phase 3, deliberately out of scope here.

**This batch should produce standard-tier ticket(s) whose deliverable is a
written, reviewable contract/decision document** (following this repo's
existing pattern — see `docs/engine/contracts/*.md` for contract-doc shape,
`docs/parity_ledger/schema.json` for a machine-readable schema example, and
`docs/REGISTRY.yaml`'s `authority`/`status` frontmatter fields as the existing
authority/freshness primitive to build on, not replace) — **not working code**.
Acceptance criteria must be things like "produces
`docs/engine/contracts/context_packet_contract.md` documenting field X" or
"resolves Open Decision N with an explicit, cited answer," not "implements
class Y" or "passes integration test Z."

**Cover these source-doc items, each traceable to a concrete deliverable:**

1. **Context-packet schema** — what fields a packet has, sourced from Open
   Decision 3 (mandatory authority/freshness metadata) and the doc's existing
   `docs/REGISTRY.yaml` authority/status primitive.
2. **Code/test index boundaries** — resolve Open Decision 2: which code/test
   relationships (AST, import, test-naming, Graphify-derived) are buildable
   deterministically today, without any new semantic code model. Investigate
   `graphify-out/` and `tools/graphify`-adjacent code to ground this in what
   already exists, not what's hypothetically possible.
3. **Retention and privacy controls** — resolve Open Decision 4 (retention/
   redaction policy for retrieval events and cache entries), consistent with
   the source doc's Risks table ("Retrieval telemetry leaks sensitive content"
   → "store hashes, IDs, counts, and reason codes only; never raw prompts or
   chunks").
4. **Default-packet scenario criteria** — resolve Open Decision 1 (which
   scenarios/phases justify a default context packet, and initial token
   budgets), grounded in `TCK-20260728-RETRIEVAL-BASELINE-METRICS`'s actual
   baseline measurements (`tools/agent-monitoring/retrieval_baseline_metrics.py`
   output) rather than a fresh guess.

**Do NOT ticket in this batch** (still gated behind this phase's own evidence,
per the doc's Sequenced Future Epic):
- Any actual retrieval/cache implementation, embedding cache, or query-result
  cache (Phase 3).
- Retrieval observability events, dashboard views, or any shared-writer change
  (Phase 4).
- Shadow context packets or workflow adoption (Phase 5-6).
- Open Decisions 5 (promotion sample-size/thresholds) and 6 (MCP tool vs.
  adapter-library exposure) — both explicitly depend on a later phase's
  evidence (shadow evaluation results, and the contract actually being
  implemented, respectively) and should stay listed as unresolved on the epic
  ticket, not force-resolved here just because this phase touches the same
  document.

If investigation reveals Phase 2 cannot be meaningfully scoped without first
resolving something Phase 0-1 should have settled but didn't, say so plainly as
a risk/open-question in the ticket rather than silently guessing.

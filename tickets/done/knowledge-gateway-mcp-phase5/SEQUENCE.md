# Sequence — knowledge-gateway-mcp-phase5

Dependency-ordered implementation sequence for `TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE5-EPIC`'s
child tickets.

1. `TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT` — no dependencies within this epic. Honestly
   measures real repeated/semantically-equivalent question demand using real historical data (not
   the frozen 7-entry corpus), cross-referenced against Phase 3/4's own already-measured, mostly
   unfavorable per-hit cache economics. Its own real recommendation determines whether children 2-3
   below are ever scoped and built at all.

2. **Canonical entity IDs and alias consolidation** — NOT YET SCOPED. Only created as a real child
   ticket if child 1's own honest measurement finds real, material repeated-demand evidence
   supporting it. If child 1 finds insufficient demand, this ticket is never created, and the epic
   closes honestly on child 1's own finding alone — a complete, valid epic outcome, not an
   incomplete one.

3. **Conservative semantic candidate matching with deterministic validation** — NOT YET SCOPED, same
   conditioning as (2). If scoped, depends on (2) existing first (proposal §11.2 step 5 treats
   semantic similarity as a candidate generator over the canonical-entity-resolved identity space,
   not a standalone mechanism).

Strictly sequential. Ticket 1 must complete and its real recommendation reviewed before any decision
is made about scoping tickets 2-3.

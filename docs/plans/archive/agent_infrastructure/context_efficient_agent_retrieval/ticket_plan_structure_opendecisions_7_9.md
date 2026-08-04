---
status: historical
layer: ai
authority: P2
audience: developer
maturity: shipped
date: 2026-08-02
archived: 2026-08-04
tags: [ai, workflows, process-improvement]
---

# Ticket Plan Structure — Context-Efficient Agent Retrieval, Open Decisions 7-9

Guide for `/create-tickets`'s Comprehend/Structure phases when parsing
`idea_context_efficient_agent_retrieval_observability.md`'s Open Decisions list, items 7-9
only.

This does **not** supersede any prior `ticket_plan_structure_phaseN.md` file — Open Decisions
1-6 and Phases 0-5 remain resolved/shipped as recorded in
`tickets/done/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`. Decisions 7-9 are a new,
independent strand raised 2026-08-02 by `TCK-20260731-PARITY-INDEX-EPIC`'s work landing a real
`parity_ledger_entry` read path (`tools/parity_index.py`) alongside the already-defined but
still-abstract `kind` vocabulary in `docs/engine/contracts/context_packet_contract.md`. They
extend, but do not reopen, that contract's Open Decision 3 resolution.

## Scope this batch to Open Decisions 7-9 only

**Same maturity posture as every prior batch in this epic**: the source doc's maturity banner
still applies in full. This batch does not authorize a new mandatory workflow gate, a
production monitoring-writer change, a new external retrieval service, or any wiring into a
real `.claude/workflows/*.js` call site. Each ticket in this batch produces a **written,
reviewable decision document** (matching the rigor/shape of
`docs/ai/default_packet_scenarios_decision.md`, `docs/ai/code_test_index_boundaries_decision.md`,
and `docs/engine/contracts/context_packet_contract.md` itself), not working code and not a
promotion verdict. Acceptance criteria must read like "resolves Open Decision N with an
explicit, cited answer," never "implements X" or "wires X into the workflow."

**Cover these three items, one ticket per item unless investigation finds a reason to merge:**

1. **Open Decision 7 — cross-kind candidate ranking/selection.** `context_packet_contract.md`
   §3 already resolved how a *single* `included[]` entry's `authority`/`freshness` are
   populated per `kind` (Open Decision 3). It never addressed how two *different* `kind`s
   competing for the same bounded `token_budget` are ranked or chosen between —
   `tools/context_packet_assembler.py::assemble_context_packet()` takes an already-decided
   `included_candidates` list and never re-sorts/weights by `kind`; `tools/hybrid_retrieval.py`'s
   reciprocal-rank-fusion only ranks *within* one corpus by similarity. The ticket must decide
   (or explicitly declare undecidable-yet-and-why) an ordering/tie-break policy across kinds —
   e.g. does an `unrated` `code_symbol` ever outrank a `P1` `doc`? Does a `parity_ledger_entry`
   with `priority: P0` get a floor guarantee regardless of similarity score? Ground the answer
   in real, already-decided precedent where one exists (e.g. `_resolve_subject_conflicts()`'s
   same-`subject_key` authority-then-recency tie-break is a *same-kind* precedent worth citing,
   not copying uncritically to the cross-kind case).
2. **Open Decision 8 — `stored_artifacts/` as a retrieval kind, and confirming
   `staging_artifacts/`'s exclusion is intentional.** Investigate whether
   `stored_artifacts/{ticket_id}/*.md`'s real frontmatter (`artifact_type`, `status`,
   `authority` — see `tools/validate_frontmatter.py`'s enums) is sufficient to support a new
   registry-indexed `kind` (e.g. `stored_artifact`), distinct from how
   `tools/generate_registry.py::join_artifact_files()` currently only attaches a flat path list
   to the parent ticket's own registry entry. If a new `kind` is warranted, this ticket
   documents the `authority`/`freshness` population rule for it (following Decision 3's
   pattern exactly — do not invent a third vocabulary if the doc's own frontmatter fields
   already map cleanly). Also explicitly confirm — with a one-paragraph rationale, not just an
   observation — that `staging_artifacts/`'s current total exclusion from
   `generate_registry.py`'s scan is the correct permanent design (WIP/scratch content for an
   open ticket, not yet reviewable) rather than an accidental gap Decision 8 should also close.
3. **Open Decision 9 — generalizing the exact-lookup pattern.** `tools/parity_index.py`'s
   `entry()`/`impact()`/`health()` establish a deterministic, exact-structural-lookup query
   shape (never similarity-ranked, always safe as gate evidence) for the `parity_ledger_entry`
   kind specifically, explicitly separate from the fuzzy RRF-fused `search`/discovery path
   (`tools/hybrid_retrieval.py`). Decide whether this exact-vs-fuzzy split deserves a named,
   documented general convention (e.g. in `docs/engine/contracts/context_packet_contract.md`
   itself, as a new section, or a new sibling contract doc) that any future `kind` needing
   gate-safe lookups should follow — or whether it should stay parity-specific pending a
   second real use case. Do not invent a second exact-lookup implementation to "prove" the
   pattern in this batch; this decision is about whether/how to *document* the pattern already
   built, not build a new one.

**Do NOT ticket in this batch:**
- Any actual implementation of a cross-kind ranking algorithm, a `stored_artifact` kind
  scanner, or a second exact-lookup module — these decisions, once made, are separately
  ticketed and separately implemented, per this epic's own established Comprehend → Investigate
  → Structure → (later, separate) implementation-ticket precedent.
- Any change to `tools/parity_index.py`, `tools/context_packet_assembler.py`,
  `tools/hybrid_retrieval.py`, or `tools/generate_registry.py` — all three remain read-only
  investigation targets for this batch, exactly as they were for every prior decision-doc
  ticket in this epic (see e.g. `TCK-20260728-CONTEXT-PACKET-SCHEMA`'s own investigation, which
  read but never modified `tools/generate_registry.py`).
- Reopening or amending Open Decisions 1-6 or `docs/engine/contracts/context_packet_contract.md`
  §3's already-resolved core resolution — Decisions 7-9 extend that contract with new sections/
  a new contract addendum, they do not edit its existing resolved text.

If investigation finds that Decision 7's cross-kind ranking question cannot be meaningfully
resolved without first choosing a concrete `kind` priority ordering that reasonable people could
contest (i.e. it is a genuine value judgment, not a technical derivation), say so plainly as an
open question needing explicit human sign-off in the ticket rather than picking an ordering
unilaterally and presenting it as settled.

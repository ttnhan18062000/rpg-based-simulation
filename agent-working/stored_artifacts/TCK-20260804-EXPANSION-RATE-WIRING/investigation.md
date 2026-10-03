---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260804-EXPANSION-RATE-WIRING
artifact_type: investigation
tags: [agent-monitoring, observability]
---

# Investigation — TCK-20260804-EXPANSION-RATE-WIRING

## Current Behavior

### No real caller anywhere performs a follow-up "expanded" retrieval today

Read `tools/retrieval_events.py`, `tools/hybrid_retrieval.py`, `tools/retrieval_cache.py`, and
`tools/context_packet_assembler.py` in full, plus grepped `tools/knowledge_search.py` and all
associated test files (`tests/tools/test_retrieval_events.py`, `test_hybrid_retrieval.py`,
`test_context_packet_assembler.py`, `test_retrieval_cache.py`) for `retry`/`widen`/`broaden`/
`expand`. **Zero hits anywhere** except the schema field names themselves and one deliberately
stubbed constant (below). None of the 3 wrapped functions
(`hybrid_fuse_and_filter`, `check_index_cache`/`check_query_cache`/`check_packet_cache`,
`assemble_context_packet`) is ever called twice for the same logical request with different
parameters, in production code or in any test harness. This confirms the ticket's premise: the
gap is not a missed one-line wiring bug, there is genuinely no real "expansion" event happening
anywhere in this codebase today for the metric to observe.

### `context_packet_assembler.py` already answers the central question — deliberately, three times over

`tools/context_packet_assembler.py:36-43`:
```python
# Open Decisions 5/6 (expansion escalation semantics) remain explicitly deferred by
# ticket_plan_structure_phase3.md — a plain string constant so this field can never accidentally
# expose a field resembling real escalation semantics (max_expansions/trigger/threshold).
EXPANSION_POLICY_STUB: str = (
    "not_yet_resolved: Open Decisions 5/6 (expansion escalation semantics) deferred — see "
    "docs/plans/agent_infrastructure/context_efficient_agent_retrieval/"
    "ticket_plan_structure_phase3.md"
)
```
This is `ContextPacket.expansion_policy` — the packet-contract-side sibling field of this
ticket's `expansion_reason`/`expansion_count` (the monitoring-event-side fields). Both concern
the exact same undefined concept: "when/why does this retrieval system expand beyond its first
attempt." Traced the citation chain:

1. `docs/plans/archive/agent_infrastructure/context_efficient_agent_retrieval/
   ticket_plan_structure_phase3.md:93-95` (now archived, read directly): "Open Decisions 5
   (promotion sample-size/thresholds) and 6 (MCP tool vs. adapter-library exposure) — both still
   explicitly deferred; **do not force-resolve either just because this phase touches adjacent
   code**." Decision 5 here is the same promotion-threshold decision that `docs/ai/
   shadow_promotion_gate_thresholds_decision.md` resolved earlier in this same session (2026-08-04,
   as part of closing/backlogging `TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC`). Decision 6
   (MCP tool vs. adapter-library exposure) was also marked resolved as part of that same
   epic-finalization pass per this session's own record.
2. **However**, resolving Decision 5 (a numeric promotion floor: 56/122/6 shadow-run counts) and
   Decision 6 (an exposure-mechanism choice: MCP tool vs. library) does not, by itself, hand
   anyone a concrete algorithm for "what counts as an expansion, and why." Those two decisions are
   about *whether/how to roll the whole shadow-packet system out*, not about *what triggers a
   second, broader retrieval attempt within it*. The code comment's parenthetical gloss
   "(expansion escalation semantics)" is the implementer's own loose connection between the two —
   not a claim that resolving 5/6 resolves the escalation algorithm itself. No document anywhere
   in the corpus (checked `idea_context_efficient_agent_retrieval_observability.md`,
   `context_packet_contract.md`, all `TCK-20260728/29-CONTEXT-PACKET-*` stored artifacts) defines
   a concrete trigger/threshold for when a real expansion should occur.
3. Three independent, separately-shipped tickets in the same epic family
   (`TCK-20260728-CONTEXT-PACKET-SCHEMA`, `TCK-20260729-CONTEXT-PACKET-ASSEMBLY`, and the module
   itself) each independently reaffirmed the same refusal to invent this logic, and
   `TCK-20260729-CONTEXT-PACKET-ASSEMBLY` shipped a **dedicated regression test**,
   `test_expansion_policy_is_a_marked_placeholder_not_real_escalation_logic`
   (`stored_artifacts/TCK-20260729-CONTEXT-PACKET-ASSEMBLY/test_plan.md:66`), whose explicit job
   is to fail if `expansion_policy` ever stops being a marked stub and starts exposing real
   escalation fields (`max_expansions`/`trigger`/`threshold`).

### `tests/tools/test_retrieval_events.py`'s `"budget_exceeded"` value is a schema fixture, not a real signal

Line 118-119 uses `"expansion_reason": "budget_exceeded"` / `"expansion_count": 1` purely as an
example value in a hand-built fixture dict to test `RETRIEVAL_EVENT_FIELDS` validation — it is
never derived from `ContextPacket`'s real fields. Checked `assemble_context_packet()`
(`context_packet_assembler.py:266-291`) directly: `budget_returned` is computed as
`len(included_candidates) * DEFAULT_EXCERPT_BUDGET` — a deterministic function of how many
candidates were already decided to be included, not a signal that assembly ever *ran twice* or
*exceeded* anything and retried. There is no `budget_exceeded` condition anywhere in the module's
actual logic; excluded candidates go into `excluded_summary` with whatever `reason` string the
caller supplied when building the `(Candidate, str)` exclusion tuples — none of which is
generated by the module itself as a budget-exceeded signal. Using this non-existent signal to
manufacture a real `expansion_reason="budget_exceeded"` value would require inventing new
exclusion/retry logic inside `assemble_context_packet()` that does not exist today — exactly the
kind of escalation-logic invention `test_expansion_policy_is_a_marked_placeholder_not_real_escalation_logic`
was built to prevent one field over.

### `generate_retro.py`'s `expansion_rate` computation itself needs no change

`tools/agent-monitoring/generate_retro.py:704-711` (unchanged, confirmed correct): counts events
where `expansion_reason is not None or expansion_count is not None`, divided by total retrieval
events. This is unconditional on `adequacy_verdict` (a prior resolved design decision, per this
ticket's own Request Summary) and requires no producer-side assumption — it is a pure, honest
function of whatever the producers actually emit. If producers emit nothing, it is honestly
0.0%, not silently wrong.

## Mechanics / Engine Constraints

N/A — agent-tooling observability infrastructure, not simulation mechanics.

## Docs Requiring Update

- `docs/agent-monitoring/schema.md`: line 287 currently reads "Present only if a follow-up expansion
  occurred," which is already accurate and forward-compatible; Plan should decide whether a
  clarifying note ("no producer currently triggers this; expansion_rate will read 0.0% until a
  future ticket resolves Open Decisions 5/6's escalation semantics for a specific producer") is
  worth adding, to prevent a future reader from treating a permanent-0.0%-today `expansion_rate`
  as a bug rather than an honestly-disclosed, architecturally-gated limitation.

## Parity Ledger Overlap

- `INFRA-292` — already covers `retrieval_baseline_metrics.py` only (unrelated to this ticket,
  confirmed via the prior sibling ticket's own parity search).
- Searched all 8 `docs/parity_ledger/*.yaml` files for `expansion_reason`/`expansion_policy`/
  `retrieval_events.py`: only `infrastructure.yaml` has hits, all under the existing
  `INFRA-297` entry (per `stored_artifacts/TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT/plan.md:512`'s
  own citation) and one line at `docs/parity_ledger/infrastructure.yaml:6201` stating
  "`expansion_policy` is stubbed as a plain marker string citing Open Decisions 5/6, never [real
  escalation logic]" — already accurate, needs no change unless Plan decides to add a producer-side
  cross-reference note.

## Prior Work

- `stored_artifacts/TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT/` — defined the `expansion_reason`/
  `expansion_count` schema fields (Resolved Decisions 1-7 cover schema shape, the
  `adequacy_verdict` heuristic, `candidate_count` approximation, version constant — none of the 7
  resolves what triggers an expansion; population was left for a future producer by design).
- `stored_artifacts/TCK-20260729-RETRIEVAL-RETRO-VIEWS/` — built `expansion_rate`'s computation
  (already correct, confirmed above).
- `stored_artifacts/TCK-20260728-CONTEXT-PACKET-SCHEMA/`,
  `stored_artifacts/TCK-20260729-CONTEXT-PACKET-ASSEMBLY/` — both independently, repeatedly refuse
  to give `expansion_policy` real content, citing the same deferred Open Decisions 5/6.

## Risks and Open Questions

**This investigation's central finding, stated plainly per the ticket's own request:** implementing
any real trigger for `expansion_reason`/`expansion_count` (Option B in the ticket's Scope) would be
implementing real expansion/escalation semantics through the monitoring-event side door, while
three separate, independently-shipped tickets in the same epic family have deliberately, repeatedly,
and with a dedicated regression test refused to do exactly that through the packet-contract front
door (`expansion_policy`) — specifically because the governing Open Decisions remain deferred, and
`ticket_plan_structure_phase3.md`'s own words are "do not force-resolve either just because this
phase touches adjacent code." `TCK-20260804-EXPANSION-RATE-WIRING` is exactly this situation: a
phase/ticket touching adjacent code (the retrieval-event wrappers) to this same deferred concept.

Recommendation for Plan (not a final decision — Plan makes the call): **Option A (plumbing-only,
honest disclosure)** is not just the safer choice but the only choice consistent with existing,
repeatedly-reaffirmed architectural precedent in this exact epic family. Option B would either (a)
invent escalation logic nobody has designed, directly contradicting the explicit "do not
force-resolve" instruction, or (b) require truly minimal, non-representative logic (e.g., a fake
"always expand once" branch) that would produce a fabricated non-zero `expansion_rate` not
reflecting real system behavior — precisely the "never a fabricated or silent number" violation
this file's own house style exists to prevent.

**What plumbing-only concretely means:** add optional `expansion_reason`/`expansion_count`
parameters to the 3 `wrap_*()` function signatures, forwarded to `emit_retrieval_event()` only
when a caller supplies them (never defaulted/fabricated) — so the mechanism is ready and available
the moment a real expansion trigger is designed in a future ticket, without this ticket having to
invent that trigger itself. `expansion_rate` will continue reading 0.0% in practice until that
future ticket lands, and this must be stated plainly in the ticket's Completion Summary and
`docs/agent-monitoring/schema.md`'s field description — an honest disclosure, not a silent gap.

## Anti-Drift Hazards

- **Do not invent any real expansion trigger, threshold, or retry logic** in any of the 3
  producer modules — this directly conflicts with `ticket_plan_structure_phase3.md`'s explicit
  instruction and would put `expansion_reason`/`expansion_count` out of sync with
  `expansion_policy`'s deliberately-stubbed sibling field.
- **Do not force-resolve Open Decisions 5/6** — they are the epic's decisions to resolve when a
  future ticket actually designs escalation semantics, not this ticket's to reinterpret.
- **Do not fabricate a fake/synthetic expansion event** anywhere (test fixtures using
  `"budget_exceeded"` as an example schema value remain fine and unchanged; production code paths
  must never manufacture one).
- **Do not touch `compute_retrieval_metrics()`'s `expansion_rate` formula** — already correct,
  confirmed above, out of scope per the ticket's own Out of Scope list.

---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260802-EXACT-LOOKUP-CONVENTION
phase: done
date: 2026-08-02
tags: [ai, documentation]
---

# TCK-20260802-EXACT-LOOKUP-CONVENTION

## Title
Decide whether to document the exact-lookup vs. fuzzy-search split as a general project convention (Open Decision 9)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
tools/parity_index.py's entry()/impact()/health() establish a deterministic, exact-structural-lookup pattern (never similarity-ranked, always gate-safe) for parity_ledger_entry specifically, distinct from the fuzzy RRF-fused search/hybrid_retrieval.py path. We need to decide whether this exact-vs-fuzzy split deserves a named, documented general convention any future kind needing gate-safe lookups should follow, or should stay parity-specific pending a second real use case. This is a documentation decision only, not license to build a second exact-lookup implementation.

## Scope
- Produce a decision document resolving Open Decision 9: whether the exact-lookup-vs-fuzzy-search split (parity_index.py vs hybrid_retrieval.py) becomes a named, documented general convention.
- If adopted, define applicability criteria in a new section of docs/engine/contracts/context_packet_contract.md or a named sibling doc, cited against the real precedent of parity_index.py vs hybrid_retrieval.py.
- If not adopted, document the explicit rationale for staying parity-specific pending a second real use case.

## Out of Scope
- No code changes to tools/parity_index.py, tools/hybrid_retrieval.py, tools/context_packet_assembler.py, or tools/generate_registry.py.
- No reopening or amending Open Decisions 1-6 or context_packet_contract.md's already-resolved §3 text.
- No building of a second exact-lookup module to "prove" the pattern — decision-document only.
- Do not absorb sibling Decisions 7/8 from the same batch; stay scoped to Decision 9 only.

## Acceptance Criteria
- [x] Decision doc states an explicit yes/no verdict on whether the exact-vs-fuzzy split (parity_index.py's entry()/impact()/health() vs. hybrid_retrieval.py's RRF-fused search) becomes a named, documented general convention. Resolved: **no**, stated in §7's "Core resolution — no." line.
- [x] If yes: doc adds a new clearly-delimited section to docs/engine/contracts/context_packet_contract.md (or a named sibling doc) defining applicability criteria, cited against the real precedent of parity_index.py vs. hybrid_retrieval.py. **Not applicable — resolved verdict is "no"** (see plan.md's "Decisions Made During Human Review" and its Acceptance Criteria Map). Satisfied-as-inapplicable: no `### Applicability Criteria` heading is written; the real-precedent citation this AC also asks for is still delivered independent of the verdict (§7's "Real precedent, both sides of the split" paragraph, verified by `test_section_7_cites_real_precedent_by_function_name`).
- [x] If no: doc states explicitly why the pattern stays parity-specific pending a second real use case. Satisfied: §7's "Core resolution — no." paragraph states the n=1/rule-of-three rationale and the Gate-A-quality-vs-generalizability distinction.
- [x] If the decision itself is a genuine value judgment the investigation cannot objectively resolve, the doc states this plainly as needing human sign-off. Satisfied: §7 contains the literal phrases "human sign-off" and "value judgment".
- [x] Files Changed contains zero diffs to tools/parity_index.py, tools/hybrid_retrieval.py, tools/context_packet_assembler.py, tools/generate_registry.py — doc file(s) only. Verified via sha256 hash-fixture test and `git diff --stat`.

## Related Tickets
- TCK-20260731-PARITY-IMPACT-PROOF
- TCK-20260731-PARITY-READPATH-GATE
- TCK-20260729-HYBRID-RETRIEVAL-FUSION
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC

## Related Docs
- docs/engine/contracts/context_packet_contract.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_opendecisions_7_9.md
- docs/ai/parity_readpath_gate_a_decision.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/parity_index.py
- tools/hybrid_retrieval.py
- tests/tools/test_parity_index.py
- tests/tools/test_gate_a_readpath_review.py

## Assumptions / Open Questions
- The decision itself (whether to name a general convention now vs. wait for a second use case) is a genuine value judgment; if authoring cannot derive an objective answer, the ticket should say so plainly, needing human sign-off, rather than presenting a self-chosen answer as settled.
- Only makes full sense read together with sibling Decisions 7/8 — confirm scoping stays isolated to Decision 9.
- Real risk of scope creep into implementation since parity_index.py's Gate A verdict was GO — explicitly forbidden in this batch.

## Implementation Notes

Implemented per `staging_artifacts/TCK-20260802-EXACT-LOOKUP-CONVENTION/plan.md`'s 5 steps.
Step 2's fork was already resolved before implementation began: the human reviewer had explicitly
chosen Branch B ("stay parity-specific, no general convention yet") during planning, recorded in
plan.md's "Decisions Made During Human Review" section, so Step 2 was implemented as a single
committed decision, not a live fork.

1. **Added `## 7. Open Decision 9 Resolution`** to
   `docs/engine/contracts/context_packet_contract.md`, appended after the existing `## 6. Open
   Decision 8 Resolution` section (separated by a `---` divider, matching §5/§6's own convention;
   §1-§6 left byte-for-byte untouched — confirmed by 3 dedicated section-unchanged tests). The new
   section: (a) opens with a verbatim blockquote of Open Decision 9's question text, sourced from
   `idea_context_efficient_agent_retrieval_observability.md` item 9 and re-verified directly
   against that file before writing (not copied unread from investigation.md); (b) a "real
   precedent" paragraph naming both sides of the split by symbol with line-number citations
   re-verified directly against current `tools/parity_index.py` (`entry()` 485-531, `impact()`
   534-593, `health()` 596-643, `_connect_readonly()` 87-92) and `tools/hybrid_retrieval.py`
   (`reciprocal_rank_fusion()` 59-77, `hybrid_fuse_and_filter()` 224-331) — all line numbers
   confirmed to match plan.md's citations exactly via `grep -n` before writing; (c) explicitly
   distinguishes the Gate A GO verdict
   (`docs/ai/parity_readpath_gate_a_decision.md`, 66.7% vs. 4.8% recall) as parity-domain-quality
   evidence, not pattern-generalizability evidence; (d) the `**Core resolution — no.**` verdict,
   with the n=1/rule-of-three rationale and the required "human sign-off"/"value judgment" framing
   sentence; (e) the five generalizable properties (read-only access, exact equality matching,
   deterministic sort, explicit typed no-match response, zero mutation surface), framed explicitly
   as a citable, non-mandatory reference ("what this pattern looks like ... not criteria a future
   `kind` must satisfy") — no `### Applicability Criteria` heading anywhere in the document; (f) an
   explicit reopening condition; (g) a closing "What does not change" paragraph matching §3/§5/§6's
   own convention.
2. **Updated the epic ticket's OPEN DECISION 9 entry**
   (`tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`) from `**UNRESOLVED**` to
   `**RESOLVED**`, in the exact shape Decisions 7 and 8's own entries use (one-paragraph outcome
   summary + citation to `docs/engine/contracts/context_packet_contract.md` §7). The summary states
   the resolved "no" verdict plainly, without hedging or referencing Branch A as if it were still
   live. Only the Decision 9 bullet was touched — confirmed by `test_epic_ticket_decision_9_marked_resolved`,
   which also asserts Decisions 1-8 still read `**RESOLVED**` (untouched, not flipped).
3. **Added `tests/tools/test_exact_lookup_convention_decision.py`** (new file, 14 tests: 13 passing
   + 1 conditional skip), using the same `Path.read_text()` static-content technique as the two
   sibling test files (no importable exact-lookup-convention module exists to exercise — this
   ticket is decision-document-only). One test fix was needed during implementation: the doc's
   "human sign-off"/"value judgment" framing sentence originally wrapped "value judgment" across a
   markdown line break (space became newline), so the literal substring check failed; fixed by
   reflowing that one paragraph in the doc so the phrase stays on one line, rather than weakening
   the test with a whitespace-normalization workaround — a cleaner fix than the blockquote case
   sibling tickets hit, since this was plain prose, not a blockquote-prefixed line. See plan.md's
   Deviations section for the test-count/naming deviation from `test_plan.md`'s literal 10-item
   list (14 tests, same or greater coverage, matching sibling test-file naming conventions more
   closely) and the pre-existing, ticket-independent `test_gate_a_readpath_review.py` fixture-path
   failure discovered during Step 5.
4. **Regression pass** — `pytest tests/tools/test_parity_index.py tests/tools/test_hybrid_retrieval.py
   tests/tools/test_context_kind_priority_decision.py tests/tools/test_stored_artifact_kind_decision.py
   tests/tools/test_exact_lookup_convention_decision.py` → 78 passed, 1 skipped (the conditional
   yes-verdict test, correctly inert under the "no" verdict). `python3 tools/validate_frontmatter.py`
   on both the contract doc and this ticket → OK. `python3 tools/generate_registry.py --check` → in
   sync. `git diff --stat` confirmed only `docs/engine/contracts/context_packet_contract.md` (+269
   lines) and `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md` (+50 lines)
   changed among pre-existing files — zero diffs to any of the four named `tools/` files, verified
   both by `git diff --stat` and the new test file's sha256 hash-fixture guard (hashes recomputed
   independently and matched the sibling test files' own recorded values for the same files,
   confirming those files are genuinely untouched by any ticket in this batch, not just this one).
   `pytest tests/tools/test_gate_a_readpath_review.py` was run and found pre-existing failures (3
   failed, 7 errored) unrelated to this ticket — confirmed via `git stash` that the identical
   failure reproduces against the pre-ticket working tree; the file's fixture path
   (`staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/gate_a_corpus.json`) no longer exists
   because that ticket's staging artifacts were already moved to `stored_artifacts/` on closure,
   and the test file was never updated to point at the new location. This was reported, not
   silently worked around, and no fix was attempted since it falls outside this ticket's scope
   (not one of the four named `tools/` files, not the contract doc).

No architectural issues surfaced; no scope conflicts found.

## Test Summary
- `pytest tests/tools/test_exact_lookup_convention_decision.py -v` — 13 passed, 1 skipped (new file).
- `pytest tests/tools/test_parity_index.py tests/tools/test_hybrid_retrieval.py tests/tools/test_context_kind_priority_decision.py tests/tools/test_stored_artifact_kind_decision.py tests/tools/test_exact_lookup_convention_decision.py -v` — 78 passed, 1 skipped.
- `pytest tests/tools/test_gate_a_readpath_review.py -v` — 3 failed, 7 errored; confirmed via `git stash` to be a pre-existing failure independent of this ticket's changes (stale fixture path, `staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/` was already migrated to `stored_artifacts/`), not caused by or fixed by this ticket.
- `python3 tools/validate_frontmatter.py docs/engine/contracts/context_packet_contract.md` — OK.
- `python3 tools/validate_frontmatter.py tickets/inprogress/TCK-20260802-EXACT-LOOKUP-CONVENTION.md` — OK.
- `python3 tools/generate_registry.py --check` — in sync.
- `git diff --stat` scoped check — confirmed zero changes to `tools/parity_index.py`, `tools/hybrid_retrieval.py`, `tools/context_packet_assembler.py`, `tools/generate_registry.py`.

## Files Changed
- `docs/engine/contracts/context_packet_contract.md` (modified — new `## 7. Open Decision 9 Resolution` section appended; §1-§6 untouched)
- `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md` (modified — OPEN DECISION 9 entry only, marked RESOLVED)
- `tests/tools/test_exact_lookup_convention_decision.py` (new)
- `tickets/inprogress/TCK-20260802-EXACT-LOOKUP-CONVENTION.md` (this ticket, updated)
- `staging_artifacts/TCK-20260802-EXACT-LOOKUP-CONVENTION/plan.md` (Deviations section added)

## Completion Summary
Open Decision 9 is resolved: the exact-vs-fuzzy (`parity_index.py` vs. `hybrid_retrieval.py`)
retrieval-type split stays an implicit, parity-specific pattern for now — **not** promoted to a
named general convention. With n=1 (no second `kind` has ever needed a gate-safe exact lookup),
rule-of-three reasoning applies, and the Gate A GO verdict's recall numbers are evidence of
parity-domain retrieval quality, not pattern generalizability, so they cannot ground applicability
criteria today. The pattern's generalizable properties (read-only access, exact equality matching,
deterministic sort, explicit typed no-match response, zero mutation surface) are recorded as a
citable, non-mandatory reference — not a mandatory convention, no `### Applicability Criteria`
heading — with an explicit reopening condition: revisit once a second real `kind` genuinely needs
a gate-safe exact lookup. This verdict reflects explicit human sign-off obtained during planning
(recorded in plan.md's "Decisions Made During Human Review"), stated plainly in the doc as a value
judgment rather than presented as a self-derived, objectively settled answer. The resolution is
recorded in `docs/engine/contracts/context_packet_contract.md` §7 and mirrored in the epic
ticket's Decision 9 tracking entry. Zero changes were made to any of the four named `tools/`
files, verified by a new static/hash-based test file (14 tests, 13 passing + 1 correctly-inert
conditional skip) plus the full pre-existing regression suite for this domain (78 tests passing,
all pre-existing files unmodified). No src/ simulation behavior changed; no parity ledger entry
required (same posture §4 already establishes for this contract family). All 5 Acceptance Criteria
are satisfied, including AC2 as satisfied-as-inapplicable under the resolved "no" verdict.

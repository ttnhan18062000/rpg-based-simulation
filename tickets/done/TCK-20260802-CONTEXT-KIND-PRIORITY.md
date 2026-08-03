---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260802-CONTEXT-KIND-PRIORITY
phase: done
date: 2026-08-02
tags: [ai, documentation]
---

# TCK-20260802-CONTEXT-KIND-PRIORITY

## Title
Resolve cross-kind candidate ranking/selection policy for the context packet (Open Decision 7)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
The context-packet contract already decided how a single included[] entry's authority/freshness get populated per kind (Open Decision 3), but never decided how two different kinds (e.g. a doc vs. a parity_ledger_entry) get ranked or chosen between when they compete for the same bounded token_budget. This gap became concrete once tools/parity_index.py landed a real parity_ledger_entry read path alongside the existing doc/ticket/code_symbol kinds with no decided precedence. We need a decision on ordering/tie-break policy across kinds, grounded in existing same-kind precedent (_resolve_subject_conflicts()'s authority-then-recency tie-break) without uncritically copying it to the cross-kind case. If this turns out to be a genuine value judgment rather than a technical derivation, that must be stated plainly as needing explicit human sign-off, not resolved unilaterally.

## Scope
- Produce a new decision document/addendum resolving Open Decision 7 (cross-kind candidate ranking/selection for the context packet's bounded token_budget).
- Explicitly compare and contrast against _resolve_subject_conflicts()'s same-kind authority-then-recency precedent and reason about whether/how it generalizes.
- Take an explicit position on both concrete competing-kind examples raised: an unrated code_symbol vs. a P1 doc, and a P0 parity_ledger_entry's inclusion-floor guarantee.
- Extend docs/engine/contracts/context_packet_contract.md with a new section/addendum — its existing §3 resolved text is not edited in place.

## Out of Scope
- No code changes to tools/context_packet_assembler.py, tools/hybrid_retrieval.py, tools/parity_index.py, or tools/generate_registry.py.
- No reopening or amending Open Decisions 1-6 or context_packet_contract.md's already-resolved §3 text.
- No implementation of ranking/scoring code — decision-document only.
- Do not absorb sibling Decisions 8/9 from the same batch; stay scoped to Decision 7 only.

## Acceptance Criteria
- [x] Decision doc explicitly cites _resolve_subject_conflicts()'s same-subject_key authority-then-recency tie-break as same-kind precedent and explains why it does or does not generalize to the cross-kind case.
- [x] Decision doc takes an explicit position on both concrete examples: an unrated code_symbol competing against a P1 doc, and whether a P0 parity_ledger_entry gets a guaranteed inclusion floor.
- [x] If the ordering is a genuine value judgment (not a technical derivation), the doc states this plainly as needing explicit human sign-off rather than presenting a self-chosen ordering as settled.
- [x] No changes made to tools/context_packet_assembler.py, tools/hybrid_retrieval.py, tools/parity_index.py, or tools/generate_registry.py; context_packet_contract.md's existing §3 text is extended via a new section, not edited in place.

## Related Tickets
- TCK-20260728-CONTEXT-PACKET-SCHEMA
- TCK-20260729-CONTEXT-PACKET-ASSEMBLY
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
- TCK-20260731-PARITY-INDEX-EPIC

## Related Docs
- docs/engine/contracts/context_packet_contract.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_opendecisions_7_9.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/context_packet_assembler.py
- tools/hybrid_retrieval.py
- tools/parity_index.py
- tests/tools/test_context_packet_assembler.py
- tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md

## Assumptions / Open Questions
- High likelihood the correct outcome is "declare undecidable pending human sign-off" since there is no existing repo precedent for cross-kind ordering — if so, this ticket's own Assumptions/Open Questions section (not its Scope/AC) must state that plainly rather than resolving it unilaterally.
- Coupled to sibling Decisions 8/9 in the same batch; must stay scoped to Decision 7 only.

## Implementation Notes
Implemented exactly per `staging_artifacts/TCK-20260802-CONTEXT-KIND-PRIORITY/plan.md`'s 4 ordered
steps, with no deviations.

1. **Added `## 5. Open Decision 7 Resolution`** to
   `docs/engine/contracts/context_packet_contract.md`, appended after the existing `## 4.
   Verification Path` section (§1-§4 left byte-for-byte untouched). The new section: (a) opens with
   a verbatim quote of Open Decision 7's question text (matching §3's own quote-only convention,
   not the full ticket-tracking entry with its UNRESOLVED/citation wrapper); (b) resolves
   Constraint A (`unrated` must not default to worst — cites §3's own "must never imply otherwise
   by, for example, defaulting to `P2`/`historical`" text as newly binding cross-kind); (c) resolves
   Constraint B (score non-comparability — cites `candidate_from_hybrid_result()`
   (`tools/context_packet_assembler.py:144-165`, real `rrf_score` float) vs. `unrated_candidate()`
   (`:98-122`, `score: float = 0.0` default at line 105) and `candidate_from_parity_ledger_fixture()`
   (`:205-224`, hardcoded `score=0.0` at line 220)); (d) resolves Constraint C
   (`_resolve_subject_conflicts()`'s structural inapplicability — cites `_CONFLICT_ELIGIBLE_
   FRESHNESS = frozenset({"active","authoritative"})` at line 49 against `unrated_candidate()`'s
   `freshness=UNRATED` at line 120 and `candidate_from_parity_ledger_fixture()`'s `freshness=
   entry["status"]` at line 222, plus `tools/parity_index.py`'s `impact()` (`:534-593`) as a second,
   intra-kind-only same-kind precedent that also does not generalize); (e) takes an explicit
   position on both named examples (unrated `code_symbol` vs. P1 doc; P0 `parity_ledger_entry`
   inclusion floor), each landing on an honest deferral rather than an invented ordering; (f) states
   the residual ordering/floor policy plainly as needing "human sign-off" — a genuine value
   judgment with zero repo precedent for an inclusion-floor/budget-trimming mechanism; (g) closes
   with a "No shared numeric scale" note re-affirming §3's silent-coercion warning. All code
   citations (line numbers, function names, the `_CONFLICT_ELIGIBLE_FRESHNESS` literal) were
   verified directly against the current `tools/context_packet_assembler.py`/`tools/parity_index.py`
   source before writing, not copied unread from investigation.md.
2. **Updated the epic ticket's OPEN DECISION 7 entry**
   (`tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`) from `**UNRESOLVED**` to
   `**RESOLVED**`, following the exact shape of sibling entries 1-6 (one-paragraph outcome summary
   + citation to the resolving doc location, `docs/engine/contracts/context_packet_contract.md`
   §5). The summary states plainly that three technical constraints were resolved and the ordering
   question was explicitly deferred pending human sign-off — it does not overstate the outcome as a
   complete ordering policy. Only this one entry was touched; entries 1-6, 8, and 9 are untouched
   (confirmed by `git diff` — 29 lines changed in this file, all within the Decision 7 bullet).
3. **Added `tests/tools/test_context_kind_priority_decision.py`** (new file, 9 tests), using the
   `Path.read_text()` static content-check technique from
   `tests/tools/test_shadow_packet_call_site.py` (no ranking logic exists anywhere to import
   against). Covers: §5 heading placement after §4; verbatim presence of the Open Decision 7 quote;
   AC1 (`_resolve_subject_conflicts`/`subject_key`/`freshness` + a generalization-verdict marker);
   AC2 (both named examples, each with an explicit stance marker — `human sign-off`/`deferred` for
   the code_symbol-vs-P1 case, matching Step 1's actual deferral wording rather than the
   `outrank`/`always` keywords test_plan.md's illustrative guess used); AC3 (`human sign-off` +
   `value judgment` literal phrases); AC4 in two parts — a byte-content check that §3's and §4's key
   sentences are still present verbatim (proving no in-place edit), and a recorded-sha256-hash
   fixture check (not a git-diff-against-base-commit check, since the working tree already carried
   several unrelated concurrent modifications from other in-flight tickets, making a single stable
   base commit impractical to pin) confirming `tools/context_packet_assembler.py`,
   `tools/hybrid_retrieval.py`, `tools/parity_index.py`, and `tools/generate_registry.py` are
   byte-identical to their pre-ticket content.
4. **Regression pass** — `pytest tests/tools/test_context_kind_priority_decision.py` (9 passed),
   `pytest tests/tools/test_context_packet_assembler.py tests/tools/test_hybrid_retrieval.py
   tests/tools/test_parity_ledger_scan.py` (35 passed, all pre-existing, unmodified),
   `python3 tools/validate_frontmatter.py` against both the contract doc and this ticket (both OK).
   `git diff --stat` scoped to the four named `tools/` files plus the contract doc and epic ticket
   confirmed only `docs/engine/contracts/context_packet_contract.md` (+104 lines) and
   `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md` (+29 lines) changed — zero
   `tools/` files in the diff.

No architectural issues surfaced; no scope conflicts found. No deviation from
`staging_artifacts/TCK-20260802-CONTEXT-KIND-PRIORITY/plan.md` occurred (see that file's own
"Deviations" note, added for completeness even though empty).

## Test Summary
- `pytest tests/tools/test_context_kind_priority_decision.py -v` — 9 passed (new file).
- `pytest tests/tools/test_context_packet_assembler.py tests/tools/test_hybrid_retrieval.py tests/tools/test_parity_ledger_scan.py -v` — 35 passed (pre-existing regression surface, unmodified, confirmed green).
- `python3 tools/validate_frontmatter.py docs/engine/contracts/context_packet_contract.md` — OK.
- `python3 tools/validate_frontmatter.py tickets/inprogress/TCK-20260802-CONTEXT-KIND-PRIORITY.md` — OK.
- `git diff --stat` scoped check — confirmed zero changes to `tools/context_packet_assembler.py`, `tools/hybrid_retrieval.py`, `tools/parity_index.py`, `tools/generate_registry.py`.

## Files Changed
- `docs/engine/contracts/context_packet_contract.md` (modified — new `## 5. Open Decision 7 Resolution` section appended; §1-§4 untouched)
- `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md` (modified — OPEN DECISION 7 entry only, marked RESOLVED)
- `tests/tools/test_context_kind_priority_decision.py` (new)
- `tickets/inprogress/TCK-20260802-CONTEXT-KIND-PRIORITY.md` (this ticket, updated)
- `staging_artifacts/TCK-20260802-CONTEXT-KIND-PRIORITY/plan.md` (Deviations section added, empty)

## Completion Summary
Resolved Open Decision 7 as a documentation-only change: three technical constraints
(`unrated`-must-not-default-to-worst, score cross-kind non-comparability, and
`_resolve_subject_conflicts()`'s structural inapplicability cross-kind) are now definitively
resolved with direct code citations in a new §5 of `context_packet_contract.md`, while the
residual P0-inclusion-floor/unrated-ordering question is honestly stated as an open value judgment
deferred pending explicit human sign-off — not invented or resolved unilaterally. The epic
ticket's OPEN DECISION 7 tracking entry now reads RESOLVED with an accurate outcome summary. Zero
changes were made to any `tools/` code (`context_packet_assembler.py`, `hybrid_retrieval.py`,
`parity_index.py`, `generate_registry.py`), verified by a new static/hash-based test file
(9 tests, all passing) plus the full pre-existing regression suite for this domain (35 tests, all
passing, unmodified). No src/ simulation behavior changed; no parity ledger entry required (same
posture §4 already establishes for this contract).

---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260802-CONTEXT-KIND-PRIORITY
artifact_type: investigation
tags: [ai, documentation]
---

# Investigation — TCK-20260802-CONTEXT-KIND-PRIORITY

## Current Behavior

**`tools/context_packet_assembler.py`** — `assemble_context_packet()` (L266-291) does **not**
select or rank candidates at all. It takes an already-decided `included_candidates: list[Candidate]`
and an already-decided `excluded: list[tuple[Candidate, str]]` as caller-supplied inputs, and:
1. Runs `_resolve_subject_conflicts()` (L172-198) over `included_candidates` to compute
   `inclusion_reason` strings for same-`subject_key` conflicts.
2. Builds one `included[]` dict per candidate via `build_included_entry()` (L231-245) — every
   passed-in candidate is included, unconditionally.
3. Computes `budget_returned = len(included_candidates) * DEFAULT_EXCERPT_BUDGET` (L287) — a
   flat per-candidate multiply, not a real token accounting against `budget_requested`.

**No selection-against-`token_budget` algorithm exists anywhere in the repo today.** There is
nothing to extend cross-kind — the gap Open Decision 7 names is upstream of every function this
module exposes.

**`_resolve_subject_conflicts()`** (L172-198) — the cited same-kind precedent. Key structural
facts, verified by reading the code, not assumed from the docstring:
- Only fires for candidates with non-`None` `subject_key` (L180-183), grouped by that key.
- Within a group, only candidates whose `freshness in _CONFLICT_ELIGIBLE_FRESHNESS` (`{"active",
  "authoritative"}`, L49) are `qualifying` (L187); groups with `< 2` qualifying candidates are
  skipped entirely (L188).
- Sort is two-pass: most-recent-`last_verified`-first (L193), then stable-sort by
  `_AUTHORITY_RANK.index(c.authority)` ascending (L194) — `_AUTHORITY_RANK = ("P0","P1","P2")`
  (L45). Both winner and losers stay in `included[]`; only `inclusion_reason` text differs
  (L195-198). Nothing is ever dropped by this function.

**Why this cannot structurally fire cross-kind today (a technical fact, not an interpretation):**
`freshness` values are populated per `kind` per `context_packet_contract.md` §3:
- `doc`/`ticket`(done) → `freshness` = REGISTRY `status` ∈ `{authoritative, active, historical,
  archive}` — the only kind whose `freshness` can ever equal `"active"`/`"authoritative"`.
- `code_symbol`/`test`/`graphify_node`/in-progress `ticket` → `freshness = "unrated"` always
  (`unrated_candidate()`, L98-122).
- `parity_ledger_entry` → `freshness` = the entry's own `status` ∈ `{verified, divergent,
  missing, unsupported, legacy_verified}` (`candidate_from_parity_ledger_fixture()`, L205-224) —
  a disjoint 5-value vocabulary that structurally never intersects `{"active","authoritative"}`.

So `_resolve_subject_conflicts()`'s `qualifying` filter (L187) mathematically excludes every
`code_symbol`/`test`/`graphify_node`/in-progress-ticket/`parity_ledger_entry` candidate before
`_AUTHORITY_RANK.index()` is ever called on them — the function cannot be invoked cross-kind by
construction, it is not merely "conceptually different." (Also worth flagging: `_AUTHORITY_RANK`
is a bare 3-tuple; `_AUTHORITY_RANK.index("unrated")` would raise `ValueError` if it were ever
reached — it never is today, but this is a latent trap if `_CONFLICT_ELIGIBLE_FRESHNESS` were
ever widened without also widening `_AUTHORITY_RANK`.)

**`candidate.score` is not a comparable cross-kind signal today** — a second concrete technical
fact:
- `candidate_from_hybrid_result()` (L144-165) sets `score = result.rrf_score`, a real
  reciprocal-rank-fusion float in the neighborhood of `sum(1/(60+rank))` per matching channel
  (`DEFAULT_RRF_K = 60`, `hybrid_retrieval.py` L37) — typically a small positive float,
  query-dependent.
- `unrated_candidate()`/`candidate_from_code_index_record()` (L98-137) default `score = 0.0`
  always (no caller in this codebase currently passes a non-default score for `code_symbol`).
- `candidate_from_parity_ledger_fixture()` (L205-224) hardcodes `score = 0.0` (L220) — parity
  entries carry no similarity/relevance score at all today.

A naive "sort all candidates by `.score` descending" would tie every `code_symbol` and
`parity_ledger_entry` candidate at `0.0` regardless of actual relevance, while ranking real
`HybridResult`-derived docs/tickets by a differently-scaled RRF float. This is a structural gap
in the current code, independent of any value judgment about priority — score-based cross-kind
ranking cannot be "the answer" without a prior (out-of-scope) normalization fix.

**`tools/hybrid_retrieval.py`** — confirmed genuinely single-corpus. `reciprocal_rank_fusion()`
(L59-77) fuses named channels (`"dense"`, `"lexical"`) of the **same query** into one score per
`doc_id` — both channels query the same `knowledge_docs`/`knowledge_vec` tables
(`_dense_candidates()` L193-210, `_fetch_row_by_doc_id()` L213-221). `filter_candidates()`
(L127-156) is a pre-fusion `authority_in`/`freshness_in` allow-list filter over that same single
result set — it excludes candidates from fusion, it does not compare across separately-sourced
kinds like `code_symbol` or `parity_ledger_entry` (neither of which ever reaches
`hybrid_retrieval.py` — those are built by `context_packet_assembler.py`'s own adapters from
different source modules entirely, `code_test_index.py` and hand-built fixtures respectively).
`resolve_metadata()` (L104-120) resolves `kind` for a `hybrid_retrieval.py` row from
`_SOURCE_TYPE_TO_KIND` (L47-52: `doc_chunk→doc`, `ticket→ticket`, `investigation→investigation`,
`working_log→working_log`) — it has no branch for `code_symbol` or `parity_ledger_entry` at all;
those kinds are produced entirely outside this module.

**`tools/parity_index.py`** — `impact()` (L534-593) confirmed same-kind-only. Its `results` list
(L558-573) is built exclusively from rows in `doc_refs`/`code_refs`/`test_refs` joined against
the `entries` table by `entry_id` (L560-562) — every row in `results` is a parity-ledger entry
reference; there is no branch anywhere in `impact()` that mixes in a doc/ticket/code_symbol row.
The sort key (L575-581): `(_PRIORITY_ORDER.get(priority, 99), _STATUS_SEVERITY.get(status, 99),
entry_id)` — `_PRIORITY_ORDER = {"P0":0,"P1":1,"P2":2}` (L79), `_STATUS_SEVERITY =
{"divergent":0,"missing":1,"unsupported":2,"verified":3,"legacy_verified":4}` (L78) — ranks
parity entries against each other only (worst-first: most-divergent P0 sorts first). This
establishes an **intra-kind severity ordering convention** (priority first, then how "broken"
the entry is) that is a second same-kind precedent worth citing alongside
`_resolve_subject_conflicts()`, but it is exact-structural-lookup output (`impact()` answers "what
parity entries reference this changed path"), never a cross-kind candidate list.

## Mechanics / Engine Constraints

This is agent-orchestration/retrieval tooling under `docs/engine/contracts/`, not simulation
logic — no `docs/mechanics/*` chapter constrains it. The binding constraint is
`docs/engine/contracts/context_packet_contract.md` §3 itself:

- §3's non-registry-backed fallback rule states the `unrated` sentinel "must never imply
  otherwise by, for example, defaulting to P2/historical as if that were a real registry read."
  This is a direct textual constraint on any cross-kind ordering this ticket proposes: an
  ordering that silently ranks every `unrated` candidate at or below `P2` would functionally
  reproduce exactly the fabricated-default behavior §3 prohibits, even though §3 was written
  about a single entry's own field population, not inter-candidate ranking. The decision doc
  must not treat "unrated sorts last" as a free technical default — it collides with existing
  contract language and needs the same explicit-judgment treatment as the rest of Decision 7.
- §3's parity extension states the parity ledger's `priority`/`status` are "a second,
  differently-shaped vocabulary... must never be silently coerced into REGISTRY's enum space."
  Any cross-kind ordering that tries to merge `priority` (P0-P2) and REGISTRY `authority`
  (P0-P2) onto one shared numeric scale needs to state explicitly that it is doing so
  deliberately (the values are lexically identical but semantically distinct: one is "how much
  do we trust this doc," the other is "how severe is this parity gap") — collapsing them without
  comment would be exactly the kind of silent coercion §3 forbids.
- `ticket_plan_structure_opendecisions_7_9.md` (item 1, read in full) is the authoritative
  scoping doc for this ticket and explicitly permits "declare undecidable-yet-and-why" as a
  valid resolution, provided the reasoning is grounded in cited precedent rather than asserted.

## Docs Requiring Update

- `docs/engine/contracts/context_packet_contract.md`: add a new §5 (or similarly-numbered
  addendum section, after existing §4 "Verification Path") resolving Open Decision 7 — per the
  ticket's Scope, §3's existing resolved text must not be edited in place.
- `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`: OPEN DECISION 7's entry
  (currently `**UNRESOLVED**`, lines 174-179) must be updated to record the resolution (or the
  explicit "needs human sign-off" outcome) and point to the new decision doc/addendum, mirroring
  how OPEN DECISION 1/2/3/4/5/6 each record `**RESOLVED**` plus a one-paragraph summary and a
  citation to their own decision doc. This is not listed as a separate line item in the ticket's
  own Scope, but is required by the same pattern every prior sibling decision ticket followed
  (confirmed by reading all six existing OPEN DECISION entries in that epic ticket) — omitting it
  would leave the epic's own tracking doc silently stale.
- A new `docs/ai/*_decision.md` file may or may not be needed depending on the Plan phase's
  choice of location: the ticket's Scope says "extend
  `docs/engine/contracts/context_packet_contract.md` with a new section/addendum," which reads as
  the primary/sole required doc change, distinct from Decisions 1/2/5/6 which each got a
  standalone `docs/ai/*_decision.md` file cited *from* the epic ticket. Decision 3 (the directly
  analogous "extends context_packet_contract.md itself" precedent) did **not** get a separate
  `docs/ai/` file — it was resolved entirely inside the contract doc's own §3. Decision 7 is the
  same shape of question (extending the same contract), so following Decision 3's precedent (one
  doc, no separate `docs/ai/*_decision.md`) is defensible and matches this ticket's explicit
  Scope wording more literally than Decisions 1/2/5/6's pattern. This is a Plan-phase call, not
  resolved here — flagged as an open question below.

## Parity Ledger Overlap

No `docs/parity_ledger/*.yaml` entry applies. This mirrors the posture already recorded in
`context_packet_contract.md` §4: "this contract governs agent-orchestration/retrieval tooling,
not simulation logic," the same posture as `docs/parity_ledger/infrastructure.yaml`'s INFRA-281
through INFRA-292 entries (`support_boundary` field, confirmed present and `null` on every
INFRA-28x/29x entry checked). `docs/parity_ledger/infrastructure.yaml` does contain entries
referencing `context_packet_assembler.py` (INFRA-294/295/296/297/298/299, found via grep on
"context_packet"/"CONTEXT-PACKET" — lines ~6109-6363) but these cover the assembler's already-
shipped field-shape/hash/exclusion-summary behavior from `TCK-20260729-CONTEXT-PACKET-ASSEMBLY`,
not the cross-kind ranking gap this ticket addresses, and this ticket makes no code change to
touch their `v2_evidence`. No update to any existing entry is required; no new entry is required
(decision-doc-only ticket, no code change, same reasoning §4 already gives for why Decision 3
needed no ledger entry).

## Prior Work

- `docs/ai/default_packet_scenarios_decision.md` (Decision 1) and
  `docs/ai/code_test_index_boundaries_decision.md` (Decision 2) — read in full as the shape/rigor
  precedent this ticket must match: both open with a verbatim quote of the Open Decision being
  resolved, ground every claim in a cited, re-verifiable artifact (a tool's real output or direct
  source inspection, never assumption), explicitly separate "resolved" from "deferred pending a
  named gap," and close by updating the epic ticket's OPEN DECISION N line rather than editing
  the idea doc directly. Decision 7's doc should follow this same skeleton.
- `context_packet_contract.md` §3 itself is the closest structural precedent for *how* to extend
  the contract in place (its own "Extension — non-registry-backed source fallback" and "Extension
  — conflicting active documents" subsections were added as call-outs after the core resolution,
  explicitly marked as this-ticket's-addition) — Decision 7's new section should use the same
  "Extension —" heading convention for consistency, and should explicitly cross-reference §3
  rather than duplicate its non-registry-backed-fallback explanation.
- `TCK-20260731-PARITY-INDEX-EPIC` (referenced in Related Tickets) is the ticket whose
  `parity_ledger_entry` read path landing is what surfaced this gap — not separately re-read in
  full here since the ticket text and `parity_index.py`'s current state already capture what's
  needed; no additional prior-work artifact from that epic was found to be directly reusable
  beyond the `impact()` severity-ordering convention already covered above.

## Risks and Open Questions

- **Primary open question (Plan-phase decision needed):** does the new content live entirely
  inside `context_packet_contract.md` as a new §5 (matching Decision 3's own precedent of
  resolving in-place), or does it also need a standalone `docs/ai/*_decision.md` file (matching
  Decisions 1/2/5/6's pattern)? The ticket's own Scope text ("Extend
  docs/engine/contracts/context_packet_contract.md with a new section/addendum") reads as
  suffient on its own; recommend defaulting to contract-only unless the Plan phase finds a
  concrete reason two files are needed.
- **Does Decision 7 resolve to a concrete ordering, a partial ordering with explicit
  undecided remainder, or a full "needs human sign-off" punt?** See the independent assessment in
  this agent's final response — three concrete technical findings (the `unrated`-must-not-
  default-to-worst constraint, the score non-comparability gap, and `_resolve_subject_conflicts`'s
  structural inapplicability) narrow the space without fully resolving it. The decision doc
  should state plainly which parts are technically derived vs. which remaining part is a genuine
  value judgment — collapsing the two into one flat "undecidable" verdict would understate what
  was actually found, and collapsing them into one flat "resolved" verdict would overstate it.
- **No existing test-file convention exists** for asserting a `docs/ai/*_decision.md` (or a
  contract addendum)'s required content — verified by search: none of Decisions 1/2/5/6 have a
  corresponding test file asserting their content, and grep for `_decision.md`/`decision.md` in
  `tests/` under `tools/` turns up nothing (the `decision` hits under `tests/unit/`,
  `tests/integration/` are unrelated simulation-domain "decision service" tests — adventure/
  faction/cooperation/progression decision phases — a false-positive naming collision, not the
  pattern the ticket's own note speculated might exist). This ticket would be the first of its
  kind to introduce such a test if the Plan phase decides one is warranted; not doing so is
  equally defensible since Decisions 1/2/5/6 shipped without one.

## Anti-Drift Hazards

- Do not edit `context_packet_contract.md` §3's existing resolved text (Decision 3) even
  incidentally while adding the new section — the ticket's Out of Scope and its own Scope line
  are explicit about this, and §3's "Extension —" subsections are easy to mistake for editable
  scaffolding since they already use the same heading pattern the new section will reuse.
- Do not let the new section imply a concrete numeric priority scale that silently coerces
  `unrated`/parity `priority`/REGISTRY `authority` onto one shared number line without saying so
  explicitly — this is the exact silent-coercion trap §3 already warns against for the
  single-entry case.
- Do not scope-creep into Decisions 8 or 9 — `ticket_plan_structure_opendecisions_7_9.md` groups
  all three under one planning doc, and it would be easy to drift into commenting on the
  `stored_artifact` kind (Decision 8) or the exact-vs-fuzzy lookup convention (Decision 9) while
  writing about `kind` vocabulary in general. Stay confined to ranking/selection between already-
  existing kinds.
- Do not touch `tools/context_packet_assembler.py`, `tools/hybrid_retrieval.py`,
  `tools/parity_index.py`, or `tools/generate_registry.py` — confirmed by this investigation that
  none of them currently implement any selection/ranking-against-budget logic at all, so there is
  no small, tempting one-line fix available; the absence of code to lightly touch should not be
  read as license to add a minimal implementation "just to be concrete" — that is explicitly Out
  of Scope.
- Do not silently skip updating the epic ticket's OPEN DECISION 7 entry — every sibling decision
  ticket updated it, and it is easy to treat "Related Tickets" as read-only context rather than a
  required update target.

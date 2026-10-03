---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT
artifact_type: investigation
tags: [ai, mcp]
---

# Investigation — TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT

## Current Behavior

### Context-scan tools run first (per CLAUDE.md), findings summarized
`mcp__knowledge-search__search_docs` (3 queries: packet-assembly/dedup/budget, token-budget/
CachedPacket budget fields, evidence-identity/conflict-handling) surfaced
`docs/plans/knowledge-gateway-mcp-proposal.md` §15/§14/§5/§1, `tickets/done/TCK-20260815-KGMCP-P1-
PACKET-ASSEMBLY`, and `docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md`
as the top-ranked real hits — consistent with the ticket's own "Related Docs" citations, no new
undiscovered doc surfaced. `graphify query "assemble_packet knowledge_gateway_packet_assembly"`
returned the real, live call graph for the module under investigation, confirming **`deduplicate_
statements()`, `_dedup_key()`, `assemble_within_budget()`, and `build_conflicts()`/`Conflict`
already exist as real symbols in `tools/knowledge_gateway_packet_assembly.py`** — this is the
single most important finding of this investigation and reframes the ticket's own Request Summary
premise (see "Ticket Premise vs. Reality" below). Both tools were called before any grep/file read,
per the Hard Rule.

### `tools/knowledge_gateway_packet_assembly.py` — read in full (667 lines)

**Ticket premise vs. reality (must be reported honestly, not silently corrected in Scope).** The
ticket's Request Summary states `assemble_packet()` "does not deduplicate context items collected
from multiple providers... and does not enforce a caller-supplied `budget_tokens` against the real
measured output size." Direct read of the live module shows **both mechanisms already exist as
real, tested code**, added by the DONE `TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY`:

- `deduplicate_statements()` (lines 328-352) already runs across the combined `context_search` +
  `graphify` statement list (both providers' `render_candidates()` output is concatenated into one
  `statements` list before dedup runs — `assemble_packet()` line 596-597) — this **is** genuine
  cross-provider deduplication, not per-provider. `test_duplicate_fact_across_two_providers_yields_
  one_statement_two_evidence_ids` (`tests/tools/test_knowledge_gateway_packet_assembly.py:289-302`)
  already asserts exactly this ticket's AC1 shape (`len(packet.statements) == 1`, `len(evidence_ids)
  == 2`) and passes today.
- `assemble_within_budget()` (lines 525-552) already measures cost via the real, frozen
  `kgmcp_char_heuristic_v1()` per statement (never `len(candidates) * constant`), greedily includes
  statements in `(priority_tier, original order)` sort until the running total would exceed
  `budget_requested`, and returns `budget_returned` as the literal running total — `budget_returned
  <= budget_requested` holds by construction. `assemble_packet(routing_decision, query_text,
  budget_requested)` (line 585) already takes a real budget parameter and threads it through.
  `tools/knowledge_gateway_mcp.py::_run_knowledge_context()` line 190 already computes
  `effective_budget = budget_tokens if budget_tokens is not None else DEFAULT_BUDGET_TOKENS` and
  passes it to `assemble_packet()` at line 239 — **`budget_tokens` already reaches
  `assemble_packet()` today; it is not stuck at the `DEFAULT_BUDGET_TOKENS` fallback.** This
  directly answers the ticket's own framing question in the prompt: budget_tokens is not "currently
  unused past the fallback" — it is live, wired, and already governs real truncation.

This does not mean the ticket has no real work — see "The Real Gaps" below — but Plan/Implement must
build on top of this existing, tested mechanism, never re-describe it as absent, and must not
duplicate `deduplicate_statements()`/`assemble_within_budget()` with a second, parallel
implementation.

### The real gaps (what this ticket must actually add)

**Gap 1 — dedup identity is text-equality, not the evidence-identity concept the ticket asks to
reuse.** `_dedup_key()` (line 324-325) is `" ".join(statement.text.strip().casefold().split())` —
a bespoke normalized-text key invented for this purpose, not a reuse of any evidence-identity
concept. Cross-referenced against `evidence_identity_kinds.schema.json` (read in full, path
confirmed real — see "Deduplication Identity" below): every one of the 8 closed kinds names its
`preferred_fingerprint` as "Content hash (sha256) of ..." — i.e., the identity concept this repo's
own contract already establishes for "is this the same evidence" is **content hash**, not
casefold-normalized text. `render_candidates()` (lines 233-319) already computes exactly this hash
for every result — `evidence_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()` (lines
252/288) — and stores it on `ContextEntry`/`EvidenceEntry`, but **`Statement` carries no
`evidence_hash` field and `deduplicate_statements()` never consults it.** Since `evidence_hash` is
computed from the exact same `text` value the dedup key is derived from, switching `_dedup_key()`
to `hashlib.sha256(statement.text.strip().encode("utf-8")).hexdigest()` (or threading the
already-computed `evidence_hash` through onto `Statement`) is a minimal, backward-compatible change
that directly satisfies the ticket's own Scope instruction ("reuse... whatever identity the
existing evidence-kind normalization already establishes... rather than inventing a new identity
concept") — the current casefold-normalize key **is** the "invented" concept the ticket's own Scope
warns against; a content-hash key would retire it in favor of the frozen contract's own vocabulary.
Verified this is behavior-compatible with every existing dedup test: both `test_duplicate_fact_
across_two_providers_yields_one_statement_two_evidence_ids` and `test_deduplication_occurs_before_
truncation_not_after` use byte-identical shared text across the "duplicate" pair, so a hash-based
key produces the same grouping. The only behavioral difference is that hash-based dedup is
*stricter* (case/whitespace-sensitive) than casefold dedup — which is the correct direction, since
the ticket's own Out of Scope explicitly forbids "semantic/fuzzy deduplication... this ticket
deduplicates only on exact/structural evidence identity" and casefold-normalization is already a
small step toward fuzziness the ticket does not authorize.

**Gap 2 — dedup has zero awareness of the conflict-signal keys `build_conflicts()` checks, which is
a real, evidenced correctness risk, not a hypothetical one.** `assemble_packet()`'s fixed order
(module docstring, lines 586-589) is: render -> **dedup (step 5)** -> negative-claim -> **conflicts
(step 7)** -> budget truncation. `deduplicate_statements()` operates purely on `Statement.text`
equality with **no visibility into** the `superseded_by`/`supersedes`/`incompatible_with` signal
keys `_structural_supersession_signal()` (lines 461-496) checks on the *raw* provider-result dicts.
Today's only conflict test (`test_conflict_only_surfaces_real_supersession_metadata`,
`tests/tools/test_knowledge_gateway_packet_assembly.py:380-392`) deliberately uses **different**
excerpt text for the "old"/"new" pair ("old value"/"new value"), so dedup never has a chance to
collide them — this test does not actually exercise the risk. If two provider results are flagged
as mutually conflicting (`superseded_by`/`incompatible_with`) but happen to render **identical**
text (a realistic case: two sources stating the same fact but disagreeing on `valid_to`/authority,
or a doc superseding another doc that still contains a byte-identical restated sentence),
`deduplicate_statements()` would silently merge them into one `Statement` (only the evidence_ids
list grows) while `build_conflicts()` — which runs on the raw, un-deduped result list, independent
of what dedup did — would still separately emit a non-empty `conflicts[]` entry for the same
subject. The resulting packet would carry `status: "CONFLICTED"` (since `conflicts` is non-empty)
alongside a `statements`/`answer` that has already silently unified the two claims into one
sentence with two evidence references — exactly the "silently-resolved item" the ticket's own
Out-of-Scope/AC4 explicitly forbids ("deduplication must only ever collapse identical evidence,
never conflicting claims presented as if agreeing... reuse [CONFLICTED handling], do not invent a
parallel conflict-suppression path"). **This is the one place this ticket must write genuinely new
logic, not just a genuinely new test** — `deduplicate_statements()` (or the `assemble_packet()`
orchestration around it) needs some mechanism to exclude conflict-flagged pairs from being merged
even when their rendered text is identical. See Risks and Open Questions for the concrete
implementation-ordering tension this creates (conflicts are currently computed *after* dedup).

**Gap 3 — no visible truncation marker; "never silent" is not yet satisfied.** `PacketAssembly`
(lines 557-572) carries `budget_requested`/`budget_returned` but nothing that lets a caller
distinguish "budget_returned is smaller than budget_requested because that's genuinely everything
the providers had" from "budget_returned is smaller because real content was dropped to fit the
budget." `assemble_packet()` already has every piece of information needed to compute this
(`statements` after dedup vs. `included_statements` after `assemble_within_budget()` — the length
delta is the omitted count) but does not surface it anywhere in `PacketAssembly` or in
`knowledge_gateway_mcp.py`'s response-dict construction (lines 241-251). This is the concrete,
required, new field-level work for AC2/AC3.

### `tools/knowledge_gateway_mcp.py::_run_knowledge_context()` — read in full (lines 149-280+)
Confirms the budget-flow finding above precisely: `budget_tokens` (Optional[int] param, line 152)
-> request dict -> schema-validated -> `effective_budget` (line 190, falls back to
`DEFAULT_BUDGET_TOKENS = 4000` only when the caller omits the field entirely) -> Level 1 cache
lookup (`perform_cache_lookup(request, routing_decision, effective_budget)`, line 228 — a cache HIT
returns immediately at line 232-237, **never calling `assemble_packet()` at all**) -> on a cache
miss, `packet = _kgpa.assemble_packet(routing_decision, query, effective_budget)` (line 239) ->
`packet.budget_requested`/`packet.budget_returned` copied verbatim into the response dict (lines
248-249). No transformation, re-derivation, or override of the budget value happens between the
caller's request and `assemble_packet()`'s parameter — the flow is a straight pass-through.

## Mechanics / Engine Constraints

Agent-orchestration/retrieval tooling, not simulation logic — no Mechanics Bible chapter or core
engine contract (`kernel.md`/`authoritative_pipeline.md`) governs this module, consistent with
every existing `infrastructure.yaml` entry for this subsystem (e.g. INFRA-336, INFRA-345, INFRA-346
all state this explicitly in their `support_boundary` field). The governing "laws" are this
subsystem's own frozen contracts:
- `docs/plans/knowledge-gateway-mcp-proposal.md` §15 (Token-Budgeted Assembly — binding on
  truncation order/measurement method), §14 (Conflict Handling — binding on what counts as a
  conflict and how it must be represented), §5 Goal 4/9 (budget + non-fabricated-consensus goals).
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_identity_kinds.schema.json` (binding on
  what "same evidence" identity means — content hash per kind, see Deduplication Identity below).
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §5/§8 (binding on the
  distinction between the payload-size-cap's "reject not truncate" rule and the
  `kgmcp_char_heuristic_v1` ±20% tolerance the budget-enforcement bar itself is measured against —
  see Open Question 1 resolution below).

## Docs Requiring Update

- `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json`: add the new
  visible budget-truncation marker field(s) (naming to be finalized by Plan, e.g. `budget_truncated`
  boolean + `omitted_statement_count`/`omitted_items_count` integer) to the `properties` block. Not
  a frozen document — it already gained `cache`/`cache_key_version` as real additive amendments
  during Phase 2 (`TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`), establishing the precedent that
  this schema evolves with each phase's real field additions, unlike `cache_migration_plan.md`/
  `evidence_cache_identity_contract.md` which explicitly declare themselves frozen. Note:
  `additionalProperties` is deliberately open at the top level (per the schema's own description),
  so a response carrying the new field(s) without a schema change would not fail validation — the
  update is still required for documentation/parity honesty, not to avoid a validation failure.
- `docs/parity_ledger/infrastructure.yaml`: new entry required, next real ID is **INFRA-347**
  (confirmed live: 346 real `INFRA-` entries exist today, max is INFRA-346, the sibling schema
  ticket's own entry) — describing the real dedup-identity change and the new budget-truncation
  marker, mirroring INFRA-336's (Phase 1 packet assembly) and INFRA-346's own level of citation
  detail.
## Docs Considered But Not Required (resolved during Document-Update, not left open)

- `docs/plans/knowledge-gateway-mcp-proposal.md` §20: originally flagged above (in an earlier draft
  of this investigation) as requiring annotation, per the epic's own Acceptance Criterion "§20's
  Phase 3 bullets are annotated Done as child tickets land." **Resolved as NOT required**, for a
  substantive reason, not an oversight: `deduplicate_statements()`/`assemble_within_budget()`/
  `kgmcp_char_heuristic_v1()` already existed as real, tested code before this ticket ran, built by
  the earlier `TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY` ticket (confirmed by the corrected `INFRA-336`
  entry). This ticket hardens those mechanisms (content-hash dedup identity, the conflict-vs-dedup
  safety fix, the budget-truncation visibility marker) but does not originate either the "Assemble
  deduplicated multi-provider packets" or "Enforce caller budgets using measured output size"
  bullet's core capability. Marking either bullet **Done** under this ticket's own name would
  misattribute origination to the wrong ticket, so §20 was deliberately left unmarked. This is the
  final resolution — not an open item for a later ticket to pick up. Whether either bullet should
  instead be retroactively marked Done under `TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY`'s own name (the
  ticket that actually built the underlying capability, even though the proposal's own phase
  boundaries didn't anticipate it landing that early) is a real, separate question this ticket does
  not resolve — flagged for the Phase 3 epic's own closure evaluation to consider, not decided here.

None of the Mechanics Bible chapters (`docs/mechanics/`) or core engine contracts require any
change — this subsystem is explicitly outside their scope (see Mechanics/Engine Constraints above).
`docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md`,
`evidence_cache_identity_contract.md`, and `evidence_identity_kinds.schema.json` must **not** be
edited — all three are frozen design docs from DONE tickets, and this ticket introduces no new
evidence-identity kind (it reuses the existing content-hash fingerprint concept, it does not add a
9th kind).

## Parity Ledger Overlap

- `INFRA-336` (`docs/parity_ledger/infrastructure.yaml`) — Phase 1 packet assembly, covers
  `deduplicate_statements()`/`assemble_within_budget()`/`build_conflicts()` as originally shipped.
  This ticket modifies the dedup-identity mechanism and adds new budget-visibility fields on top of
  that same code — re-verify INFRA-336's own line-range citations for drift once this ticket's
  diff lands (same caveat the sibling schema ticket's own investigation already flagged for
  INFRA-341/343 in its own subsystem).
- `INFRA-345` (size-cap recalibration hotfix) — its own `support_boundary` text explicitly states
  "no change to what gets cached (response envelope shrinking, field exclusion, compression — **that
  remains Phase 3's explicit 'Enforce caller budgets using measured output size' deliverable, out of
  scope here**)" (confirmed by direct read, `docs/parity_ledger/infrastructure.yaml:9442-9444`) —
  direct, in-ledger confirmation that this ticket's own budget-enforcement work was explicitly
  deferred here and is now this ticket's job to close.
- `INFRA-346` (sibling schema ticket) — no functional overlap (schema-only, this ticket never
  touches `tools/retrieval_cache.py`), but shares the same epic and subsystem file.
- No P0 entries are touched by this ticket's scope — the KGMCP subsystem's existing entries in this
  ledger are consistently P1/P2 (INFRA-336, INFRA-345, INFRA-346 all confirmed P1 by direct read).
  The new INFRA-347 entry this ticket adds should also be P1, consistent with that pattern, not P0
  (no `test_path` gate gap gate risk from a P0 misclassification).

## Prior Work

- `TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY` (DONE) — shipped the real `assemble_packet()`,
  `deduplicate_statements()`, `assemble_within_budget()`, `build_conflicts()` this ticket extends.
  Its own module docstring's "Honesty notes" (lines 17-37) already document, in the same style this
  ticket's own investigation continues, exactly which branches (`build_conflicts()` against real
  providers, `NegativeClaimSupport` SCOPED/COMPLETE) are real-but-currently-unreachable against live
  Phase 1 provider data — the same honesty discipline this investigation applies to the dedup/budget
  gaps above.
- `TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE` (DONE) — shipped `_run_knowledge_context()`'s real
  `budget_tokens` -> `effective_budget` -> `assemble_packet()` wiring this investigation traced.
- `TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION` (DONE) — its own `INFRA-345` entry is the
  direct textual precedent (quoted above) confirming budget-enforcement-as-response-shrinking was
  explicitly deferred to this ticket, not silently assumed done.
- `TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS` (DONE, sibling child 1) — no code
  dependency on this ticket (confirmed by the epic framing and by this ticket's own Out of Scope);
  its investigation.md was read for artifact-shape/rigor precedent only, not for technical content
  this ticket reuses (schema-only work, disjoint file set: `tools/retrieval_cache.py` vs.
  `tools/knowledge_gateway_packet_assembly.py`).

## Risks and Open Questions

**1. Budget-enforcement tolerance mechanism — resolved.** §5's "reject not truncate, never silently
incomplete" rule (`redaction_retention_policy.md:119-124`) governs the **cache payload write-time
size cap** (`MAX_PAYLOAD_BYTES`, a hard technical ceiling on what can be persisted to a single SQLite
row) — a fundamentally different concern from a caller's *requested* `budget_tokens` on a
`knowledge_context` read, which §15 already frames as an optimization/prioritization problem
("optimize packet content in this order... 1. Hard invariants... 5. Optional background"), not a
pass/fail gate. §15 explicitly authorizes partial delivery ("Deduplication should occur before
truncation" presupposes truncation is a normal, expected outcome, not a rejection). §5's model does
not transfer: rejecting an entire `knowledge_context` response because the caller's budget was
smaller than the full available content would violate §5 Goal 4 ("Return useful context within a
caller-provided token budget") by returning *nothing* instead of the best-fitting partial answer.
The existing `assemble_within_budget()`/§16 budget-assembly-failure fallback already implements the
correct partial-delivery model (drop lowest-priority statements, and only fall back to an
empty/PARTIAL packet in the genuine edge case where the budget cannot fit even the single
cheapest/highest-priority statement). **Resolution: extend the existing partial-delivery model with
a visible marker, do not adopt §5's reject-whole-payload model.** The response schema already has no
existing field for this (confirmed by direct read of `knowledge_context_response.schema.json` above
— only `budget_requested`/`budget_returned` integers exist, no boolean/count marker) — so naming and
adding the marker field(s) is real, undecided work for Plan, not something this ticket can skip by
finding an existing field to reuse.

**2. Deduplication identity — resolved.** `evidence_identity_kinds.schema.json`'s real path is
`docs/engine/contracts/knowledge_gateway_mcp/evidence_identity_kinds.schema.json` (confirmed, matches
the ticket's own citation exactly — no path correction needed). It defines a closed 8-kind enum
(`DOCUMENT`, `DOCUMENT_SECTION`, `FILE`, `SYMBOL`, `TICKET`, `PARITY_ENTRY`, `REGISTRY_ENTRY`,
`PROVIDER_GENERATION`), each with a `stable_identity_form` (the `doc:`/`file:`/`symbol:`/`ticket:`
prefix forms `_evidence_id_for_*()` already implements) and a `preferred_fingerprint` — **for all 7
content-bearing kinds, "Content hash (sha256) of..."** is the stated fingerprint; only the coarse,
fallback-only `PROVIDER_GENERATION` kind has none. This is the identity concept to reuse: content
hash, which the module already computes as `evidence_hash` for every rendered result but never
threads into dedup (see Gap 1 above). **A structural note that complicates naive identity-based
(evidence_id) dedup, evidenced directly**: `_evidence_id_for_context_search_result()`'s duplicate-
anchor disambiguation (lines 100-125, `anchor_counts`) deliberately makes two DOCUMENT_SECTION
results sharing a heading get *different* `evidence_id`s (`#overview`, `#overview-2`) even when their
`excerpt` content is byte-identical — so evidence_id-based dedup would under-collapse relative to
today's (and the recommended hash-based) approach. **Recommendation for Plan: dedup key = content
hash of the rendered statement text (already computed elsewhere as `evidence_hash`), not the
`evidence_id` string itself.**

**3. Conflict-vs-duplicate boundary — partially resolved, one real open implementation question for
Plan.** §14 (`proposal.md`) and the already-real `build_conflicts()`/`Conflict`/`ConflictClaim`/
`CONFLICTED` status path are the existing, real machinery this ticket must hook into — **not**
entirely new logic, contrary to the ticket's own Assumptions framing ("is there already a real code
path... or is this entirely new logic"). The genuinely new, undecided piece is *how* dedup becomes
aware of conflict-flagged pairs given the current fixed step ordering (dedup at step 5, conflicts
computed at step 7, from the raw un-deduped result list) — seetGap 2 above for the concrete
evidenced risk. Two implementation directions exist and neither is obviously mandated by the frozen
docs, so Plan must decide explicitly, not silently:
  (a) Compute (or partially compute — just the structural-signal pairing, not full `Conflict`
      construction) conflict-participant identification *before* dedup runs, and pass an exclusion
      set of "do not merge these" text-keys/indices into `deduplicate_statements()`.
  (b) Reorder so `build_conflicts()` runs before dedup, and feed dedup a per-statement "is this
      statement part of any conflict pair" flag derived from the already-computed `conflicts[]`.
  Both preserve the current test suite's guarantees (`test_deduplication_occurs_before_truncation_
  not_after` only constrains dedup-vs-truncation ordering, not dedup-vs-conflict ordering); this is
  not a case of an existing test locking in one specific ordering already.

**4. Level 1 cache interaction — resolved, no interaction exists.** Confirmed by direct read of
`_run_knowledge_context()`: the Level 1 cache-lookup call (`perform_cache_lookup()`, line 228) runs
*before* `assemble_packet()` is ever called, and a genuine cache HIT returns immediately (line
232-237) without calling `assemble_packet()` at all. `assemble_packet()`'s dedup/budget logic
therefore only ever runs on the live-provider-call path, structurally, by construction — there is no
partial-cache-hit / partial-live-call mixed scenario to handle. This ticket's own scope is correctly
bounded to live provider outputs only, with zero cache-awareness needed.

**5. Naming collision risk for the new marker field(s), not yet flagged elsewhere.** Whatever name
Plan chooses for the truncation-visibility field(s) should avoid colliding with this subsystem's
already-crowded "budget"/"omitted" vocabulary — `provider_failures` (already an array-of-strings
field for a related-but-distinct "content is missing" concept) is the closest existing precedent for
"always-present, never-omitted-when-empty" field shape (see its own schema description: "Always
present as an array (possibly empty) — never a silent omission when a provider fails"). The new
marker should follow that same "always present, never omitted" precedent (a plain `false`/`0` when
nothing was truncated, not an absent key) to genuinely satisfy "never silent," which the response
schema's `_omit_none()`-based construction in `knowledge_gateway_mcp.py` (line 138-144) would
otherwise strip — Plan must ensure the new field(s) are added directly to the response dict, not
routed through `_omit_none()`, or a `False`/`0` value could theoretically look identical to an
omitted key to a loosely-written caller (schema-wise `False`/`0` are never `None` so `_omit_none`
would not actually strip them — this is a low risk, but worth an explicit test, see test_plan.md).

## Anti-Drift Hazards

- **Do not reimplement `deduplicate_statements()`/`assemble_within_budget()`/`build_conflicts()`
  from scratch** — they are real, DONE, tested code from Phase 1. This ticket's job is a targeted
  identity-key change to dedup, a conflict-awareness guard for dedup, and new visible-marker fields —
  not a rewrite. Re-describing existing working code as "not implemented yet" (per the ticket's own
  Request Summary, which this investigation found to be inaccurate) must not lead to a duplicate,
  parallel implementation.
- **Do not change `kgmcp_char_heuristic_v1()`'s formula or tolerance** — frozen at
  `redaction_retention_policy.md` §8, ratified, with its own dedicated parity test
  (`test_kgmcp_char_heuristic_v1_matches_frozen_formula`). Reuse the callable; the ticket's own Scope
  already says this explicitly.
- **Do not touch `tools/knowledge_gateway_router.py`** — explicit Out of Scope and Acceptance
  Criterion (byte-unchanged), verified today by `test_module_does_not_edit_knowledge_gateway_router`
  (runs the router's own test suite as a proxy signal, since the router file itself is untracked in
  this working tree).
- **Do not touch `tools/retrieval_cache.py` or any Level 1/Level 2 cache code** — this ticket's Out
  of Scope explicitly excludes Level 2 cache work (the sibling schema ticket's job) and this
  investigation confirms zero interaction exists with Level 1 (Risk/Open-Question 4 above). The
  existing `test_module_does_not_modify_or_import_retrieval_cache` guard (asserting `"retrieval_
  cache" not in source` and `"sqlite3" not in source`) must keep passing.
- **Do not silently switch dedup from exact/structural to semantic/fuzzy matching** — the ticket's
  own Out of Scope explicitly reserves that for Phase 5. The recommended hash-based identity key
  (Gap 1) is *stricter* than today's casefold key, moving further away from fuzziness, not toward
  it — any Plan/Implement approach that starts comparing statement texts by similarity score,
  embedding distance, or substring containment would violate this boundary.
- **Do not let the new budget-truncation marker collapse into the existing `status: "PARTIAL"`
  value alone** — `status` already means several different things (`budget_assembly_failed`,
  provider `failures`, or a truncated-but-non-empty result all currently map to `PARTIAL`,
  `assemble_packet()` lines 634-636) and a caller cannot currently distinguish "budget truncated some
  content" from "a provider failed" from either `status` or `provider_failures` alone in every case
  (a budget truncation with zero provider failures still reports `PARTIAL` with an empty
  `provider_failures` array today) — the whole point of AC2/AC3 is to add a distinguishing signal,
  not to reuse the already-overloaded `status` field for it.
- **Do not add a 9th evidence-identity kind or edit `evidence_identity_kinds.schema.json`** — the
  recommended dedup-identity change reuses the existing content-hash fingerprint concept already
  defined for the 7 real kinds; it does not need, and must not introduce, a new kind.

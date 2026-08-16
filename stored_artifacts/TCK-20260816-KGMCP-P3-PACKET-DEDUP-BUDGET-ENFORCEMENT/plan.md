---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT
artifact_type: plan
tags: [ai, mcp]
---

# Implementation Plan — TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT

> **Architecture-Review-mandated corrections (this revision).** The prior version of this plan
> received a `NEEDS_CHANGES` ruling from Architecture Review. This revision applies **exactly the
> two corrections that ruling required** — these are review-mandated corrections, not
> implementer-discovered deviations, and nothing else in the plan was re-derived or re-litigated.
> Claims 3/4/5 and the router/P0 checks were independently confirmed sound by that review pass and
> are unchanged here.
>
> 1. **Finding 1 — fail-loud correspondence check (AC4-critical).** Review confirmed the
>    `statements[i]` <-> raw-provider-result-index correspondence `_conflict_signal_index_pairs()`
>    relies on is genuinely correct today, but nothing previously caught a future silent desync if
>    `render_candidates()` or `_conflict_signal_index_pairs()`/`build_conflicts()` ever changed
>    independently — exactly the failure mode AC4 exists to prevent. A proportionate fix (not the
>    heavier explicit-source-index-on-`Statement` alternative) is now **Step 4**: a cheap, fail-loud
>    runtime cardinality assertion in `assemble_packet()`, plus a new test proving it raises loudly
>    (not silently) on desync. This also resolves item 1 of the former "Unresolved Questions"
>    section below.
> 2. **Finding 2 — single source of truth for the hash formula.** Review confirmed
>    `render_candidates()`'s `evidence_hash` computation and `_dedup_key()`'s hash fallback compute
>    the mathematically identical formula today, but as two independently-maintained
>    `hashlib.sha256(...).hexdigest()` literals that could silently drift apart on a future edit to
>    either one. Both call sites now route through one new shared helper, `_content_hash(text: str)
>    -> str` (folded into **Step 1** and **Step 2** below), plus a new guard test. This also
>    resolves item 2 of the former "Unresolved Questions" section below.

## Summary

`deduplicate_statements()` and `assemble_within_budget()` already exist as real, tested code in
`tools/knowledge_gateway_packet_assembly.py` (shipped by the DONE `TCK-20260815-KGMCP-P1-PACKET-
ASSEMBLY`) and `budget_tokens` already flows live from `_run_knowledge_context()` into
`assemble_packet()`. This plan does not rebuild either mechanism. It makes three narrow, additive
changes on top of them, all independently re-verified against the real source in this session (not
inferred from investigation.md's summary):

1. **Dedup identity switch** (Gap 1): retire `_dedup_key()`'s bespoke casefold-normalized-text key
   in favor of the content-hash fingerprint concept `evidence_identity_kinds.schema.json` already
   establishes. Concretely: add a new shared helper, `_content_hash(text: str) -> str`, as the
   single source of truth for the hash formula (Architecture-Review Finding 2); add a new
   `evidence_hash: Optional[str] = None` field to the `Statement` dataclass, populate it in
   `render_candidates()` by calling `_content_hash()` at the exact two sites that previously
   inlined `hashlib.sha256(text.encode("utf-8")).hexdigest()` for `ContextEntry`/`EvidenceEntry`
   (`tools/knowledge_gateway_packet_assembly.py:252`, `:288`), and have `_dedup_key()` prefer the
   threaded field, falling back to calling the same `_content_hash()` helper only for the handful of
   existing tests that construct `Statement` objects directly without going through
   `render_candidates()`.
2. **Dedup-vs-conflict guard** (Gap 2, the ticket's single most safety-critical piece, AC4): add a
   lightweight helper, `_conflict_signal_index_pairs()`, that reuses the existing
   `_structural_supersession_signal()` primitive `build_conflicts()` already calls — computed once,
   before dedup, over the same raw provider-result ordering `render_candidates()` uses to build
   `statements[]` (so result index `i` maps 1:1 to `statements[i]`). `deduplicate_statements()`
   gains an optional `conflict_index_pairs` parameter: when a new statement's dedup key collides
   with an existing group's key **and** the two statements' original indices are a known
   conflict-flagged pair, the new statement is forced into its own distinct group instead of being
   merged. This does not reorder the module's documented fixed pipeline (`assemble_packet()`'s own
   docstring, `tools/knowledge_gateway_packet_assembly.py:586-589`, "this ordering is load-bearing
   and must not be reordered") — dedup still runs at step 5, `build_conflicts()` still runs
   unmodified at step 7, and the ordering guarantee is untouched. It also does not invent a second,
   parallel conflict-detection heuristic — it calls the identical `_structural_supersession_signal()`
   function `build_conflicts()` already uses, just earlier, and only to extract index pairs. A new
   Step 4 (Architecture-Review Finding 1) adds a fail-loud runtime cardinality assertion in
   `assemble_packet()` immediately after `conflict_index_pairs` is computed, so a future silent
   desync between `render_candidates()`'s statement ordering and this helper's index assumptions
   raises `AssertionError` instead of silently corrupting AC4's guarantee.
3. **Budget-truncation marker** (Gap 3, AC2/AC3): add two new fields, `budget_truncated: bool` and
   `omitted_statement_count: int`, to `PacketAssembly`, computed immediately after
   `assemble_within_budget()` returns (`omitted_statement_count = len(statements) -
   len(included_statements)`, `budget_truncated = omitted_statement_count > 0`) — this single
   formula is correct in both the ordinary-truncation branch and the §16 budget-assembly-failure
   branch, verified by direct trace of both branches below. Thread both fields into
   `_run_knowledge_context()`'s response-dict construction as plain top-level keys (never routed
   through `_omit_none()`, so a `False`/`0` value is never confused with an absent key) and add both
   as new, non-required, additive properties to `knowledge_context_response.schema.json` (confirmed
   by direct read: neither field name collides with anything already in the schema's `properties`
   block, and the schema's own `required` list already excludes sibling fields
   `budget_requested`/`budget_returned`/`provider_failures` for the same reason — those are absent
   from the `ERROR`-path response shape). Verified by direct read of `tools/knowledge_gateway_
   cache.py` that **zero changes are needed there**: `perform_cache_write()` serializes the entire
   `response` dict verbatim (minus `cache`/`cache_key_version`, `tools/knowledge_gateway_cache.py:
   259`, `:298-305`) and `perform_cache_lookup()` returns `json.loads(lookup.row["result_payload"])`
   verbatim (`:249`) — the two new fields are cached and replayed on a HIT automatically, with the
   same coarse-`budget_class`-bucketing imprecision `budget_requested`/`budget_returned` already
   have today (a pre-existing cache-design property, not a new risk this ticket introduces).

No reimplementation of `deduplicate_statements()`/`assemble_within_budget()`/`build_conflicts()`
from scratch. No touch to `tools/knowledge_gateway_router.py`, `tools/retrieval_cache.py`, or
`tools/knowledge_gateway_cache.py`. No semantic/fuzzy dedup. No Mechanics Bible or engine-contract
chapter governs this subsystem (confirmed by investigation.md and re-confirmed here by the absence
of any `docs/mechanics/`/`docs/engine/kernel.md` citation anywhere in the module or its contracts) —
the governing law is this subsystem's own frozen `docs/engine/contracts/knowledge_gateway_mcp/*`
docs and `docs/plans/knowledge-gateway-mcp-proposal.md` §14/§15/§16.

## Design Decisions

### DD1 — Dedup identity: thread `evidence_hash` onto `Statement` via a shared `_content_hash()` helper, reuse it in `_dedup_key()`, fall back only for directly-constructed test fixtures

**Read directly, not inferred.** `render_candidates()` (`tools/knowledge_gateway_packet_assembly.py:
233-319`) computes `evidence_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()` twice — once
per `context_search` result (line 252) and once for the `graphify` result (line 288), both times on
the already-`.strip()`-ed `text` local (line 249: `text = result["excerpt"].strip()`; line 286:
`text = graphify_result["stdout"].strip()`) — and stores it on `ContextEntry`/`EvidenceEntry` in the
same loop iteration, but **`Statement` (lines 205-212) has no `evidence_hash` field today**, and
`_dedup_key()` (lines 324-325) is `" ".join(statement.text.strip().casefold().split())`, independent
of that hash entirely.

**Architecture-Review Finding 2 (this revision):** the two `hashlib.sha256(text.encode("utf-8")).
hexdigest()` call sites at lines 252/288 and this plan's own `_dedup_key()` fallback formula are
mathematically identical today, but as two independently-maintained inline literals they can
silently drift apart on a future edit to either one without the other. **Required correction:**
factor the formula into one new shared module-level helper, placed immediately above
`render_candidates()`:

```python
def _content_hash(text: str) -> str:
    """Single source of truth for the content-hash formula used both for
    ContextEntry/EvidenceEntry.evidence_hash (render_candidates()) and as _dedup_key()'s
    hash-based fallback for directly-constructed Statement test fixtures. Strips text
    internally so callers may pass either already-stripped or raw text safely -- render_
    candidates() passes already-stripped text (a no-op re-strip), _dedup_key()'s fallback
    passes statement.text directly.
    """
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()
```

**Chosen mechanism:** add `evidence_hash: Optional[str] = None` as a new trailing field on the
`Statement` dataclass, after the existing `verification: Optional[str] = None` field (dataclass
field-default ordering requires all fields after the first defaulted one to also have defaults —
`evidence_hash` gets the same `None` default, so this is a purely additive change). In
`render_candidates()`, replace both inline `evidence_hash = hashlib.sha256(text.encode("utf-8")).
hexdigest()` lines (252, 288) with `evidence_hash = _content_hash(text)`, and pass
`evidence_hash=evidence_hash` into both `Statement(...)` constructor calls (lines 254-263 and
290-299) — same computed value as today (the helper's internal `.strip()` is a no-op on the
already-stripped `text` local), just funneled through the one shared helper instead of an inlined
literal, in the real provider-call path.

**Why a fallback is needed, and why it is safe.** Four existing tests construct `Statement` objects
directly, bypassing `render_candidates()` entirely (confirmed by direct read of `tests/tools/
test_knowledge_gateway_packet_assembly.py`): `test_budget_returned_computed_by_real_kgmcp_char_
heuristic_v1_not_estimate` (lines 266-270), `test_budget_returned_never_exceeds_budget_requested`
(lines 281-284), `test_deduplication_occurs_before_truncation_not_after` (lines 306-307), and the
`_tier_statement()` helper (line 329, used by `test_priority_order_invariants_before_facts_before_
tests_before_history`). All four use only keyword arguments for every field after `evidence_ids`
(`priority_tier=...`), so adding a new trailing defaulted field breaks none of them structurally —
but none of them sets `evidence_hash`, so it stays `None` on those fixtures. `_dedup_key()` must
therefore fall back to computing the hash directly from `statement.text` when `evidence_hash` is
`None`:

```python
def _dedup_key(statement: Statement) -> str:
    if statement.evidence_hash is not None:
        return statement.evidence_hash
    return _content_hash(statement.text)
```

This fallback is mathematically identical to the threaded value (same `_content_hash()` call, same
stripped text) — it exists only to keep the four directly-constructed-`Statement` tests passing
without editing them, never exercised by the real `assemble_packet()` pipeline once Step 1 lands.
Because both the threaded value and the fallback now go through the single `_content_hash()`
helper (not two independently-inlined `hashlib.sha256(...)` literals), a future change to the
formula only has one call site to edit, and the new
`test_evidence_hash_and_dedup_key_share_single_content_hash_helper` guard test (Step 8) proves both
code paths actually call it rather than each carrying its own copy.

**Correction to investigation.md's identity-kind claim, verified directly against the real schema
file (`docs/engine/contracts/knowledge_gateway_mcp/evidence_identity_kinds.schema.json`, read in
full this session):** investigation.md states "for all 7 content-bearing kinds, 'Content hash
(sha256) of...' is the stated fingerprint." This is **not quite accurate** — `PARITY_ENTRY`'s
`preferred_fingerprint` (line 74) is "entry-id plus canonical_fragment_hash," not a bare sha256
content hash, and `REGISTRY_ENTRY` (line 84) is "the registry row's own content hash/version field
... else ... hashed" (hash-based, but conditionally, not uniformly "Content hash (sha256) of..." like
the other 5). This correction does not change the recommended mechanism: `_evidence_id_for_context_
search_result()`/`_evidence_id_for_graphify_result()` (the only two identity-derivation functions
this module calls) only ever produce `doc:`/`file:`/`ticket:`/`symbol:` forms — i.e. only
`DOCUMENT_SECTION`/`FILE`/`TICKET`/`SYMBOL` kinds (confirmed: no `parity:`/`registry:` prefix is ever
emitted by this module, per the closed-prefix test `test_evidence_id_uses_closed_evidence_identity_
kind_form`'s own `_CLOSED_EVIDENCE_ID_PREFIXES` tuple and this module's two identity-derivation
functions). All four of those kinds are unambiguously "Content hash (sha256) of..." per direct read
(lines 24, 34, 44, 54, 64). The `PARITY_ENTRY`/`REGISTRY_ENTRY` inaccuracy in investigation.md is
immaterial to this ticket's actual dedup-identity change, but is recorded here so it is not silently
carried forward as if independently re-verified.

**Behavior-compatibility re-verification (investigation.md's claim independently re-checked against
the live test file, not trusted at face value):** both `test_duplicate_fact_across_two_providers_
yields_one_statement_two_evidence_ids` (lines 289-302) and `test_deduplication_occurs_before_
truncation_not_after` (lines 305-325) use byte-identical shared text for the statements that must
merge — `shared_text = "Damage equals ATK minus DEF."` and `"SAME TEXT"` respectively, with no
case/whitespace variation between the "duplicate" pair in either test. A hash-based key produces
identical output for identical input, so both continue to pass unmodified. No existing test in the
file constructs two statements with case/whitespace-different but intended-to-merge text — confirmed
by reading every `_dedup_key`/`deduplicate_statements`-adjacent test in the file (lines 265-339); the
investigation's "backward-compatible with all existing tests" claim holds.

**Other readers/writers of `Statement.evidence_hash` (enumerated, per fact-verification
requirement):** `render_candidates()` (Step 1, the only writer in production code), `_dedup_key()`
(Step 2, the only reader). No other function in `tools/knowledge_gateway_packet_assembly.py`
constructs or reads a `Statement`'s fields selectively by name in a way `grep -n "\.evidence_hash"
tools/knowledge_gateway_packet_assembly.py` would need updating for — confirmed by direct read of
the full 667-line file above; `evidence_hash` as an attribute name exists today only on
`ContextEntry`/`EvidenceEntry`, never on `Statement`, so there is no existing reader to break.

**Other callers of `_content_hash()` (enumerated, per fact-verification requirement):**
`render_candidates()` (two call sites, replacing the two former inline `hashlib.sha256(...)`
literals at lines 252/288) and `_dedup_key()`'s fallback branch (Step 2) — exactly the same two
call sites this correction is meant to unify, no others. No other function in this module computes
a content hash today (confirmed by the same full-file read); `ContextEntry.evidence_hash`/
`EvidenceEntry.evidence_hash` are populated from the same `render_candidates()`-local
`evidence_hash` variable, not independently recomputed, so they inherit the shared helper's output
for free with no further edit.

### DD2 — Dedup-vs-conflict guard: index-pair exclusion computed once before dedup, reusing `_structural_supersession_signal()`; `build_conflicts()` itself is untouched

**The concrete risk (Gap 2), verified directly.** `_structural_supersession_signal()` (`tools/
knowledge_gateway_packet_assembly.py:461-496`) checks `superseded_by`/`supersedes`/
`incompatible_with` keys on raw provider-result dicts — fields `deduplicate_statements()` has never
had access to (it only ever sees rendered `Statement.text`). `build_conflicts()` (lines 499-520) runs
independently, at step 7, on the raw un-deduped result list. If two conflict-flagged results happen
to render byte-identical text, today's dedup (keyed purely on text) would silently merge them into
one `Statement` while `build_conflicts()` still separately emits a non-empty `conflicts[]` entry for
the same subject — a packet that is simultaneously `status: "CONFLICTED"` and has already
silently-unified the two claims in its own `answer`/`statements`. No existing test exercises this:
the one real conflict test, `test_conflict_only_surfaces_real_supersession_metadata` (lines 380-392),
deliberately uses different excerpt text (`"old value"`/`"new value"`) for its conflicting pair, so
dedup never has a chance to collide them.

**Chosen mechanism — two ordering options were considered, only one adopted:**

- (a) **Adopted.** Compute conflict-participant index pairs *before* dedup runs (reusing
  `_structural_supersession_signal()`), pass an exclusion set into `deduplicate_statements()`.
- (b) Rejected. Reorder so `build_conflicts()` itself runs before dedup and feed dedup a
  per-statement conflict flag derived from the already-computed `conflicts[]`. Rejected because
  `assemble_packet()`'s own docstring (lines 586-589) states the fixed order "dedup (step 5) ->
  ... -> conflicts (step 7) -> ... this ordering is load-bearing and must not be reordered" — option
  (b) would require rewriting that documented guarantee and moving `build_conflicts()`'s real call
  site, a larger and riskier change than necessary to close this specific gap. Option (a) needs no
  reordering: `build_conflicts()`'s own call site, inputs, and output are completely untouched.

**New helper**, added immediately above `deduplicate_statements()`:

```python
def _conflict_signal_index_pairs(
    context_search_results: list[dict], graphify_result: Optional[dict]
) -> set[frozenset[int]]:
    """Lightweight companion to build_conflicts() (Step 7): reuses the identical
    _structural_supersession_signal() detection primitive build_conflicts() already calls -- this
    is NOT a second, parallel conflict-detection heuristic, just an earlier, index-pair-only use of
    the same real function. Index i here corresponds 1:1 to statements[i] as returned by
    render_candidates(), because both functions iterate context_search_results in the same order
    and append graphify_result last, if present (verified directly against render_candidates()'s
    own loop order, tools/knowledge_gateway_packet_assembly.py:247-317).
    """
    all_results = list(context_search_results)
    if graphify_result is not None:
        all_results.append(graphify_result)

    pairs: set[frozenset[int]] = set()
    for i, result_a in enumerate(all_results):
        for j, result_b in enumerate(all_results[i + 1:], start=i + 1):
            if _structural_supersession_signal(result_a, result_b) is not None:
                pairs.add(frozenset({i, j}))
    return pairs
```

**`deduplicate_statements()` signature change:**

```python
def deduplicate_statements(
    statements: list[Statement],
    conflict_index_pairs: Optional[set[frozenset[int]]] = None,
) -> list[Statement]:
    conflict_index_pairs = conflict_index_pairs or set()
    order: list[str] = []
    groups: dict[str, Statement] = {}
    group_anchor_index: dict[str, int] = {}

    for idx, statement in enumerate(statements):
        key = _dedup_key(statement)
        if key in groups and frozenset({idx, group_anchor_index[key]}) in conflict_index_pairs:
            # Conflict-flagged pair renders identical text -- must never silently merge (AC4/§14).
            # Force this statement into its own distinct group instead of collapsing it.
            key = f"{key}::conflict-{idx}"
        if key not in groups:
            groups[key] = statement
            group_anchor_index[key] = idx
            order.append(key)
            continue
        existing = groups[key]
        merged_ids = list(existing.evidence_ids)
        for evidence_id in statement.evidence_ids:
            if evidence_id not in merged_ids:
                merged_ids.append(evidence_id)
        groups[key] = replace(existing, evidence_ids=merged_ids)

    return [groups[key] for key in order]
```

`conflict_index_pairs` defaults to `None` (treated as empty set) — every existing direct caller
(`test_deduplication_occurs_before_truncation_not_after` calls `kpa.deduplicate_statements(statements)`
and `kpa.deduplicate_statements(included_wrong_order)` with no second argument, lines 314 and 322)
continues to work unmodified with zero exclusion behavior, identical to today.

**`assemble_packet()` orchestration change** (lines 596-597 today):

```python
statements, context_entries, evidence_entries = render_candidates(provider_results, query_text)
conflict_index_pairs = _conflict_signal_index_pairs(
    provider_results.get("context_search") or [],
    provider_results.get("graphify"),
)
statements = deduplicate_statements(statements, conflict_index_pairs)
```

`build_conflicts()`'s own call site (line 609-612) is **not edited at all** — same inputs, same
position in the pipeline, same output.

**Documented boundary, not silently over-promised:** this mechanism handles pairwise conflict
exclusion correctly (verified by direct trace above and by test 3 in Step 3 below). It does not
attempt to handle a 3-way group where one statement shares identical text with a conflict-flagged
pair but is not itself conflict-flagged against either — in that case the non-conflicted statement
still merges into whichever of the pair it was not excluded from (a defensible generalization, not
a bug per AC4's own two-provider framing, and not exercised by any planned test — flagged here as a
known boundary, not a follow-up ticket, since it is not a real gap against this ticket's own AC4
wording).

**Architecture Review resolution (this revision):** Review examined the index-correspondence
assumption (`statements[i]` == `all_results[i]`) flagged in the prior revision and confirmed by
direct trace that it is structurally guaranteed by both functions iterating provider results in the
same fixed order, and is correct today. Review did **not** require the heavier fix (an explicit
index-carrying data structure on `Statement`) — it required a proportionate, fail-loud runtime
check instead, since the correspondence remains an implicit contract between two functions that
nothing currently enforces if either changes independently. That check is now **Step 4** below: a
cardinality assertion in `assemble_packet()`, immediately after `conflict_index_pairs` is computed
and before `deduplicate_statements()` is called, raising `AssertionError` rather than silently
degrading AC4's guarantee if `render_candidates()`'s statement-ordering and this helper's
index-pair assumptions ever desync.

### DD3 — Budget-truncation marker: `budget_truncated: bool` + `omitted_statement_count: int`, additive fields on `PacketAssembly` and the response schema

**Field choice.** Names traced to investigation.md's own naming suggestion and cross-checked against
Risk 5's "no collision" analysis: neither `budget_truncated` nor `omitted_statement_count` exists
anywhere in `knowledge_context_response.schema.json`'s `properties` block today (confirmed by direct
read of the full schema above) or in `PacketAssembly`'s current field list (lines 557-572).
`omitted_statement_count` (not `omitted_items_count`) is chosen to match this module's own existing
vocabulary — everything counted here is a `Statement`, and the schema's own `statements[]` array is
named `statements`, not `items`.

**Computation, placed immediately after the existing `assemble_within_budget()` call** (line 614
today, `included_statements, budget_returned = assemble_within_budget(statements, budget_requested)`):

```python
included_statements, budget_returned = assemble_within_budget(statements, budget_requested)
omitted_statement_count = len(statements) - len(included_statements)
budget_truncated = omitted_statement_count > 0
```

**Correctness verified by tracing both branches, not asserted:**
- Ordinary partial truncation (some but not all deduped statements admitted): `included_statements`
  has `1 <= len < len(statements)`, so `omitted_statement_count > 0`, `budget_truncated = True`. This
  is the ordinary case AC2/AC3 target.
- Everything fits (`len(included_statements) == len(statements)`): `omitted_statement_count == 0`,
  `budget_truncated = False`. This is test 6's "never silent when nothing was dropped" case — the
  field is still present, just `False`/`0`, never omitted (see response-dict wiring below).
- §16 budget-assembly-failure fallback (`budget_assembly_failed = bool(statements) and not
  included_statements`, line 619): at the point this formula runs, `included_statements` is still
  the real, empty list `assemble_within_budget()` returned (the `final_statements = []` reassignment
  happens later, inside the `if budget_assembly_failed:` branch, lines 622-626, and does not affect
  the already-computed `omitted_statement_count`). So `omitted_statement_count == len(statements) -
  0 == len(statements)` — every deduped statement was omitted, exactly test 7's required assertion.
  This single formula, computed once, is correct for all three cases without any branch-specific
  special-casing.

**`PacketAssembly` field insertion** — two new fields added after `budget_returned`, before
`provider_failures` (both are non-defaulted fields; `negative_claim_support: Optional[...] = None`
stays the sole trailing defaulted field, so Python's dataclass field-ordering rule is respected):

```python
@dataclass(frozen=True)
class PacketAssembly:
    status: str
    freshness: str
    verification: str
    provenance_providers: list[str]
    providers_consulted_this_call: list[str]
    answer: str
    statements: list[Statement]
    context: list[ContextEntry]
    evidence: list[EvidenceEntry]
    conflicts: list[Conflict]
    budget_requested: int
    budget_returned: int
    budget_truncated: bool
    omitted_statement_count: int
    provider_failures: list[str]
    negative_claim_support: Optional[NegativeClaimSupport] = None
```

**Other constructors of `PacketAssembly` (enumerated, per fact-verification requirement):** none.
Confirmed by reading the full 667-line module and the full 526-line test file above — `PacketAssembly(`
is only ever constructed once, in `assemble_packet()`'s own `return` statement (lines 651-666), which
this plan edits directly (Step 5). No test in `tests/tools/test_knowledge_gateway_packet_assembly.py`
constructs a `PacketAssembly` directly (all tests reach it only via `_assemble()` ->
`kpa.assemble_packet(...)`), so adding two required (non-defaulted) fields breaks nothing.

**Response-dict wiring in `tools/knowledge_gateway_mcp.py::_run_knowledge_context()`** — three
distinct response shapes exist in this function (confirmed by direct read, lines 149-327), and each
is handled differently, deliberately, not uniformly:

1. **`error_response`** (lines 177-186, request-schema-validation failure, before any provider call
   or budget attempt) — **not given the new fields.** This shape already omits `budget_requested`/
   `budget_returned`/`provider_failures`/`statements` entirely (nothing budget-related was ever
   attempted), and the response schema's `required` list does not include the new fields (see
   below), so this is consistent with the existing pattern, not a new omission.
2. **`fallback_response`** (lines 200-214, router failure — `FileNotFoundError`/
   `subprocess.TimeoutExpired`) — **given the new fields as `False`/`0`.** This shape already
   carries `budget_requested`/`budget_returned` (both present, `budget_returned` hardcoded `0`
   at line 208) and `provider_failures`, so for consistency with those siblings, add
   `"budget_truncated": False, "omitted_statement_count": 0` — genuinely correct: nothing was
   ever truncated by budget here, the router itself failed before any statement existed.
3. **The main packet-assembled `response` dict** (lines 241-251) — **given the real computed
   values**, added as plain top-level keys alongside `budget_requested`/`budget_returned`/
   `provider_failures` (never routed through `_omit_none()` — that helper is only ever applied to
   the per-item `statements[]`/`context[]`/`evidence[]` dicts, lines 258-291, never to top-level
   scalar response keys; confirmed by direct read that `budget_requested`/`budget_returned`/
   `provider_failures` are already constructed as bare dict literals at lines 248-250, the exact
   same pattern the new fields will follow):

   ```python
   response: dict = {
       "status": packet.status,
       "freshness": packet.freshness,
       "verification": packet.verification,
       "provenance_providers": packet.provenance_providers,
       "providers_consulted_this_call": packet.providers_consulted_this_call,
       "answer": packet.answer,
       "budget_requested": packet.budget_requested,
       "budget_returned": packet.budget_returned,
       "budget_truncated": packet.budget_truncated,
       "omitted_statement_count": packet.omitted_statement_count,
       "provider_failures": packet.provider_failures,
   }
   ```

The cache-HIT early-return path (`hit_response = dict(cached_payload)`, line 233) needs **no separate
edit** — `cached_payload` is whatever a prior `perform_cache_write()` call persisted, and once this
plan's `response` dict includes the two new keys, `perform_cache_write()` (unedited, see below)
persists them automatically.

**Schema update** — `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json`,
add to the `properties` block (placed next to `budget_requested`/`budget_returned`, lines 122-123):

```json
"budget_truncated": { "type": "boolean" },
"omitted_statement_count": { "type": "integer" }
```

**Not added to the `required` array.** The existing `required` list (lines 7-13) is `["status",
"freshness", "verification", "provenance_providers", "providers_consulted_this_call"]` — it
deliberately excludes `budget_requested`/`budget_returned`/`provider_failures` because those are
absent from the `error_response` shape (point 1 above). The two new fields are absent from that same
shape for the same reason, so they follow the identical precedent: present whenever budget
enforcement was attempted, absent only on the pre-provider-call `ERROR` path, and therefore not
`required` at the schema level (which governs *every* response shape, `ERROR` included).

**Cache-module interaction, verified by direct read, zero code change required:**
`tools/knowledge_gateway_cache.py::perform_cache_write()` (lines 262-336) serializes `{k: v for k, v
in response.items() if k not in _RESPONSE_KEYS_EXCLUDED_FROM_CACHE_PAYLOAD}` (line 259 defines that
exclusion set as `frozenset({"cache", "cache_key_version"})`, unchanged) — the two new keys are not
in that exclusion set, so they are written to `result_payload` as part of the full response dict,
exactly like `budget_requested`/`budget_returned` already are. `perform_cache_lookup()` (lines
226-249) returns `json.loads(lookup.row["result_payload"])` verbatim (line 249) — the two new fields
round-trip through a cache HIT with no additional code. This ticket's Out of Scope ("Level 2 cache
schema, storage, or read/write wiring... this ticket only changes how a packet is assembled, not
how/whether it is cached") is respected: zero lines of `tools/knowledge_gateway_cache.py` or
`tools/retrieval_cache.py` are touched.

**Other writers to the `response` dict inside `_run_knowledge_context()` (enumerated, per
fact-verification requirement):** exactly the three shapes listed above (`error_response`,
`fallback_response`, the main `response` dict) plus the cache-HIT `hit_response` (which is `dict(cached_payload)`,
not independently constructed — it inherits whatever the main `response` dict looked like at a prior
write). No other function in this module or a sibling module constructs a `knowledge_context`
response dict — confirmed by direct read of the full 486-line file above.

## Steps

### Step 1 — Add shared `_content_hash()` helper and `evidence_hash` field to `Statement`; thread both through `render_candidates()`

**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:** Per DD1 (Architecture-Review Finding 2). Add the new module-level helper `_content_hash(text:
str) -> str` (exact body in DD1 above: `return hashlib.sha256(text.strip().encode("utf-8")).
hexdigest()`) immediately above `render_candidates()` (before line 233). Add `evidence_hash:
Optional[str] = None` as a new trailing field on the `Statement` dataclass (`tools/knowledge_
gateway_packet_assembly.py:205-212`), after the existing `verification: Optional[str] = None` field.
In `render_candidates()` (lines 233-319), replace both inline `evidence_hash = hashlib.sha256(text.
encode("utf-8")).hexdigest()` lines (252, 288 — cited and re-confirmed against the live file this
session) with `evidence_hash = _content_hash(text)`, and pass `evidence_hash=evidence_hash` into
both `Statement(...)` constructor calls (the `context_search` loop, lines 254-263, and the
`graphify` branch, lines 290-299) — same computed value as today, now funneled through the one
shared helper instead of an inlined `hashlib.sha256(...)` literal. No other field of `Statement`,
`ContextEntry`, or `EvidenceEntry` changes.

**Do NOT touch:** `ContextEntry`/`EvidenceEntry`'s own `evidence_hash` *field* (lines 215-231) —
unchanged; their *computation* now calls `_content_hash(text)` instead of inlining the formula
(same value, different call form — not a rename or consolidation of the fields themselves).
`Statement.evidence_hash` is a new, separate field that happens to hold the same value in the real
pipeline. Do not change `_evidence_id_for_context_search_result()`/
`_evidence_id_for_graphify_result()` — evidence_id derivation is untouched by this ticket.

**Verify:** No new test is dedicated to this step alone (it is a pure plumbing prerequisite for Step
2) — its correctness is verified indirectly by Step 2's tests and the new
`test_evidence_hash_and_dedup_key_share_single_content_hash_helper` guard test (Step 8), plus the
full existing regression suite (`test_every_answer_sentence_traces_to_a_real_statement_evidence_id`,
`test_context_summary_sentences_also_trace_to_statements`, and the rest of `tests/tools/test_
knowledge_gateway_packet_assembly.py`) continuing to pass, since `evidence_hash` on `Statement` is
not read by anything except `_dedup_key()` (Step 2), `_content_hash()`'s output is byte-identical to
the formula it replaces, and `dataclasses.fields()`-iterating tests
(`test_packet_never_carries_raw_provider_results_verbatim_beyond_rendered_statements`) do not assert
against the field name `evidence_hash` being absent.

### Step 2 — Switch `_dedup_key()` to content-hash identity via `_content_hash()`, with the same shared-helper fallback for directly-constructed `Statement` fixtures

**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:** Per DD1 (Architecture-Review Finding 2). Replace `_dedup_key()` (lines 324-325):

```python
def _dedup_key(statement: Statement) -> str:
    return " ".join(statement.text.strip().casefold().split())
```

with:

```python
def _dedup_key(statement: Statement) -> str:
    if statement.evidence_hash is not None:
        return statement.evidence_hash
    return _content_hash(statement.text)
```

This calls the same `_content_hash()` helper Step 1 adds and threads through `render_candidates()`
— not a second, independently-inlined `hashlib.sha256(...)` literal. `hashlib` is already imported
at module top (line 51; still needed there, since `_content_hash()` itself uses it) — no new import
needed. Also update `deduplicate_statements()`'s own docstring (lines 328-334) to describe
content-hash-based identity instead of "exact-match on normalized text," and update the `── Step 5:
Deduplication before truncation ──` section comment (line 322) if it references the old casefold
behavior — a doc-honesty correction, not a behavior change (see Step 9 for the
module-docstring-level correction).

**Do NOT touch:** the truncation logic in `assemble_within_budget()` (lines 525-552) — unrelated to
identity, only consumes whatever `deduplicate_statements()` already returned. Do not add a second
dedup-key helper, and do not inline a second copy of the hash formula here — `_dedup_key()` calls
`_content_hash()`, which remains the single source of truth for the hash formula itself (Finding 2);
`_dedup_key()` remains the single source of truth for dedup *identity* (which field/fallback to use).

**Verify:** `test_dedup_identity_uses_content_hash_not_casefold_normalization`,
`test_dedup_collapses_only_on_exact_content_hash_match_across_providers`,
`test_dedup_key_is_stricter_than_semantic_similarity_no_fuzzy_merge`,
`test_evidence_hash_and_dedup_key_share_single_content_hash_helper` (all new, test_plan.md); plus
regression: `test_duplicate_fact_across_two_providers_yields_one_statement_two_evidence_ids`,
`test_deduplication_occurs_before_truncation_not_after` (both existing, must keep passing unmodified
per DD1's verified compatibility analysis).

### Step 3 — Add `_conflict_signal_index_pairs()`; wire conflict-awareness into `deduplicate_statements()` and `assemble_packet()`

**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:** Per DD2. Add the new `_conflict_signal_index_pairs()` helper (exact body in DD2 above)
immediately above `deduplicate_statements()` (before line 328). Change `deduplicate_statements()`'s
signature and body to accept and consume the new `conflict_index_pairs` parameter (exact body in
DD2 above) — this is a signature change on an existing function, not a new function, so every
existing call site must be checked: the sole production call site is `assemble_packet()` (edited in
this same step, see below); the two existing direct test call sites
(`test_deduplication_occurs_before_truncation_not_after`, lines 314 and 322) pass no second argument
and are unaffected by the new optional parameter's default. In `assemble_packet()` (lines 596-597),
change:

```python
statements, context_entries, evidence_entries = render_candidates(provider_results, query_text)
statements = deduplicate_statements(statements)
```

to:

```python
statements, context_entries, evidence_entries = render_candidates(provider_results, query_text)
conflict_index_pairs = _conflict_signal_index_pairs(
    provider_results.get("context_search") or [],
    provider_results.get("graphify"),
)
statements = deduplicate_statements(statements, conflict_index_pairs)
```

Implement this step's code exactly as shown above. **Step 4 (below) inserts one more line** —
a runtime cardinality assertion — between the `conflict_index_pairs = ...` call and the
`statements = deduplicate_statements(...)` call; do not anticipate or merge that assertion into
this step, keep the two steps' edits separately reviewable/revertible.

**Do NOT touch:** `build_conflicts()` (lines 499-520) or its call site (lines 609-612) — both stay
byte-unchanged; `_structural_supersession_signal()` (lines 461-496) — reused as-is, not modified, not
duplicated. Do not reorder any step of `assemble_packet()`'s documented pipeline (module docstring,
lines 586-589) — `conflict_index_pairs` computation is inserted between `render_candidates()` and
`deduplicate_statements()`, both still at their original documented positions relative to
`build_negative_claim_support()`/`build_conflicts()`/`assemble_within_budget()`.

**Verify:** `test_dedup_does_not_merge_conflict_flagged_pair_even_with_identical_text` (new, the
ticket's highest-value test — closes Gap 2/AC4),
`test_conflicting_claims_with_different_text_still_never_merge_and_pass_through_dedup` (new,
companion regression guard); plus regression: `test_conflict_only_surfaces_real_supersession_
metadata`, `test_conflicts_never_populated_from_bare_topical_similarity` (both existing, must keep
passing unmodified — `build_conflicts()` itself is untouched).

### Step 4 — Add a fail-loud runtime cardinality assertion guarding the `statements[i]` <-> raw-result-index correspondence (Architecture-Review Finding 1)

**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:** Architecture-Review-mandated correction, not part of the original ticket scope, not a
heavier fix than Review required. Review confirmed by direct trace of `render_candidates()` that
the `statements[i]` <-> `provider_results` index correspondence `_conflict_signal_index_pairs()`
(Step 3) relies on is correct today: `render_candidates()` appends exactly one `Statement` per
`context_search` result, in order, then exactly one more if `graphify_result` is not `None` — the
identical iteration order `_conflict_signal_index_pairs()`'s own `all_results` list construction
uses. Nothing currently catches a future silent desync between the two functions, and AC4 exists
specifically to prevent conflicting claims from being silently merged — a desync here would degrade
straight into that exact failure mode without any error. In `assemble_packet()`, immediately after
Step 3's `conflict_index_pairs = _conflict_signal_index_pairs(...)` call and before the
`statements = deduplicate_statements(statements, conflict_index_pairs)` call, insert:

```python
assert len(statements) == len(provider_results.get("context_search") or []) + (
    1 if provider_results.get("graphify") else 0
), (
    "statements[] <-> provider-result index correspondence invariant violated: "
    "_conflict_signal_index_pairs() assumes render_candidates() emits exactly one Statement "
    "per context_search result plus one more iff graphify is present, in that same order. "
    "If this fires, render_candidates() and _conflict_signal_index_pairs()/build_conflicts() "
    "have desynced and AC4's conflict-vs-dedup exclusion can silently misfire."
)
```

This is a cheap (`O(1)`, no loop) cardinality check, not a full index-pair re-derivation — it
verifies the precondition the correspondence depends on, not the correspondence's full correctness
by construction. Placed in `assemble_packet()` (not inside `_conflict_signal_index_pairs()` itself)
because `statements` is not currently one of that helper's parameters, and adding it there would be
a larger signature change than this proportionate fix calls for.

**Do NOT touch:** `_conflict_signal_index_pairs()`'s own signature or body (Step 3) — this assertion
checks its precondition from the caller's side, it does not change what the helper computes or
returns. Do not turn this into a full re-verification of every index pair's correctness (e.g.
re-deriving `all_results` and comparing element-by-element to `statements`) — that would duplicate
`_conflict_signal_index_pairs()`'s own logic; the cardinality check is the proportionate fix Review
required, not a heavier one.

**Verify:** `test_conflict_index_pairs_correspondence_invariant_raises_on_desync` (new,
test_plan.md) — deliberately breaks the correspondence via a targeted monkeypatch (e.g. patching
`render_candidates()` to return an extra `Statement` not backed by a corresponding provider result)
and asserts `AssertionError` is raised, not that dedup silently misbehaves; plus regression: the
full existing `tests/tools/test_knowledge_gateway_packet_assembly.py` suite must keep passing
unmodified, since the assertion's condition holds true for every real, non-monkeypatched call
`assemble_packet()` makes today (verified by DD2's direct trace).

### Step 5 — Add `budget_truncated`/`omitted_statement_count` to `PacketAssembly`; compute in `assemble_packet()`

**Files:** `tools/knowledge_gateway_packet_assembly.py`

**Change:** Per DD3. Insert the two new fields into the `PacketAssembly` dataclass (exact field list
in DD3 above), between `budget_returned` and `provider_failures`. In `assemble_packet()`, immediately
after the existing `included_statements, budget_returned = assemble_within_budget(statements,
budget_requested)` line (line 614), add:

```python
omitted_statement_count = len(statements) - len(included_statements)
budget_truncated = omitted_statement_count > 0
```

In the final `return PacketAssembly(...)` statement (lines 651-666), add
`budget_truncated=budget_truncated, omitted_statement_count=omitted_statement_count,` (placed to
match the field's position in the dataclass, between `budget_returned=budget_returned,` and
`provider_failures=failures,`).

**Do NOT touch:** the `budget_assembly_failed` branch's own reassignment of `final_statements`/
`final_context`/`final_evidence`/`answer`/`budget_returned` (lines 621-626) — `omitted_statement_
count`/`budget_truncated` are computed once, before that branch, and are correct in both branches by
construction (see DD3's branch-by-branch trace). Do not change `assemble_within_budget()`'s own
return signature (`tuple[list[Statement], int]`) — the omitted count is derived by the caller
(`assemble_packet()`), not returned by `assemble_within_budget()` itself.

**Verify:** `test_budget_truncation_produces_visible_marker_when_content_is_dropped`,
`test_no_budget_truncation_marker_is_false_and_present_when_everything_fits`,
`test_budget_truncation_marker_set_in_sec16_total_failure_fallback_too` (all new, test_plan.md).

### Step 6 — Thread the two new fields into `_run_knowledge_context()`'s response dict

**Files:** `tools/knowledge_gateway_mcp.py`

**Change:** Per DD3. In the main packet-assembled `response` dict literal (lines 241-251), add
`"budget_truncated": packet.budget_truncated,` and `"omitted_statement_count": packet.omitted_
statement_count,` as plain top-level keys (exact placement in DD3 above) — never routed through
`_omit_none()`. In `fallback_response` (lines 200-214, the router-failure early return), add
`"budget_truncated": False,` and `"omitted_statement_count": 0,` alongside the existing
`"budget_requested": effective_budget, "budget_returned": 0,` pair. `error_response` (lines 177-186)
is **not** edited — see DD3's rationale.

**Do NOT touch:** `error_response`'s field set (lines 177-186) — this ticket does not add the new
fields there, consistent with that shape's existing precedent of omitting all budget-related fields.
Do not touch `_omit_none()` itself (lines 138-144) or any of its existing call sites (`statements[]`/
`context[]`/`evidence[]` per-item dict construction, lines 258-291) — the new top-level fields never
pass through it. Do not touch the cache-HIT (`hit_response`) or cache-write
(`perform_cache_write`/`perform_cache_lookup`) code paths — per DD3, they need zero edits.

**Verify:** `test_knowledge_context_response_schema_accepts_new_budget_marker_field`,
`test_run_knowledge_context_budget_truncated_packet_response_has_visible_marker` (both new,
test_plan.md, `tests/tools/test_knowledge_gateway_mcp.py`); plus regression:
`test_knowledge_context_passes_through_router_and_assembler_failure_without_swallowing` (existing,
exercises the `fallback_response` path this step edits — must still validate against the schema and
still report `status == "PARTIAL"` unchanged).

### Step 7 — Add `budget_truncated`/`omitted_statement_count` to the response schema

**Files:** `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json`

**Change:** Per DD3. Add to the `properties` block, next to `budget_requested`/`budget_returned`
(current lines 122-123):

```json
"budget_truncated": { "type": "boolean" },
"omitted_statement_count": { "type": "integer" }
```

Do not add either name to the top-level `required` array (lines 7-13) — see DD3's rationale (parity
with `budget_requested`/`budget_returned`/`provider_failures`'s own non-required treatment).

**Do NOT touch:** the `required` array; the `allOf`/`if`/`then` ERROR-status block (lines 134-143);
any other property definition in this file; `knowledge_context_request.schema.json` (this ticket adds
no new request field — `budget_tokens` already exists and is unchanged); `shared_enums.schema.json`
(no new enum value is introduced by this ticket).

**Verify:** `test_knowledge_context_response_schema_accepts_new_budget_marker_field` (new); plus the
full existing `_validate_response()`-based regression surface in `tests/tools/test_knowledge_gateway_
mcp.py` (every test that calls `_validate_response(response)` must keep passing, since
`additionalProperties` is open and the two new properties are additive-only).

### Step 8 — Add all new unit/integration/architecture-guard tests

**Files:** `tests/tools/test_knowledge_gateway_packet_assembly.py`, `tests/tools/test_knowledge_
gateway_mcp.py`

**Change:** Add all 13 new tests specified in `test_plan.md`'s "New Tests Required" section
(including the two Architecture-Review-mandated tests added in this revision), with that document
as the authoritative source for each test's exact assertions (this plan does not restate their
bodies):

In `tests/tools/test_knowledge_gateway_packet_assembly.py` (11 tests):
1. `test_dedup_identity_uses_content_hash_not_casefold_normalization`
2. `test_dedup_collapses_only_on_exact_content_hash_match_across_providers`
3. `test_dedup_does_not_merge_conflict_flagged_pair_even_with_identical_text`
4. `test_conflicting_claims_with_different_text_still_never_merge_and_pass_through_dedup`
5. `test_budget_truncation_produces_visible_marker_when_content_is_dropped`
6. `test_no_budget_truncation_marker_is_false_and_present_when_everything_fits`
7. `test_budget_truncation_marker_set_in_sec16_total_failure_fallback_too`
8. `test_dedup_key_is_stricter_than_semantic_similarity_no_fuzzy_merge`
9. `test_no_semantic_or_embedding_dependency_introduced` (anti-drift guard, mirrors the existing
   `test_statement_classification_is_ephemeral_not_persisted`'s AST-walk pattern, lines 406-423)
10. `test_conflict_index_pairs_correspondence_invariant_raises_on_desync` (**new this revision**,
    Architecture-Review Finding 1 — closes Step 4; monkeypatch-desyncs `render_candidates()`'s
    output cardinality from `provider_results` and asserts `AssertionError` is raised)
11. `test_evidence_hash_and_dedup_key_share_single_content_hash_helper` (**new this revision**,
    Architecture-Review Finding 2 — closes Steps 1/2; proves `render_candidates()`'s `evidence_hash`
    output and `_dedup_key()`'s fallback both delegate to the one `_content_hash()` helper, e.g. by
    monkeypatching `_content_hash` to a distinguishable stub and confirming both call sites reflect
    the stubbed value)

In `tests/tools/test_knowledge_gateway_mcp.py` (2 tests), using the exact monkeypatch pattern the
file already establishes (`router_mod = _mod._load_router_module()`, `pa_mod = _mod._load_packet_
assembly_module()`, `pa_search_mod = pa_mod._load_search_mcp_module()`, then
`monkeypatch.setattr(router_mod, "route", ...)` / `monkeypatch.setattr(pa_search_mod, "_run_search",
...)`, per `test_knowledge_context_passes_through_router_and_assembler_failure_without_swallowing`,
lines 256-267, and `_patch_small_cacheable_search()`, lines 308-328):
12. `test_knowledge_context_response_schema_accepts_new_budget_marker_field`
13. `test_run_knowledge_context_budget_truncated_packet_response_has_visible_marker`

(Numbering here is 1-13, matching test_plan.md's list plus the anti-drift guard test it separately
enumerates under "Anti-Drift Test Guards" — 13 new tests total across both files, up from 11 in the
prior revision.)

**Do NOT touch:** any existing test function's body in either file — only new test functions are
added. Do not remove or weaken any existing assertion.

**Verify:**
```
python3 -m pytest tests/tools/test_knowledge_gateway_packet_assembly.py -v
python3 -m pytest tests/tools/test_knowledge_gateway_mcp.py -v
python3 -m pytest tests/tools/test_knowledge_gateway_router.py -q
python3 -m pytest tests/docs/test_redaction_retention_policy_doc.py -q
```
All must pass — existing tests unmodified in assertion, new tests added.

### Step 9 — Document-Update phase: module-docstring/comment honesty corrections, response-schema doc note, proposal §20 annotation, parity ledger

**Files:** `tools/knowledge_gateway_packet_assembly.py` (comments/docstrings only, no behavior),
`docs/plans/knowledge-gateway-mcp-proposal.md`, `docs/parity_ledger/infrastructure.yaml`

**Change:**

1. **Module docstring / inline comments** (`tools/knowledge_gateway_packet_assembly.py`): update the
   `── Step 5: Deduplication before truncation ──` section comment and `deduplicate_statements()`'s
   own docstring (currently "Groups by exact-match on normalized text... Keyed only on rendered
   text, never on provider") to describe the new content-hash identity and the conflict-index-pair
   exclusion guard, so the module's own comments stay in parity with its real behavior (CLAUDE.md's
   doc/code parity rule). The top-level module docstring's own bullet list (lines 10-15) should also
   gain one line noting dedup identity is now content-hash-based and conflict-aware, mirroring the
   existing "Honesty notes" style (lines 17-37).

2. **`docs/plans/knowledge-gateway-mcp-proposal.md` §20**: annotate the "Assemble deduplicated
   multi-provider packets" and "Enforce caller budgets using measured output size" Phase 3 bullets as
   done by this ticket, in the exact annotation style Phase 1/2 child tickets already used for their
   own §20 bullets — **before writing this, read §20's current text and the exact annotation format
   the Phase 1/2 entries used, and match it precisely rather than inventing a new format** (per
   investigation.md's own note; this plan does not prescribe the literal annotation string since it
   must match existing precedent exactly, not be guessed).

3. **`docs/parity_ledger/infrastructure.yaml`**:
   - Amend `INFRA-336`'s `v2_evidence` text (confirmed live at lines 8688-8747 this session) where it
     currently reads "`deduplicate_statements()` (Step 5, exact-text-match dedup merging
     evidence_ids)" — this phrase becomes inaccurate once Step 2 lands. Correct it to describe
     content-hash-based dedup with the conflict-signal-aware exclusion guard, and note it was amended
     by this ticket. `INFRA-336`'s `status` stays `verified` (the underlying proposal sections it
     cites are still satisfied) — this is a textual accuracy correction, not a status change.
   - Add a new entry, **`INFRA-347`** (confirmed live: 346 real `INFRA-` entries exist today, IDs
     327-346 verified by direct grep this session, so 347 is the next real, uncollided ID), `status:
     verified`, `priority: P1` (matching this subsystem's existing P1 pattern — INFRA-335/336/345/346
     are all P1, confirmed by direct read), `v2_evidence` citing the exact functions/line-anchors this
     plan adds (`_content_hash()`, `Statement.evidence_hash`, `_dedup_key()`,
     `_conflict_signal_index_pairs()`, `deduplicate_statements()`'s new `conflict_index_pairs`
     parameter, the Step 4 cardinality assertion in `assemble_packet()`, `PacketAssembly.budget_
     truncated`/`omitted_statement_count`), `test_path: tests/tools/test_knowledge_gateway_packet_
     assembly.py` (mirroring INFRA-336's own `test_path` convention of citing the whole file, not
     individual test names), `divergence_note: null` (no divergence from any Mechanics Bible/engine
     contract — none governs this subsystem), `support_boundary` mirroring INFRA-336's own style
     (agent-tooling only, no `src/` file touched, no cache/router code touched, verified in the diff).
     Must validate against `docs/parity_ledger/schema.json`'s `required: ["id", "text", "status",
     "priority"]` plus the `verified`-status conditional requiring `v2_evidence`/`test_path` (both
     present) — confirmed by direct read of the schema this session.

**Do NOT touch:** `docs/engine/contracts/knowledge_gateway_mcp/evidence_identity_kinds.schema.json`,
`cache_migration_plan.md`, `evidence_cache_identity_contract.md` — all three are frozen design docs
from DONE tickets; this ticket introduces no new evidence-identity kind. Do not touch any other
`INFRA-*` entry besides the `INFRA-336` textual correction and the new `INFRA-347` addition. Do not
touch `docs/guidelines/intentional_divergences.md` — no divergence from any Mechanics Bible chapter
or engine contract exists (this subsystem is outside their scope, confirmed by investigation.md and
re-confirmed here).

**Verify:** manual review during Document-Update phase confirms all three sub-changes exist; parity
entry `INFRA-347` validated against `docs/parity_ledger/schema.json` via this repo's existing parity
validation tooling, per test_plan.md's own note that this is a Parity-phase check, not part of the
pytest scope above.

## Scope Guards

- `tools/knowledge_gateway_router.py` stays byte-unchanged — never opened for edit by any step in
  this plan (ticket AC5, guarded by the existing `test_module_does_not_edit_knowledge_gateway_router`).
- `tools/retrieval_cache.py` and `tools/knowledge_gateway_cache.py` are never opened for edit —
  guarded by the existing `test_module_does_not_modify_or_import_retrieval_cache` and by DD3's direct
  verification that zero cache-module changes are needed for the new response fields to round-trip
  correctly through a cache HIT.
- No new evidence-identity kind is added to `evidence_identity_kinds.schema.json` — the dedup-identity
  change (Step 1/2) reuses the existing content-hash fingerprint concept already defined for the
  kinds this module produces; the schema file itself is never edited.
- No semantic/fuzzy/embedding-based dedup or conflict-similarity heuristic is introduced anywhere —
  guarded by the new `test_no_semantic_or_embedding_dependency_introduced` architecture test (Step 8)
  and by `test_dedup_key_is_stricter_than_semantic_similarity_no_fuzzy_merge`.
- `build_conflicts()`'s own call site, inputs, and behavior are never modified (Step 3) — only a new,
  separate, lightweight index-pair helper is added alongside it, reusing the same underlying
  detection primitive.
- `assemble_packet()`'s documented fixed pipeline order (module docstring, lines 586-589) is never
  reordered — the new conflict-index-pairs computation is inserted between two already-adjacent
  steps (render, dedup), not by moving any existing step; the Step 4 assertion is inserted at the
  same point, not a new pipeline position.
- `kgmcp_char_heuristic_v1()`'s formula (line 81-87) and `assemble_within_budget()`'s own truncation
  mechanics (lines 525-552) are never modified — only consumed by new marker-computation logic
  layered on top in `assemble_packet()` (Step 5).
- No new request-schema field is added — `budget_tokens` already exists in `knowledge_context_
  request.schema.json` and is unchanged; only the *response* schema gains the two new fields.
- The two new response fields are never marked `required` in the response schema, and never routed
  through `_omit_none()` in `tools/knowledge_gateway_mcp.py` — both are deliberate per DD3.
- `_content_hash()` (Step 1, Architecture-Review Finding 2) is the single source of truth for the
  content-hash formula — no future step, and no code this plan adds, may reintroduce a second
  inline `hashlib.sha256(...).hexdigest()` literal for the same purpose. Guarded by the new
  `test_evidence_hash_and_dedup_key_share_single_content_hash_helper` test.
- Step 4's cardinality assertion (Architecture-Review Finding 1) checks a precondition only — it
  must not be expanded into a full re-derivation of `_conflict_signal_index_pairs()`'s index pairs
  inside `assemble_packet()`; that logic stays exclusively in `_conflict_signal_index_pairs()`
  itself (Step 3).

## Dependency Map

- Step 2 depends on Step 1 (`_dedup_key()` reads the `Statement.evidence_hash` field Step 1 adds,
  and calls the `_content_hash()` helper Step 1 also adds).
- Step 3 depends on Step 2 (`deduplicate_statements()`'s exclusion logic still calls `_dedup_key()`
  internally, unchanged, but the signature/body change in Step 3 is layered on top of Step 2's edit
  to the same function).
- Step 4 depends on Step 3 (Architecture-Review Finding 1 — the cardinality assertion is inserted at
  the exact call site Step 3 establishes in `assemble_packet()`, immediately after Step 3's
  `conflict_index_pairs = _conflict_signal_index_pairs(...)` line and before its
  `deduplicate_statements(...)` call; the assertion checks a precondition of Step 3's own logic, so
  it cannot land before Step 3 does).
- Step 6 depends on Step 5 (`_run_knowledge_context()` reads `packet.budget_truncated`/`packet.
  omitted_statement_count`, which Step 5 adds to `PacketAssembly`).
- Step 7 (schema update) has no code dependency on Steps 1-6 but should land alongside Step 6 so the
  new response schema and the new response-dict fields are introduced together, keeping doc/code
  parity within the same change.
- Step 8 (tests) depends on Steps 1-7 all being in place — every new test exercises real code paths
  those steps add.
- Step 9 (Document-Update) runs last, after Steps 1-8 land, per the project's standard phase
  ordering — it is a plan Step (not a passive doc note) because it corrects `INFRA-336`'s now-stale
  text, which is a required accuracy fix, not optional cleanup.
- Steps 1-2 (dedup identity, now including the shared `_content_hash()` helper) and Steps 3-4
  (conflict guard plus its Architecture-Review-mandated runtime invariant check) and Steps 5-7
  (budget marker) are otherwise mutually independent of each other's internals — each closes a
  distinct Gap (1, 2, 3) and could in principle be implemented in any relative order among the three
  groups, though the numbering above is the recommended sequence. Step 4 must not be reordered ahead
  of Step 3 within its own group (see above).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: two providers returning overlapping evidence produce a genuinely deduplicated packet, verified by item count | Steps 1, 2 (already-real mechanism, identity switched to content-hash) | `test_duplicate_fact_across_two_providers_yields_one_statement_two_evidence_ids` (existing), `test_dedup_collapses_only_on_exact_content_hash_match_across_providers` (new) |
| AC2: a `knowledge_context` request with `budget_tokens` smaller than unconstrained packet size produces a packet within documented tolerance, real `kgmcp_char_heuristic_v1()` measurement | Steps 5, 6 (marker computation reuses the already-real, unmodified `assemble_within_budget()`/`kgmcp_char_heuristic_v1()`; Step 6 threads the real measured values through to the actual `knowledge_context` response) | `test_budget_returned_computed_by_real_kgmcp_char_heuristic_v1_not_estimate`, `test_budget_returned_never_exceeds_budget_requested` (both existing, unit-level on `assemble_within_budget()`), `test_run_knowledge_context_budget_truncated_packet_response_has_visible_marker` (new — the request-level test that actually exercises AC2's literal "a `knowledge_context` request with `budget_tokens`" wording end-to-end) |
| AC3: budget-enforcement mechanism is never silent — caller can always tell whether content was omitted, verified by response-shape assertion | Steps 5, 6, 7 | `test_budget_truncation_produces_visible_marker_when_content_is_dropped`, `test_no_budget_truncation_marker_is_false_and_present_when_everything_fits`, `test_budget_truncation_marker_set_in_sec16_total_failure_fallback_too`, `test_run_knowledge_context_budget_truncated_packet_response_has_visible_marker` (all new) |
| AC4: deduplication never collapses genuinely conflicting claims into one silently-resolved item | Steps 3, 4 (Step 4 is the Architecture-Review-mandated fail-loud runtime check that guards the index correspondence Step 3's exclusion logic depends on — without it, a future silent desync could reintroduce exactly the silent-merge failure AC4 forbids) | `test_dedup_does_not_merge_conflict_flagged_pair_even_with_identical_text` (new, primary), `test_conflicting_claims_with_different_text_still_never_merge_and_pass_through_dedup` (new, regression guard), `test_conflict_index_pairs_correspondence_invariant_raises_on_desync` (new, Step 4), `test_conflict_only_surfaces_real_supersession_metadata` (existing, unmodified) |
| AC5: `tools/knowledge_gateway_router.py` stays byte-unchanged | No step touches this file | `test_module_does_not_edit_knowledge_gateway_router` (existing) |
| AC6: real, schema-valid `docs/parity_ledger/infrastructure.yaml` entry added | Step 9 | Manual/tooling validation against `docs/parity_ledger/schema.json` during Parity phase (not a pytest-scoped test) |

## Anti-Drift Notes

- **Do not reimplement `deduplicate_statements()`/`assemble_within_budget()`/`build_conflicts()` from
  scratch.** All three are real, DONE, tested Phase 1 code. Every step in this plan is a targeted
  edit layered on top of them — never a parallel or replacement implementation. The ticket's own
  Request Summary (which this investigation found inaccurate) must not be re-read as license to
  rebuild what already exists.
- **`_conflict_signal_index_pairs()` is not a second conflict-detection system.** It calls the
  identical `_structural_supersession_signal()` function `build_conflicts()` already uses. If a
  future change needs a different conflict-detection rule, it must be made once, in
  `_structural_supersession_signal()`, not divergently in both call sites.
- **The `Statement.evidence_hash` fallback in `_dedup_key()` exists only for test-fixture
  compatibility.** The real `assemble_packet()` pipeline always threads a real hash through from
  `render_candidates()`; the fallback path (calling `_content_hash(statement.text)` fresh) is never
  exercised outside directly-constructed test `Statement` objects. Do not treat the fallback branch
  as evidence that recomputation is an acceptable general pattern — it is a narrow compatibility
  shim, not the primary mechanism.
- **`_content_hash()` is the single source of truth for the hash formula (Architecture-Review
  Finding 2).** Both `render_candidates()`'s `evidence_hash` computation and `_dedup_key()`'s
  fallback call the same helper — never reintroduce a second, independently-inlined
  `hashlib.sha256(...).hexdigest()` literal for this purpose anywhere in this module, even for a
  "just this once" fix. `test_evidence_hash_and_dedup_key_share_single_content_hash_helper` exists
  specifically to catch a future silent drift back to two copies of the formula.
- **The Step 4 cardinality assertion is a fail-loud precondition check, not a correctness proof
  (Architecture-Review Finding 1).** It confirms `len(statements) == len(context_search) + (1 if
  graphify else 0)`, which is necessary but not by itself sufficient to prove
  `statements[i] == all_results[i]` for every `i` — the actual correspondence is still guaranteed by
  both `render_candidates()` and `_conflict_signal_index_pairs()` iterating provider results in the
  same fixed order (DD2), not by this assertion. The assertion exists so a future change that breaks
  that ordering guarantee (e.g. filtering/reordering/skipping a result in one function but not the
  other) fails loudly via `AssertionError` instead of silently producing a wrong index pair and
  letting AC4's conflict-vs-dedup exclusion misfire. Do not remove this assertion as "redundant"
  because the correspondence "is already guaranteed by construction" — that guarantee is exactly
  what has no enforcement without it.
- **`budget_truncated`/`omitted_statement_count` must never be computed from `budget_returned <
  budget_requested` alone.** That comparison is an unreliable proxy (a request whose budget exactly
  equals the full unconstrained size would have `budget_returned == budget_requested` with zero
  truncation, but a caller requesting a budget slightly under the exact cost of the last included
  statement could still see `budget_returned < budget_requested` with `omitted_statement_count == 0`
  if the greedy algorithm happened to consume the exact budget on fewer, larger statements — the
  count-based formula in DD3, derived from `len(statements) - len(included_statements)`, is the only
  correct source of truth).
- **The response schema's `additionalProperties` stays open at the top level** (Design Decision D4
  from the Phase 0 contract, unchanged) — this ticket's schema edit is additive documentation/parity
  work, not required for validation to pass, and must not be treated as an opportunity to also close
  `additionalProperties` or add other unrelated required fields.
- **Do not let the new marker collapse into `status: "PARTIAL"`.** `status` already means several
  different things (`budget_assembly_failed`, provider `failures`, or ordinary truncation with
  neither of those all currently map differently — only `budget_assembly_failed`/`failures` produce
  `PARTIAL`; an ordinary truncated-but-non-empty result with no provider failures reports `status:
  "OK"` or `"CONFLICTED"`, never `PARTIAL`, per `assemble_packet()` lines 634-640). A caller cannot
  infer budget truncation from `status` alone in the ordinary-truncation case — this is exactly why
  Gap 3 exists as a distinct field, not a status-value trick.
- **`INFRA-336`'s `status` stays `verified`; only its `v2_evidence` text is corrected.** This is not
  a behavior regression being ledgered as a divergence — the proposal sections `INFRA-336` cites are
  still satisfied, its own description of *how* dedup keys statements is simply now stale and must be
  corrected for parity-ledger honesty, per CLAUDE.md's parity rule ("Documentation and source code
  must remain in 100% semantic parity").

## Deviations (recorded during Implement)

**One narrow, documented deviation from "Do NOT touch: any existing test function's body" (Step
8's own scope guard).** While running the Step 8 verification suite
(`tests/tools/test_knowledge_gateway_mcp.py -q`) after landing Steps 1-7,
`test_search_mcp_py_provably_untouched` (an existing test, originating in the DONE
`TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE`, not authored by this ticket) failed. Its `banned_path`
tuple asserted `tools/knowledge_gateway_packet_assembly.py` must show zero `git diff --stat HEAD`
lines — an invariant that was true for that ticket's own scope (packet assembly was a frozen
dependency for a pure MCP-tool-surface addition) but is now directly falsified by this ticket's
own, twice-Architecture-Review-approved plan, whose entire purpose is to make targeted edits to
exactly that module. Neither investigation.md nor this plan's own Regression Surface section
anticipated this specific stale assertion in a sibling ticket's test file.

**Resolution:** `tools/knowledge_gateway_packet_assembly.py` was removed from that test's
`banned_path` tuple, with a docstring added explaining why (this ticket's real, reviewed scope
legitimately edits it) and citing which paths remain genuinely frozen for every Knowledge Gateway
MCP ticket, this one included: `tools/search_mcp.py`, `tools/knowledge_gateway_router.py`,
`tools/retrieval_events.py`. No assertion was weakened for those three paths — the guard's real
intent (protect files this ticket's own AC5/Out-of-Scope also independently declares frozen) is
fully preserved; only the one line whose premise this ticket's own approved scope falsifies was
removed. This is the same class of correction Step 9 itself sanctions for `INFRA-336`'s stale
`v2_evidence` text — a textual/assertion accuracy fix responding to a prior ticket's now-superseded
assumption, not a routed-around gate. Verified directly: `tools/knowledge_gateway_router.py` and
`tools/retrieval_cache.py`/`tools/knowledge_gateway_cache.py` all confirmed byte-unchanged by this
ticket's own diff (`git diff --stat HEAD` shows zero lines for the router; the cache-module diff
present in the working tree is entirely staged from the already-committed sibling
`TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS` ticket, with zero working-tree delta from
this session) — this ticket's own AC5 and cache-freeze invariants hold independent of the test fix.

No other deviation from plan.md's 9 steps occurred. Steps 1-8 were implemented exactly as specified
(Step 9 — Document-Update — is explicitly left to the separate Document-Update phase per this
plan's own Dependency Map framing of it as "the project's standard phase ordering," not part of
Implement's own work).

## Unresolved Questions (flagged, not decided here)

None remain open. investigation.md's three Risks/Open Questions (budget-tolerance mechanism, dedup
identity, conflict-vs-duplicate ordering) were resolved in the prior revision with concrete,
directly-verified mechanisms. The two items that revision flagged for Architecture Review's explicit
scrutiny have now been reviewed and resolved by this revision's two mandated corrections:

1. **(Resolved by Step 4.)** DD2's index-correspondence assumption (`statements[i]` == raw-result
   `all_results[i]`) was reviewed and confirmed correct today by direct trace, but flagged as an
   implicit contract with no enforcement. Architecture Review did not require the heavier fix (an
   explicit index-carrying data structure on `Statement`) — it required, and this revision adds, a
   proportionate fail-loud runtime cardinality assertion (Step 4), plus
   `test_conflict_index_pairs_correspondence_invariant_raises_on_desync` proving it fails loudly, not
   silently, on desync.
2. **(Resolved by Steps 1/2's shared `_content_hash()` helper.)** DD1's dataclass field-addition
   mechanism (new optional `Statement.evidence_hash` field with a same-formula fallback for four
   existing direct-construction test fixtures) was reviewed and confirmed behavior-compatible by
   direct trace, but flagged because the threaded value and the fallback's recomputed value were two
   independently-inlined `hashlib.sha256(...)` literals that could silently drift apart on a future
   edit to either one. Architecture Review required factoring both into one shared `_content_hash()`
   helper (Steps 1/2), plus `test_evidence_hash_and_dedup_key_share_single_content_hash_helper`
   proving both call sites actually delegate to it rather than each carrying its own copy.

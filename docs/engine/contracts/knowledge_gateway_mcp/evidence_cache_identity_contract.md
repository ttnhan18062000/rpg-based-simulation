---
status: historical
layer: ai
authority: P1
audience: agent
tags: [ai, schema, mcp]
---

# Knowledge Gateway MCP — Evidence & Cache Identity Contract

This document defines a **contract for a future implementation**. No `src/` or `tools/` code
implementing evidence-identity resolution, cache invalidation, or a live gateway exists yet, and
none is added by this ticket (`TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`). It is placed under
`docs/engine/contracts/knowledge_gateway_mcp/` alongside the sibling wire-contract document,
`docs/engine/contracts/knowledge_gateway_mcp_contract.md`, whose own `:17-19` explicitly assigns
evidence identity, cache-lookup identity, and repository/branch/working-tree cache scope to this
ticket rather than to itself. This document is Phase 0's identity-freeze half:
`docs/plans/knowledge-gateway-mcp-proposal.md` §11.1/§11.2 (lookup vs. validity identity), §12.1
(the 8 evidence identity kinds), and §12.3 (repository/branch/working-tree cache scope).

The only real, already-existing code this document references is
`tools/retrieval_cache.py` — cited by name and line for its existing normalization primitives and
its `check_*_cache()`/`write_*_cache()` function shapes. Nothing in this document is implemented
by, imported into, or executed against that module or the real `knowledge-index/retrieval_cache.db`
by this ticket.

---

## 1. Lookup identity

Per §11.2, **lookup identity** answers only one question: *which cached candidate should the
gateway examine next for this request?* It is a routing key, not a truth claim. A lookup hit
selects a candidate; it carries no assertion about whether that candidate is still valid or safe to
return — see §3, the Non-collapse rule.

The lookup-identity tuple has exactly these fields:

| Field | Meaning |
|---|---|
| `normalized_intent` | The caller's query/intent, normalized for routing (case/whitespace-folded, not semantically reinterpreted). |
| `resolved_entity_ids` | Any entity IDs the caller's intent already resolved to, expressed in the deterministic identity forms below. |
| `filters` | The caller-supplied filter set (e.g. scope, source restriction), normalized to a stable, order-independent form. |
| `budget_class` | The caller's budget tier (token/latency budget bucket), not the raw numeric budget. |
| `routing_policy_version` | The version of the routing policy that selected this candidate — bumped when routing logic itself changes, independent of evidence content. |
| `repo_branch_scope` | The repository identity + branch the request is scoped to (see §5). |

**Deterministic identity forms.** Where `resolved_entity_ids` names a specific entity, it uses one
of these closed, deterministic string forms — never a free-text description:

- `symbol:<qualified-name>`
- `ticket:<ticket-id>`
- `parity:<entry-id>`
- `doc:<registry-id>`
- `subsystem:<registered-name>`

**Grounding against existing code.** `tools/retrieval_cache.py` already implements the nearest
real precedent for "normalized intent" and "filters" at the query-cache level:
`_normalize_query()` (`tools/retrieval_cache.py:175-176`) lowercases and collapses whitespace
before hashing, and `_hash_filters()` (`tools/retrieval_cache.py:179-180`) serializes the filter
dict via `json.dumps(..., sort_keys=True)` then hashes it through `_hash_text()`
(`tools/retrieval_cache.py:171-172`, SHA-256). This document's `normalized_intent` and `filters`
fields are defined to be consistent with those two existing normalization primitives — a future
implementation should reuse the same normalize-then-hash shape, not invent a second one — but
nothing here imports, calls, or edits that code.

**Lookup identity is a routing key only.** It selects which cached row(s) to examine. It is never,
by itself, evidence that the examined candidate is fresh, correct, or safe to return without a
separate validity check (§2).

---

## 2. Evidence-validity identity

Per §11.1, **evidence-validity identity** answers a different question: *given a candidate the
lookup step already selected, is it still safe to return right now?* This is a disjoint field set
from §1 — **zero field names are shared between the two structures.** Reusing a lookup field name
(e.g. `filters_hash`, `query_hash`) as a validity field name is itself a contract violation, not
merely a style issue, because it is the exact collapse this document exists to prevent.

The evidence-validity-identity field set has exactly these fields:

| Field | Meaning |
|---|---|
| `evidence_fingerprints` | The direct, kind-specific fingerprint(s) of the evidence actually cited (per the 8 kinds in `evidence_identity_kinds.schema.json` — see §12.1/`evidence_identity_kinds.schema.json`). |
| `validated_negative_scopes` | For claims of absence ("no result found"), the search scope that was actually validated as empty — a negative claim is only as fresh as the scope it was checked against. |
| `adapter_version_at_validation` | The provider adapter version in effect when validity was last checked — distinct from `routing_policy_version` in §1, which governs routing, not evidence trust. |
| `working_tree_overlap` | Whether the caller's changed-paths set (§5) intersects the evidence's dependency paths. |
| `provider_generation_at_validation` | The fallback-only, coarse corpus-generation signal — consulted only when no finer-grained fingerprint from `evidence_fingerprints` is available (see §4). |

**Enum cross-reference, not redefinition.** Validity outcomes are expressed using the already-frozen
`freshness` (`FRESH`/`NEEDS_REVALIDATION`/`STALE`/`UNKNOWN`) and `verification`
(`VERIFIED`/`SUPPORTED`/`INFERRED`/`UNVERIFIED`) enums, defined at
`docs/engine/contracts/knowledge_gateway_mcp/shared_enums.schema.json:11-18`. This document
references those enums by name only. Where their value lists are quoted above for readability, the
quotation is verbatim and must be kept in exact sync with `shared_enums.schema.json` — this
document does not define a competing or overlapping enum.

---

## 3. Non-collapse rule

No function, table row, or schema object may expose both a lookup-identity field (§1) and a
validity-verdict field (§2) keyed by the same primary identity in a way that lets a lookup hit be
read as a validity result without a separate, explicit validity check step.

Concretely:

- A lookup-table row (or its equivalent) may carry lookup-identity fields and, at most, a status
  used purely for cache bookkeeping (e.g. `hit`/`miss`/`stale-rejected`, matching
  `tools/retrieval_cache.py`'s existing `HIT`/`MISS`/`STALE_REJECTED` constants) — never a
  freshness/verification verdict about the underlying evidence's current truth.
- A function that performs a lookup (i.e. one shaped like `tools/retrieval_cache.py`'s existing
  `check_index_cache()`/`check_query_cache()`/`check_packet_cache()`) must not return a
  `freshness`/`verification` field. Confirmed today: none of the three does — each returns only a
  `status`/`reason_code` pair (`IndexCacheResult`, `QueryCacheResult`, `PacketCacheResult`,
  `tools/retrieval_cache.py:198-218`, `:260-288`, `:329-362`). Any future addition of a
  freshness/verification field to one of those return shapes without a separate validity-check
  function is a violation of this rule, not an enhancement.
- Evidence-validity identity (§2) must be computed by a distinct step, consulted after a lookup hit,
  never folded into the lookup query itself.

---

## 4. Provider-generation fallback rule

`PROVIDER_GENERATION` (one of the 8 evidence identity kinds — see
`evidence_identity_kinds.schema.json`) is consulted **only** when an evidence record's own
kind-specific fingerprint is unavailable, or already known-stale by a finer signal. It is the
coarsest, corpus-wide generation signal available (analogous in spirit to
`tools/retrieval_cache.py`'s existing `_corpus_generation()`, `tools/retrieval_cache.py:183-191`,
which proxies `knowledge-index/manifest.json`'s `built_at` field) — but it must never be treated as
a default dependency for kinds that have a finer fingerprint.

**Hard rule:** a `SYMBOL`- or `FILE`-backed evidence record — both of which have a finer,
kind-specific fingerprint available per `evidence_identity_kinds.schema.json`'s
`preferred_fingerprint` table — must never be invalidated by an unrelated corpus-wide
`PROVIDER_GENERATION` bump alone. Only evidence kinds whose `preferred_fingerprint` entry states no
finer fingerprint is available (today, only `PROVIDER_GENERATION` itself) fall back to the
generation signal as their primary/only freshness dependency.

This is the concrete, testable form of AC3: `tests/tools/test_evidence_cache_identity_contract.py`
asserts this rule against fixture records structurally, per §5's fixture pattern, since no live
invalidation function exists yet at Phase 0.

---

## 5. Repository/branch/working-tree cache scope

Per §12.3, cache-scope compatibility follows these rules:

1. **A new commit alone is not automatically a cache miss.** A packet cached against the same
   repository identity and the same branch, whose direct evidence fingerprints (§2's
   `evidence_fingerprints`) are unchanged, remains compatible after a new commit lands on that
   branch — the identity axis that matters is evidence-fingerprint stability, not raw commit SHA
   equality.
2. **Branch identity is a hard partition, not a soft signal.** A packet cached while the caller's
   scope was a feature branch is never reused when the current scope is a different branch (e.g.
   `main`), even if every evidence fingerprint happens to be identical. Cross-branch reuse is
   rejected unconditionally, before any fingerprint comparison is even consulted.
3. **Working-tree fingerprinting uses changed-paths intersection, not whole-tree hashing.** Rather
   than hashing the entire working tree on every request, the gateway intersects the caller-supplied
   `changed_paths` set against the set of file paths a cached packet's evidence actually depends on.
   `changed_paths` is an already-frozen request field — an array of strings — per
   `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_request.schema.json`'s `properties`
   (asserted structurally at
   `tests/tools/test_knowledge_gateway_contract_schemas.py:178`, `props["changed_paths"]["type"] ==
   "array"`). This document references that field by name and does not redefine it. Only an
   intersection hit forces re-validation of the affected packet; a `changed_paths` set that does not
   intersect a cached packet's dependency paths leaves that packet presumed compatible without a
   full-tree hash.

---

## 6. Cross-references

- `docs/engine/contracts/knowledge_gateway_mcp/evidence_identity_kinds.schema.json` — the 8 closed
  evidence identity kinds, each with its stable-identity form, preferred fingerprint, and
  normalization rules (§12.1).
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md` — the migration design
  document for adding new tables to `knowledge-index/retrieval_cache.db` in place (§10.1/§19).
- `docs/engine/contracts/knowledge_gateway_mcp/shared_enums.schema.json` — `freshness`/`verification`
  enum definitions, referenced by §2, not redefined here.
- `docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_request.schema.json` — the
  `changed_paths` request field, referenced by §5, not redefined here.
- `docs/engine/contracts/knowledge_gateway_mcp_contract.md` — the sibling wire-contract document;
  its `:17-19` assigns this document's content area to this ticket.

No `docs/parity_ledger/` entry accompanies this document — this subsystem is
agent-orchestration/retrieval tooling, the same category `context_packet_contract.md` §4 and the
sibling `knowledge_gateway_mcp_contract.md` §5 already classify as not requiring a parity ledger
entry.

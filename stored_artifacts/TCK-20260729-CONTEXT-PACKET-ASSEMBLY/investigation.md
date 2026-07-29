---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260729-CONTEXT-PACKET-ASSEMBLY
artifact_type: investigation
tags: [ai, schema]
---

# Investigation — TCK-20260729-CONTEXT-PACKET-ASSEMBLY

## Current Behavior

**No `ContextPacket` assembly code exists in the repo today.** This ticket is the fourth and last
of Phase 3's code-producing batch, and per its own Assumptions it is hard-blocked on the other
three, which are now `tickets/done/`. Their real, landed shapes (not the idea doc's aspirational
prose) are what this ticket must consume.

- **`tools/hybrid_retrieval.py`** (`TCK-20260729-HYBRID-RETRIEVAL-FUSION`, done) — `HybridResult`
  (`tools/hybrid_retrieval.py:163-182`), a frozen dataclass with exactly these 13 fields: `doc_id`,
  `path`, `heading`, `section`, `text`, `rrf_score`, `dense_rank`, `lexical_rank`,
  `semantic_score`, `keyword_score`, `authority`, `freshness`, `kind`. `hybrid_fuse_and_filter()`
  (`:224-331`) is the entrypoint; it returns `list[HybridResult]`. `kind` is populated by
  `_SOURCE_TYPE_TO_KIND` (`:47-52`) — only `doc`, `ticket`, `investigation`, `working_log`. There
  is **no `code_symbol`, `test`, `graphify_node`, or `parity_ledger_entry` kind ever produced by
  this module**, because its underlying corpus (`knowledge_docs`/`knowledge_vec`, built by
  `tools/knowledge_search.py`) explicitly excludes `src/`, `tests/`, and
  `docs/parity_ledger/` (`_SKIP_DOC_SUBDIRS`, confirmed in `tools/generate_registry.py:42` and
  restated in `tools/hybrid_retrieval.py`'s own docstring). `authority`/`freshness` are already
  resolved per-row by `resolve_metadata()` (`:104-120`): a REGISTRY-indexed path gets its real
  `authority`/`status` value; every other path (including every `tickets/inprogress/` ticket body,
  since REGISTRY only indexes `tickets/done/`) gets the `UNRATED = "unrated"` sentinel
  (`tools/hybrid_retrieval.py:41-45`, with an import-time
  `assert UNRATED not in AUTHORITY_VALUES and UNRATED not in STATUS_VALUES` guarding against enum
  collision). `HybridResult` carries **no `hash` field and no `source_id` field distinct from
  `doc_id`** — the contract's `included[]` shape (see below) must be built by mapping `doc_id` →
  `source_id`, `path`+`heading`/`section` → `path`+`heading_or_symbol`, and computing `hash`
  independently (nothing in `HybridResult` already carries one).
- **`tools/retrieval_cache.py`** (`TCK-20260729-RETRIEVAL-CACHE-LEVELS`, done) — three
  `check_*_cache()`/`write_*_cache()` function pairs, each returning a tiny frozen-dataclass result
  with exactly `status` (`hit`/`miss`/`stale-rejected`, module constants `HIT`/`MISS`/
  `STALE_REJECTED`, `:60-62`) and `reason_code` (`str | None`): `IndexCacheResult` (`:198-201`),
  `QueryCacheResult` (`:260-263`), `PacketCacheResult` (`:329-332`). Critically,
  `check_packet_cache()` (`:335-362`) "**operates on raw fields only — `ContextPacket` does not
  exist as a class yet**" (its own docstring, `:341-343`, matching `context_packet_contract.md`
  §4's "No code enforces this contract yet"). It takes `packet_key_hash: str,
  current_cited_hashes: list[str], corpus_generation: str, policy_version: str` — never an
  assembled packet object. This ticket must not invent an import of a `ContextPacket` class into
  `retrieval_cache.py`, and must not assume the cache module returns anything packet-shaped; it
  only returns a hit/miss/stale-reject verdict plus reason code, which this ticket's module may
  consult but does not need to unwrap further.
- **`tools/code_test_index.py`** (`TCK-20260729-DETERMINISTIC-CODE-INDEX`, done) — `build_records()`
  (`:171-196`) returns `list[dict]`, each with exactly `id`, `module`, `symbol`, `docstring`,
  `owned_component`, `associated_tests`. **This module carries no `kind` field of its own** and is
  not one of C1's (`hybrid_retrieval.py`) or C3's (`retrieval_cache.py`) outputs — it is a third,
  independent module this ticket's own Related Code Areas lists but the ticket's Request Summary
  text ("from C1's fused retrieval results and C3's cached results") does not name as an input.
  Since AC1 requires a `code_symbol` `included[]` item and `HybridResult.kind` can never be
  `code_symbol` (see above), **this ticket's assembler must also directly consume
  `code_test_index.py` records as a third candidate source**, not merely C1+C3 — see Risks below;
  this is a real gap in how the ticket names its own inputs, not a misunderstanding on this
  investigation's part. `docstring`/`associated_tests` use explicit gap sentinels
  (`DOCSTRING_GAP`, `ASSOCIATED_TESTS_GAP`, `:79-80`) rather than `None`/`""`/`[]` — the assembler
  must never re-derive or silently drop these; if surfaced in an `included[]` entry's
  `inclusion_reason` or elsewhere, the sentinel string should be preserved verbatim, not
  reinterpreted.
- **`docs/engine/contracts/context_packet_contract.md`** §2 (`:54-99`) — the authoritative field
  list this ticket implements against:
  - `ContextPacket` top level: `packet_id`, `corpus_generation`, `retrieval_version`,
    `budget_requested`, `budget_returned`, `included[]`, `excluded_summary[]`, `expansion_policy`.
  - `included[]` — **exactly 10 sub-fields**: `source_id`, `kind`, `path`, `heading_or_symbol`,
    `hash`, `authority`, `freshness`, `score`, `inclusion_reason`, `excerpt_budget`.
  - `excluded_summary[]` — **exactly 4 sub-fields**: `source_id`, `kind`, `reason`, `count`.
  - `expansion_policy` — listed as a field with **no resolved definition anywhere** (Open
    Decisions 5/6 both explicitly deferred per the idea doc and `ticket_plan_structure_phase3.md`'s
    "Do NOT ticket" list). Must be stubbed as a clearly-marked placeholder, never invented
    escalation semantics.
  - §3 "Extension — non-registry-backed source fallback" (`:123-139`, **Decision A**): for
    `code_symbol`, `test`, `graphify_node`, or a `tickets/inprogress/` ticket body, `authority` AND
    `freshness` are both the literal sentinel `unrated` — never defaulted to `P2`/`historical`.
    For `parity_ledger_entry` (`:140-149`), `authority`/`freshness` are populated from that entry's
    own `priority` (`P0`/`P1`/`P2`) and `status` (`verified`/`divergent`/`missing`/`unsupported`/
    `legacy_verified`, `docs/parity_ledger/schema.json:16-23`) — a **second, differently-shaped**
    5-value vocabulary, never coerced into REGISTRY's 4-value `status` enum.
  - §3 "Extension — conflicting active documents" (`:151-169`, **Decision B**): two `included[]`
    docs both `status: active`/`authoritative` on the same subject are **both** included, ranked
    by `authority` (`P0 > P1 > P2`) then `last_verified` recency as tie-break; the lower-ranked
    entry's `inclusion_reason` names the higher-ranked entry's `source_id` as superseding (example
    format `"superseded-by:<source_id>"`, explicitly non-normative).
- `docs/REGISTRY.yaml` (regenerated `2026-07-29T05:15:35Z`, confirmed live) — each doc entry:
  `type: doc`, `path`, `title`, `status`, `layer`, `authority`, `audience`, `tags`, `last_verified`
  (ISO date string, e.g. `'2026-06-06'`) — the exact shape `resolve_metadata()` already joins
  against. Ticket entries add `ticket_id`, `tier`, `ticket_type`, `date`, `related_code_areas`,
  `artifact_files`, `tags` (no `authority`/`status` — tickets are indexed by
  `tools/generate_registry.py` but ticket authority/status semantics are governed by the ticket's
  own frontmatter/body fields, not identical to the doc shape; this investigation did not find a
  ticket-vs-doc-authority distinction needed by AC2's specific two-active-docs scenario, since AC2
  names "candidate docs," not tickets — flagged as an open question below only if a future AC
  needs ticket-vs-ticket tie-break).
- `tools/validate_frontmatter.py:44,54` — `STATUS_VALUES = {"authoritative", "active",
  "historical", "archive"}`, `AUTHORITY_VALUES = {"P0", "P1", "P2"}`. No `unrated` value has ever
  been added to either — `tools/hybrid_retrieval.py:45`'s assertion is the only place this
  disjointness is currently enforced in code; this ticket's module should reuse (import) that same
  `UNRATED` constant, never re-literal `"unrated"` as a fresh string, to avoid future drift between
  two independently-spelled sentinels.

## Mechanics / Engine Constraints

No `docs/mechanics/` chapter or `docs/engine/` contract other than
`docs/engine/contracts/context_packet_contract.md` itself governs this ticket — this is
agent-orchestration/retrieval tooling, not simulation logic, matching the posture the three just-
closed sibling tickets already established (`INFRA-293`/`294`/`295`, all `support_boundary:`
"Agent-orchestration/retrieval tooling only — no simulation behavior, Mechanics Bible chapter, or
engine contract governs this module's semantics"). `context_packet_contract.md` §4 itself states:
"a future Phase 3 ticket... will not need a `docs/parity_ledger/` entry... this contract governs
agent-orchestration/retrieval tooling, not simulation logic" — directly pre-empting any expectation
that this ticket's own module needs a `P0` gate. The contract is nonetheless the load-bearing spec
this ticket must implement byte-for-byte on field names/counts (AC3 tests this directly).

## Parity Ledger Overlap

`docs/parity_ledger/infrastructure.yaml`:
- `INFRA-293` (`TCK-20260729-DETERMINISTIC-CODE-INDEX`) — `status: verified`, `priority: P2`,
  `test_path: tests/tools/test_code_test_index.py`. Passing (module exists, tests exist).
- `INFRA-294` (`TCK-20260729-HYBRID-RETRIEVAL-FUSION`) — `status: verified`, `priority: P2`,
  `test_path: tests/tools/test_hybrid_retrieval.py`. Passing.
- `INFRA-295` (`TCK-20260729-RETRIEVAL-CACHE-LEVELS`) — `status: verified`, `priority: P2`,
  `test_path: tests/tools/test_retrieval_cache.py`. Passing.

No entry exists yet for `TCK-20260729-CONTEXT-PACKET-ASSEMBLY` itself. Following the exact
precedent of the three entries above (`id`, `text`, `status: verified`, `priority: P2` — no `P0`
entry, matching §4's explicit note that this ticket needs no parity ledger gate at all beyond the
batch's own established convention), a new `id: INFRA-296` entry should be appended at
implementation time, citing the new module's `v2_evidence` line ranges and
`test_path: tests/tools/test_context_packet_assembler.py`, `support_boundary:` matching the
`INFRA-293`–`295` wording verbatim. No `P0` entries are touched by this ticket, so no ledger entry
blocks a passing `test_path` requirement beyond this ticket's own new tests.

`docs/parity_ledger/schema.json:16-23` (`priority`/`status` enums) is read-only reference material
for Decision A's `parity_ledger_entry` branch — not modified by this ticket.

## Prior Work

- `stored_artifacts/TCK-20260728-CONTEXT-PACKET-SCHEMA/investigation.md` and its sibling `plan.md`
  — the origin of the field schema and Decision A/B resolutions this ticket implements. Its own
  Risks section (lines 156-171) already anticipated exactly the two gaps this investigation
  reconfirms: (1) non-REGISTRY-indexed sources need an explicit fallback (resolved as `unrated`),
  and (2) "conflicting active documents" had no prior representation (resolved as the
  include-both-and-rank tie-break). Nothing in that resolution has changed since.
- `stored_artifacts/TCK-20260729-HYBRID-RETRIEVAL-FUSION/plan.md` — explicitly states (Step 4)
  `HybridResult`'s field set is "a designed, stable return shape —
  `TCK-20260729-CONTEXT-PACKET-ASSEMBLY` has a hard, load-bearing dependency on this field set. Do
  not reshuffle field names without checking that ticket first." Confirms the field contract this
  ticket's assembler is written against did not drift between planning and landing.
- `stored_artifacts/TCK-20260729-RETRIEVAL-CACHE-LEVELS/plan.md` — Anti-Drift Notes explicitly:
  "`ContextPacket` does not exist as a class yet... Step 4's packet-cache functions must take raw
  fields... never import or assume a `ContextPacket` class/serializer." This ticket is the first to
  actually construct that class/shape; the cache module deliberately does not import it, and this
  ticket must not retroactively make `retrieval_cache.py` import a `ContextPacket` type either
  (Out of Scope: "Implementing C1's fusion logic or C3's cache logic itself").
- `stored_artifacts/TCK-20260729-DETERMINISTIC-CODE-INDEX/plan.md` — confirms `code_test_index.py`
  records carry no `kind` field and are not wired into `knowledge_search.py`'s corpus; explicit
  "Do not build hybrid retrieval fusion, cache layers, or `ContextPacket` assembly in this ticket
  — those belong to the three sibling tickets" (Scope Guards), confirming that ticket intentionally
  left `code_test_index.py` unconnected to C1/C3 and expected a later ticket (this one) to bridge
  it.
- `tests/tools/test_hybrid_retrieval.py`, `tests/tools/test_retrieval_cache.py`,
  `tests/tools/test_code_test_index.py` establish this batch's established test conventions: no
  live ML dependency required (fakes/monkeypatches for BM25/embeddings), `tmp_path`+`monkeypatch`
  isolation for any SQLite/file-path module state, small hand-built fixtures (never asserting
  against live `graph.json`/`knowledge.db` counts), and static AST-based guards for
  import-isolation/naming-collision checks (`test_code_test_index.py` doesn't have one, but
  `test_retrieval_cache.py`'s Step 6 does — the same AST-parse-the-module-source pattern is the
  natural fit for this ticket's own AC5 "grep-based regression test asserts zero references" to
  `.claude/workflows/*.js`).
- No relevant `tickets/done/` ticket outside this batch of four was found relevant by title/module
  overlap (`REGISTRY.yaml` query on `related_code_areas`/`tags` intersecting `ai`/`schema` surfaced
  only the four batch tickets and unrelated older `context`-named tickets like
  `TCK-20260524-LAB-REQUEST-CONTEXT`, already ruled irrelevant by the Phase 2 schema investigation).

## Risks and Open Questions

- **The ticket's own framing ("C1's fused retrieval results and C3's cached results") does not
  account for `code_test_index.py` (a third, separate module) as an input, yet AC1 requires a
  `code_symbol` entry — a kind `HybridResult` can never produce.** The assembler must accept at
  least three distinct candidate shapes as input: `list[HybridResult]` (docs/tickets/
  investigations/working_log, kind ∈ {doc, ticket, investigation, working_log}),
  `list[dict]` from `code_test_index.py::build_records()` (kind should be assigned `code_symbol` by
  the assembler itself, since the source module never tags it), and a parity-ledger-entry source
  (see next bullet). This is not this investigation collapsing an open decision — it is a real,
  confirmed structural gap between what the ticket names as its inputs and what its own ACs
  require. The planner must decide the exact function signature/normalization boundary (e.g. a
  `Candidate` intermediate dataclass each of the three sources maps into before `included[]`/
  `excluded_summary[]` construction) rather than literally writing "consume `list[HybridResult]`
  and `PacketCacheResult`" as the sole inputs.
- **No source anywhere in the repo currently emits a `parity_ledger_entry`-kind candidate at all.**
  `docs/parity_ledger/` is excluded from both `docs/REGISTRY.yaml` (`_SKIP_DOC_SUBDIRS`) and the
  `knowledge_docs` corpus `hybrid_retrieval.py` reads from (same exclusion, inherited from
  `knowledge_search.py`'s corpus definition). Implementing Decision A's `parity_ledger_entry`
  branch (Scope bullet 2, "parity_ledger_entry kind uses its own priority/status fields") therefore
  requires the assembler to independently parse `docs/parity_ledger/*.yaml` (schema:
  `docs/parity_ledger/schema.json`) as a fourth candidate source, bypassing C1/C3 entirely for this
  one kind. None of the ticket's five ACs literally exercises a `parity_ledger_entry` scenario
  (AC1 is `code_symbol`, AC2 is two docs) — only the Scope section requires the code path to exist.
  This is a real risk: an implementer could satisfy every literal AC while leaving the
  `parity_ledger_entry` branch untested or even unreachable from any wiring. The test plan below
  adds a dedicated unit test for this branch to close that gap, since Scope is binding even where
  ACs are silent.
- **`kind` for a raw Graphify node (`graphify_node`) has no existing module producing it either.**
  `code_test_index.py` records are graphify-derived but are their own distinct, already-indexed
  shape (module/symbol/docstring/etc.), not a raw graph node passthrough. Whether `graphify_node`
  as a distinct `included[]` kind is ever populated by this ticket, or is documented as an
  currently-unreachable kind value (same class of gap as `parity_ledger_entry`, but this ticket's
  Scope only explicitly names it as one of the "gets `unrated`" kinds, not as a kind requiring its
  own ingestion path) is a planner decision, not something this investigation should assume an
  answer to.
- **`test`-kind sourcing is similarly unresolved.** No module in this repo (not
  `hybrid_retrieval.py`, whose corpus excludes `tests/`; not `code_test_index.py`, whose records
  represent code symbols with an `associated_tests` list field, not standalone test-file records)
  currently emits a candidate with `kind == "test"`. A `test`-kind `included[]` entry, if
  implemented, would most plausibly be derived from a `code_test_index.py` record's
  `associated_tests` list (one candidate per associated test file) — but this is this
  investigation's inference, not a resolved design; the ticket does not ask for it and no AC
  exercises it. Flagging so the planner does not silently assume `test`-kind population is either
  fully solved or fully out of scope without saying which.
- **`HybridResult` has no `hash` field; the contract requires one per `included[]` entry, and AC4
  forbids raw text anywhere in the packet.** `HybridResult.text` (the raw chunk text) must be
  hashed (the cache module's own `_hash_text()` — `hashlib.sha256(...).hexdigest()`,
  `tools/retrieval_cache.py:171-172` — is the established convention to reuse) and then **discarded
  entirely**, never copied into any packet field. This is a real correctness risk, not just an
  implementation detail: a naive "map every `HybridResult` field into the closest-named contract
  field" implementation would either drop `hash` (contract violation) or accidentally pass `text`
  through into an `inclusion_reason` string or similar free-text field (AC4 violation) if a
  `heading`/`section` value happens to contain excerpt-like text. The test plan below add a direct
  raw-text-leakage assertion.
- **Decision B's tie-break needs `last_verified` date comparison**, and `docs/REGISTRY.yaml`'s
  `last_verified` is a plain ISO-date string (e.g. `'2026-06-06'`), sometimes potentially absent for
  non-`authoritative` docs (`_validate_doc` only requires it when `status: authoritative`, not for
  `status: active`) — two `status: active` docs being tie-broken might have one or both missing
  `last_verified`. The contract's own §3 text does not specify a missing-`last_verified` fallback
  for the tie-break's second key; this is a genuine underspecified edge the planner should resolve
  explicitly (e.g., treat missing `last_verified` as oldest) rather than the implementer guessing
  silently.
- **`expansion_policy`'s stub shape is unspecified beyond "clearly-marked placeholder."** The ticket
  Scope's own wording ("not invented escalation semantics") is the only constraint. A concrete,
  low-risk shape (e.g. a dict/string literal containing an explicit "not yet resolved — Open
  Decisions 5/6" marker, never a real policy object with fields like `max_expansions` or `trigger`)
  should be the planner's explicit choice, not left to implementer improvisation, since an
  under-specified stub is exactly the kind of field an implementer might over-build into real
  logic by accident.

## Anti-Drift Hazards

- **Do not copy `HybridResult.text` (or any code-symbol source excerpt/docstring body used as
  excerpt content) verbatim into any `included[]`/`excluded_summary[]` field.** AC4 is explicit and
  machine-checkable; a hash-then-discard pattern (mirroring `retrieval_cache.py`'s own
  `MAY_LIST_COLUMNS` no-raw-content discipline) is the correct and only correct approach.
- **Do not re-literal the `"unrated"` string.** Import `UNRATED` from `tools.hybrid_retrieval`
  (already guarded there against enum collision) rather than defining a second, independently-
  spelled sentinel constant in the new module — two sentinels that happen to both say `"unrated"`
  today could silently diverge later if one is ever renamed.
- **Do not coerce `parity_ledger_entry`'s `priority`/`status` into REGISTRY's `AUTHORITY_VALUES`/
  `STATUS_VALUES` enums.** The two vocabularies are confirmed structurally different (3-value
  `priority` maps cleanly to `authority`, but parity's 5-value `status` has different semantics
  than REGISTRY's 4-value `status`) — a well-intentioned "just reuse the same mapping" refactor
  would violate the contract's explicit "must never be silently coerced" language.
- **Do not invent fields beyond the contract's exact 10 (`included[]`) / 4 (`excluded_summary[]`)
  lists**, and do not invent `expansion_policy` escalation semantics — Open Decisions 5/6 remain
  explicitly deferred by the batch-scoping doc; a stub is required, not a best-effort design.
- **Do not wire this module into any `.claude/workflows/*.js` file**, and do not import it from
  any file that itself is imported by a workflow file (transitive wiring is still wiring) — AC5's
  grep-based test should check for references to the new module's filename/import path across
  `.claude/workflows/`, not merely a literal top-level import statement in those exact files.
- **Do not modify `tools/hybrid_retrieval.py`, `tools/retrieval_cache.py`,
  `tools/code_test_index.py`, `docs/REGISTRY.yaml`, or `docs/parity_ledger/*.yaml`'s existing
  entries** — this ticket is a pure consumer per its own Out of Scope ("Implementing C1's fusion
  logic or C3's cache logic itself... does not reimplement them"); only a new `INFRA-296` append is
  in scope for the parity ledger file.
- **Do not force-resolve the `test`/`graphify_node`/`parity_ledger_entry` ingestion-path gaps
  identified above by guessing a design** — if the planner does not explicitly resolve them, they
  should be implemented narrowly (e.g., a documented, deliberately-unreachable-by-current-wiring
  code path with its own direct unit test using a hand-built fixture, same as this batch's
  established "prove the function is correct even if nothing calls it live yet" pattern already
  used for `retrieval_cache.py`'s `check_packet_cache()`) rather than silently skipped or silently
  over-engineered into real routing logic no AC asked for.

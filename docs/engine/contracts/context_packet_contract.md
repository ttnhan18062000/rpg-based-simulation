---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, registry, schema]
---

# Context-Packet Contract

This document defines a **schema contract for a future implementation**. No `src/` or `tools/`
code implementing `ContextRequest`/`ContextPacket` construction, serialization, or hashing exists
yet, and none is added by this ticket (`TCK-20260728-CONTEXT-PACKET-SCHEMA`). It is placed under
`docs/engine/contracts/` rather than `docs/ai/` (where sibling decision records such as
`docs/ai/monitoring_writer_decision.md` and `docs/ai/code_test_index_boundaries_decision.md`
live) because it defines a data-shape *contract* that a future Phase 3 ticket implements against —
mirroring `task_result_update_substrate_contract.md`'s role for the engine's Task/Result/Update
substrate — whereas the `docs/ai/*_decision.md` documents are evidentiary decision records for
orchestration-process questions. This document also resolves Open Decision 3 of
`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`
(tracked by epic `TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC`). Per that epic's maturity
banner, this document does not authorize a new mandatory workflow gate, a production
monitoring-writer change, or a new external retrieval service — it only fixes a field shape that
future, separately-scoped tickets may build against.

The packet is a retrieval artifact, not a new source of truth. Consumers must re-read the cited
source before making a high-impact change and reject packets whose source hashes no longer match.

---

## 1. ContextRequest

`ContextRequest` is the input to context classification and retrieval. Fields, verbatim from the
idea doc's Proposed Architecture §1:

- `task_ref | ticket_id | free-text intent` — identifies what the requesting agent is working on:
  a task reference, a ticket ID, or (when neither applies) a free-text statement of intent.
- `provider` — the LLM provider/runtime issuing the request (provider-neutral by design).
- `agent_role` — which agent type is requesting context (e.g. implementer, investigator,
  architecture-reviewer).
- `workflow` — the named workflow the request is running under, if any.
- `phase` — the pipeline phase within that workflow (e.g. Scope, Implement, Verify).
- `risk_tier` — the risk classification of the work driving the request.
- `changed_paths` — the set of file paths already known to be in scope or already modified.
- `scenario` — the named retrieval scenario being served (see idea doc §"Retrieval layers").
- `token_budget` — the maximum context budget the requester is willing to spend.

→ classify and retrieve. This is the request's disposition — a `ContextRequest` is always
consumed by classification and retrieval logic that produces a `ContextPacket` in response; it is
not a new field.

---

## 2. ContextPacket

`ContextPacket` is the bounded, versioned response to a `ContextRequest`. Fields, verbatim from
the idea doc's Proposed Architecture §1:

- `packet_id` — a unique identifier for this packet instance.
- `corpus_generation` — the generation/version marker of the underlying corpus (docs, registry,
  code index) the packet was built against.
- `retrieval_version` — the version of the retrieval logic/scenario definitions used to build the
  packet.
- `budget_requested` — the `token_budget` echoed back from the originating `ContextRequest`.
- `budget_returned` — the actual token cost of the packet as assembled.
- `included[]` — the list of sources selected for inclusion. Each entry has ten sub-fields:
  - `source_id` — a stable identifier for the source (e.g. a `docs/REGISTRY.yaml` entry key, a
    code symbol path, a ticket ID).
  - `kind` — the source's category (e.g. `doc`, `ticket`, `code_symbol`, `test`, `graphify_node`,
    `parity_ledger_entry`). This field is what disambiguates registry-backed sources (indexed by
    `docs/REGISTRY.yaml`) from non-registry-backed sources — see §3 below for how `authority`/
    `freshness` are populated differently depending on `kind`.
  - `path` — the file or resource path the source resolves to.
  - `heading_or_symbol` — the specific heading, section, or code symbol within that path.
  - `hash` — a content hash of the cited excerpt, used by the consumer to detect staleness (see
    the load-bearing constraint above: packets with a stale hash must be rejected, not trusted).
  - `authority` — the source's authority ranking. For a `docs/REGISTRY.yaml`-indexed `kind`
    (`doc`, `ticket` under `tickets/done/`), this is populated directly from that source's
    registry `authority` value (`P0`/`P1`/`P2`). For every other `kind` — `code_symbol`, `test`,
    `graphify_node`, a `tickets/inprogress/` ticket body, or a `parity_ledger_entry` — no
    REGISTRY.yaml value exists to copy; see §3 "Extension — non-registry-backed source fallback"
    for the exact value this field must carry instead.
  - `freshness` — the source's recency ranking. For a REGISTRY-backed `kind`, this is derived from
    that source's registry `status` plus `last_verified` (see §3). For every other `kind`, see the
    same §3 extension — there is no registry-backed freshness signal to derive from.
  - `score` — the retrieval relevance score that ranked this source into the packet.
  - `inclusion_reason` — why this source was selected (also carries the conflicting-active-doc
    tie-break annotation described in §3 "Extension — conflicting active documents").
  - `excerpt_budget` — the token allowance granted to this source's excerpt within the packet's
    overall `budget_requested`.
- `excluded_summary[]` — sources considered but not included, summarized (not itemized in full) by:
  - `source_id`
  - `kind`
  - `reason`
  - `count`
- `expansion_policy` — the rule set and escalation conditions governing when a consumer may
  request an expanded packet (e.g. widen `token_budget`, broaden `scenario`) beyond what was
  initially returned.

---

## 3. Open Decision 3 Resolution

> Which authority/freshness metadata should be mandatory for a packet source, and how should
> conflicting active documents be represented?

**Core resolution.** A packet's `authority`/`freshness` fields are not a new, independently
invented vocabulary. For any `included[]` entry whose `kind` identifies a source indexed by
`docs/REGISTRY.yaml` (a doc under `docs/` outside `_SKIP_DOC_SUBDIRS`, or a `tickets/done/`
entry):

- `authority` is populated directly from that source's frontmatter `authority` field — one of
  `P0`, `P1`, `P2` (`tools/validate_frontmatter.py:54`, `AUTHORITY_VALUES`).
- `freshness` is derived from that source's frontmatter `status` — one of `authoritative`,
  `active`, `historical`, `archive` (`tools/validate_frontmatter.py:44`, `STATUS_VALUES`) — plus
  `last_verified` recency where present. `status: authoritative` with a recent `last_verified` is
  freshest by construction; `status: historical`/`archive` is stale by construction. This is not a
  new independent numeric freshness score — it is a direct read of the existing two-field
  primitive `docs/REGISTRY.yaml` already carries for every doc it indexes
  (`tools/generate_registry.py`'s `collect_docs` copies `status`/`authority`/`last_verified`
  straight from frontmatter with no re-derivation).

### Extension — non-registry-backed source fallback (this ticket's addition, not in the idea doc's original field list)

`tools/generate_registry.py`'s `_SKIP_DOC_SUBDIRS` (`{"archive", "parity_ledger", "scenarios",
"entity"}`, line 42) and its restriction to `docs/` plus `tickets/done/` mean several `included[]`
`kind` values have no `docs/REGISTRY.yaml` entry to read `authority`/`status` from at all:

- **`code_symbol`, `test`, `graphify_node`, or a `tickets/inprogress/` ticket body** carry no
  authority/freshness primitive anywhere in the repo today. For these `kind` values, the packet's
  `authority` and `freshness` fields must both be set to the literal value `unrated` — a sentinel
  used only within this contract's `included[]` field, distinct from and not one of REGISTRY's
  `P0`/`P1`/`P2` or `authoritative`/`active`/`historical`/`archive` values. This states plainly
  that the source carries no registry-backed authority signal; the packet must never imply
  otherwise by, for example, defaulting to `P2`/`historical` as if that were a real registry read.
  This is a documentation statement only — it does not add `unrated` to
  `tools/validate_frontmatter.py`'s `AUTHORITY_VALUES` or `STATUS_VALUES` enums, which govern doc
  *frontmatter*, a different namespace from a packet's per-source-item field value. No code change
  accompanies this document.
- **`parity_ledger_entry`** sources (`docs/parity_ledger/*.yaml`, explicitly excluded from
  `docs/REGISTRY.yaml` by `_SKIP_DOC_SUBDIRS`) are not "unrated" — they carry their own,
  differently-shaped authority proxy: `priority` (`P0`/`P1`/`P2`, `docs/parity_ledger/schema.json`
  lines 20-23) and `status` (`verified`/`divergent`/`missing`/`unsupported`/`legacy_verified`,
  same schema, lines 16-19). For this `kind`, the packet's `authority`/`freshness` fields are
  populated from the parity ledger entry's own `priority`/`status`, not from
  `docs/REGISTRY.yaml` (the entry is not indexed there). This is a **second, differently-shaped
  vocabulary** — 3 values for `priority` mapping cleanly onto `authority`, but a 5-value `status`
  enum with different semantics than REGISTRY's 4-value `status` — and must never be silently
  coerced into REGISTRY's enum space.

### Extension — conflicting active documents (advisory guidance, not a REGISTRY.yaml schema change)

No mechanism in `docs/REGISTRY.yaml`, its generator, or `tools/validate_frontmatter.py` represents
two documents both marked `status: active` (or `authoritative`) disagreeing on the same subject —
this is a genuine, confirmed gap, not an oversight of this contract. The resolution is an
advisory, doc-only tie-break rule for a future packet-assembly implementation, not a schema
change:

When two `included[]` entries are both docs with `status: active` or `status: authoritative`
(`tools/validate_frontmatter.py:44`) and address the same subject, the packet includes **both**
entries rather than silently dropping one. They are ranked by `authority` (`P0 > P1 > P2`,
`tools/validate_frontmatter.py:54`) and then, as a tie-break, by `last_verified` recency. The
lower-ranked entry's `inclusion_reason` is set to explicitly name it as the superseded/
lower-priority alternative — e.g. `"superseded-by:<source_id of higher-ranked entry>"` as an
illustrative, non-normative example format — so a consumer never mistakes it for an equally
authoritative, independent source. This is advisory documentation guidance for a future
packet-assembly implementation's `inclusion_reason` population logic; it adds no new
`docs/REGISTRY.yaml` field, since `inclusion_reason` is already a listed `ContextPacket` field
(§2) and this only constrains how it is populated in this one case.

### What does not change

`docs/REGISTRY.yaml`'s generator (`tools/generate_registry.py`), its schema, and its enum values
(`STATUS_VALUES`, `AUTHORITY_VALUES`, or any other enum in `tools/validate_frontmatter.py`) are
untouched by this resolution. No existing doc requires a new frontmatter field. No
`tools/validate_frontmatter.py` code change accompanies this document — everything above is a
specification for how a future `ContextPacket`-assembly implementation reads existing, unmodified
data.

---

## 4. Verification Path

The field list in §1/§2 is sourced verbatim from
`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`
§"Proposed Architecture" → "1. Context-packet contract" (lines 91-106); that section remains the
source of truth for the field shape. §3 above is this contract's authoritative answer to Open
Decision 3, tracked by epic `TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC`.

No code enforces this contract yet — there is no `ContextPacket`/`ContextRequest` class,
constructor, or serializer anywhere in `src/` or `tools/` as of this document landing. A future
Phase 3 ticket that implements `ContextPacket` construction/serialization must add its own
`tests/`-path verification for that code. That future ticket will not need a
`docs/parity_ledger/` entry: this contract governs agent-orchestration/retrieval tooling, not
simulation logic, the same posture already recorded for agent-monitoring tooling under
`docs/parity_ledger/infrastructure.yaml`'s INFRA-281 through INFRA-292 entries (`support_boundary`
field). A future reader should not read the absence of a parity ledger entry here as a gap.

---

## 5. Open Decision 7 Resolution

> Open Decision 3 fixed how a single `included[]` entry's `authority`/`freshness` are populated
> per `kind`, but never how competing candidates of *different* `kind`s are ranked or chosen
> between under a bounded `token_budget`. What cross-kind candidate-selection/ranking policy
> applies?

**Core resolution.** No selection-or-ranking-against-`token_budget` algorithm exists anywhere in
`tools/context_packet_assembler.py` today — `assemble_context_packet()`
(`tools/context_packet_assembler.py:266-291`) takes an already-decided `included_candidates` list
as a caller-supplied input and includes every one of them unconditionally; there is nothing to
extend cross-kind, because the gap Open Decision 7 names sits upstream of every function this
module exposes. This section resolves three technical constraints that any future cross-kind
policy must respect, and states plainly which part of Decision 7 remains an undecided value
judgment rather than inventing an answer for it.

**Constraint A — `unrated` must not default to worst.** §3's "Extension — non-registry-backed
source fallback" above already states that the `unrated` sentinel "must never imply otherwise by,
for example, defaulting to P2/historical as if that were a real registry read." That constraint
was written about a single entry's own field population, but it is equally binding on any
cross-kind ordering: an ordering rule that silently places every `unrated` candidate (`code_symbol`,
`test`, `graphify_node`, an in-progress `tickets/inprogress/` ticket body — see
`unrated_candidate()`, `tools/context_packet_assembler.py:98-122`, which sets both `authority` and
`freshness` to `UNRATED` at line 119-120) below every `P2` document would functionally reproduce
the exact fabricated-default behavior §3 already forbids, just moved from a single field into an
inter-candidate comparison. This is not new load-bearing text — it is §3's existing constraint,
newly binding on Decision 7.

**Constraint B — `score` is not a cross-kind-comparable signal today.**
`candidate_from_hybrid_result()` (`tools/context_packet_assembler.py:144-165`) sets
`score = result.rrf_score` — a real reciprocal-rank-fusion float produced by
`reciprocal_rank_fusion()` (`tools/hybrid_retrieval.py:59-77`, `DEFAULT_RRF_K = 60`,
`tools/hybrid_retrieval.py:37`), typically a small, query-dependent positive value. By contrast,
`unrated_candidate()` (`tools/context_packet_assembler.py:98-122`) defaults `score: float = 0.0`
at line 105 — the value every `code_symbol` candidate carries today via
`candidate_from_code_index_record()` (`tools/context_packet_assembler.py:125-137`), since no
caller in this codebase currently passes a non-default score for that kind — and
`candidate_from_parity_ledger_fixture()` (`tools/context_packet_assembler.py:205-224`) hardcodes
`score = 0.0` at line 220 for every `parity_ledger_entry` candidate. A naive "sort all candidates
by `.score` descending" would tie every `code_symbol` and `parity_ledger_entry` candidate at
`0.0` regardless of actual relevance while ranking `HybridResult`-derived docs/tickets by a
differently-scaled RRF float. This is a structural gap in the current code, independent of any
policy choice: no resolution of Decision 7 may rely on `.score` as a cross-kind ranking signal
without also naming cross-kind score normalization as a separate, out-of-scope prerequisite that
does not exist yet.

**Constraint C — `_resolve_subject_conflicts()` cannot structurally fire cross-kind.**
`_resolve_subject_conflicts()` (`tools/context_packet_assembler.py:172-198`) is the cited same-kind
precedent for authority-then-recency tie-breaking: within a `subject_key` group, only candidates
whose `freshness in _CONFLICT_ELIGIBLE_FRESHNESS` (`frozenset({"active", "authoritative"})`,
`tools/context_packet_assembler.py:49`) are `qualifying` (line 187), and a group with fewer than
two qualifying candidates is skipped entirely (line 188) before `_AUTHORITY_RANK.index()` is ever
called. Per §3 above, `freshness` is populated per `kind`: a REGISTRY-backed `doc`/done-`ticket`
can have `freshness ∈ {authoritative, active, historical, archive}` — the only `kind` whose
`freshness` can ever equal `"active"`/`"authoritative"` — while `code_symbol`/`test`/
`graphify_node`/in-progress-`ticket` candidates always carry `freshness = "unrated"`
(`unrated_candidate()`, line 120) and `parity_ledger_entry` candidates carry `freshness =
entry["status"]`, a disjoint 5-value vocabulary (`verified`/`divergent`/`missing`/`unsupported`/
`legacy_verified`, `candidate_from_parity_ledger_fixture()`, line 222) that structurally never
intersects `_CONFLICT_ELIGIBLE_FRESHNESS`. So the `qualifying` filter mathematically excludes
every `code_symbol`/`test`/`graphify_node`/in-progress-ticket/`parity_ledger_entry` candidate from
this function's conflict logic before comparison ever begins — this is a structural fact about the
current code, not a policy stance. "Just reuse `_resolve_subject_conflicts()` for the cross-kind
case" is therefore not an available option today; it would require first widening
`_CONFLICT_ELIGIBLE_FRESHNESS` to admit `unrated` and the parity `status` values, which is itself
an unresolved design question this section does not settle (see below).

**Explicit position on both named examples.**

- *Unrated `code_symbol` vs. a P1 doc.* Constraint A forbids ranking the `unrated` `code_symbol`
  below the `P1` doc by silent default, and Constraint B forbids using `.score` to break the tie
  instead (the `code_symbol` candidate's score is `0.0` by construction, not a real relevance
  signal). With both of the obvious tie-break mechanisms ruled out by existing constraints, no
  defensible ordering between these two candidates can be derived from existing code or contract
  text today. This specific pair is deferred pending human sign-off on where `unrated` should sit
  relative to `P1`/`P2` once "don't default to worst" is honored.
- *P0 `parity_ledger_entry` inclusion-floor guarantee.* No inclusion-floor or budget-trimming
  mechanism exists anywhere in this repository today — confirmed by investigation, with no
  precedent found in `tools/context_packet_assembler.py`, `tools/hybrid_retrieval.py`, or
  `tools/parity_index.py`. `tools/parity_index.py`'s `impact()` (`tools/parity_index.py:534-593`)
  does rank parity entries against each other by `(_PRIORITY_ORDER, _STATUS_SEVERITY, entry_id)`
  (`tools/parity_index.py:575-581`), but this is an intra-kind severity ordering over parity
  entries only — it never mixes in a doc/ticket/`code_symbol` row and does not establish a
  cross-kind inclusion floor. Whether a `P0` `parity_ledger_entry` should bypass ordinary ranking
  and always be included in the packet is therefore a genuine, undecided policy choice, not a
  technical derivation from any existing same-kind sort.

**Human sign-off required.** The residual ordering/floor policy — where exactly `unrated` sits
relative to `P1`/`P2` once Constraint A is honored, and whether `P0` `parity_ledger_entry` sources
get a hard inclusion floor — needs explicit human sign-off. It is a genuine value judgment with
zero existing repo precedent for the underlying mechanism (an inclusion-floor/budget-trimming
concept does not exist anywhere in this codebase today), and is therefore left open pending a
human decision rather than resolved by this document. This is not a self-chosen ordering presented
as settled; it is an honest deferral. If a human reviewer later supplies a concrete ordering/floor
policy, a follow-up ticket should extend this section with it.

**No shared numeric scale.** Nothing above merges parity `priority` and REGISTRY `authority` onto
one number line. As §3's parity extension already states, the two are lexically identical
(`P0`-`P2`) but semantically distinct — one is "how much do we trust this doc," the other is "how
severe is this parity gap" — and collapsing them without saying so would be exactly the kind of
silent coercion §3 already warns against.

---

## 6. Open Decision 8 Resolution

> Should `stored_artifacts/{ticket_id}/*.md` (`investigation.md`/`plan.md`/`test_plan.md`,
> each carrying real frontmatter — `artifact_type`, `status`, `authority`) become its own
> registry-indexed `kind` (e.g. `stored_artifact`), so the rationale/decision content
> inside a closed ticket's artifacts is retrievable on its own terms rather than only
> visible via the parent ticket's `artifact_files` path list (`tools/generate_registry.py`
> ::`join_artifact_files()`)? Relatedly: confirm whether `staging_artifacts/`'s current
> total exclusion from `generate_registry.py`'s scan (correct today, since it holds
> in-progress/scratch content for open tickets) should be recorded as an explicit,
> permanent design decision rather than an implicit gap, once/if Decision 8 gives
> `stored_artifacts/` its own retrieval treatment.

**Core resolution — yes.** `stored_artifacts/{ticket_id}/*.md` (scoped to the canonical
`investigation.md`/`plan.md`/`test_plan.md` triplet — see the corpus-heterogeneity caveat below)
warrants a new registry-indexed `kind`, `stored_artifact`. The status quo being changed:
`tools/generate_registry.py::join_artifact_files()` (lines 105-112) globs `stored_artifacts/
{ticket_id}/*.md` non-recursively and returns only a **flat sorted list of path strings** into the
parent ticket's `artifact_files` field — no frontmatter (`status`/`authority`/`artifact_type`) from
any artifact file is read or copied anywhere today. This is the concrete gap the "yes" verdict
addresses: rationale/decision content inside a closed ticket's artifacts is currently retrievable
only by a human or agent opening each path in that flat list, not as an independently
authority/freshness-ranked source in a `ContextPacket`.

**Branch classification — Branch 1, REGISTRY-backed direct mapping.** Of §3's three named
branches (REGISTRY-backed direct mapping / `unrated` sentinel / differently-shaped-primitive
mapping), `stored_artifact` falls into **Branch 1**. `stored_artifacts/{ticket_id}/*.md`
frontmatter carries six fields — `status`, `layer`, `authority`, `audience`, `ticket_id`,
`artifact_type` — validated by `tools/validate_frontmatter.py::_validate_artifact()` (lines
214-225), and its `status` values (`historical`/`active`/`authoritative`/`archive`) and
`authority` values (`P0`/`P1`/`P2`) are drawn from the **exact same enums** (`STATUS_VALUES`,
`AUTHORITY_VALUES`, `tools/validate_frontmatter.py:44` and `:54`) that `docs/REGISTRY.yaml`'s own
`doc`/`ticket` entries use — not a second, disjoint vocabulary the way `parity_ledger_entry`'s
5-value `status` enum is (Branch 3, §3's parity extension). This rules out Branch 2 (`unrated`
sentinel): unlike `code_symbol`/`test`/`graphify_node`/in-progress-ticket-body sources, which carry
**no** authority/freshness primitive anywhere in the repo, `stored_artifacts/*.md` files carry
real, populated values — an empirical corpus scan found 2,941 real artifact files with an
`authority` spread of `P0=4`/`P1=258`/`P2=1698`. The field-shape match means the only reason
`docs/REGISTRY.yaml` doesn't already treat these as a REGISTRY-backed kind is that `collect_docs()`
(`tools/generate_registry.py:186-238`) walks `root / "docs"` only (`docs_dir = root / "docs"`,
line 192; `docs_dir.rglob("*.md")`, line 199) — `stored_artifacts/` sits at repo root, a sibling of
`docs/`, structurally unreachable by that walk regardless of `_SKIP_DOC_SUBDIRS` — a
**directory-scope gap**, not a schema mismatch that would push this toward Branch 2 or 3.

**`last_verified` absence.** Artifact frontmatter carries **no `last_verified` field** at all —
confirmed against `_validate_artifact()` (`tools/validate_frontmatter.py:214-225`), which requires
only the six fields above; `last_verified` appears only in `_validate_doc()`, conditionally
required when `status == "authoritative"`. Per §3's own Branch 1 text ("`freshness` is derived
from ... `status` ... plus `last_verified` recency where present"), this is not disqualifying:
freshness for a `stored_artifact` kind would derive from `status` alone
(`historical`/`active`/etc.), the same partial-derivation already tolerated for any REGISTRY-backed
doc lacking `last_verified` today.

**Corpus-heterogeneity caveat — scope boundary, not resolved here.** The real `stored_artifacts/`
corpus is not uniform. Alongside the canonical triplet (`investigation`: 639, `plan`: 620,
`test_plan`: 582 files), the same directory tree also contains 412 `index.md` files — a separate,
deliberate `tools/generate_artifact_pages.py` Docusaurus-build output with a structurally different
frontmatter shape (`title`/`description`/`artifact_type: index`/`layer`/`tags` only, no
`status`/`authority`/`audience`/`ticket_id`) — one `notice`-typed file, ~20 legacy non-`TCK-*`
directories, and dozens of non-canonical filenames (`walkthrough.md`, `task.md`,
`implementation_plan.md`, `parity.md`, `security_review.md`, etc.) that `join_artifact_files()`'s
non-recursive glob already picks up today. This "yes" verdict applies to the canonical
`investigation.md`/`plan.md`/`test_plan.md` triplet's clean six-field shape; a future
`stored_artifact`-kind scanner (out of scope here — no scanner is implemented by this document)
would need to filter to that triplet or define separate handling for `index`/other shapes. This
paragraph flags that complexity as a scope boundary for that future ticket; it does not resolve it.

**`staging_artifacts/` exclusion — intentional, permanent design.** `staging_artifacts/`'s total
exclusion from `generate_registry.py`'s scan is intentional permanent design, not an accidental
gap. Four points of evidence support this: (a) the idea doc's own Open Decision 8 text quoted
above already asserts this is "correct today, since it holds in-progress/scratch content for open
tickets"; (b) `tools/gate_checks/done_checker_static.py` (lines 279-282) already documents
awareness of the asymmetry via its comment on `content_type_override="artifact"`, showing this is
known, existing behavior, not an overlooked one; (c) empirically, `staging_artifacts/{ticket_id}/`
directories that exist on disk map 1:1 to open `tickets/inprogress/` tickets, none orphaned —
consistent with the "Move staging artifacts to `stored_artifacts/`" step in this project's workflow
rule, which treats the transition as a move, not a copy, so a `staging_artifacts/` directory's
lifetime is bounded to exactly the ticket's open window; (d) indexing ephemeral WIP content as a
retrievable, authority-ranked source would conflict with this contract's own load-bearing principle
that "packets with a stale hash must be rejected, not trusted" — staging content is expected to
churn or disappear before a packet consumer could act on it. This paragraph does not reopen or
re-litigate the question; it records an already-correct decision as durable and explicit.

**What does not change.** `docs/REGISTRY.yaml`'s generator, schema, and enum values remain
untouched by this resolution. No `tools/generate_registry.py`, `tools/context_packet_assembler.py`,
or `tools/hybrid_retrieval.py` code change accompanies this document. A future, separately-scoped
ticket implementing a `stored_artifact`-kind scanner must handle the corpus-heterogeneity caveat
above and add its own `tests/`-path verification; this document only records the decision that
such a scanner is warranted and which branch it falls into.

---

## 7. Open Decision 9 Resolution

> `tools/parity_index.py`'s `entry()`/`impact()`/`health()` functions establish a
> deterministic, exact-structural-lookup query pattern (never similarity-ranked, always
> gate-safe, explicitly distinct from the fuzzy RRF-fused `search`/`tools/hybrid_retrieval.py`
> path) for the `parity_ledger_entry` kind specifically. Should this exact-vs-fuzzy
> retrieval-type split be documented as a general project convention that any future `kind`
> needing gate-safe lookups should follow, rather than remaining an implicit, parity-specific
> pattern?

**Real precedent, both sides of the split.** Exact-lookup side: `entry()`
(`tools/parity_index.py:485-531`) is an exact primary-key lookup (`SELECT * FROM entries WHERE id
= ?`) with a typed `{"entry_id": entry_id, "found": False}` no-match shape — never an exception,
never a silently empty result. `impact()` (`tools/parity_index.py:534-593`) is an exact
path-equality lookup across `_IMPACT_PATH_TABLES` plus `test_refs`, distinguishing
`{"status": "no_filter_provided"}` from `{"status": "no_match"}` as two different "nothing
happened" states rather than collapsing them, and sorts deterministically by
`(_PRIORITY_ORDER, _STATUS_SEVERITY, entry_id)` (`tools/parity_index.py:575-581`) — never a
similarity score. `health()` (`tools/parity_index.py:596-643`) applies exact equality filters on
`subsystem`/`priority` with a deterministic `ORDER BY`, and carries no ranking field at all. All
three sit behind `_connect_readonly()`'s `mode=ro` URI connection (`tools/parity_index.py:87-92`)
— a connection-string-level read-only guarantee, not merely the absence of a write call site.
Fuzzy side: `reciprocal_rank_fusion()` (`tools/hybrid_retrieval.py:59-77`) produces a literal RRF
similarity score, and `hybrid_fuse_and_filter()` (`tools/hybrid_retrieval.py:224-331`) unions
dense (ANN) and lexical (BM25) candidates and orders them by that fused score. These are two
structurally different retrieval shapes, not two configurations of one shape.

The Gate A GO verdict (`docs/ai/parity_readpath_gate_a_decision.md`, 66.7% vs. 4.8% recall) is
evidence that `impact()`/`entry()`/`health()` perform well as a *parity-domain* retrieval path.
It is not evidence that the exact-vs-fuzzy pattern shape generalizes to a different `kind`'s data
— the GO decision's own "Next action" scopes the next step as wiring this specific path behind a
workflow gate, not generalizing it. These are two different claims, and this section does not
conflate them.

**Core resolution — no.** The exact-vs-fuzzy split stays an implicit, parity-specific pattern for
now; it is not promoted to a named general convention. No second `kind` has ever needed a
gate-safe exact lookup — with a sample size of one (n=1), rule-of-three reasoning applies: any
applicability criteria written today from a single instance could not be tested against a second
real case, and would either overfit to `parity_index.py`'s specific implementation choices
(SQLite, the materialized `entry_health` table, the fixed `_REF_TABLES` list) or be abstracted so
far that it becomes unfalsifiable. As stated above, the Gate A GO verdict's recall numbers speak
to parity-domain retrieval quality, not to whether an analogous module for a different `kind`
would carry the same payoff — that distinction is the reason this resolution is "no," not just
context for it. Whether to name a general convention from a single instance is a genuine
value judgment investigation could not resolve from repo evidence alone; the verdict above
reflects explicit human sign-off, not a self-chosen answer presented as objectively settled.

Even without a named convention, the pattern has generalizable properties worth recording as a
citable, non-mandatory reference — what this pattern looks like, for reference if a similar need
arises, not criteria a future `kind` must satisfy:

- Read-only access to the underlying store, at a connection- or transaction-level guarantee (not
  merely the absence of a write call site) — mirroring `_connect_readonly()`'s `mode=ro` URI.
- Exact equality/primary-key matching only — no similarity ranking, no fuzzy scoring field.
- Deterministic sort order via explicit typed keys, never a relevance score.
- An explicit, typed no-match response distinguishing "no filter provided" from "filter provided,
  zero hits" — never a bare exception or a silently empty collection.
- Zero mutation surface — no write path back into the source of truth.

**Reopening condition.** If a second real `kind` genuinely needs a gate-safe exact lookup, a
follow-up ticket should revisit this decision and derive applicability criteria from real
second-instance evidence, rather than the single-instance criteria that would otherwise have to
be written speculatively today.

**What does not change.** `tools/parity_index.py` and `tools/hybrid_retrieval.py` are untouched by
this resolution — no `search` CLI subcommand or other code-shaped artifact is added to either
module to "prove" the pattern. No second exact-lookup module is built for any other `kind`. This
document only records that the exact-vs-fuzzy split remains an implicit, parity-specific pattern
today, with the properties above available for citation if and when a second real use case makes
generalizing it worth another look.

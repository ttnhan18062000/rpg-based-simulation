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

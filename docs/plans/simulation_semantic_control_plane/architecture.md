---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, documentation, schema]
---

# Architecture — Simulation Semantic Control Plane

Part of [the epic](README.md). Defines the model, not the rollout order — see
[rollout_plan.md](rollout_plan.md) for sequencing.

---

## 1. Why this is a control plane, not a document

The project now has two independently-built, independently-frozen bodies of knowledge:

| | What it owns | Size |
|---|---|---|
| **World Rule Catalog** (`docs/world_rules/`) | Target semantics — what must/may/must-never be true about the simulated world | 172 Rule IDs, 12 batches |
| **Mechanism Registry** (`registries/mechanisms.yaml`) | Realization — what mechanisms exist, their state, their implementation binding, their verification | 93 mechanisms, 7 systems |

Checked directly: **neither cites the other.** No Rule file anywhere under `docs/world_rules/`
references a `mechanism_id`; `registries/mechanisms.yaml` never cites a Rule ID. The World Rule
Catalog's own review-exports carry a per-*rule-family* (not per-Rule) prose section,
"Implementation Candidates — Non-Binding," that gestures at realization
(e.g. `places-territory-batch-11a-review.md`'s entry for Territory naming `owner_faction_id`) —
that is real, useful groundwork, but it is prose, not machine-checkable, and cites no mechanism id.

The failure mode this repo already paid for once (`mechanism_registry_initiative.md` §1: five
independently-maintained status artifacts, ~147 hand-written badge texts, none of them agreeing)
is exactly what happens if a third, fourth, and fifth place independently start asserting "is this
Rule realized" without one shared model. This document is that shared model — logical, not
necessarily a new database: a set of canonical registries, validated together, queried through one
surface, same shape as the Mechanism Registry already is.

## 2. Five truths, kept permanently distinct

Collapsing these is the single most expensive mistake this repo's own history demonstrates:
`combat_judgement` was correctly `state: done` (a real, reachable, called implementation) and
*write-only* across four real test conditions — "implemented" and "actually works" are different
claims, and every other pair below is a real instance of the same shape.

| Truth | Question it answers | Owned by |
|---|---|---|
| **Semantic** | What must the simulated world mean? | `docs/world_rules/` (Rule Catalog) |
| **Realization** | What mechanisms currently exist to express that meaning? | `registries/mechanisms.yaml` (`state` field) |
| **Implementation** | What code implements a given mechanism? | Source code, indexed by `implemented_by` |
| **Evidence** | What has actually been observed, and by what instrument? | `registries/mechanisms.yaml` (`verified` block) |
| **Delivery / accepted-divergence** | Does the current build even claim to realize this semantic right now? | `docs/guidelines/intentional_divergences.md` + the Rule Catalog's own admission-discipline categories (see §5) |

**No sixth truth is introduced here.** A `Conformance Profile` concept was proposed and explicitly
rejected for now (§5) — this repo already has two mechanisms that cover the delivery-truth
question, and a third would be exactly the "five documents independently asserting one fact"
problem one layer up.

## 3. Rule ↔ Mechanism mapping — the one new relation

**Shape: many-to-many, typed, never assumed 1:1.** A single Rule (e.g. `TERR-01`, the
seven-way claim/control/jurisdiction/ownership/occupation/cultural-association/residence split)
constrains several mechanisms; a single mechanism (e.g. `combat_resolution`) can realize or be
constrained by several Rules across different domains.

**Do not generate the Cartesian product.** 172 Rules × 93 mechanisms = 15,996 theoretical pairs.
The overwhelming majority of these have no real relationship at all. A mapping entry is recorded
only when a real relationship is found through actual investigation — everything else stays
`UNKNOWN`, which is a valid, permanent, expected state (§7), never coerced into `MISSING` (that
would claim "investigated, absent" for something never investigated at all).

**Typed edges**, so the mapping records *what kind* of relationship, not just that one exists:

| Edge | Meaning |
|---|---|
| `REALIZES` | This mechanism is a real implementation of what this Rule requires/permits. |
| `PARTIALLY_REALIZES` | Realizes part of the Rule's scope; some clause is not yet covered by any mechanism. |
| `CONSTRAINED_BY` | The Rule bounds how this mechanism may behave, without the mechanism being the Rule's primary realization. |
| `PRODUCES_INPUT_FOR` / `CONSUMES_RESULT_OF` | A causal-chain relation between two mechanisms that a Rule's own scenario cites, not a Rule-to-mechanism edge itself — recorded because the Catalog's own scenario banks already trace these chains in prose (e.g. `TERR-01`'s scenarios PT-S06–S10). |

**Never overload `depends_on` with this.** `registries/mechanisms.yaml`'s own header already states
`depends_on`'s narrow meaning (functional prerequisite only) and the three axes it must not absorb
(containment, execution order, collaboration) — this mapping is a fourth, semantic-realization axis
and lives in a sibling structure, not inside the Mechanism Registry.

**Where it lives.** Decided by `roadmap.md` M0
(`TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION`): three separate YAML files, siblings to
`registries/mechanisms.yaml` and mirroring its own hand-authored, dict-of-list-of-dicts shape —

- `registries/rule_mechanism_edges.yaml` — top-level key `edges:`, each row
  `{rule_id, mechanism_id, edge_type, evidence, date}`, `edge_type` one of
  `REALIZES | PARTIALLY_REALIZES | CONSTRAINED_BY`.
- `registries/mechanism_causal_edges.yaml` — top-level key `edges:`, each row
  `{producer_mechanism_id, consumer_mechanism_id, evidence, date}`, deliberately with **no**
  `edge_type` field and no row shape shared with the file above.
- `registries/rule_classifications.yaml` — top-level key `classifications:`, each row
  `{rule_id, classification, evidence, review_date}`, `classification` one of the six-value
  vocabulary in §4, exactly one record per Rule ID present in the file.

All three are validated by `tools/semantic_control_plane/registry.py::validate_all()` (plus a
`check_duplicate_keys()` guard against `yaml.safe_load()`'s silent-last-key-wins risk, mirroring
`tools/mechanism_registry/registry.py`'s own split), proven against deliberately-broken fixtures
the same way the Mechanism Registry's own validator was. `rule_id` resolves against a live scan
of `docs/world_rules/**/*.md` headings, not a hardcoded list; `mechanism_id` resolves via the
existing `MechanismRegistry`. An absent row for a given Rule×mechanism pair or Rule is not itself
an error — per §7's own discipline, `UNKNOWN` is a permanent, expected value, never coerced to
`MISSING`.

**Two distinct records, not one.** M0 must define both: (1) the individual Rule↔Mechanism mapping
edges described above, and (2) a separate, Rule-level *realization classification* record (§4) —
one Rule's aggregate `SUPPORTED`/`PARTIAL`/`CONFLICTING`/`MISSING`/`INERT-OFF`/`UNKNOWN` verdict,
with its own evidence and review date. A Rule can have several mapped mechanisms in different
relations (one `CONSTRAINED_BY`, one `PARTIALLY_REALIZES`) while its own realization classification
is a single human judgment call that does not mechanically fall out of the edge list — recording
only the edges and trying to *infer* the classification from them would silently reintroduce the
exact "mechanical derivation of a relation that isn't actually mechanical" failure this design
already rejected once for the `system` tier (§background in `mechanism_tier_model_initiative.md`).

## 4. Realization classification is reused, not reinvented

The World Rule Catalog's own review exports already classify Rules against the repository using
exactly this vocabulary (confirmed by reading real entries, e.g. `TERR-01`):

```
SUPPORTED | PARTIAL | CONFLICTING | MISSING | INERT-OFF | UNKNOWN
```

This is the same shape as the Mechanism Registry's own `state` enum
(`done|partial|gap|orphan|gated|skeleton`) but is **not identical to it and must not be silently
equated**. A Rule's realization classification is a judgment about whether the Rule's *semantic
requirement* is met; a mechanism's `state` is a judgment about whether the *mechanism itself* is
built/reachable. `TERR-01` is `CONFLICTING` (a shared field actively serves three incompatible
concepts) even though the mechanisms reading `owner_faction_id` are all `state: done` — the code
works exactly as written; the semantics it expresses are wrong. The mapping (§3) is what lets a
Rule's realization be *derived* from its mapped mechanisms' states plus a human judgment call on
whether that combination actually satisfies the Rule — not simply copied from either side.

**Rule modality stays REQUIRED/PERMITTED. No `FORBIDDEN` yet.** After 12 batches and a full
freeze, the real Catalog never once needed a third modality — every one of 172 Rules is REQUIRED
(67) or PERMITTED (26); `FORBIDDEN` appears zero times. A REQUIRED invariant already expresses
prohibition (`TERR-01`: distinctness is REQUIRED, therefore silently collapsing the relations is
invalid) without a new enum value. Add `FORBIDDEN` only if real future work proves REQUIRED/
PERMITTED insufficient — not because a three-value enum is aesthetically cleaner.

## 5. Delivery truth reuses two existing mechanisms — no Conformance Profile yet

The World Rule Catalog's own batch admission discipline already has a category for exactly
"this is real target semantics but not claimed right now": **Scope-Deferred Boundary** (one of the
five admission categories every batch report already uses). Separately,
`docs/guidelines/intentional_divergences.md` already exists specifically to record deliberate
behavior deviations from documented law, with a rationale class and a verification path.

A `Conformance Profile` abstraction ("this build currently claims to realize semantic X") was
considered and **deliberately not introduced**. Between Scope-Deferred Boundary (a Rule-side
declaration) and `intentional_divergences.md` (a code-side declaration), the delivery-truth
question already has two homes. Building a third before either of the first two is shown
insufficient by real use would repeat this epic's own opening problem one layer up. Revisit only
if a real Rule×mechanism mapping exercise (Stage B) hits a case neither existing mechanism can
express.

## 6. State Ownership — capability first, registry maybe later

A recurring drift pattern in this repo (documented at length in
`docs/plans/mechanism_claims_as_tests_initiative.md` §3.2, the `trauma` misattribution) is two
different concerns silently sharing one field or one class. `TERR-01`'s own finding —
`owner_faction_id` read as control, taxation-authority, and sovereignty simultaneously by three
different consumers — is the same shape at the data-ownership level.

**The capability needed: answer "who owns this durable fact?" without reading five documents.**
This does **not** mean building a new first-class "State Concept" registry immediately. Initially,
this is derived/indexed directly from the Rule↔Mechanism mapping (§3) plus the Rule Catalog's own
existing prose (Rules already name their state-ownership claims, e.g. `TERR-01`'s explicit
seven-relation-type split) — a query over existing data, not a new authored corpus. Promote it to
a first-class, separately-registered tier only if real use over several slices demonstrates the
derived/indexed view is insufficient. Building the registry before that evidence exists risks
becoming a second place recording the same fact the mapping and the Rule prose already carry.

## 7. Unknown is permanent, not a bug to eliminate

Two places in this repo already learned this the hard way and it applies here without
modification:

- The Mechanism Registry's own completeness checker sweeps exactly 2 of roughly 15 real source
  directories (`TCK-20260920-MECHANISM-COMPLETENESS-CHECK-SCOPE-GAP`) — "93 mechanisms" is a real
  count of what has been catalogued, not a claim about everything that exists. An unregistered
  class is `UNKNOWN`, never `not a mechanism`.
- This mapping will start, and likely stay for a long time, majority-`UNKNOWN` (172 × 93 minus
  whatever a first slice and normal engineering work actually resolve). `UNKNOWN` must never be
  silently read as `MISSING` — `MISSING` is an investigated, evidenced absence; `UNKNOWN` is simply
  "not yet looked at."

A management view (§8) must always show `mapped` vs. `unmapped` counts alongside any percentage —
never a percentage computed only from the pre-filtered known subset. This is the exact lesson of
the pre-filtered-sample confirmation-rate incident
(`TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN`, where a 100%-pass batch was actually a
100%-pass-on-a-population-selected-for-passing).

## 8. Management Plane — a projection, never a source of truth

Agents and humans both need to answer "how deep is this domain, really" without reading every Rule
family and every mechanism entry by hand. This is generated, never hand-maintained, and never a
single collapsed number (a single "Territory: 63% complete" figure hides exactly what the
Mechanism Registry's own rollup rule already forbids — see
`mechanism_tier_model_initiative.md` §5, "rollups report counts, never a badge"). Minimum axes,
kept independent and never averaged into one score:

```
DESIGN          — how much of the domain's target semantics is drafted/frozen
REALIZATION     — SUPPORTED / PARTIAL / CONFLICTING / MISSING / UNKNOWN, against the mapping
IMPLEMENTATION  — implemented_by coverage
VERIFICATION    — code_trace vs. real runtime (scenario/corpus_run/census) share, same distinction
                  the Mechanism Registry already tracks as runtime_verified_share
INTEGRATION     — do cross-mechanism causal chains this domain depends on actually compose
OBSERVED OUTCOME — what real corpus/scenario runs actually produced, when available
```

A domain can legitimately be design-mature, realization-partial, verification-weak, and
integration-unknown all at once — that is real information, and collapsing it into one number
destroys it, the same way a single atlas badge once did for mechanisms.

## 9. Explicit non-goals

- **No Cartesian-product mapping.** Record real relationships only; everything else is `UNKNOWN`.
- **No `FORBIDDEN` modality** until real usage proves REQUIRED/PERMITTED insufficient (§4).
- **No new Conformance Profile system** until Scope-Deferred Boundary and
  `intentional_divergences.md` are shown insufficient by real use (§5).
- **No first-class State Concept registry** built ahead of evidence that a derived/indexed view is
  insufficient (§6).
- **No overloading `depends_on`** with the Rule↔Mechanism relation, execution order, or
  containment (§3).
- **No single collapsed completion percentage** for a domain (§8).
- **No Context Compiler built before real query patterns exist** — see
  [rollout_plan.md](rollout_plan.md) Stage F. `graphify` remains the load-bearing structural-query
  tool in the meantime; this plane indexes semantic/realization facts, it does not replace
  `graphify` for code-structure questions, and it must degrade gracefully when `graphify` or
  semantic search is unavailable. Confirmed during this epic's own work: the `knowledge-search`
  MCP server was down this session, and invoking `tools/knowledge_search.py` with a bare `python3`
  fails for lack of `sentence-transformers` — it only works through its own dedicated environment
  (`make knowledge-index-update`, which runs it via `.venv-knowledge/bin/python3` and worked
  cleanly). Both failure paths are real; neither is fatal on its own, but this plane must not
  assume either is always reachable.
- **No new permanent document per task.** See `agent_operating_model.md`'s completion-output
  section.

## Related

- `docs/world_rules/README.md` — the semantic truth this plane connects to.
- `registries/mechanisms.yaml`, `docs/plans/mechanism_registry_initiative.md` — the realization
  truth and its own founding rationale.
- `docs/plans/mechanism_tier_model_initiative.md` — the rejected-derivation lesson this design
  applies to the Rule↔Mechanism mapping (declared, not derived, from the start).
- `docs/plans/mechanism_claims_as_tests_initiative.md` — the drift/search-failure catalogue this
  design's own drift-detection requirement (`rollout_plan.md` Stage B) is built to extend.
- `docs/guidelines/intentional_divergences.md` — one of the two existing delivery-truth homes (§5).
- `docs/brainstorm/simulation_semantic_control_plane_external_draft.md` — the external-AI draft
  this epic was authored from (historical, not itself normative).

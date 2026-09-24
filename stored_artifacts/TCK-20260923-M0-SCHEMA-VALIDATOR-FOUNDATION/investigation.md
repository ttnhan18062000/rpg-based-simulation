---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION
artifact_type: investigation
tags: [architecture, schema, documentation, testing]
---

# Investigation — TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION

## Current Behavior

**Nothing connects the two catalogs today.** Confirmed directly (not just cited from
`architecture.md`): zero of the 172 Rule IDs under `docs/world_rules/**/*.md` cite a
`mechanism_id`, and zero of the 93 mechanisms in `registries/mechanisms.yaml` cite a Rule ID.
`architecture.md` §3 (lines 86-90) currently reads "Deliberately undecided in detail here" for
the mapping's file path/format — this is the exact placeholder this ticket must replace.

**`registries/mechanisms.yaml`** (`registries/mechanisms.yaml:109-116` for structure) is the
format precedent this ticket's three new schemas must mirror:
- Top-level YAML dict with named block keys: `layers:` (a dict) and `mechanisms:` (a list of
  dicts), each entry `- id: ...` followed by indented fields.
- A long, prose-heavy header comment (lines 1-107) explaining every field's semantics, explicitly
  calling out which axes are NOT represented (containment, execution order) to prevent a future
  editor from silently overloading a field — the same three-axis discipline `architecture.md` §3
  invokes when it says "Never overload `depends_on`."
- `evidence`-shaped fields use YAML block scalars (`note: >-`) for multi-paragraph citations with
  inline ticket-ID references (e.g. `registries/mechanisms.yaml:130-185`, the `combat_resolution`
  entry's `verified.note`) — this is the precedent for a rich `evidence` field on the new schemas,
  not a bare one-line string.
- Validated with a real `validate(data: dict) -> List[str]` function
  (`tools/mechanism_registry/registry.py:273-487`) that never raises for a business-logic
  violation, only for structurally missing top-level keys, and returns every violation found in
  one pass (`registry.py:45-49` docstring rationale, "build the failure loud").
- A **separate** function, `check_duplicate_keys(path)` (`registry.py:259-270`), catches
  duplicate-YAML-key corruption that `yaml.safe_load()` would silently swallow — this must run
  against the real file path, not the parsed dict, and is documented as a distinct, structurally
  necessary split from `validate()` (`registry.py:210-257` docstring). The new validator should
  follow the same split if the new schemas are also hand-edited YAML (they are, per the file-path
  decision below).
- `MechanismRegistry.__init__()` (`registry.py:156-162`) loads once via `yaml.safe_load()` and
  indexes mechanisms by `id` into a dict — the id-resolution pattern (`ids = {m["id"] for m in
  mechanisms if "id" in m}`, `registry.py:289`) that the new validator's `rule_id`/
  `mechanism_id`/`producer_mechanism_id`/`consumer_mechanism_id` resolution checks should mirror.

**`depends_on`** (`registries/mechanisms.yaml:32-46` header, invariant 1 at `registry.py:309-317`,
invariant 2 acyclicity at `registry.py:318-346`) is a **mechanism-to-mechanism** edge already,
narrowly meaning "cannot produce a meaningful result without this other mechanism already having
run" (functional prerequisite only — not containment, not execution order, not collaboration).
This is exactly the axis the new `producer_mechanism_id`/`consumer_mechanism_id` causal-edge
schema must stay distinct from: `depends_on` is unordered-in-time prerequisite; the new schema is
a directed "A produces input for B" causal fact tied to a scenario/evidence citation, generated
inverse rather than stored both ways. `depends_on` is stored as a plain YAML list of bare id
strings inline on each mechanism (`depends_on: [movement, status_effects, entity_role]`,
`registry.py:123`) — the new schema's edges live in a physically separate file per the ticket's
own Scope/AC, so there is no structural risk of them being read as `depends_on` entries by
accident; the risk is only conceptual (a future editor conflating the two), which is why
`registries/mechanisms.yaml`'s header already carries an explicit "Never overload `depends_on`"
warning that `architecture.md` §3 (lines 81-84) repeats.

**`tools/mechanism_registry/system_registry.py`** (`system_registry.py:1-193`) is the closest
existing precedent for *adding a new, separate registry file* alongside `mechanisms.yaml` without
folding it into that file: `registries/system_registry.jsonl`, append-only JSONL (one JSON object
per line via `json.dumps(entry, sort_keys=True) + "\n"`, `system_registry.py:140-141`), with its
own `load_registry()`, `add_system()`, and a `canonical_form_violation()` regex-based shape check
(`system_registry.py:43-54`). This is JSONL, not YAML — appropriate there because each entry is a
flat, 3-field vocabulary registration (`system`, `added_date`, `note`) with no nested blocks and
no multi-paragraph evidence citation, and because the registry is genuinely append-only (a system
name, once registered, is never edited). The three new schemas in this ticket are structurally
closer to `mechanisms.yaml` itself than to `system_registry.jsonl`: each row needs a real evidence
citation (likely multi-line, citing a code path or a Rule's own review-export prose, per
`architecture.md` §3's "no entry without a citation" precedent from `roadmap.md` M1) and rows are
correctable, not append-only (a re-reviewed classification can change its own verdict the same way
`registries/mechanisms.yaml`'s own header states mechanism `state` correction is "expected,
ordinary maintenance, not a violation," `registries/mechanisms.yaml:6-11`).

**`tests/unit/tools/test_mechanism_registry.py`** (`test_mechanism_registry.py:1-150+`) structures
its deliberately-broken-fixture pattern as: one small, self-contained dict fixture per invariant,
each invalid for exactly *one* invariant at a time (docstring, `test_mechanism_registry.py:5-9`,
"so a validator that only implements 1 of the 4 checks can't accidentally pass all six
invalid-fixture tests by coincidence"), asserting `validate(fixture)` returns a non-empty list and
that the returned error string names the specific offending id (`assert any("foo" in e and
"nonexistent_id" in e for e in errors)`, `test_mechanism_registry.py:98`). A `registry_data`
module-scoped fixture loads the real committed file for the "passes on real/seed data" tests
(`test_mechanism_registry.py:35-38`). `tests/unit/tools/conftest.py` carries an **autouse**
fixture (`_empty_system_registry_by_default`) that neutralizes a whole-corpus-shaped invariant
(orphan-system, invariant 10) for every small synthetic fixture in the directory by default,
documented as necessary because that one invariant is non-compositional (a property of the whole
registry, not of any subset) — `registry.py:443-465`'s own long comment explains why. This matters
for the new validator only if any of its three new invariants end up being similarly
whole-corpus-shaped (none of the ones named in the ticket's Scope/AC appear to be — id-resolution,
enum membership, and no-duplicate-triple are all per-row checks, not whole-corpus checks — but the
implementer should double check this assumption before writing new fixtures).

**`docs/world_rules/**/*.md` Rule ID heading format** — confirmed directly by regex sweep of every
canonical domain-rule file (excluding `docs/world_rules/review-exports/`, which use a different
heading vocabulary — `## Rule Inventory`, `## Repository Findings`, etc., never a bare Rule ID
heading): `^## ([A-Z]{2,8}-[0-9]{2})\b` matches exactly **172** headings across 45 files, matching
the ticket's own stated Rule ID count exactly. Real examples: `## TERR-01 — Territorial claim, de
facto control, ...` (`docs/world_rules/places-culture/territory-control.md:27`), `## LEARN-01 —
An experience's epistemic effect ...`, `## PROG-07 — Different forms of effective power ...`. The
format is consistently `## <ID> — <one-line English restatement>` (an em dash, `—`, not a hyphen)
across every family checked (AGENCY, AUTH, BEL, BODY, CAP, CULT, LEARN, PLACE, PROG, SETT, TERR).
**The parser must scan only the canonical domain-rule files, not `review-exports/`** — the latter
contains prose *about* Rules (batch reports, candidate findings) and would produce false Rule ID
matches or double-counts if included; confirmed by directly grepping both sets. 172 confirmed
unique today (ticket's own stated fact, independently reproduced by this investigation's own
sweep, same count).

**Realization classification vocabulary already exists in prose**, not yet machine-readable: the
Rule Catalog's own review exports already classify Rules against this exact 6-value vocabulary
(`SUPPORTED | PARTIAL | CONFLICTING | MISSING | INERT-OFF | UNKNOWN`) — e.g.
`docs/world_rules/places-culture/territory-control.md:56-59`, TERR-01's own "Repository evidence:
CONFLICTING for control/sovereignty ... MISSING for cultural association and residence
specifically" line, cited by `architecture.md` §4 as the source vocabulary this ticket's schema
(3) reuses rather than invents. **No file exists that reuses this vocabulary in a structured,
per-Rule, one-record form today** — it is embedded, one Rule at a time, inside free-form Markdown
paragraphs. Schema 3 is the first machine-checkable home for it.

## Mechanics / Engine Constraints

This ticket builds infrastructure (schema + validator), not simulation behavior — no
`docs/mechanics/` chapter or `docs/engine/` contract governs its shape directly, the same
conclusion `stored_artifacts/TCK-20260915-MECHANISM-REGISTRY-FOUNDATION/investigation.md`'s own
"Mechanics / Engine Constraints" section reached for the original mechanism registry (precedent
directly on point, same kind of ticket). The one real constraint is architectural, not
mechanics-Bible: `architecture.md` §7's "UNKNOWN is permanent, not a bug to eliminate" discipline
must be structurally enforceable by the schema/validator (an absent mapping row or classification
record must never be treated as an error, and the classification enum must accept `UNKNOWN` as a
first-class, non-error value per AC's own explicit line) and §3/§9's "no Cartesian-product
generation" non-goal must hold — the validator must never fabricate rows for unmapped pairs, only
validate rows that are actually present.

## Docs Requiring Update

- `docs/plans/simulation_semantic_control_plane/architecture.md`: §3 (lines 86-90) currently reads
  "Deliberately undecided in detail here"; the ticket's own AC requires this replaced with the
  actual chosen file path(s)/field names/serialization format for all three schemas, per its own
  explicit Scope line ("Replace architecture.md §3's ... current lines 86-90 ... leave every other
  section of architecture.md unchanged").

`docs/plans/simulation_semantic_control_plane/roadmap.md` is not required to change for this
ticket: it already states M0's deliverables at the level of "three separate schemas, a validator,
proof against broken fixtures" without committing to a specific file path or format (its own line
27-30 explicitly defers that decision to M0's own execution) — this ticket's decision satisfies,
rather than contradicts, what the roadmap already says, so no correction is needed there.

`docs/plans/simulation_semantic_control_plane/rollout_plan.md` is not required to change: it
describes Stage A/B/C at a level of abstraction this ticket's concrete file-path choice does not
alter (`docs/plans/simulation_semantic_control_plane/rollout_plan.md`, Stage A: "Add only the
minimum structured data required to represent..." — a description this ticket's schema satisfies
without needing rewording).

`docs/plans/mechanism_tier_model_initiative.md` is not required to change: this ticket's schema 3
non-derivation rule (§3/§4 of `architecture.md`, restated in the ticket's own Scope/AC) is the
*same* lesson that doc's own §3 "why systems are declared, not derived" already documents for a
different tier (system membership) — this ticket applies an established precedent, it does not
revise the precedent doc itself, and the ticket's own AC does not ask for any edit there.

`registries/mechanisms.yaml`'s own header comment is not required to change: the ticket's AC
explicitly requires `depends_on` and the file's existing semantics stay unchanged (AC: "the
existing depends_on field is unchanged after this ticket"); the new schemas live in physically
separate sibling files, so nothing in `mechanisms.yaml` itself needs updating to describe them.

No `docs/parity_ledger/*.yaml` entry needs updating — see Parity Ledger Overlap below.

## Parity Ledger Overlap

None. This ticket adds schema/validator infrastructure only — no real mapping rows, no simulation
behavior change (the ticket's own Out of Scope: "No real mapping entries/rows/edges/classifications
populated for any actual Rule or Mechanism"). Searched all nine `docs/parity_ledger/*.yaml` files
for any entry whose `text` references the Mechanism Registry, the World Rule Catalog, or the
Semantic Control Plane by name — none found; the parity ledger tracks legacy-vs-V2 simulation
behavior parity, a different axis entirely from this ticket's Rule-Catalog-to-Mechanism-Registry
cross-reference work. This mirrors `TCK-20260915-MECHANISM-REGISTRY-FOUNDATION`'s own investigation
finding for the original mechanism registry (also a schema/tooling ticket, also zero parity ledger
overlap) and `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT`'s (same conclusion, same
class of ticket). Re-verify this at Parity phase if the implementation ends up touching any
Rule/mechanism whose parity status is independently tracked (unlikely given the Out of Scope line
above, but not something this investigation can rule out with certainty for M1+ work).

## Prior Work

- `stored_artifacts/TCK-20260915-MECHANISM-REGISTRY-FOUNDATION/` — the direct structural precedent
  for "schema + validator + broken-fixture proof" as one ticket; its own investigation.md explicitly
  scoped out cross-referencing `docs/mechanics/`/parity ledger (same conclusion reached above), and
  its plan.md/test_plan.md are the template this ticket's own artifacts should structurally resemble
  (deliberately-broken-fixture-per-invariant, `validate()` returns list-of-strings, real/seed-data
  zero-error pass).
- `stored_artifacts/TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION/` — the most recent
  precedent for *adding a new sibling registry file* next to `mechanisms.yaml` (there,
  `registries/system_registry.jsonl` plus `tools/mechanism_registry/system_registry.py`) with its
  own load/validate functions wired into `registry.py::validate()` as two new invariants (9/10).
  Useful precedent for *how* to wire a new file's checks into an existing validate()-shaped
  function, even though this ticket's three schemas are YAML-shaped (mirroring `mechanisms.yaml`
  itself) rather than JSONL-shaped (mirroring `system_registry.jsonl`) — see Current Behavior above
  for why the format choice differs.
- `docs/plans/mechanism_tier_model_initiative.md` §3 — the "declared, not derived" lesson for the
  `system` tier, directly cited by both `architecture.md` §3 and the ticket's own Request Summary as
  the precedent schema 3's non-derivation rule must not repeat the mistake of. Already investigated
  in depth above (Current Behavior).
- `TCK-20260920-MECHANISM-REGISTRY-CI-WIRING` (referenced by both the ticket and `roadmap.md`) — the
  "prove on deliberately broken input, not just clean input" discipline this ticket's own AC and
  `roadmap.md` M0 explicitly reuse. Its own CI-wiring step is explicitly Out of Scope for this
  ticket (a distinct, later-layer ticket).

## Risks and Open Questions

**(a) File path(s) and serialization format for the three new registries — this investigation's
recommendation.** Three new YAML files, sibling to `registries/mechanisms.yaml`, each with a named
top-level list key mirroring that file's own `layers:`/`mechanisms:` shape rather than
`system_registry.jsonl`'s flat JSONL shape:

```
registries/rule_mechanism_edges.yaml
  edges:
    - rule_id: TERR-01
      mechanism_id: regional_sovereignty
      edge_type: CONSTRAINED_BY   # REALIZES | PARTIALLY_REALIZES | CONSTRAINED_BY
      evidence: >-
        one or more lines, code path and/or Rule review-export citation
      date: "2026-09-23"

registries/mechanism_causal_edges.yaml
  edges:
    - producer_mechanism_id: movement
      consumer_mechanism_id: combat_resolution
      evidence: >-
        ...
      date: "2026-09-23"

registries/rule_classifications.yaml
  classifications:
    - rule_id: TERR-01
      classification: CONFLICTING   # SUPPORTED | PARTIAL | CONFLICTING | MISSING | INERT-OFF | UNKNOWN
      evidence: >-
        ...
      review_date: "2026-09-23"
```

Rationale: (1) mirrors the one YAML precedent already in `registries/` rather than inventing a
third file shape; (2) block-scalar `evidence` fields support the same multi-paragraph, ticket-ID-
citing evidence style `mechanisms.yaml`'s own `verified.note` already uses, which a flat JSONL line
would awkwardly truncate or require escaping newlines for; (3) `check_duplicate_keys()`-style
protection against `yaml.safe_load()`'s silent-last-value-wins behavior (the exact corruption
`registry.py:210-257` documents happening for real on `mechanisms.yaml` itself) is directly
reusable/mirrorable for these three files precisely because they share its YAML shape; a JSONL
choice would not need that specific protection but would also lose block-scalar evidence support.
This is a recommendation for the planner/implementer to confirm, not a decision this investigation
can finalize unilaterally — the ticket explicitly leaves it open for "this ticket" (meaning the
full ticket, including Plan/Implement) to resolve.

**(b) `producer_mechanism_id == consumer_mechanism_id` self-edge — this investigation's
recommendation: reject.** A mechanism cannot meaningfully "produce input for" itself within one
directed causal fact — the inverse-lookup function (AC: "what does mechanism B consume") would
return B itself as one of B's own inputs, which is not a real causal fact the architecture.md §3
vocabulary (`PRODUCES_INPUT_FOR`/`CONSUMES_RESULT_OF`) describes; every real example in
`architecture.md` and `roadmap.md` (e.g. `TERR-01`'s own PT-S06–S10 scenario chains) describes a
causal relationship between two *distinct* mechanisms. Unlike `depends_on`'s cycle check (invariant
2, which explicitly guards against multi-node cycles, implying 2+ distinct nodes were always
assumed), nothing in the design docs states whether a longer causal cycle (A produces input for B,
B produces input for A) is intended to be valid or not — `roadmap.md` does not require the causal
edge graph to be acyclic the way `depends_on` must be, and a real feedback loop across two distinct
mechanisms is plausible. **This investigation recommends rejecting only the degenerate
self-edge case** (producer == consumer on the same row), leaving multi-node cycles unaddressed
(no AC requires cycle detection for schema 2, and the ticket's own invariant list does not name
one) — flagged here explicitly so the planner does not silently assume cycle-freedom is required
when it is not in scope.

**Gap: neither the ticket nor `architecture.md` names the exact module the new validator should
live in.** The ticket's Scope says "new module or extension" without deciding between the two.
Recommendation for the planner: a new module is cleaner than extending
`tools/mechanism_registry/registry.py` directly, since these three schemas reference
`docs/world_rules/` (a corpus `registry.py` has never needed to read) and `registries/mechanisms.yaml`
only as a foreign-key target, not as their own home file — bolting three more schemas' validation
logic onto `registry.py` would grow a single-subject module into a two-subject one. A sibling
package (e.g. `tools/semantic_control_plane/`) mirroring `tools/mechanism_registry/`'s own
package shape (`__init__.py` re-exporting a `registry.py`-equivalent module) keeps the two subjects
separated the same way `tools/mechanism_registry/` itself is separated from `tools/layer_registry.py`
today. This is not one of the two open questions explicitly assigned to this ticket by name, but it
blocks Plan-phase file-path decisions the same way (a) does, so it is flagged here rather than left
implicit.

**Risk: the rule_id resolution parser is new code with a real, unverified regex.** This
investigation confirmed `^## ([A-Z]{2,8}-[0-9]{2})\b` matches exactly 172 headings across the
canonical (non-review-export) `docs/world_rules/**/*.md` files by direct execution, not just by
inspection — but the parser also needs to correctly *exclude* `review-exports/`, and no test for
that exclusion exists yet; the planner should require a test asserting the parser does not pick up
a false ID from a review-export file's own prose (none currently match the 2-8-letter-then-2-digit
pattern in a sample check, but this should be a proven invariant, not an assumption).

**Open question left genuinely unresolved by this investigation**: whether `edge_type` in schema 2
needs its own enum at all (the ticket's Scope explicitly says schema 2 has no `edge_type` field —
"no shared edge_type field with schema 1" is itself an AC line) — confirmed already resolved by
the ticket itself, not actually open; listed here only to make explicit that this investigation
checked and found no residual ambiguity on that specific point.

## Anti-Drift Hazards

- **Do not let schema 3's classification become mechanically derivable from schema 1/2's edges**,
  even indirectly (e.g. a helper that "suggests" a classification from edge counts, technically
  distinct from a helper that "sets" one, is still the same drift the ticket's own AC #13
  ("No function in the codebase takes only the edge list ... as input and returns or writes a
  classification value") and `architecture.md` §3's closing paragraph explicitly forbid). Enforce
  by omission — do not write the function at all, not even as an unused utility.
- **Do not fold the causal edge schema's `producer`/`consumer` concept into schema 1's `edge_type`
  enum.** `roadmap.md` (lines 48-51) names this exact mistake as something "an earlier draft of
  this roadmap did exactly this," producing rows where half the declared values don't have a real
  `rule_id` to attach to — the two schemas must stay physically separate files with no shared
  `edge_type` enum, per AC #5.
- **Do not populate any real mapping rows.** Out of Scope is explicit; a seed/example row used only
  to prove `validate()` passes on non-empty data (AC's "real/empty/seed data" line) must be clearly
  synthetic/placeholder, not a real Rule-to-mechanism claim presented as investigated fact — a test
  fixture, not a `registries/` committed row, unless the ticket's own "seed data" language is read
  to require a tiny committed example (if so, the planner should flag it as clearly illustrative,
  not a real M1 finding, to avoid being mistaken for real ingested data later).
- **Do not let the rule_id parser silently include `docs/world_rules/review-exports/`.** These
  files use Rule-ID-shaped prose in tables and citations (e.g. `TERR-01` mentioned inline) without
  being the canonical heading source — a parser that scans the whole `docs/world_rules/` tree
  indiscriminately risks both false-positive matches and double-counting real IDs that also appear
  cited inline elsewhere.
- **Do not touch `registries/mechanisms.yaml`'s `depends_on` field or its header comment.** AC is
  explicit and this is the one piece of existing, heavily-invariant-protected state in this area —
  any edit here, even a seemingly cosmetic doc clarification, risks the same kind of drift
  `architecture.md` §3 exists specifically to prevent.
- **Do not alter any section of `architecture.md` other than §3.** The ticket's own AC and Scope
  both call this out explicitly as a hard boundary — §§1/2/4-9 are settled design context this
  ticket must read but not edit.

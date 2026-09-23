---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, documentation, schema]
---

# Status Axis Model

This repo carries four separate status vocabularies that describe overlapping facts about the same
mechanisms/Rules, with nothing previously binding them to each other. This doc is that binding: it
states how many distinct axes actually exist, what question each answers, which vocabulary is
canonical for each, and how values compare across axes wherever a real relationship exists.

**Reconcile, not merge.** The four vocabularies sit on genuinely different axes. Collapsing them
into one enum would destroy real information current tooling depends on — `VALID_STATES`,
`VALID_VERDICTS`, and `VALID_RULE_CLASSIFICATIONS` are all independently enforced today by separate
validators. This doc keeps the axes declared and separate, never collapsed — the same principle
`docs/plans/simulation_semantic_control_plane/architecture.md` §7/§9 already applies to its own
`UNKNOWN` value ("never coerced," "no single collapsed completion percentage").

## 1. The four axes

Axes A and B are the load-bearing reference: 93 real mechanism rows carry a value, and both are
enforced by `tools/mechanism_registry/registry.py::validate()`. Axis D is enforced but currently
empty (M1's job is to populate it, not this doc's). Axis C is the least authoritative of the four —
aspirational prose with no enforcement and no data behind it. The table below is ordered by that
authority, not alphabetically or historically.

| Axis | Question it answers | Canonical vocabulary | Home | Enforcement / data status |
|---|---|---|---|---|
| A — implementation completeness | Is the mechanism built/reachable? | `state`: `done \| partial \| gap \| orphan \| gated \| skeleton` | `registries/mechanisms.yaml:71`, enforced by `VALID_STATES` (`tools/mechanism_registry/registry.py:139`) | **Enforced, 93 real rows.** |
| B — evidentiary verification | What did an instrument actually find, and how strong is that evidence? | `verified.verdict`: `observed \| contradicted \| inconclusive`, paired with `instrument` (`code_trace` static; `census`/`scenario`/`corpus_run` runtime) | same file, `VALID_VERDICTS` (`tools/mechanism_registry/registry.py:149`) | **Enforced.** No independent rollup view today (only per-row + `mechanism_verification_view.md`). |
| C — runtime reach/liveness | Does it actually run in a real simulation, and how widely? | Compass §10: `MISSING \| DESIGNED \| EXPERIMENTAL \| OFF \| DORMANT \| STARVED \| REACH-LIMITED \| LIVE \| DEPRECATED \| REPLACED` | `docs/brainstorm/core_rpg_design_direction.md:472` | **Aspirational prose, unenforced.** 0 mechanism rows carry a §10 value. Only `STARVED` (line 475) and `REACH-LIMITED` (line 476) have a real one-line definition; the other eight are undefined anywhere in the repo. |
| D — Rule-semantic realization | Does the world Rule's semantic requirement hold, given its mapped mechanisms? | `SUPPORTED \| PARTIAL \| CONFLICTING \| MISSING \| INERT-OFF \| UNKNOWN` | `docs/plans/simulation_semantic_control_plane/architecture.md:125`, enforced by `VALID_RULE_CLASSIFICATIONS` (`tools/semantic_control_plane/registry.py:58-60`) | **Enforced, 0 populated rows today** (M1's job, not this doc's or this ticket's). |

A judgment call, not a mechanical derivation, separates D from A: `TERR-01` is `CONFLICTING` even
though every mechanism reading `owner_faction_id` is `state: done` — the code works exactly as
written, the semantics it expresses are wrong
(`docs/plans/simulation_semantic_control_plane/architecture.md:128-136`).

## 2. Binding table

Every cross-axis pair with a real or claimed relationship, labelled `equivalence` /
`implication` / `correlation` / `no defined relationship`. Pairs not listed in this table have no
defined relationship — see the closing line at the end of this section.

| Pair | Relationship | Rationale |
|---|---|---|
| `MISSING` (C) × `MISSING` (D) | **Correlation, not equivalence.** | Different granularity (mechanism vs. Rule) and different evidentiary bar. C's `MISSING` is undefined in prose beyond its list position; D's `MISSING` carries an explicit "investigated, evidenced absence" requirement, distinct from `UNKNOWN` ("not yet looked at") per `docs/plans/simulation_semantic_control_plane/architecture.md:189-190`. A Rule classified `MISSING` (D) very likely has every mapped mechanism at "`MISSING`-if-it-existed" on axis C, but the converse does not hold, and C has no enforcement to check the correlation against today anyway. |
| `OFF` (C) × `INERT-OFF` (D) | **Equivalence in intent, non-identical evidentiary rigor.** | `INERT-OFF` carries a real, repeatedly-applied definition: `docs/world_rules/README.md:172` ("`knowledge_model` has no decision consumer, INERT/OFF; `PerceptionUpdatePhase` has zero production call sites, INERT/OFF") and `docs/world_rules/roadmap.md:581` ("object provenance is **PARTIAL/INERT-OFF**, not MISSING" — code exists, wired in some sense, zero real production effect, often feature-gated). `OFF` is undefined in prose beyond its list position but reads the same way in plain English. When both apply to the same mechanism/Rule pair, prefer citing `INERT-OFF`'s evidence. Neither value is renamed (see §3). |
| `partial` (A) × `PARTIAL` (D) | **Correlation, not equivalence.** | Same pattern as the `MISSING` pair: mechanism-level completeness judgment vs. Rule-level semantic judgment. A Rule mapped to `partial`-state mechanisms is more likely itself `PARTIAL`, but the converse does not hold, and axis A's `partial` is never a mechanical determinant of axis D's `PARTIAL` — `docs/plans/simulation_semantic_control_plane/architecture.md:119-136` already makes exactly this argument for the shape generally. |
| `gated` (A) × `OFF` (C) | **Correlation.** | `gated` means "code exists, reachable, but sits behind a currently-default-off condition" — confirmed by two real registry rows: `registries/mechanisms.yaml:747` (`temporal_pressure`, gated behind `ENABLE_MEMORY_UPDATE` default OFF) and `:754-758` (a reproduction-path mechanism gated behind `ENABLE_REPRODUCTION_HUMANOID_PATH`, default OFF). This is evidence-suggestive of `OFF` on the runtime axis but not an implication: `gated` states a structural fact (a gate exists) without stating whether that gate is open in the profile being asked about — a `gated` mechanism could be `LIVE` in a profile where its flag is on. |
| `orphan` (A) × `DORMANT` (C) | **No defined relationship.** | `DORMANT` has zero prose definition anywhere in `core_rpg_design_direction.md` (8 of 10 §10 values are undefined). Do not force a mapping to `orphan` on inference alone; record as undefined until `DORMANT` gets a real one-line definition. |
| `skeleton` (A) × [no §10 counterpart] | **No defined relationship.** | `skeleton` is never mentioned in `core_rpg_design_direction.md` (zero hits). It is a purely registry-internal implementation-completeness notion — a scaffold before `gap`/`partial`/`done` — with no runtime-reach meaning at all. |
| `STARVED`/`REACH-LIMITED` (C) × `verified.verdict: contradicted` + a runtime `instrument` (B) | **Correlation.** | A STARVED/REACH-LIMITED case is one plausible cause of a `contradicted` runtime verdict, but `contradicted` alone does not distinguish "conditions almost never occur" from "the logic is outright broken." This is exactly why §4 below records a prose-note convention rather than adding a registry field. |

**All other cross-axis value pairs not listed above have no defined relationship.**

## 3. Homograph decisions

Two value collisions exist across axes. Both are resolved the same way: **keep both words,
document the relationship, never rename.** Renaming either of D's enum values
(`VALID_RULE_CLASSIFICATIONS` in `tools/semantic_control_plane/registry.py`) would widen M0's
already-landed schema, which this ticket does not charge against M1's one bounded schema revision
allowance.

- **`MISSING` × `MISSING` (C vs. D).** Kept distinct as documented in §2 above — correlation, not
  equivalence. The two answer different questions at different granularity and evidentiary bar.
- **`OFF` × `INERT-OFF` (C vs. D).** Kept distinct in name, treated as equivalent in intent per §2
  above. `INERT-OFF` is the more evidenced term (real, repeatedly-applied definition); when both
  apply to the same case, cite `INERT-OFF`'s evidence.

## 4. STARVED / REACH-LIMITED registry-representation decision

**Decision: do NOT add a new registry field.** Runtime reach stays compass-axis-only (Axis C),
qualitative, and is deliberately not registry-resident as a structured value.

The §11 admission test (`docs/brainstorm/core_rpg_design_direction.md:490-501`) was applied against
a hypothetical new `reach` field on the mechanism registry's `verified` block, using
`tactical_decision` (`registries/mechanisms.yaml:186-225` — `state: done`,
`verified.verdict: contradicted`, `instrument: corpus_run`, a textbook STARVED case per §10's own
definition, corroborated by `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION`) as the
concrete test case:

- **Q4 (which system consumes it) fails.** No system consumes a structured `reach` value today; a
  new field with no current consumer is exactly the case the admission test's closing line flags
  with suspicion ("State with no interaction, no consumer, no behavioural effect... should be
  treated with suspicion").
- **Q12 (does it duplicate an existing mechanism under different terminology) fails.** The existing
  `verified.note` free-text field already fully captures this exact case — `tactical_decision`'s own
  `note` (lines 196-204) already states "no evidence the decision logic itself is wrong, only that it
  essentially never selects ATTACK in these worlds' real play," the full STARVED story, unabbreviated,
  in prose the registry already has a field for.

**Lighter-weight alternative adopted instead: a documented convention, not a schema field.** When
`verified.verdict: contradicted` is paired with a runtime `instrument`, the `note` field should name
which of STARVED / REACH-LIMITED / genuinely-broken applies, in prose. This is a convention, not a
new YAML key — **AC 6's "if a registry field is added, `validate()` enforces it" is not triggered**,
since no field is added and `validate()` has nothing new to enforce.

## 5. §10 enforcement status

Confirmed unenforced: 0 mechanism rows carry a §10 value in any field; no validator (`tools/mechanism_registry/registry.py`, `tools/semantic_control_plane/registry.py`) checks any §10 term; only
2 of the 10 values (`STARVED`, `REACH-LIMITED`) are defined in prose anywhere in the repo. §10 is
positioned as the least authoritative of the four axes per §1's table above — it should not be read
as co-equal with Axes A, B, or D, which all have real enforcement (and, for A and B, real data)
behind them.

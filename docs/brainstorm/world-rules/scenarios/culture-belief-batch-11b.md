---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Scenario Bank: Culture / Collective Belief (Batch 11B)

**Purpose/scope.** Ten scenarios used to pressure-test the Culture and Collective Belief rule
families in `places-culture/culture.md` and `collective-belief.md`, per
`tmp/world-rule-batch-11-ext-ai.md`'s own §32 seed list — the Culture/Belief half of Batch 11,
split from Places/Settlements/Territory (Batch 11A) per that instruction's own explicit §1
size/split permission.

Per the standing direction (`tmp/world-rule-direction.md`): a scenario failing against the
current repository does not mean the scenario or its Rule fails. Scoring uses the same
vocabulary as prior batches: **covered** / **partially covered** / **blocked** / **revealed
missing rule** / **revealed contradiction**, against current repository behavior, not the
ideal design.

---

## CB-S01 — Culture spans border

A political border changes; the same culture continues on both sides.

- **Rules invoked:** CULT-01.
- **Result: revealed missing rule.** `CultureState` is keyed by `region_id`, and
  `region.owner_faction_id` is the political-control field — nothing structurally prevents two
  regions under different political control from sharing similar `CultureState` values, but
  no mechanism was found that positively models a *single* culture spanning multiple regions
  as one tracked entity, nor one that preserves a culture's own continuity through a
  political-control change specifically. Confirmed MISSING for the positive claim.

## CB-S02 — One territory, multiple cultures

Different communities inhabit the same polity; cultural state is not collapsed into political
membership.

- **Rules invoked:** CULT-01.
- **Result: covered, structurally, by construction.** `CultureState` is keyed per-region, not
  per-faction/polity — a single polity controlling multiple regions with different
  `CultureState` values is already representable exactly as this scenario requires, confirming
  culture is not collapsed into political membership at the data-shape level, even without any
  richer cultural content realized.

## CB-S03 — Individual rejects local culture

A settlement's cultural pattern exists; a resident rejects a major norm; collective ≠
individual.

- **Rules invoked:** CULT-02, CULT-03.
- **Result: revealed missing rule.** No individual-level cultural-participation field exists
  at all (CULT-03's own MISSING finding) — there is no positive mechanism for an individual to
  align with the regional `CultureState` in the first place, so there is equally no mechanism
  to represent that individual *rejecting* it. The absence is symmetric: this repository
  neither forces cultural alignment nor represents deliberate rejection.

## CB-S04 — Migrant adopts some practices

An individual migrates; repeated social exposure follows; selected practices are adopted;
original identity/history remains.

- **Rules invoked:** CULT-03, Inherited (identity remains distinct through change, Batch 01/05
  identity family).
- **Result: revealed missing rule.** No migration mechanism exists at all
  (`places-culture/settlements.md`'s own confirmed finding, cross-referenced), so this
  scenario's own precondition cannot occur; no individual-level cultural-adoption mechanism
  exists either (CULT-03's own finding) — confirmed MISSING on both the migration
  precondition and the cultural-adoption consequence.

## CB-S05 — Cultural contact without adoption

Two groups interact or trade; each learns about the other; no cultural adoption occurs.

- **Rules invoked:** CULT-04.
- **Result: revealed missing rule, though the Rule's own permission is confirmed coherent
  regardless.** No individual- or group-level cultural-contact/learning mechanism exists to
  exercise either the "learn about" half or the "no adoption results" half — CULT-04's own
  explicit permission (encountering a culture never implies adopting it) remains valid and
  testable in principle even without a mechanism to check it against yet.

## CB-S06 — Cultural blending

Persistent contact; a declared transmission/adaptation process; a new mixed practice emerges.

- **Rules invoked:** CULT-04.
- **Result: revealed missing rule.** Confirmed MISSING — no cultural-blending mechanism of
  any kind exists; `CultureCarryForward`'s own regional drift is event-driven, not
  contact-driven between two distinct cultural patterns.

## CB-S07 — False shared belief

A community believes a false historical story; institutions or individuals act on it; a real
consequence follows.

- **Rules invoked:** BEL-01.
- **Result: partially covered.** `BeliefInstitution`'s own real, well-shaped structure
  (belief grounded in real Chronicle history, distinct from individual belief and from world
  truth) is exactly the shape this scenario probes — but checked directly, it has "no live
  caller yet," so while a *false* collective belief is representable in principle (nothing
  requires `origin_event_id`'s own significance to be accurately interpreted), no mechanism
  currently causes any institution or individual to *act* on a `BeliefInstitution` record at
  all. The structure is right; the causal consequence half is confirmed MISSING/INERT.

## CB-S08 — Sacred place without magic

An ordinary place gains cultural/religious interpretation; it becomes sacred; pilgrims react
differently; no supernatural effect is required.

- **Rules invoked:** BEL-02, BEL-03.
- **Result: revealed missing rule.** No sacred-place mechanism of any kind exists (BEL-03's
  own confirmed MISSING finding, via direct search for "sacred"/"pilgrimage"/"shrine" terms).
  BEL-02's own boundary (no supernatural mechanism required) is trivially satisfied by the
  same absence — there is neither a cultural sacredness mechanism nor a supernatural one to
  conflate.

## CB-S09 — Real magic, no cultural recognition (boundary probe)

A supernatural event occurs; nobody learns or understands it; culture does not automatically
change.

- **Rules invoked:** BEL-02, Inherited (recognition requires an information path).
- **Result: blocked.** This scenario explicitly probes the Culture/Belief ↔ Magic boundary
  without designing Magic content, per the batch instruction's own explicit "do not design
  Magic content" — since no supernatural-event mechanism exists at all (out of this family's
  own scope to build), this scenario cannot be meaningfully scored either way; it is recorded
  as blocked, confirming the boundary itself is coherent (culture should not auto-change from
  an unrecognized supernatural event) without exercising it against real content.

## CB-S10 — Doctrine vs. personal belief

An institution declares a doctrine; a member privately rejects it; membership remains
possible where declared.

- **Rules invoked:** Inherited (doctrine tolerates private dissent, reusing ORG-02 + BEL-01).
- **Result: revealed missing rule.** No institution in this repository currently declares a
  doctrine as its own canonical fact (`ClanState`/`FactionState` have no doctrine field
  distinct from `BeliefInstitution`, and `BeliefInstitution` itself has no live consumer) —
  confirmed MISSING; the Inherited entry's own target permission (membership survives private
  dissent) remains coherent with nothing yet to check it against.

---

## Cross-batch note

CB-S01's own finding (culture keyed per-region, with no cross-region "single culture"
concept) and CB-S02's own finding (culture already not collapsed into political membership,
confirmed by construction) show this family's own realization is genuinely mixed — not
uniformly MISSING the way most of Batch 10's own Politics/Law territory was, and not uniformly
CONFLICTING the way Batch 11A's own territorial-ownership finding was. `CultureState` is real
and consumed, just structurally mismatched to this family's own richer target concept
(CULT-01's own CONFLICTING finding) — a third distinct shape of repository/target-semantics
relationship this Catalog has now documented, alongside "missing entirely" and "present but
ungated."

CB-S07's own finding (`BeliefInstitution` is real, well-shaped, and grounded in real history,
but has no live caller) is a genuinely positive structural match, the same "built, not yet
visible in play" shape Batch 08 already found for `ItemInstance`'s own object-provenance
mechanism — a recurring pattern across batches where this repository's own design intent
already anticipated a Rule this Catalog would later draft, without yet wiring it to any
consumer.

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

## CB-S03 — Individual rejects local culture / four-way divergence

A settlement's cultural pattern exists; a resident rejects a major norm; collective ≠
individual. **Extended per the 2026-09-22 follow-up's own §5 probe:** a single individual
knows the local culture well, practices one of its customs, rejects another, and does not
identify with the culture overall — all four facts hold simultaneously and independently.
This extended clause is designed to fail any realization that reduces all four facts to one
scalar (e.g., a single `cultural_affinity` value).

- **Rules invoked:** CULT-02, CULT-03.
- **Result: revealed missing rule.** No individual-level cultural-participation field exists
  at all (CULT-03's own MISSING finding) — there is no positive mechanism for an individual to
  align with the regional `CultureState` in the first place, so there is equally no mechanism
  to represent that individual *rejecting* it. The absence is symmetric: this repository
  neither forces cultural alignment nor represents deliberate rejection. **Extended clause:
  revealed missing rule, and the Rule's own distinctness requirement is confirmed coherent
  regardless.** With no individual-level field of any kind, the four-way divergence (knowledge
  ≠ practice ≠ rejection ≠ identification) cannot be exercised — but CULT-03's own requirement
  that these remain independently representable is precisely what would fail a future
  single-scalar realization; this scenario exists to hold that requirement visible until a
  real mechanism is built, per the follow-up's own explicit corrected Implementation Candidate.

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

## CB-S07 — False shared belief / institution-free folk belief

A community believes a false historical story; institutions or individuals act on it; a real
consequence follows. **Extended per the 2026-09-22 follow-up's own §7 probe, covering BEL-01's
own institution-*free* half explicitly:** a story, taboo, or folk belief becomes socially
shared across a population with no formal institution ever declaring it; individuals may
still dissent; the shared belief causes coordinated or statistically meaningful behavior;
world truth is unchanged.

- **Rules invoked:** BEL-01 (revised).
- **Result: partially covered, for the institution-backed clause only; revealed missing rule
  for the institution-free clause.** `BeliefInstitution`'s own real, well-shaped structure
  (belief grounded in real Chronicle history, distinct from individual belief and from world
  truth) is exactly the shape the institution-backed half of this scenario probes — but
  checked directly, it has "no live caller yet," so while a *false* collective belief is
  representable in principle for a specific clan, no mechanism currently causes any
  institution or individual to *act* on a `BeliefInstitution` record at all. **Extended
  clause: revealed missing rule.** The institution-*free* case (a folk myth/taboo with no
  declaring institution) has no candidate mechanism whatsoever — confirmed MISSING, not
  merely unconsumed, since `BeliefInstitution` itself cannot represent this case at all (it is
  always keyed to a `clan_id`). This confirms BEL-01's own broader permission is only
  partially realized: the institution-backed half is a real, unconsumed structure; the
  institution-free half has nothing built for it at all.

## CB-S08 — Sacred place without magic / divergent attribution

An ordinary place gains cultural/religious interpretation; it becomes sacred; pilgrims react
differently; no supernatural effect is required. **Extended per the 2026-09-22 follow-up's
own §6 probe:** Culture/Group A regards Place P as sacred; Culture/Group B knows of P but
regards it as ordinary, or interprets it differently; no supernatural effect exists either
way; both states — A's attribution and B's differing view — must be simultaneously
representable, neither one overriding or invalidating the other.

- **Rules invoked:** BEL-02, BEL-03 (revised).
- **Result: revealed missing rule.** No sacred-place mechanism of any kind exists (BEL-03's
  own confirmed MISSING finding, via direct search for "sacred"/"pilgrimage"/"shrine" terms).
  BEL-02's own boundary (no supernatural mechanism required) is trivially satisfied by the
  same absence — there is neither a cultural sacredness mechanism nor a supernatural one to
  conflate. **Extended clause: revealed missing rule, and the Rule's own relational
  requirement is confirmed coherent regardless.** With no attribution mechanism of any kind,
  Group A's and Group B's own divergent views cannot be exercised — but BEL-03's own revised
  requirement (attribution is always relative to a specific attributor, and divergent
  attributions must remain simultaneously representable, never collapsed to one "the place is/
  isn't sacred" answer) is exactly the shape any future realization must satisfy, confirmed
  independently coherent even with nothing yet built to check it against.

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
CONFLICTING the way Batch 11A's own territorial-ownership finding was (itself narrowed,
2026-09-22, to a specific control-vs-sovereignty conflation rather than the field's bare
existence). `CultureState` is real and consumed, just structurally mismatched to this
family's own richer target concept (CULT-01's own CONFLICTING finding) — a third distinct
shape of repository/target-semantics relationship this Catalog has now documented, alongside
"missing entirely" and "present but ungated."

CB-S07's own finding (`BeliefInstitution` is real, well-shaped, and grounded in real history,
but has no live caller) is a genuinely positive structural match, the same "built, not yet
visible in play" shape Batch 08 already found for `ItemInstance`'s own object-provenance
mechanism — a recurring pattern across batches where this repository's own design intent
already anticipated a Rule this Catalog would later draft, without yet wiring it to any
consumer. **Narrowed 2026-09-22 per external follow-up review:** this match covers only the
institution-backed subset of BEL-01 (`BeliefInstitution` is always keyed to a `clan_id`) — the
institution-free half of BEL-01's own permission (CB-S07's own extended clause) has no
structural match of any kind, confirmed MISSING rather than merely unconsumed.

**Cross-batch consistency re-confirmed 2026-09-22 (per the follow-up's own item 8):** Place
identity ≠ Settlement identity (11A's own re-opened SETT-01); territorial cultural
association ≠ Culture (`territory-control.md`'s own terminology fix); Culture ≠ average
individual belief (CULT-02, reworded); individual cultural knowledge/practice/identity/
rejection remain non-collapsed (CULT-03, its Implementation Candidate corrected); collective
belief ≠ individual belief (BEL-01); collective belief does not require an institution
(BEL-01, now with its own dedicated scenario clause); attributed significance/sacredness ≠
universal recognition (PLACE-02/BEL-03, both revised to be attribution-relative); attributed
sacredness ≠ supernatural truth (BEL-02, unchanged, still holds); political control/conquest
does not automatically rewrite culture (CULT-04's own no-default-convergence clause, unchanged,
still holds — no conquest-driven cultural-rewrite mechanism was found either way);
`owner_faction_id`'s own classification now matches directly-traced evidence rather than
schema appearance alone (`territory-control.md`'s own re-verified TERR-01/TERR-03). No
universal Significance system was created as part of this update, per the follow-up's own
explicit prohibition.

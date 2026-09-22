---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Scenario Bank: Places / Settlements / Territory (Batch 11A)

**Purpose/scope.** Fourteen scenarios used to pressure-test the Places, Settlements, and
Territory/Control rule families in `places-culture/places.md`, `settlements.md`, and
`territory-control.md`, per `tmp/world-rule-batch-11-ext-ai.md`'s own §32 seed list — the
Places/Settlements/Territory half of Batch 11, split from Culture/Collective Belief
(Batch 11B) per that instruction's own explicit §1 size/split permission.

Per the standing direction (`tmp/world-rule-direction.md`): a scenario failing against the
current repository does not mean the scenario or its Rule fails. Scoring uses the same
vocabulary as prior batches: **covered** / **partially covered** / **blocked** / **revealed
missing rule** / **revealed contradiction**, against current repository behavior, not the
ideal design.

---

## PT-S01 — Same place, new name

A settlement is renamed after conquest; identity persists unless a declared replacement
occurs.

- **Rules invoked:** PLACE-01.
- **Result: covered.** `PlaceState.place_id` never changes on rename — a name field is not
  even part of the canonical identity key — confirming renaming alone cannot, by construction,
  create a new identity.

## PT-S02 — Same location, new place (counter)

An ancient temple is destroyed; centuries later an unrelated settlement is built on the same
ground; spatial location is the same; place identity may differ.

- **Rules invoked:** PLACE-01, PLACE-03.
- **Result: revealed missing rule.** No mechanism was found for retiring a `place_id` and
  later assigning a genuinely new one at the same coordinates — `PlaceState`'s own
  `prior_kind`/`transformed_tick` trail always continues the *same* `place_id`, confirming this
  repository currently has no realized case of the "new place at the same location" half of
  PLACE-03's own permitted range, only the "same place, changed kind" half.

## PT-S03 — Village becomes town

Population/activity/infrastructure change; settlement capability/state changes; identity
persists.

- **Rules invoked:** SETT-01, SETT-03.
- **Result: partially covered.** Identity persistence through a kind/scale change is
  structurally supported (`place_id` stable, `PlaceKind.CITY`'s own `scale` field could in
  principle represent this). No causal mechanism was found that actually drives a
  population/activity change into a `scale` change — confirmed MISSING for the causal half,
  consistent with SETT-02's own finding.

## PT-S04 — Town becomes ruin

War or disaster; population collapses; the settlement stops functioning; place/history
persists.

- **Rules invoked:** PLACE-03, SETT-03.
- **Result: covered, for the identity/kind-transition half.** This is exactly the one real,
  confirmed case `PlaceState.prior_kind`/`transformed_tick` already realizes — a CITY
  transformed into a RUIN keeps the same `place_id`, with the kind change itself recorded.
  Whether "history persists" beyond the bare `prior_kind` field (a fuller record of what the
  town *was*) is a further, unconfirmed claim — see PLACE-02's own MISSING significance-field
  finding.

## PT-S05 — Abandoned and resettled

A settlement is abandoned; later a population returns; continuity must be explicitly
determined.

- **Rules invoked:** PLACE-03.
- **Result: revealed missing rule.** No resettlement-after-abandonment mechanism was found —
  confirmed MISSING. PLACE-03's own requirement (a domain must explicitly determine
  continuity for this case) has nothing yet to check against, since the case itself does not
  occur in this repository.

## PT-S06 — Claim without control

A kingdom claims a region; it has no effective presence or reach there; the claim persists;
practical control is absent.

- **Rules invoked:** TERR-01, TERR-02, TERR-03.
- **Result: revealed contradiction.** `region.owner_faction_id` is a single field that, by
  construction, cannot represent "claimed by A, controlled by neither A nor anyone else" — the
  field either names a controller or is `None`; there is no way to record a claim independent
  of the control field at all. This is TERR-03's own confirmed CONFLICTING finding exercised
  directly: the data shape actively forecloses this scenario, not merely leaves it unrealized.

## PT-S07 — Control without recognized claim

An army occupies territory; practical control is real; formal legitimacy/claim is absent.

- **Rules invoked:** TERR-01, TERR-02, TERR-03, Inherited (authority/power/legitimacy
  distinctness, Batch 10's INST-03).
- **Result: revealed contradiction, same underlying gap as PT-S06.** `owner_faction_id`'s
  single-field shape cannot distinguish "controls without a recognized claim" from "controls
  with a fully legitimate claim" — both look identical in this repository's own state,
  confirming the same CONFLICTING finding from the opposite direction.

## PT-S08 — Contested territory

Actor A claims; actor B controls; population C recognizes neither; separate facts must
coexist.

- **Rules invoked:** TERR-01, TERR-03.
- **Result: revealed contradiction.** The clearest, richest exercise of TERR-03's own
  CONFLICTING finding — a three-way divergence (claim/control/local-recognition) has no
  representable shape at all in a single nullable `owner_faction_id` field.

## PT-S09 — Jurisdiction without ownership

A government's law applies within a territory; the government does not own every private
property inside it.

- **Rules invoked:** Inherited (jurisdiction is one declared scope among several, reusing
  Batch 10's LAW-03).
- **Result: revealed missing rule, for a different underlying reason than PT-S06/S07/S08.**
  Property ownership (Batch 08 evidence) is already confirmed structurally separate from
  `owner_faction_id` — the "ownership ≠ jurisdiction" half of this scenario's own claim holds
  by construction. The "jurisdiction applying territorially" half is confirmed MISSING, since
  no law/jurisdiction concept exists at all (Batch 10's own LAW-01 finding, reused) — there is
  no jurisdiction mechanism here to test against ownership in the first place.

## PT-S10 — Ownership without sovereignty

A merchant owns an estate; the merchant has no political jurisdiction over the surrounding
territory.

- **Rules invoked:** TERR-01.
- **Result: covered.** Confirmed structurally by construction — an entity's own owned
  building/resource state (Batch 01/08 evidence) has no relationship whatsoever to
  `region.owner_faction_id`; nothing in this repository derives political control from
  property ownership, or vice versa.

## PT-S11 — Migration changes settlement

Population arrives or leaves; labor/resource/cultural pressures change; settlement state
changes.

- **Rules invoked:** SETT-01, SETT-02.
- **Result: revealed missing rule.** No migration mechanism exists at all (confirmed MISSING,
  `settlements.md`'s own Repository Findings) — the causal chain this scenario probes has no
  input to trace, let alone a settlement-state-change output.

## PT-S12 — Settlement growth without a "level"

Real causal changes accumulate; the settlement becomes functionally more capable; no numeric
settlement level is required for this to hold.

- **Rules invoked:** SETT-02.
- **Result: revealed missing rule, but the Rule's own permission is confirmed coherent
  regardless.** No causal growth mechanism of any kind exists (numeric or otherwise) —
  confirmed MISSING. SETT-02's own explicit permission (growth need not be represented as a
  numeric level at all) remains valid and testable in principle even with nothing to check it
  against yet.

## PT-S13 — Settlement level with no consumer (counter)

If a settlement tier/level field exists, an increase that changes nothing is inert rather than
semantic depth.

- **Rules invoked:** SETT-02.
- **Result: blocked.** `PlaceKind.CITY`'s own `scale` field exists and is plausibly readable
  as a "level"-shaped value, but whether anything downstream actually consumes it (prices,
  service availability, opportunity generation) was not exhaustively traced this batch — this
  scenario is recorded as blocked pending that further investigation, rather than scored
  either way without evidence.

## PT-S14 — Ordinary place becomes historically significant (flagship)

An unremarkable crossroads hosts a major historical event; survivors tell others; records/
cultural memory persist; later travelers react to this specific place differently.

- **Rules invoked:** PLACE-02, Inherited (recognition requires an information path).
- **Result: revealed missing rule.** Confirmed MISSING at every stage checked: no
  significance-tracking field exists on `PlaceState` (the "event → place provenance" link is
  absent), so "information transmission → shared recognition → changed behavior" has nothing
  to transmit in the first place. This mirrors, at the Place scale, the identical flagship gap
  already found for individuals (Batch 07/09) and organizations (Batch 10) — see the
  cross-batch note below.

---

## Cross-batch note

PT-S14's own finding is the fourth scale (after individual, Batch 07; lineage, Batch 09;
organization, Batch 10) at which the identical "ordinary subject → historically significant
subject, recognized by specific others" gap has now been found — this is no longer an
isolated missing feature at any one scale; it is a recurring cross-domain structural pattern,
per this batch's own §37 explicit request to record whether this now constitutes a clear
integration concern. It does.

PT-S06/S07/S08's own shared finding (a single nullable `owner_faction_id` field cannot
represent contested claim/control) is this sub-batch's own single most significant repository
mismatch — structurally analogous to, but more severe than, Batch 10's own single-field
`owner_id` warning (which was raised there as a risk to avoid, not yet confirmed as an actual
present violation the way this batch's own direct inspection confirms it here).

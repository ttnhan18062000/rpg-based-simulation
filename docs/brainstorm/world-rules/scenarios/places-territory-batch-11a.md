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
(Batch 11B) per that instruction's own explicit §1 size/split permission. Extended twice on
2026-09-22, by two successive follow-up reviews (`tmp/world-rule-batch-11-followup-ext-
ai.md`, then `tmp/world-rule-batch-11-followup-2-ext-ai.md`) — PT-S03, PT-S05, PT-S06, PT-S07,
and PT-S08 each carry probes added or corrected by one or both follow-ups, extended in place
rather than as new IDs.

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

## PT-S03 — Village becomes town / transformation with default continuity

Population/activity/infrastructure change; settlement capability/state changes; identity
persists. **Extended per the second 2026-09-22 follow-up's own §7 "Transformation With
Default Continuity" probe:** a village grows into a town; its functional/type state changes;
Place identity remains — testing that PLACE-03's own *corrected* default (continuity is the
default outcome of a transformation, not a coin-flip) actually holds for a growth
transformation, not merely the one already-confirmed CITY→RUIN case.

- **Rules invoked:** SETT-01 (revised), SETT-03, PLACE-03 (corrected).
- **Result: partially covered.** Identity persistence through a kind/scale change is
  structurally supported (`place_id` stable, `PlaceKind.CITY`'s own `scale` field could in
  principle represent this) — consistent with PLACE-03's own corrected default (identity
  continuity is the default outcome of a transformation), even though no growth-transformation
  mechanism exists to positively exercise it. No causal mechanism was found that actually
  drives a population/activity change into a `scale` change — confirmed MISSING for the
  causal half, consistent with SETT-02's own finding.

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
determined. **Extended per the 2026-09-22 follow-up's own §1 counter-scenario:** an existing
settlement at Place P is completely abandoned; Place P persists as a geographic/historical
Place; after a long discontinuity, a *different, unrelated* population establishes a
settlement at the same Place. Place-identity continuity and Settlement-identity continuity
must be evaluated as two independent questions, never assumed to move together — "same
Place" does not, by itself, imply "same settlement."

- **Rules invoked:** PLACE-03, SETT-01 (revised).
- **Result: revealed missing rule, on both independent questions.** No resettlement-after-
  abandonment mechanism was found — confirmed MISSING. PLACE-03's own requirement (a domain
  must explicitly determine continuity for this case) has nothing yet to check against, since
  the case itself does not occur in this repository. **Extended clause: revealed missing
  rule, and the two independent questions the follow-up asked to keep separate remain equally
  open.** Whether Place P's own `place_id` would persist through total abandonment and later
  resettlement is untested (the one real transformation case this repository has,
  `PlaceState.prior_kind`/`transformed_tick`, is a kind change, not an abandonment-then-
  resettlement case). Whether the *settlement* founded by the new, unrelated population would
  be the same settlement or a genuinely new one is a second, further-untested question — this
  repository has no mechanism to answer either question, let alone confirm they resolve the
  same way. SETT-01's own revised text explicitly declines to assume they do. **Further
  extended per the second 2026-09-22 follow-up's own §7 "Depopulated Settlement" probe:** a
  settlement's own population reaches zero; its active settlement function ends or becomes
  dormant; Place/history persists regardless. **Result: partially covered.** SETT-01's own
  revised default (settlement status may end/become dormant while the underlying Place's own
  identity persists, per PLACE-03's corrected default) is now stated as this Rule's own target
  semantics — but checked directly, no settlement-status field distinct from raw population
  presence exists at all (SETT-01's own re-verified finding), so this default is confirmed
  coherent as a target requirement without yet being positively exercised against any real
  dormant/active status transition.

## PT-S06 — Claim without control

A kingdom claims a region; it has no effective presence or reach there; the claim persists;
practical control is absent.

- **Rules invoked:** TERR-01, TERR-02, TERR-03.
- **Result: revealed contradiction (restored 2026-09-22 by a second external follow-up
  review, correcting an intermediate same-day revision).** `region.owner_faction_id` is a
  single field this repository currently treats as the complete, authoritative answer to "who
  controls this territory" — checked directly, this active, singular role structurally
  forecloses ever representing a claim independent of that control value, not merely because
  "claim" happens to be unattempted, but because the field's own current use *is* the
  authoritative slot a claim concept would need to share or displace. This is TERR-01/TERR-03's
  own CONFLICTING finding exercised directly, not a bare absence.

## PT-S07 — Control without recognized claim

An army occupies territory; practical control is real; formal legitimacy/claim is absent.

- **Rules invoked:** TERR-01, TERR-02, TERR-03, Inherited (authority/power/legitimacy
  distinctness, Batch 10's INST-03).
- **Result: revealed contradiction, same underlying finding as PT-S06.** `PlaceState.
  owner_faction_id`'s own field comment calls the same field a "Sovereignty override," direct
  evidence that this repository's own code already treats bare military/administrative
  control as if it were legitimate sovereignty — the same field cannot distinguish "controls
  without a recognized claim" from "controls with a fully legitimate claim," confirming the
  CONFLICTING finding from this scenario's own opposite direction.

## PT-S08 — Contested territory

Actor A claims; actor B controls; population C recognizes neither; separate facts must
coexist.

- **Rules invoked:** TERR-01, TERR-03.
- **Result: revealed contradiction.** The clearest, richest exercise of TERR-01/TERR-03's own
  restored CONFLICTING finding — a three-way divergence (claim/control/local-recognition) has
  no representable shape at all in a single field this repository currently treats as the
  sole authoritative territorial-control answer.

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

- **Rules invoked:** PLACE-02 (revised), Inherited (recognition requires an information
  path).
- **Result: revealed missing rule.** Confirmed MISSING at every stage checked: no
  attributed-significance field exists on `PlaceState` (the "event → attribution by some
  specific actor/group" link is absent), so "information transmission → recognition of that
  attribution → changed behavior" has nothing to transmit in the first place. Per PLACE-02's
  own revision, even a future realization of this scenario must keep "significant" scoped to
  whichever specific attributor holds it — never a bare, attributor-free property the crossroads
  simply has. This mirrors, at the Place scale, the identical flagship gap already found for
  individuals (Batch 07/09) and organizations (Batch 10) — see the cross-batch note below.

---

## Cross-batch note

PT-S14's own finding is the fourth scale (after individual, Batch 07; lineage, Batch 09;
organization, Batch 10) at which the identical "ordinary subject → historically significant
subject, recognized by specific others" gap has now been found — this is no longer an
isolated missing feature at any one scale; it is a recurring cross-domain structural pattern,
per this batch's own §37 explicit request to record whether this now constitutes a clear
integration concern. It does.

PT-S06/S07/S08's own shared finding was revised twice on 2026-09-22. A first follow-up review
traced actual consumers rather than reasoning from the field's shape alone, and (correctly)
found `owner_faction_id` is actively read as both control (taxation, `suppression_active`)
and, per `PlaceState`'s own field comment, "sovereignty" — but (incorrectly) concluded from
this that the *contested-claim* half specifically should be downgraded to MISSING/INCOMPLETE,
on the reasoning that "claim" itself was never separately attempted. A second follow-up
review corrected this: the conflict does not depend on claim having been attempted — it
follows from the field's own current, active role as the *sole* authoritative territorial-
control slot, which structurally forecloses ever representing a diverging claim or a
contested state without conflating it with, or overwriting, that same value. The restored
CONFLICTING finding remains structurally analogous to Batch 10's own single-field `owner_id`
warning, now correctly scoped to what the evidence actually supports on both passes, not
merely the first.

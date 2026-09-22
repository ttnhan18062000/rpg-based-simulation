---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Scenario Bank: Magic / Supernatural (Batch 12)

**Purpose/scope.** Sixteen scenarios used to pressure-test the Magic/Supernatural rule family
in `magic-supernatural/supernatural.md`, per `tmp/world-rule-batch-12-ext-ai.md`'s own §24
minimum scenario suite. No additional scenarios were added beyond this minimum, per that
instruction's own explicit "do not force unsupported content merely to hit a number" — the
near-total MISSING repository realization confirmed below leaves no further ambiguity for
additional scenarios to expose.

Per the standing direction (`tmp/world-rule-direction.md`): a scenario failing against the
current repository does not mean the scenario or its Rule fails. Scoring uses the same
vocabulary as prior batches: **covered** / **partially covered** / **blocked** / **revealed
missing rule** / **revealed contradiction**, against current repository behavior, not the
ideal design.

---

## MAG-S01 — Real magic, no witness

A real supernatural event occurs; nobody observes it; nobody believes in it; no institution
recognizes it; no culture assigns significance to it; the supernatural world-state consequence
still occurs.

- **Rules invoked:** MAG-01.
- **Result: revealed missing rule.** No supernatural-event mechanism of any kind exists to
  occur unwitnessed in the first place — confirmed MISSING. MAG-01's own requirement
  (objective truth never requires recognition unless a mechanism explicitly declares it as a
  prerequisite) remains independently coherent regardless.

## MAG-S02 — False magic belief

A population strongly believes a place is cursed; the belief affects travel, economics,
politics, ritual behavior, or settlement behavior; no supernatural curse actually exists.

- **Rules invoked:** MAG-02.
- **Result: revealed missing rule, though the Rule's own permission is confirmed coherent
  regardless.** No mechanism connects any belief record to real social/economic/political
  consequence in this specific shape (belief about a *place* driving *settlement-level*
  behavior) — confirmed MISSING. Separately and positively confirmed: nothing anywhere
  derives objective world truth from belief (MAG-02's own SUPPORTED-by-absence finding) — the
  "no supernatural curse actually exists" half of this scenario holds trivially, since no
  mechanism could make it exist from belief alone even if one tried.

## MAG-S03 — Ordinary event mistaken for magic

An observer sees an unexplained phenomenon; the actual cause is ordinary but unknown to that
observer; the observer attributes it to magic.

- **Rules invoked:** MAG-01, Inherited (Perception/Knowledge, Batch 06).
- **Result: revealed missing rule.** No supernatural-attribution mechanism exists for an
  observer to incorrectly form — confirmed MISSING. The general "ordinary cause, incomplete/
  wrong observer belief" pattern this scenario needs is otherwise well-supported generically
  (Batch 06's own belief/knowledge machinery), but nothing ties it to a *magic* attribution
  specifically.

## MAG-S04 — Real magic mistaken for ordinary cause

Objective magic occurs; the observer's own attribution is wrong (an ordinary cause is
assigned instead).

- **Rules invoked:** MAG-01.
- **Result: revealed missing rule.** Same underlying gap as MAG-S03, from the opposite
  direction — confirmed MISSING, since no objective supernatural truth exists for an observer
  to misattribute in either direction.

## MAG-S05 — Conflicting explanations of one magical event

The same evidence is available to three observers; observer A believes it was ordinary;
observer B correctly attributes it to magic; observer C believes a different supernatural
explanation; all three observed the same event.

- **Rules invoked:** MAG-01.
- **Result: revealed missing rule.** Confirmed MISSING — no supernatural event/evidence
  mechanism exists for three observers to diverge over. MAG-01's own claim (one objective
  event may support several simultaneously-held, observer-relative explanations without
  changing what happened) remains coherent and testable in principle, reusing the same
  per-observer belief architecture (`BeliefEntry`, `KnowledgeFact`) already confirmed real and
  independent per entity in prior batches.

## MAG-S06 — Capability without use

A supernatural capability exists; no effect occurs.

- **Rules invoked:** Inherited (supernatural capability ≠ effect).
- **Result: revealed missing rule.** No supernatural capability field exists on any entity —
  confirmed MISSING. The general capability-without-exercise pattern this scenario needs is
  otherwise well-established for non-supernatural capability (Batch 07 evidence, reused
  directly) — nothing supernatural exists to check the same boundary against yet.

## MAG-S07 — Failed spell/ritual

A valid attempt is made; the supernatural effect fails or is interrupted.

- **Rules invoked:** Inherited (magic may fail), MAG-05.
- **Result: revealed missing rule.** Confirmed MISSING — no spell/ritual-attempt mechanism
  exists to fail or succeed. The general attempt-may-fail pattern this scenario needs is
  otherwise well-established (Batch 07/10 evidence, reused directly).

## MAG-S08 — Persistent cursed object changes owner

Ownership and a supernatural property diverge: the object remains cursed when stolen; the
owner changes but the supernatural property remains; the object belongs legally to A while
physically possessed by B; B does not know it is cursed; C knows the curse exists.

- **Rules invoked:** MAG-03.
- **Result: revealed missing rule.** No supernatural-property field exists on any object —
  confirmed MISSING. The ownership/possession/knowledge distinctness this scenario also
  exercises is otherwise already real and confirmed for non-supernatural cases (Batch 08's
  own `PROP-01`: ownership/possession/custody/access/control distinct — reused directly) —
  nothing supernatural exists yet to attach to that already-sound machinery.

## MAG-S09 — Sacred place without magic

A place is culturally sacred; no supernatural property or effect exists.

- **Rules invoked:** MAG-04, Inherited (BEL-03, Batch 11B).
- **Result: covered, by direct reuse of Batch 11B's own evidence.** BEL-03's own confirmed
  finding (a place may become sacred through cultural interpretation alone, with no
  supernatural component) already establishes this half of MAG-04's own seven-way split —
  reused directly, not re-investigated, since Batch 11B already confirmed the target
  semantics coherent even though no sacred-place mechanism of any kind is realized (MISSING,
  cross-referenced from BEL-03).

## MAG-S10 — Magical place without recognition

A place has objective supernatural truth only; nobody culturally recognizes it.

- **Rules invoked:** MAG-04.
- **Result: revealed missing rule.** This is the specific half of MAG-04's own seven-way
  split that Batch 11B's own "Real Magic, No Cultural Recognition" boundary probe explicitly
  left blocked rather than positively defined (per this batch's own §4 framing, "the inverse
  of Batch 11B's boundary... now positively defined"). Confirmed MISSING: no objective
  supernatural-property field exists on `PlaceState` for this scenario to exercise, but
  MAG-04's own positive requirement (objective supernatural truth never requires cultural
  recognition) is now stated as this family's own target semantics, closing the boundary
  Batch 11B could only block.

## MAG-S11 — Same place, different sacred interpretations

Group A regards a place as sacred; Group B regards the same place as ordinary or interprets
it differently.

- **Rules invoked:** MAG-04, Inherited (BEL-03/PLACE-02, both revised).
- **Result: covered, by direct reuse of Batch 11B's own follow-up evidence.** This is exactly
  the divergent-attribution clause Batch 11B's own follow-up added to CB-S08 — BEL-03's own
  revised text already requires multiple, simultaneous, non-reconciled attributions to remain
  representable, confirmed coherent there and reused here without re-investigation.

## MAG-S12 — Institution declares false miracle

An institution declares that a miracle occurred; the population believes it; no supernatural
event actually occurred.

- **Rules invoked:** MAG-04, Inherited (BEL-01/BEL-02, Batch 11B; authority entry, Batch 10).
- **Result: revealed missing rule.** Confirmed MISSING: no institutional-doctrine-about-a-
  supernatural-event mechanism exists (the same underlying gap `collective-belief.md`'s own
  doctrine-dissent Inherited entry already found for doctrine generally). MAG-04's own claim
  (institutional declaration never makes a supernatural claim objectively true) remains
  coherent regardless, directly reusing BEL-01's own "false collective belief still produces
  real behavior" finding.

## MAG-S13 — Unrecognized real miracle

A real supernatural event (a miracle) occurs; no institution recognizes it.

- **Rules invoked:** MAG-04, Inherited (authority entry, Batch 10).
- **Result: revealed missing rule.** Same underlying gap as MAG-S10/S12, from the
  institutional-recognition angle specifically — confirmed MISSING. Directly parallels this
  batch's own §14 "person has real supernatural capability; institution refuses recognition"
  probe, reusing Batch 10's own authority-never-guaranteed-by-power pattern.

## MAG-S14 — Supernatural information channel

A supernatural information channel (telepathy, clairvoyance, divine revelation) establishes a
bounded information path.

- **Rules invoked:** Inherited (supernatural information channel).
- **Result: partially covered.** `PerceptionGate`'s own `magic_sense`/`magic_signal` channel
  is real, live, structurally-ready infrastructure for exactly this — gated by the same
  threshold/confidence discipline as any ordinary sense, confirmed by direct inspection. The
  gap: no content anywhere currently emits a non-default `magic_signal` for this channel to
  actually carry any real supernatural information through — INERT/OFF, not MISSING, since
  the gating mechanism itself is real.

## MAG-S15 — Ritual practice without supernatural effect

A cultural/religious ritual is practiced; it has no supernatural effect at all.

- **Rules invoked:** MAG-05, Inherited (CULT-01/02, Batch 11B).
- **Result: covered, by direct reuse of Batch 11B's own evidence.** Culture/collective-belief
  content existing with no supernatural component at all is already the default case this
  entire family assumes throughout (MAG-02's own "belief causes only ordinary consequences by
  default" finding) — a ritual practiced purely for cultural meaning requires no supernatural
  mechanism to exist, and none does, confirmed by the same absence.

## MAG-S16 — Supernatural effect without cultural ritual

A supernatural effect occurs without requiring any cultural ritual framing by default.

- **Rules invoked:** MAG-05.
- **Result: revealed missing rule, though the Rule's own permission is confirmed coherent
  regardless.** No supernatural-effect mechanism exists at all (the same underlying gap as
  every other MAG-01/03/04 scenario), so it cannot be checked whether one would require
  cultural framing — but MAG-05's own explicit requirement (a supernatural mechanism's own
  activation is never assumed to require cultural/ritual framing by default, exactly as it
  is never assumed to be belief-gated by default) remains coherent regardless.

---

## Cross-batch note

MAG-S09/S11/S15's own "covered, by direct reuse" results are this batch's own distinctive
shape: rather than finding new gaps, these three scenarios confirm that Batch 11B's own
already-frozen Rules (BEL-03, PLACE-02, CULT-01/02) already fully answer the "cultural/
attributed" half of this batch's own required boundary (§12) without needing re-investigation
— the new content this batch adds is specifically the *objective supernatural* half (MAG-01,
MAG-04) those Rules deliberately left open pending this batch's own arrival.

MAG-S14's own finding (`PerceptionGate`'s `magic_sense`/`magic_signal` channel, real and
structurally ready, but INERT/OFF) is this batch's own version of the recurring "built, not
yet visible in play" pattern this Catalog has now found repeatedly — `BeliefInstitution`
(Batch 11B), `ItemInstance`'s own provenance mechanism (Batch 08), and now this genuinely
positive perception-channel match, each anticipating exactly the kind of content a later
batch's own target semantics would require.

Every other scenario (MAG-S01–S08, S10, S12, S13, S16) confirms the same pattern Batch 10's
own Law/Enforcement family first established at this scale: an entire rule family with
essentially no in-world repository counterpart to check against, recorded honestly as a
load-bearing semantic gap per the standing direction, not as evidence against the target
semantics themselves.

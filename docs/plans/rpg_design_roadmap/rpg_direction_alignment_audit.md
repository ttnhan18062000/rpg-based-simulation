---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, content]
---

# Direction Alignment Audit — RPG Design Roadmap vs. The Unwritten World

**Purpose**: for work this large, re-reviewing every one of 65 investigated ideas against the creative
direction is slower and noisier than reviewing the direction itself once and tracing it back through what's
already scored. This audit does the latter: a full re-read of `docs/brainstorm/the_unwritten_world.html` (the
8 creative-direction principles), cross-checked against `docs/brainstorm/design_merit_scorecard.html`'s
Direction Fit axis (all 65 ideas, one real per-idea score each) and this roadmap's own Known Open Items.

**Headline finding**: no idea or milestone contradicts a principle. Where drift exists it is by omission —
undersold connections and unanswered open questions — not by commission. Nothing here argues for reversing a
decision already made.

## Method

1. Read `the_unwritten_world.html` in full (all 8 principles, their scale/example/failure-mode/craft-
   implication text, and the closing "what this document is for" section), not just the compressed manifesto
   list.
2. Extracted all 65 rows of `design_merit_scorecard.html`'s Direction Fit column plus its "the take" one-
   liner, and read the scorecard's own "Reshape notes" self-critique section in full.
3. Cross-checked every idea scored Direction Fit 0–1 against its full atlas card, to separate ideas that are
   correctly low (pure formula/governance tuning, no principle surface) from ideas whose *fix* restores
   principle-serving behavior the axis's "core mechanism" framing doesn't credit.
4. Cross-checked this roadmap's existing "Known open items" list (below in this same folder) against the 8
   principles for the same undersold-connection pattern.
5. Hunted `the_unwritten_world.html` for every place it poses an open question or names a craft-implication
   without resolving it, and checked whether any of the 66 current ideas answers it.

## A. Confirmed strong alignments (no drift — worth naming, not fixing)

- **Idea 33 (Marriage) and idea 13 (Team-Up)** both preserve genuine refusal on both sides — a direct
  instance of Principle 2's own worked example ("a marriage proposal either side is genuinely free to
  decline").
- **Idea 63 (Belief)** derives belief from real accumulated history rather than an authored pantheon —
  Principle 1 done correctly, independent of the idea's separately-flagged underspecification (see this
  roadmap's existing Known Open Items).
- **Idea 39 (affiliation doesn't flip automatically on conquest)** and **idea 56 (Drifting Loyalty — a City's
  felt allegiance eroding from accumulated cultural drift, no single trigger)** are real, verified instances
  of Principle 4 and Principle 6 respectively — checked against the actual card text, not assumed from the
  idea titles.
- **This session's Expected Events section** (`rpg_expected_schemas.html`) operationalizes Principle 8's own
  question — "how would this become visible to a watching observer" — for all 32 stateful ideas.

## B. Undersold Direction Fit scores — a second, independent fix pattern

Idea 1 (Wire the nine orphans) scores Direction Fit 1/5 ("a checklist, not a feature") under the axis's own
rule — correctly low, since fixing a dormant system isn't a *novel* mechanism. But Principle 7's own named
failure example is, word for word, the "precise, invisible, load-bearing for nothing" pattern idea 1 fixes.
That undersold connection is not unique to idea 1. Full audit of all 10 ideas scored Direction Fit 0–1 found:

| Idea | DF score | The take | Undersold principle |
|---|---|---|---|
| 3. Finish BreakthroughService bonuses | 1 | "Real bonuses sitting in a registry, applied by a function that does nothing." | 7 — idea 1's shape, in miniature |
| 42. Fix town_center pointer bug | 1 | "Every consumer has been silently checking distance from (0,0)." | 5/6 — idea 56 measures a City's isolation *by distance*; this bug has been silently corrupting an already-designed Principle-6 mechanism |
| 17. Wound/Scar penalty mechanics | 0 | "No wound has ever healed." | 2 — a working scar system is a body carrying visible evidence of what happened to it (weaker case; the card's own framing is mostly about a wrong constant, not an unwired system) |
| 8. Prune or finish the dead cognition schema | 0 | "Cleanup, not a feature." | 7, conditionally — see correction below |

**Correction (found while preparing the drafts in Section F, before this doc was merged):** idea 8 was
initially treated as correctly-low alongside 9/15/16/18/19. It isn't a clean case. Idea 8's own card is
exactly `core/cognition.py`'s orphaned model, framed as a binary "prune or finish" decision — DF=0 is a fair
score for the card *as written*, since it's a governance choice, not a mechanism, same shape as idea 9. But
the "finish" branch, if taken, is a direct Principle-7 remediation on the same footing as ideas 1/3/42 — and
nothing in the card or its score currently signals that one of its two branches carries real principle weight
and the other doesn't. See Section E for the precise scope of what's actually orphaned.

Ideas 9, 15, 16, 18, 19 remain correctly low — pure governance/formula/doc-drift items the takes themselves
describe as having no principle surface.

**Idea 66 (Region Contains Multiple Places) is the only idea absent from the Scorecard's table** — added
after the full 65-idea scoring pass, never run through Direction Fit or any of the other 6 axes.

## C. The Scorecard's own blind spot (new finding, not self-acknowledged)

The Scorecard's "Reshape notes" section already self-flags five real limitations: whether Pillar Reach should
normalize to 0–5, an explicit decision *against* ever collapsing the 7 axes into one composite ("this project
has real history with SimQ score-gaming... a single Merit Score would invite the same failure mode"), an open
question about who should score the two subjective axes (Direction Fit, Narrative Generativity) and whether
they need a second independent read, whether pure governance ideas (9, 15–19) should be excluded from scoring
rather than scored near-zero, and a partial 8-idea blind re-score that found real drift on Leverage (idea 34:
5 vs. 2) and Groundedness (idea 21: 3 vs. 5; idea 59: 2 vs. 4).

None of those five mention that **Direction Fit only scores a new idea's novel mechanism — never whether an
already-built system currently complies with or violates one of the 8 principles.** That's the mechanism
behind every finding in section B above, and it is not previously named anywhere in the existing docs.
Recommend adding it as a sixth Reshape note the next time the Scorecard is revisited.

## D. Known Open Items with undersold principle connections

Cross-checking this roadmap's existing "Known open items" list (same folder, `rpg_design_roadmap.md`) against
the 8 principles surfaced connections not previously named:

| Open item (already tracked) | Principle it actually serves | Why |
|---|---|---|
| `CultureDeriver`/`CulturalBiasApplicator` dormant, blocks 3 milestones | 7 | Same failure shape as idea 1 — precise, typed, never fed real data — independently blocking M4/M5/M6 |
| CHURCH's Blessing/Resurrection services, coded, placed in 0 worlds | 7 | A second, independent live instance of the same pattern, distinct from the CultureDeriver case |
| ReputationService has zero tests | 8 | Reputation is the document's own named worked exemplar of Principle 8 ("legible from outside") — an untested flagship means the principle's own proof case is unverified |
| Permadeath bug (`PERMADEATH` bypasses deactivation) | 8 | Inverted Principle 8: the internal record claims the entity died, the observable world shows it still acting — neither "correct underneath" nor "legible from outside" |
| Sense/Drive/Need/Cognition profile caps (6–7 entries each) | 3 | A structural ceiling on how behaviorally distinct any species/individual can get, not just a content-volume note |
| Missing Mechanics Bible social/relationship/political chapter (`social_narrative.yaml`, 265 entries, no chapter home) | 2, 4, 6, 8 | The single least-documented subsystem is exactly the one carrying the most principle-weight — loyalty conflict, relationship drift, reputation legibility |
| Idea 37's race-diversity corpus gap (no test world varies race composition) | 3 + 7 | Any future species-distinctness work risks becoming another "never fed real data" system |
| Idea 30 (Possessions With Personal History) | 5 | The object-level counterpart to "places remember" — an item legible as "the sword that killed the chieftain," not a generic instance |

## E. Open questions The Unwritten World poses and leaves unanswered

The source document itself flags several things as open or "worth building toward," beyond the
already-known trust/grudge-decay gap. Checked each against current idea coverage:

- **Principle 2 — individuals distinguishable by lived history.** Two characters with identical starting
  stats should be tellable apart after "survived three near-deaths and grown warier" versus an easy run.
  **Not addressed by any current idea** — personality is assigned once at entity creation and never shifts
  from accumulated events. No idea number to point to; a genuine gap, not a drifted one.
- **Principle 3 — species psychology, not reskins.** Explicit warning: "giving every creature the same trust
  number, just tuned to different thresholds, would quietly undo this whole principle." **Idea 14 (Species
  Classification layer) is scored Direction Fit 5/5 for exactly this ambition, but its current spec is a
  coarse intelligence tier** — the axis credits the ambition; the spec doesn't yet deliver genuinely divergent
  per-species behavioral logic.
- **Principle 5 — places remember (two distinct extensions).** (a) Political geography: a border that moved
  five times or a city that changed hands three times should carry visible trace. **Not addressed** — idea 66
  (Region→Place) and idea 48 (place-kind transitions) cover physical/structural memory only. (b) "Characters
  should remember places too": a hero grieving a home city that later fell. **Not addressed** — idea 59
  (Home, Exile & Return) tracks `home_region_id` as a live pointer, not a historical or emotional relationship
  to a place that changed after the bond formed.
- **Principle 6 — living relationship decay.** Explicitly marked "genuinely open, not yet decided" in the
  source document: an untested trust or grudge score between two living parties shouldn't sit at a fixed
  value forever. **Not addressed** — idea 55 only decays *inherited* feuds across generations; idea 56 only
  decays *population-scale* political allegiance. No idea touches two-party living-relationship decay.
- **Principle 7 — an existing idea's card undersells the document's own worked cautionary example.**
  ("A self-model, a richer private-trust model, more than one competing memory system... built carefully and
  then never actually switched on") is not hypothetical — it names, almost verbatim, a real system already in
  the codebase: `core/cognition.py`. **Correction to an earlier draft of this section:** this system is not
  un-ticketed — it *is* idea 8 (Prune or finish the dead cognition schema), distinct from idea 1's nine
  orphans (GeneticsSystem, EmotionalModel, EvolutionService, InformationNeedDetector,
  evaluate_social_consequence, SabotageAction, MemoryUpdatePhase, ReputationUpdateService,
  compute_elder_attribute_update). Checking `core/cognition.py` directly, rather than trusting the atlas's
  summary, also narrows the claim: not all ~40 declared dataclasses are orphaned — roughly two-thirds
  (`CommitmentEntry`, `PublicReputationProfile`, `HabitMemory`, `EmotionalModel`, `IdentityDoctrine`,
  `RecoveryState`, `RoleFitPreference`, `PerceptionModel`, three time-tracking entries, `CausalMemoryEntry`)
  have real consumers in `src/domains/`. The genuinely orphaned subset — `SelfModel`, `RiskModel`,
  `SubjectiveModel`, `TrustEntry`, `RelationshipModel`, `PartnerMemory`, `CommitmentModel`, `MotivationModel`,
  `AmbitionProfile`, `ValuePreferenceProfile`, `MoralPreferenceProfile` — is narrower but is still exactly the
  private-trust/relationship/self-model shape Principle 7 names, and `domains/culture/applicator.py`'s own
  docstring explicitly documents skipping `ValuePreferenceProfile` and `MotivationModel` — a system
  consciously declining to feed this data, which sharpens the finding rather than weakening it. The real gap
  isn't a missing idea number, it's that idea 8's DF=0 score treats "prune" and "finish" as equivalent when
  only one of the two branches serves the principle (see Section B's correction).

## F. Recommended next steps

1. **One candidate new idea, drafted here for review — not yet added to the atlas or given an idea number:**
   - *Living Relationship Decay* — a mechanism for two living parties' trust/grudge score to drift toward
     neutral (or curdle further) from time and inattention alone, distinct from idea 55's generational
     inheritance and idea 56's population-scale allegiance. Likely depends on whichever schema idea 37
     (currently underspecified) ultimately settles on for relationship state.
   - *Cognition Schema Wiring is not a new idea — idea 8 already covers this decision.* An earlier draft of
     this section proposed it as a new candidate before checking whether an idea already existed; it doesn't
     need one. What's actually missing is a correction to idea 8 itself: its "finish" branch is a real
     Principle-7 remediation (the genuinely orphaned subset is `SelfModel`, `RiskModel`, `SubjectiveModel`,
     `TrustEntry`, `RelationshipModel`, `PartnerMemory`, `CommitmentModel`, `MotivationModel`,
     `AmbitionProfile`, `ValuePreferenceProfile`, `MoralPreferenceProfile` — see Section E), and its DF=0
     score doesn't distinguish that branch from "prune," which carries no such weight. Recommend a note on
     idea 8's atlas card and Scorecard row splitting the two branches' Direction Fit, rather than a new idea.
2. **Scope extensions to existing ideas** (not new ideas — spec additions to already-approved ones), pending
   review before folding into their atlas cards:
   - Idea 14: require genuinely divergent per-species behavioral logic in acceptance criteria, not a single
     scalar/tier, to guard against the exact anti-pattern Principle 3 names.
   - Idea 59 / idea 66: consider whether `PlaceState` and `home_region_id` need a transformation-history or
     prior-owner trail, not just current kind/pointer, to satisfy Principle 5's political-geography and
     personal-memory asks.
3. **Small credit corrections**, low-risk, can ride in the same pass as the scope extensions: cite Principle
   7 explicitly on ideas 1, 3, 42's atlas cards; cite Principle 2 (lower confidence) on idea 17's; split idea
   8's "prune" vs. "finish" branches on its own card and Scorecard row so only "finish" carries Principle-7
   credit; add the sixth Reshape note to the Scorecard (Section C); tag the Known Open Items rows in Section D
   with their principle numbers directly in `rpg_design_roadmap.md`.
4. Re-run Direction Fit (and the other 6 axes) on idea 66 the next time the Scorecard is revisited, so it
   isn't the one idea in the set that's never been checked against the creative direction at all.

None of the above blocks any milestone above. This audit closes the "review the direction" pass; items 1–3
are proposals awaiting your go-ahead before they change any published page.

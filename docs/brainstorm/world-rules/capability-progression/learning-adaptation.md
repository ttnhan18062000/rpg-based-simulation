---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Learning / Adaptation

**Purpose/scope.** Whether repeated exposure, success, or failure produce durable change, and —
critically — *what kind* of durable change each produces. Does not collapse learning, practice,
adaptation, conditioning, habit, mastery, and transformation into one concept unless semantics
justify it; does not build detailed neuroscience/psychology.

**Status.** Batch 07 (Capability/Progression/Conflict), first draft. Candidates below
originated as external-reviewer hypotheses (`tmp/world-rule-batch-7-ext-ai.md`); each carries
this session's disposition and repository evidence. Structured per the normalized five-category
methodology established in Batch 05/06's admission-discipline passes. This family is smaller
than `capability-progression.md` — a genuine two-Rule family, not a target to pad; "a family
with 2 genuine Rules is valid," per the batch instruction's own explicit statement.

---

## Domain Rules

## LEARN-01 — "Learning" mechanisms in this repository are epistemic by default, not capability-improving

> Every mechanism in this repository that could be called "learning" — refining a threat
> estimate, extracting a causal lesson from failure, gaining regional familiarity from repeated
> presence — changes what a subject *believes or knows*, never its own combat capability
> directly. Capability itself changes only through Progression's own declared mechanisms
> (`capability-progression.md`'s PROG-01). This is a real, checked boundary, not an assumption:
> a future mechanism could cross it (a "training" path that genuinely improves an attribute),
> but none currently does.

**Disposition: ACCEPT.** Passes the admission test: no earlier Rule states this specific
mapping — that this repository's own "learning-shaped" mechanisms all resolve to the
Knowledge/Memory side of the Perception/Knowledge/Agency boundary (Batch 06), never the
Capability side. This is new content precisely because it resolves an ambiguity the batch
instruction's own conceptual grammar (`Experience → Accumulation → Adaptation/Learning →
Capability`) leaves open: does "Learning" write to Capability, or only feed it indirectly
through decisions? This repository's answer, checked directly, is the latter, and not even
that in most cases.

**Repository evidence: SUPPORTED, across three independent mechanisms, none of which touches
capability.** `CombatLearning.learn()` (`src/domains/combat_engagement/`, declared law per
`docs/mechanics/04_strategic_cognition.md` §13, gated `ENABLE_COMBAT_ENGAGEMENT` OFF) refines an
`OpponentModel`'s *estimate* of another entity's power — an epistemic correction, never a
combat-stat change for either participant. `CausalAttributionService.attribute()`
(Batch 05/06 Memory-domain evidence) extracts a `CausalMemoryEntry` (cause/advice) from a
qualifying failure event (`combat_loss`/`failed_search`/`failed_craft`/`party_abandoned`) — read
back only as a route-scoring bias adjustment (`avoid_enemy` → suppress `HUNT_WEAK_ENEMY`) when
`ENABLE_MEMORY_UPDATE` is on, never as an attribute or stat change.
`SpatialMemoryUpdateService.update_region_visit()` raises regional *familiarity* purely from
repeated presence (`+0.15`/tick, capped at `1.0`) — again epistemic, never a capability change.
All three "learning-shaped" mechanisms this repository has are confirmed to sit entirely on the
Knowledge/Memory side of the boundary Batch 06 already drew.

**Scenarios:** [CP-S03](../scenarios/capability-progression-batch-07.md#cp-s03) (failure
teaches), [CP-S04](../scenarios/capability-progression-batch-07.md#cp-s04) (experience with no
durable change, counter).

---

## LEARN-02 — Success and mere repetition/failure need not be treated identically for capability-relevant progression

> A world's own rules decide which experience-types translate into durable capability change,
> and they are not required to treat qualifying success, mere repetition, and failure
> identically. A world may grant capability-relevant progression only for success, only for
> failure, for both, or for neither — this is a legitimate design choice each mechanism states
> for itself.

**Disposition: ACCEPT.** Passes the admission test: no earlier Rule addresses whether success
and repetition/failure must be treated identically for progression purposes — this is new,
domain-specific content answering the batch instruction's own §5 question ("does success matter
differently from mere repetition? can failure teach?").

**Repository evidence: SUPPORTED — this repository's own answer is asymmetric and consistent.**
For *capability* (XP/Level, the only durable capability-progression channel this family found):
only a qualifying success event (a kill, a completed quest) grants XP — `CombatRewardClassificationService`
and the `QUEST` conservation-path source kind are both success-gated; no failure or mere
repetition anywhere grants XP. For *epistemic* state (LEARN-01's own domain): failure *does*
teach, but only epistemically — `CausalAttributionService` is explicitly triggered by failure
events (`combat_loss`, `failed_search`, `failed_craft`), never by success; mere repeated
exposure without either success or failure also produces an epistemic change (spatial
familiarity, LEARN-01's own third example). This repository's own consistent shape: success
feeds capability; failure and repetition feed only belief/knowledge; neither is required to
feed the other, and this repository does not.

**Scenarios:** [CP-S01](../scenarios/capability-progression-batch-07.md#cp-s01),
[CP-S02](../scenarios/capability-progression-batch-07.md#cp-s02),
[CP-S03](../scenarios/capability-progression-batch-07.md#cp-s03).

---

## Inherited / Applied Foundational Rules

### A durable change requires a real, declared causal bridge from the originating experience

> An experience producing a durable change — capability or epistemic — must trace to a real,
> declared mechanism connecting the two; not every experience is required to produce a durable
> change at all.

**Disposition: INHERITED — direct reuse of CAUSE-01, restated at `capability-progression.md`'s
own point of use and reused here for Learning/Adaptation's own parallel claim. No new content:
this entry exists so this file's own LEARN-01/02 are read against the same causal-path
discipline `capability-progression.md` already cites, without duplicating that citation's own
rationale.**

**Repository evidence: SUPPORTED**, reused directly — see `capability-progression.md`'s own
fuller evidence for this same inherited entry.

**Scenarios:** [CP-S04](../scenarios/capability-progression-batch-07.md#cp-s04).

---

## Scope / Deferred Boundaries

### Detailed conditioning/habit/psychological modeling

> This family does not build detailed neuroscience or psychology — conditioning, habit
> formation, and mastery-as-a-distinct-accumulating-state beyond what this repository already
> evidences (continuous attribute-driven skill-power scaling, `SkillScalingService`) are not
> introduced as new concepts here, per the batch instruction's own explicit "do not build
> detailed neuroscience/psychology" instruction — matching Batch 06's own analogous discipline
> for cognitive-state modeling.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

- **Confirmed — every "learning-shaped" mechanism in this repository is epistemic, never
  capability-affecting.** See LEARN-01 above. This is a clarifying finding, not a gap: it
  answers a genuine ambiguity in the batch's own conceptual grammar rather than exposing an
  absence.
- **Cross-referenced from `capability-progression.md`**: `TRAIN_SKILL`'s unreachable
  opportunity-generation (MISSING) is the concrete place a genuine capability-improving
  "practice" mechanism would live if built — this file does not repeat that finding's own
  evidence, only notes that it is the natural landing point for LEARN-01's own stated future
  exception ("a future mechanism could cross it... none currently does").

## Cross-domain links recorded here

- LEARN-01 → Perception/Knowledge/Agency (Batch 06's KNOW-02/MEM-02, the Knowledge/Memory side
  of the boundary every one of this repository's "learning" mechanisms falls on), Capability/
  Progression (`capability-progression.md`'s PROG-01, the Capability side nothing currently
  crosses into)
- LEARN-02 → Capability/Progression (`capability-progression.md`'s PROG-05, the
  success-only-grants-XP finding this Rule's own evidence reuses)

## Open questions carried forward

1. Whether a future "practice" mechanism should be built that genuinely crosses LEARN-01's own
   boundary (epistemic → capability) is the same open design question `capability-
   progression.md`'s own `TRAIN_SKILL` finding already carries forward — not duplicated as a
   second decision here.
2. Whether repeated passive observation should ever refine an estimate beyond what combat
   currently provides (§13.5 of `04_strategic_cognition.md` explicitly names this as *not*
   specified, "a future ticket... would be building a mechanism this section explicitly does not
   specify") is flagged for whichever future batch first needs it — not decided here.

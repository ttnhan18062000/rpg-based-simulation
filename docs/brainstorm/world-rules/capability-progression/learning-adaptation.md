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

**Status.** Batch 07 (Capability/Progression/Conflict), drafted 2026-09-22, revised the same
day per a follow-up Rule-admission and semantic cleanup
(`tmp/world-rule-batch-7-followup-ext-ai.md`): the original LEARN-01 ("this repository's
learning is epistemic, not capability") and LEARN-02 ("only success grants XP here") were
primarily repository findings, not target world laws — LEARN-02 is retired entirely to
Repository Findings; LEARN-01 is rewritten into a genuinely normative statement that keeps the
target design open to practice → capability, failure → learning, exposure → adaptation, and
success → progression, whichever a world actually declares, rather than fixing this
repository's own current success-only pattern as a law. This family ends up with exactly one
genuine Domain Rule — "a family with 2 genuine Rules is valid" per the batch instruction's own
statement, and by the same logic, a family with one (or zero) is equally valid when that is
what survives the admission test.

---

## Domain Rules

## LEARN-01 — An experience's epistemic effect and its capability effect are distinct, independently-declared outputs

> An experience may produce an epistemic effect (a change in what a subject believes or
> knows), a capability effect (a change in what a subject can do), both, or neither — these are
> conceptually distinct outputs, and a world's own declared rules decide, per experience type,
> which output(s) result. Neither output is guaranteed by the other, and no experience-type
> (practice, failure, exposure, success) is privileged by this family in general — a world
> remains free to declare a mechanism connecting any of them to either output.

**Disposition: ACCEPT, revised 2026-09-22 per follow-up review — rewritten from a repository
description ("this repository's learning is epistemic, not capability") into the genuinely
normative claim underlying it.** Passes the admission test: no earlier Rule states that
epistemic and capability effects are separable outputs of one experience, decided per
experience-type by declared rules — Batch 06's KNOW-02 already states belief/knowledge changes
only through a declared path, and this family's own PROG-01 already states capability changes
only through a declared mechanism, but neither states that the two are *distinct possible
outputs of the same originating experience*, which a world may connect to either, both, or
neither. This is new content precisely because it resolves an ambiguity the batch instruction's
own conceptual grammar (`Experience → Accumulation → Adaptation/Learning → Capability`) leaves
open, and it deliberately keeps the target design open rather than fixing any one repository's
own current pattern (e.g. "only success grants capability") as a law — the follow-up review
explicitly required this openness.

**Repository evidence: SUPPORTED for the distinctness claim, via three independent mechanisms,
all landing on the epistemic side; MISSING for any mechanism this repository has declared that
crosses into the capability side from a non-XP experience.** `CombatLearning.learn()`
(`src/domains/combat_engagement/`, declared law per `docs/mechanics/04_strategic_cognition.md`
§13, gated `ENABLE_COMBAT_ENGAGEMENT` OFF) refines an `OpponentModel`'s *estimate* of another
entity's power — epistemic, never a combat-stat change for either participant.
`CausalAttributionService.attribute()` (Batch 05/06 Memory-domain evidence) extracts a
`CausalMemoryEntry` from a qualifying failure event — read back only as a route-scoring bias
adjustment when `ENABLE_MEMORY_UPDATE` is on, never an attribute or stat change.
`SpatialMemoryUpdateService.update_region_visit()` raises regional *familiarity* purely from
repeated presence — again epistemic. This repository's own choice, checked directly, is to
declare only success (combat/quest) as a capability-affecting experience-type, and to route
failure/repetition/exposure exclusively to the epistemic output — a specific, narrow instance
of what this Rule permits generally, not the Rule's own requirement.

**Scenarios:** [CP-S01](../scenarios/capability-progression-batch-07.md#cp-s01),
[CP-S02](../scenarios/capability-progression-batch-07.md#cp-s02),
[CP-S03](../scenarios/capability-progression-batch-07.md#cp-s03) (failure teaches),
[CP-S04](../scenarios/capability-progression-batch-07.md#cp-s04) (experience with no durable
change, counter), [CP-S17](../scenarios/capability-progression-batch-07.md#cp-s17) (non-combat
lived experience, added per 2026-09-22 follow-up).

---

## Inherited / Applied Foundational Rules

### A durable change requires a real, declared causal bridge from the originating experience

> An experience producing a durable change — capability or epistemic — must trace to a real,
> declared mechanism connecting the two; not every experience is required to produce a durable
> change at all.

**Disposition: INHERITED — direct reuse of CAUSE-01, restated at `capability-progression.md`'s
own point of use and reused here for Learning/Adaptation's own parallel claim. No new content.**

**Repository evidence: SUPPORTED**, reused directly — see `capability-progression.md`'s own
fuller evidence for this same inherited entry.

**Scenarios:** [CP-S04](../scenarios/capability-progression-batch-07.md#cp-s04).

### Capability changes only through a declared mechanism

> A subject's capability changes only through a declared, traceable mechanism — never an
> arbitrary edit.

**Disposition: INHERITED — direct reuse of this same batch's own PROG-01
(`capability-progression.md`). LEARN-01's own claim depends on this boundary existing on the
capability side; no new claim about capability itself is added here.**

**Repository evidence: SUPPORTED**, reused directly — see `capability-progression.md`'s own
fuller evidence for PROG-01.

**Scenarios:** none newly traced; reuses PROG-01's own evidence directly.

### Belief/knowledge changes only through a declared arrival/revision path

> A subject's belief or knowledge model changes only through a declared process — observation,
> report, deduction, contradiction, or decay — never automatic re-sync or hidden-truth
> injection.

**Disposition: INHERITED — direct reuse of Batch 06's KNOW-02. LEARN-01's own claim depends
on this boundary existing on the epistemic side; no new claim about belief/knowledge itself is
added here.**

**Repository evidence: SUPPORTED**, reused directly — see `knowledge-agency/
knowledge-information.md`'s own fuller evidence for KNOW-02.

**Scenarios:** none newly traced; reuses KNOW-02's own evidence directly.

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

- **Retired from Domain Rule to Repository Finding, per the 2026-09-22 follow-up review: every
  "learning-shaped" mechanism this repository currently has is epistemic, never
  capability-affecting.** `CombatLearning.learn()`, `CausalAttributionService.attribute()`, and
  `SpatialMemoryUpdateService.update_region_visit()` all confirmed to sit entirely on the
  Knowledge/Memory side of the boundary Batch 06 already drew, never the Capability side
  LEARN-01's own Rule (above) permits but does not require them to reach.
- **Retired from Domain Rule to Repository Finding, per the 2026-09-22 follow-up review: this
  repository's own answer to "which experience-types feed capability" is success-only, and
  asymmetric with what feeds epistemic state.** For *capability* (XP/Level): only a qualifying
  success event (a kill, a completed quest) grants XP — `CombatRewardClassificationService` and
  the `QUEST` conservation-path source kind are both success-gated; no failure or mere
  repetition anywhere grants XP. For *epistemic* state: failure *does* teach
  (`CausalAttributionService`, triggered by failure events, never success), and mere repeated
  exposure without either success or failure also produces an epistemic change (spatial
  familiarity). **This is a fact about this repository's own current implementation, not a
  target design requirement** — LEARN-01's own Rule explicitly keeps the target design open to
  a world declaring practice → capability, exposure → adaptation, or any other combination;
  this repository simply has not declared any of those yet.
- **Cross-referenced from `capability-progression.md`**: `TRAIN_SKILL`'s unreachable
  opportunity-generation (MISSING) is the concrete place a genuine capability-improving
  "practice" mechanism would live if built — this file does not repeat that finding's own
  evidence, only notes that it is the natural landing point for LEARN-01's own permitted (not
  required) practice → capability path.

## Cross-domain links recorded here

- LEARN-01 → Perception/Knowledge/Agency (Batch 06's KNOW-02, inherited above), Capability/
  Progression (`capability-progression.md`'s PROG-01, inherited above)

## Open questions carried forward

1. Whether a future "practice" mechanism should be built that genuinely exercises LEARN-01's
   own capability-side permission is the same open design question `capability-
   progression.md`'s own `TRAIN_SKILL` finding already carries forward — not duplicated as a
   second decision here.
2. Whether repeated passive observation should ever refine an estimate beyond what combat
   currently provides (§13.5 of `04_strategic_cognition.md` explicitly names this as *not*
   specified, "a future ticket... would be building a mechanism this section explicitly does not
   specify") is flagged for whichever future batch first needs it — not decided here.
3. Whether this repository should ever declare a non-success experience-type (failure,
   repetition, exposure) as capability-affecting is a real design question LEARN-01's own Rule
   leaves fully open — not decided here, and not foreclosed by this repository's current
   success-only pattern either.

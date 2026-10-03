# Implementation Sequence — m2-foundational-systems

Tickets must be implemented in this order. Generated automatically from intra-batch
dependency analysis. `implement-epic` reads this file to override alphabetical order.

## Order

1. TCK-20260831-CAPABILITY-DRIVEN-TARGETING  (no deps in this batch)
2. TCK-20260831-CLAN-STATE-SCHEMA  (no deps in this batch)
3. TCK-20260831-CLASS-TIER-BRANCHING  (no deps in this batch)
4. TCK-20260831-CREATURE-TERRITORY-LIFECYCLE  (no deps in this batch)
5. TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION  (no deps in this batch)
6. TCK-20260831-HABIT-BIAS-WIRING  (no deps in this batch)
7. TCK-20260831-ITEM-INSTANCE-HISTORY  (no deps in this batch)
8. TCK-20260831-METAMORPHIC-LAB-PILOT  (no deps in this batch)
9. TCK-20260831-POPULATION-COHORT-SEEDING  (no deps in this batch)
10. TCK-20260831-RACE-RELATIONS-MATRIX  (depends on: TCK-20260831-METAMORPHIC-LAB-PILOT)
11. TCK-20260831-READINESS-SPEED-FORMULA  (no deps in this batch)
12. TCK-20260831-SPECIES-INTELLIGENCE-TIER  (no deps in this batch)
13. TCK-20260831-ROLE-MODEL-IMITATION  (depends on: TCK-20260831-SPECIES-INTELLIGENCE-TIER)
14. TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION  (no deps in this batch)
15. TCK-20260831-TRUST-GATED-TEACHING  (no deps in this batch)

## Why This Order Matters

Running alphabetically would attempt tickets before their dependencies are in place.
Re-run `/implement-epic` with the same folder after any gate failure — already-done
tickets are skipped automatically.

Two real intra-batch dependencies, both discovered during investigation (not present
in the source epic's own idea list):

- **RACE-RELATIONS-MATRIX** must not even be *started* (not just not merged) until
  **METAMORPHIC-LAB-PILOT** has landed and passed — the pilot proves the metamorphic
  lab tool works against real content before idea 37's own race-relations matrix
  becomes its first real-world exercise.
- **ROLE-MODEL-IMITATION** has a real hard dependency on **SPECIES-INTELLIGENCE-TIER**
  via `intelligence_tier` — the epic's own "standalone" grouping for idea 27 was
  wrong; this was caught during investigation, not inherited from the source doc.

Two M2 ideas (35 — City ownership/sovereignty, and 48 — Place-type transitions) were
deliberately excluded from this batch entirely, per the roadmap's own Sequencing
Rules recommendation: both are gated on idea 66 (Region/Place rebuild, tracked under
M8), which has not landed. They will be ticketed once idea 66 lands.

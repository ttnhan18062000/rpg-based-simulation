---
status: authoritative
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# Scenario Bank: History / Provenance Completion Pass

**Purpose/scope.** Two new scenarios, probing the two History/Provenance rules (HP-01, HP-02)
that make a genuinely new claim rather than migrating or consolidating an existing one. HP-03
through HP-06 reuse Batch 01/02 scenarios directly (`FND-S04`, `FND-S09`, `FND-S20`, `FND-S21`,
`TAR-S13`) rather than requiring fresh traces — migrating a rule's canonical home does not
invalidate evidence already gathered for it, and re-tracing it here would duplicate work rather
than add anything.

---

## HP-S01 — A lineage's history survives three transformations

An entity is reborn through succession, changes `kind` via evolution, and is later referenced in
a descendant's inherited feud after death. At every step, the causal history connecting these
events remains attached to the correct subject or its declared successor.

- **Rules invoked:** HP-01 (historical continuity survives ordinary change).
- **Result: covered.** Reuses `EvolutionSystem.evaluate()` (kind change, same id),
  `ClanLifecycleService.process_succession()` (role/authority to a new occupant, tracked
  separately from identity per AUTH-06), and `_transfer_inherited_feud()` (history surviving
  death) — three different kinds of change, none of which severs the underlying causal record.

## HP-S02 — A false rumour with real provenance

A witness reports a false claim about a rival's whereabouts. The rumour has entirely real
provenance (a real source entity, a real tick, a real report event) — the record of *who said
this and when* is fully traceable — while the claim itself never becomes true.

- **Rules invoked:** HP-02 (provenance requires a real causal ancestor, distinct from truth).
- **Result: covered.** `process_rumor()`'s `BeliefEntry`/`LeadState` carry `source_entity_id`
  and `certainty=0.3` as two separate fields — the causal ancestor (who produced this record) is
  never in doubt even when the content is. This is the cleanest possible confirmation that
  provenance-tracking and truth-tracking are architecturally distinct questions.

---

## Cross-batch note

Both scenarios here are deliberately narrow — this completion pass drafts six rules, but only
two (HP-01, HP-02) needed new evidence gathering; the other four (HP-03–06) are direct
migrations or consolidations of already-traced Batch 01/02 findings. Re-tracing all six would
have produced no new information, only restated conclusions this catalog already reached once.

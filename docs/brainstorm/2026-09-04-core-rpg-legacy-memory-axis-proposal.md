---
status: active
layer: mechanics
authority: P1
audience: agent
tags: [content, architecture]
---

# Core RPG Legacy/Memory Axis Proposal

Date: 2026-09-04

Status: brainstorming proposal for review

Scope: the expected simulation after the proposed core-RPG roadmap and accepted design portfolio are
available, focused specifically on how information, reputation, and emotion outlive the individual event
or entity that produced them — as distinct from the Knowledge/Belief axis (what one living entity
currently knows or believes) and the Social/Relationship axis (present-tense relationships between two
living entities)

Constraint: this document does not approve implementation, change an existing plan, create tickets, or
define a player-control system

## Purpose

A fifth cross-cutting dimension, the same shape as space, time, social/relationship, and knowledge/belief
above. M5 ("Memory, Reputation & Legacy," `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md`)
depends on it the same direct way M3 depends on the Temporal axis and M5/M6's own reputation branches
depend on the Social axis — yet it never received the brainstorm-proposal-plus-roadmap-section treatment
the other four got. This gap was found while checking whether M5 is safe to start implementing: two of
M5's three branches are self-contained, but its third branch (ideas 57, 62, 63 — "history and belief")
sits directly on top of an undecided architectural question this document exists to name.

Unlike the Social axis (undocumented, live) or the Knowledge axis (documented, structurally split), this
axis's starting condition is a third shape: **the mechanism it needs (Chronicle) is real, live, and
stateless by design, but the specific "does the past change as it recedes" behavior every M5 idea in this
branch assumes does not exist yet, has no consumer today, and — critically — is not a gap in one
component, it's an absent capability across three.**

## Existing foundations (confirmed via direct code read, not assumed)

- **Chronicle is a stateless compiler/renderer, not a memory store.** `src/domains/chronicle/
  significance.py`'s own docstring: "Pure stateless classifier. No durable state. No engine imports."
  `EventSignificanceScorer.score()`/`.is_chronicle_worthy()` classify `NarrativeLedgerEntry` objects for
  inclusion; `ChronicleCompiler.compile()` renders markdown/JSON from them. Chronicle has no field that
  ages, decays, or distorts a past event — it renders whatever the ledger already recorded, verbatim,
  every time.
- **`CultureDeriver` is the one real precedent for "the past shaping the present," at region scale.**
  `src/domains/culture/deriver.py`: `CultureDeriver.derive(hierarchy: ChronicleHierarchy, entity_names)
  -> Dict[str, CultureState]`, stateless, aggregating all chronicle-worthy events per region into a
  `CultureState`. This is real, live, and tested (confirmed in the 2026-09-02 hardening pass, `docs/
  plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md`) — not the "dormant substrate" earlier
  drafts of M4/M5/M6 assumed. M5's idea 57 ("Living Legend Feedback Loop") is explicitly scoped to "copy
  `CultureDeriver`'s aggregation shape rather than invent new event-scoring logic."
- **Cross-episode memory exists, but only at Campaign granularity, exporter/importer-shaped, not a
  continuous in-world process.** `src/domains/campaigns/social_memory.py`: `SocialMemoryExporter`/
  `SocialMemoryImporter`, "Populated by: E43B SocialMemoryExporter (end-of-episode hook). Consumed by:
  E43B SocialMemoryImporter (start-of-episode hook). Stored in: `CampaignState.social_memories`." This is
  the same mechanism the Social axis proposal already found produces zero passive decay in live gameplay
  (`SocialMemoryDecay.apply_decay()` "operates on a separate Campaign-only structure and never touches
  live gameplay state," `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`'s Social/Relationship axis
  section). A snapshot taken and restored between episodes is not the same capability as a testimony that
  degrades, gets retold, or gets contradicted while the world keeps running.
- **No "testimony" concept exists anywhere in `src/` today** — confirmed via repo-wide grep. The temporal-
  axis proposal's own §7.9 ("Bounded temporal provenance") and its Household/Chronicle references describe
  an intended future capability, not a present one.
- **`CampaignScorecardEvaluator` cannot observe this axis failing.** Already flagged in M9's own findings
  (`docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`, M9 section): "4 ideas (53, 55, 58, 62) can only
  be tested by a real multi-episode Campaign run, and `CampaignScorecardEvaluator` itself has zero fields
  today that would even catch a failure in any of them" — a distinct test-infrastructure gap layered on
  top of the missing mechanism gap this proposal names.

## The real gap this axis names

Three M5 ideas (57, 62, 63 — the "history and belief" branch, sequenced 62 → 57 → 63 per the epic plan)
all assume some version of "the past is retrievable, but not perfectly, and not identically to everyone"
— and none of the three real building blocks above (Chronicle, `CultureDeriver`, campaign social memory)
provide that. Concretely:

- **Idea 62 ("Generations Misremember")** needs a transform between "what actually happened" (the
  ledger's own recorded events, ground truth) and "what a given entity/generation currently believes
  happened" — which is a *belief*, squarely the Knowledge/Belief axis's own territory
  (`BeliefEntry`/`KnowledgeFact`), not a new parallel structure. The M5 epic plan already independently
  spotted this ordering ("idea 62 before idea 57, then idea 63"), but did not connect it to the
  Knowledge axis's own still-unresolved `BeliefEntry`/`KnowledgeFact` reconciliation question
  (`TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION`, filed 2026-09-04, not yet decided).
  Building idea 62 before that reconciliation lands risks creating a *third* independent belief
  representation, the same failure mode the Knowledge axis proposal already found once (`BeliefEntry` vs.
  `KnowledgeFact`, zero cross-references).
- **Idea 57 ("Living Legend Feedback Loop")** needs Chronicle output to accumulate into something an
  entity can act on later — but Chronicle itself has no accumulation state (it's a stateless renderer).
  `CultureDeriver` is the real precedent, but it operates at region scale over the full chronicle-worthy
  event set; idea 57 needs an entity-scale or reputation-scale equivalent, which does not yet exist and
  is not simply "call `CultureDeriver` again with different grouping" without design work.
- **Idea 63 ("Belief Grows Around Real History")** is explicitly confirmed in the epic plan as "a genuine
  downstream composite, needing both idea 36 (Clan, as container) and idea 57 (fame substrate) first" —
  it inherits both of the above gaps and adds nothing new architecturally, but is the idea most exposed
  if either upstream piece has to be reworked.

By contrast, M5's other two branches do not touch this gap:
- **Death-and-lineage (55+58)** is a single on-death dispatch hook writing a one-time transfer — no
  accumulation, no decay, no cross-generational retelling.
- **Reputation (60 → 53/54)** is a one-time birth-seed write onto an existing, already-covered
  (`SOC-263`) field — also no new accumulation/decay mechanism.

## Accepted in this brainstorm pass

- Legacy/memory is an overlapping axis, not a containment layer, the same shape as the other four: an
  event's significance, a reputation's currency, and a belief's accuracy all decay/transform on
  independent clocks, not one shared "memory age" scalar.
- Chronicle remains downstream of this axis (confirmed, not merely assumed): it renders recorded events,
  it does not decide what a future generation currently believes about them. This mirrors the Knowledge
  axis proposal's own finding that Chronicle sits downstream of *that* axis too — Chronicle is a shared
  rendering endpoint for multiple axes, not owned by any one of them.
- `CultureDeriver`'s stateless, hierarchy-driven aggregation is the correct shape to extend from, not a
  new event-scoring engine — already an explicit scope note in M5's own epic plan for idea 57.
- Idea 62 is a Knowledge/Belief-axis consumer, not a new parallel memory representation. Any
  implementation of idea 62 should be gated on the `BeliefEntry`/`KnowledgeFact` reconciliation decision,
  not proceed independently of it. **Gate cleared, 2026-09-04:**
  `tickets/done/TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION.md` confirmed the split is
  deliberate (structured query responses → `KnowledgeFact`; raw witnessed events → `BeliefEntry`,
  contradiction-tracked) — the reconciliation decision this gate names is made. Idea 62 is unblocked to
  proceed as a `BeliefEntry` consumer specifically (it models degrading *witnessed* memory, not queried
  facts), not gated on any further Knowledge/Belief-axis work.
- Cross-episode Campaign social memory (`social_memory.py`) and this axis's in-world "testimony decay"
  question are related but distinct: the former is a snapshot/restore mechanism between episodes, the
  latter (if built) would be a continuous within-episode process. Confusing the two risks building a
  Campaign-only feature that idea 55/58/60/53/54 — all single-episode-relevant — cannot use.

## Genuinely new capabilities (not restatements of existing plans)

1. **A testimony/retelling model** — how a recorded event's *represented* content diverges from its
   *ground-truth* content as it propagates through retellings, distinct from both Chronicle (which never
   diverges) and `BeliefEntry`/`KnowledgeFact` (which model one entity's current belief, not a chain of
   transmission). **Delivered, 2026-09-05:** see
   `docs/brainstorm/2026-09-05-testimony-retelling-model-design.md` — confirms the gap is real (no
   existing mechanism bridges Chronicle's output to belief formation about historical events),
   proposes a `TestimonyDeriver` sibling to `CultureDeriver`/`FameDeriver`, and discloses two open
   questions: whether content-string distortion is actually load-bearing for idea 63 (vs.
   confidence-only decay, which `BeliefEntry.certainty` already supports), and an unresolved
   tick-vs-episode unit mismatch between `BeliefCycleSystem`'s decay and Chronicle's episode-scoped
   events.
2. **An entity/reputation-scale aggregation shape**, sibling to `CultureDeriver`'s region-scale one, for
   idea 57's "does this entity's past deeds currently make them a Living Legend" question.
   **Delivered, 2026-09-04:** see
   `docs/brainstorm/2026-09-04-idea57-entity-scale-fame-aggregation-design.md` — the shape mirrors
   `CultureDeriver` exactly (keyed by `NarrativeLedgerEntry.subject_id` instead of `region_id`, no
   new schema field needed); the real open question found is which event types actually feed it,
   since the Narrative Ledger's 4-type vocabulary has no `combat_victory` signal today and idea 57's
   own atlas text conflates Chronicle's output with the separate, already-live `heroism_score` field.
3. **A decay/significance-erosion rule for Chronicle-worthy events**, since `EventSignificanceScorer`
   today has no time dimension at all — a century-old rescue and a same-tick rescue score identically.

## Priority table

| Proposal | Status relative to current roadmap | Priority | First responsibility |
|---|---|---:|---|
| Confirm Chronicle/`CultureDeriver` stay downstream, not rearchitected | Verification, not new work | P0 | Design-authority confirmation before M5's history/belief branch starts |
| Gate idea 62 on the Knowledge/Belief reconciliation decision | **Cleared, 2026-09-04** — see above | P0 | Whoever scopes idea 62's ticket |
| Entity/reputation-scale aggregation shape (idea 57's real dependency) | **Delivered, 2026-09-04** — see above | P1 | M5, once idea 62's gate clears |
| Testimony/retelling model | **Delivered, 2026-09-05** — see above | P2 | Design review — dedicated proposal delivered; 2 open questions remain (content distortion vs. confidence-only, tick/episode unit mismatch) |
| Chronicle significance decay | New, small | P2 | `EventSignificanceScorer`, once a real consumer needs it (not speculative) |
| Campaign-only social-memory / in-world testimony distinction, documented explicitly | Documentation-only | P1 | Whoever next touches `social_memory.py` or scopes idea 55/58 |

## Suggested integration with the existing roadmap

This should not become a tenth axis-of-axes review pass. Its responsibility is narrow and immediate:

1. **Cleared, 2026-09-04:** the Knowledge/Belief axis's `BeliefEntry`/`KnowledgeFact` reconciliation
   decision this branch was gated on is resolved (deliberate split, both kept — see the Accepted section
   above). M5's history-and-belief branch (62 → 57 → 63) is now unblocked to start on this specific
   gate; idea 62 proceeds as a `BeliefEntry` consumer.
2. M5's death-and-lineage and reputation branches are unaffected by this proposal and do not need to wait
   for it (confirmed via the gap analysis above — neither touches accumulation/decay/retelling).
3. If idea 57's entity-scale aggregation shape is accepted, document it as a named sibling capability to
   `CultureDeriver`, not a new pattern invented from scratch — same precedent-reuse discipline the
   temporal axis proposal applied to the duration/rate formula (reusing `move_cost`/`readiness_speed`
   rather than inventing a new shape).
4. The testimony/retelling model (item 1 in the new-capabilities list) is explicitly **not** required for
   M5's committed 8 ideas to land — none of them currently claim it. Flag it as a future idea-portfolio
   candidate, the same disposition the temporal proposal gave several of its own P3/deferred extensions
   (generational cohorts, anniversaries), not a blocker.

## Risks and safeguards

| Risk | Safeguard |
|---|---|
| Idea 62 builds a third independent belief representation | Explicit gate on the Knowledge/Belief reconciliation decision before idea 62 is ticketed |
| Idea 57 invents new event-scoring logic instead of reusing `CultureDeriver`'s shape | Already an explicit scope note in the M5 epic plan; this proposal reinforces it with the region-vs-entity-scale distinction |
| Campaign-only social memory gets conflated with in-world testimony decay | Name them as explicitly distinct in any ticket that touches either |
| This proposal scope-creeps into designing the full testimony/retelling model now | Priority table marks it P2/deferred; M5's 8 committed ideas do not require it |
| M5's death-and-lineage/reputation branches get blocked unnecessarily by this proposal | Explicitly confirmed unaffected above — safe to start those two branches now |

## References

- `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md`
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` (Temporal axis, Social/Relationship axis,
  Knowledge/Belief axis sections; M9 section's `CampaignScorecardEvaluator` finding)
- `docs/brainstorm/2026-09-02-core-rpg-knowledge-belief-axis-proposal.md`
  (`BeliefEntry`/`KnowledgeFact`, the reconciliation this proposal's idea-62 gate depends on)
- `docs/brainstorm/codex/2026-08-28-core-rpg-temporal-axis-proposal.md` (§7.9 bounded temporal
  provenance, §6.5 memory/identity/legacy — the temporal proposal's own forward pointer to this gap)
- `docs/plans/rpg_design_roadmap/rpg_culture_drift_hardening_plan.md` (`CultureDeriver`/
  `CulturalBiasApplicator` confirmed real, live, tested)
- `TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION` (the gating decision for idea 62)

No current brainstorm, plan, ticket, code, or agent record is modified by this document.

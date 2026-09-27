---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated review/instruction record for the systemic-world roadmap, copied from the local working file `rpg-core-next-investigation-review.md` on 2026-09-27. An input to the planning work, not current status.

# Review: `rpg-core-next-investigation-ext-ai.md` + Roadmap Integration Options

**Purpose of this file.** Review of the investigation brief at `tmp/rpg-core-next-investigation-ext-ai.md`
(entity decision-making, personality/characteristic/archetype semantics, and life-trajectory
divergence), plus the information needed to decide how — or whether — to integrate its eventual
findings into `docs/world_rules/roadmap.md`. This is a decision-support document, not a decision.
Scratch/local (`tmp/`), not part of the Catalog.

---

## 1. What the brief is

A large (23-section) investigation-only brief asking: what currently causes two otherwise-similar
entities to make different choices, develop differently, and become meaningfully different people
over a lifetime? It investigates personality/characteristics/archetypes as *starting examples*, not
the whole question, and explicitly defers any Rule change ("Do not make implementation changes or
modify World Rules unless separately instructed").

It is the natural next step after the Catalog's own Final Integration Batch, which already found and
named the gap this brief now investigates in depth: `review-exports/final-integration-history-
significance-review.md:414` — "the single most consistently recurring late-stage gap this entire
Catalog has found... a recurring, shared *late-stage* gap at six of seven subject scales" in the
lived-history → recognition → reaction chain, with the composing Rules already named (HP-01/02/05,
PROG-06, INFO-01/02, KNOW-01/02, BEL-01, PLACE-02/ORG-01).

## 2. Review verdict: strong, with two concrete fixes needed before dispatch

**Strengths:**
- Correctly avoids inventing a monolithic "Character Development" domain (§15) — matches the
  Catalog's own already-established position (Final Integration Batch explicitly tested and
  rejected a standalone `UniversalSignificanceSystem` on the same grounds).
- The causal/derived/social-label/narrative classification (§2, A–D) sharpens the Catalog's
  existing actor-truth-vs-observer-interpretation distinction, applied specifically where
  personality/archetype language is most likely to get muddled.
- Correctly warns that Mechanism Registry absence ≠ repository absence (Registry `implemented_by`
  coverage is organic, 76/93 populated, never backfilled in one pass — `rollout_plan.md:104-105`).
- Investigation-only, Rule-changes deferred — matches the batch workflow's existing separation of
  scenario/investigation from rule-drafting.

**Gap 1 — missing the exact prior-art citation.** The brief never cites the Final Integration
Batch's own already-documented finding above. Without it, a fresh investigator (this brief will
likely be run by an agent with no session memory) re-derives already-settled ground instead of
starting from "here is the known gap, dig into whether personality/disposition is the missing
front-end cause."

**Gap 2 — missing a second, closer piece of prior art.** `tickets/done/TCK-20260809-COMBAT-
OUTCOME-FLEE-VS-FIGHT-PERSONALITY.md` already confirmed real, live personality data
(`data/content/entities/entity_archetypes.yaml`'s `bravery` field) causally dampening a real
decision (flee-vs-fight, via `EngagementRiskEvaluator`) — the same mechanism `conflict-combat.md`'s
own Repository Findings already cite. §3's "is personality directly consumed, or stored but inert?"
question already has a partial, verified answer sitting in a closed ticket.

**Polish note — vocabulary risk.** §16's five-way classification ("Already covered adequately" /
"Covered but realization incomplete" / "Semantically ambiguous" / "Genuine World Rule gap" /
"Derived/narrative concern only") answers a genuinely different question than the Catalog's
`SUPPORTED`/`PARTIAL`/`CONFLICTING`/`MISSING`/`INERT-OFF`/`UNKNOWN` vocabulary (does a Rule exist at
all, vs. is an existing Rule realized) — but the near-overlapping words risk exactly the kind of
quiet vocabulary-conflation `docs/plans/status_axis_model.md` was just written to prevent for a
different pair of axes. One clarifying sentence disambiguating the two would head this off.

**Scope-size flag.** Comparable in breadth to the entire Final Integration Batch (18 scenarios, 7
subject scales). Worth explicitly permitting a split up front (Personality/Decision-pipeline as one
pass, Life-trajectory/Opportunity-generation as a second) — the same way Batch 11 split into 11A/11B
mid-batch when it got too broad — rather than forcing one report to cover both at full depth and
risking a diffuse, harder-to-act-on result.

No duplicate-work risk found: no existing ticket or `docs/plans/` track covers entity-development or
life-trajectory as a named initiative.

## 3. Live coordination risk — read before scheduling this

**M4 of the Semantic Control Plane is in flight right now** (`TCK-20260924-M4-COMBAT-SLICE-CROSS-
DOMAIN-VIEW`, dispatched by `rpg-feature-planning`), and it is actively building Rule↔Mechanism
mapping edges against exactly the files this new investigation would also touch:
`capability-progression/conflict-combat.md` and its siblings (Batch 07's own family). If this
investigation's Personality/Characteristics/Archetypes sections (§3–5) produce new or refined Rules
in that same family while M4 is mid-mapping, the two tracks can race: M4 could map against a Rule ID
that's about to change, or this investigation could propose a Rule ID M4 has already cited in a
mapping edge.

This is the Hard Rules' own "detect and stop on duplicate work... architectural mismatch" case,
concretely instantiated. Two ways to avoid it, not mutually exclusive:
- **Sequence:** hold this investigation's *Rule-writing* step (not the investigation itself) until
  M4 merges — the investigation/report can run now, since it makes no Rule changes either way.
- **Scope guard:** if dispatched now, explicitly instruct the investigator to report
  Capability/Progression/Conflict-family findings as flagged-for-later rather than drafting Rule
  text against those specific files while M4 is live.

## 4. Roadmap integration — three options, no recommendation forced

The Catalog (`docs/world_rules/roadmap.md`) is marked frozen — all 12 batches + Final Integration,
PASS. This investigation's eventual findings need a home. Three shapes, ordered by how much they
reopen the frozen artifact:

### Option A — New numbered batch (e.g. "Batch 13") appended post-freeze
Treat this as a real Catalog batch: scenarios, Domain Rules, review export, freeze — full rigor,
same process as Batches 01–12. Roadmap's own governance already permits this explicitly: "If
scenario evidence reveals a missing foundational family: add it explicitly, but require a semantic
reason rather than taxonomy completeness."
- **Pro:** Single source of truth stays single. New Rules get real IDs, scenarios, review exports —
  the Catalog's own established rigor, no parallel process invented.
- **Con:** Reopens a document currently described as fully frozen. `roadmap.md`'s own "ready to
  freeze" framing and the Final Integration Batch's "Zero new Rules were required" claim would both
  need a footnote acknowledging a later, deliberate reopening — not a correction, but worth being
  explicit about so a future reader doesn't read "frozen" as "closed forever."

### Option B — Separate standalone track, only surgical patches back to the Catalog
Investigation report lives in its own `docs/plans/` directory, never becomes a numbered batch. If it
finds a genuine Rule gap, that gap gets a small, targeted ticket (same shape as the
TERR-04/jurisdiction resolution — an Inherited entry or a narrow Rule addition, not a full batch).
- **Pro:** Keeps "frozen" meaning something durable. Matches the surgical-fix pattern already used
  successfully twice this week (TERR-04, combat_engagement staleness).
- **Con:** If the investigation finds something as large as a genuinely new causal-composition
  requirement (not just a missing citation), forcing it through a "small patch" framing undersells
  it, and duplicates the batch process's own scenario/review-export infrastructure under a different
  name if the finding turns out to need that much rigor anyway.

### Option C — Investigation first, integration path decided per-finding after
Run the investigation now as a standalone report (promoted from `tmp/` to `docs/plans/` once
written, not directly into the Catalog). Its own §16 classification (already-covered /
covered-but-incomplete / ambiguous / genuine-gap / narrative-only) then routes each individual
finding: a genuine-gap finding with real weight → Option A's batch process; a covered-but-incomplete
finding (repository realization only) → the Semantic Control Plane's existing M3 triage stream, not
a new mechanism; a narrative-only finding → no Catalog action at all.
- **Pro:** Doesn't presuppose the answer before the evidence exists — the same discipline already
  applied to TERR-04 and the CONFLICTING-vs-PARTIAL question (cite precedent, don't guess). Reuses
  M3 for realization-only findings instead of building a second triage mechanism.
- **Con:** No standing process today explicitly names "post-freeze investigation intake" as a step —
  this would need a short governance addition to `roadmap.md`, mirroring the Semantic Control Plane
  roadmap's own explicit framing of M3 as "a permanent, ongoing stream."

**My lean, offered for information only, not as the decision:** Option C — it's the same
evidence-before-commitment discipline already used successfully on the last two peer-routed
decisions, and it avoids committing to "this is definitely a new batch" before the investigation has
actually run. But the choice among these three is yours to make, per the standing routing agreement
for calls like this.

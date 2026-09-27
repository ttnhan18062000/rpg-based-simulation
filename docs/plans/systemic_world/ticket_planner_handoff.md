---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
last_verified: "2026-09-27"
---

# Systemic World First Wave — Ticket-Planner Handoff — PROPOSED / FOR REVIEW

**Status: `PROPOSED / FOR REVIEW`.** It becomes usable once the owner accepts
`first_wave_plan.md`. Frontmatter `status: active` means "live working document", not approval;
see the plan's header note.

**Audience.** The ticket planner who decomposes approved epics into tickets for the implementation
agents.

**Scope of each card.** One card per first-wave epic. Each card gives the context needed to write
tickets without re-deriving the architecture. Outcomes, contracts, boundaries and completion
evidence live in `first_wave_plan.md` §2 and are not repeated here.

**What this handoff does not contain**: classes to edit, data schemas, test filenames, or a chosen
fix. Ticket granularity, technical investigation, acceptance tests and assignment are yours.

---

## Card A — Authoritative life, death and cross-tick world continuity

**Where the epic is defined**: plan §2, Epic A.

**Invariant**: a death reached through ordinary world processes is recorded under one declared
authority, with a cause and a time, and its lineage consequences follow.

**Domain owners and interfaces**:
- engine-core authoritative apply, and lifecycle/lineage;
- interfaces with every other death cause (combat, hazard, passive decay);
- interfaces with anything that reads an entity's active/alive state.

**Verified evidence (sources)**:
- Natural-aging defect, runtime reproduction, 2026-09-27.
  - Setup: seed 42, `PROD_SMALL`, two entities; the subject ages from 0 to max age 3 carrying one
    item, and its heir is designated.
  - Result: after 6 ordinary kernel ticks the subject is inactive from tick 3 onward, with no death
    reason and no succession. It never recovers.
  - Diagnosis: roadmap §7.1.
- Single hop works when the starting state is staged:
  - `tests/simulation_quality/test_heir_inventory_transfer_corpus.py`;
  - `tests/integration/campaigns/test_lineage_dispatch_deterministic_kernel_tick.py`.

  Both passed on 2026-09-27. Both stage age past the maximum, which is why they miss the defect.
- The engine refuses mid-run state staging (`ReadOnlyError`), so composition evidence must come
  from ordinary ticks.

**Known gaps, by evidence level**:
- Natural-aging silent death: runtime-confirmed.
- Two-hop composition: `BLOCKED` by the above.
- Starvation/sleep-debt death may be equally silent: `UNKNOWN`, from code inspection only.
- Spawns created inactive may currently rely on the same code path to become active: `UNKNOWN`,
  from code inspection only.

**Questions for the ticket planner / implementers**:
1. Which path is the declared authority for old-age deactivation, and what is the resolution rule
   when two paths disagree?
2. Does the correction shift the tick on which death is recorded? If so, is that acceptable, and how
   is it pinned?
3. Is the inactive-spawn behaviour intended? If answering requires deciding what such an entity
   means in the world, return it to the roadmap instead of choosing a default.
4. Is the starvation path really silent at runtime? If so, fix it within Epic A or split it out.
5. What is the minimum run length that makes the two-hop claim causally sufficient?

**Contract-level risks**: any change to how active/alive state is decided can alter:
- combat and hazard death;
- dirty-set/passive-decay consumers;
- group/clan lifecycle phases, which read same-tick deaths;
- economy vacancy signals, which react to deaths.

Existing tests for these must pass unmodified, or any change must be justified explicitly.

**Registry/SCP follow-through**:
- add dated evidence notes to the `aging_death` and `succession` registry entries;
- update the matching parity-ledger entry;
- no SCP mapping exists for these mechanisms, so none is required.

**Background, non-binding**:
- The M1 ticket draft is summarized in the Appendix. It is unreviewed, and its framing of the fix is
  not a roadmap decision.
- Local branch `natural-aging-old-age-dispatch-fix-unreviewed` (not pushed) holds a prototype
  change and a natural-aging scenario that failed 3/3 against current code. It was never run
  against the suite and does not address the inactive-spawn question. Inspect or discard it; it is
  not an approved fix.

---

## Card B — Situated evidence and observer contract (design)

**Where the epic is defined**: plan §2, Epic B.

**Invariant**: players and in-world observers learn only through viewpoint-scoped evidence, and no
surface leaks hidden world truth.

**Domain owners and interfaces**:
- perception/observation;
- the probe event's own domain, which is lifecycle/lineage by default;
- interfaces with cognition (beliefs, knowledge), social memory (witness vs hearsay), and any future
  presentation layer — at contract level only.

**Verified evidence (sources)**, all read-only inspection on 2026-09-27 (roadmap §7.2):
- The perceived-entity record carries only id, kind, position, salience and confidence
  (`src/core/cognition.py:28-33`).
- The perception update phase has no production caller, confirmed by repo grep.
- The knowledge model assimilates only paid information facts (resources, recipes, danger, leads).
- The inheritance transfer carries no origin marker
  (`src/systems/lifecycle_systems/lifecycle.py:252-257`).
- The only in-world effect of the death is the grief trigger for trusted allies
  (`src/observability/event_extractor.py:1722-1762`). It is location-independent and carries the
  death, not the inheritance.

**Known gaps, by evidence level**:
- Encounter: `BLOCKED` (no carrier).
- Provenance: `ABSENT`.
- Inference: `BLOCKED`.
- Non-leakage: vacuous today; untestable until a carrier exists.
- Grief-trigger epistemic fit: `UNKNOWN`, owned by the §3.4 track.

**Questions for the ticket planner / designers**:
1. Which probe event? The default is inheritance, pending owner memo decision 2.
2. What is the minimum domain-owned route from that event to a viewpoint-scoped clue? Inspection
   surfaced two non-binding directions: a perception-side signal (which would require the perception
   phase to run in production), and a witness-scoped event.
3. Is the resulting clue ambiguous or event-specific, and is that sufficient for the claim it
   supports?
4. What must never leak? At minimum the private cognition/strategic fields named in roadmap §7.2.
5. How does the observer contract stay reusable for witness/hearsay work later, without assuming
   one storage shape for all three cases?

**Contract-level risks**:
- Wiring perception into production may affect every consumer of perceived state, and performance.
- Any event route must not become a global feed or an omniscient read.

**Registry/SCP follow-through**:
- If the chosen route creates or activates a mechanism, register it through the normal process with
  its verified tier.
- Record the player-side status (`BLOCKED` → `PENDING`) in roadmap §7.3; never record it as a
  mechanism verdict.

---

## Card C — Authority-boundary verification program

**Where the epic is defined**: plan §2, Epic C. Three independent items, each with its own owner and
its own completion state.

**Invariant**: a durable fact with more than one producer resolves under a declared rule.

**Verified evidence (sources)**: roadmap §3.1's audit table.
- Precedence comments at `src/systems/world_systems/groups.py:99` and
  `src/engine/pipeline_phases/clan_lifecycle.py:19`.
- Same-phase concatenation before one merge at `src/engine/pipeline.py:255-283`.
- Two reputation producers:
  - `src/domains/campaigns/social_memory.py:528`;
  - `src/domains/campaigns/orchestrator.py:928`.

**Known gaps**: all three boundaries are `UNKNOWN_WITH_REASON`. There is a plausible rule or
ordering in each case, but no scenario exercises the collision.

**Questions for the ticket planner / implementers**:
1. For each boundary, is a same-tick collision reachable in production, or only in a harness?
2. What does the merge do, and is that a declared rule or incidental ordering?
3. When a scenario genuinely cannot be staged, the outcome is `BLOCKED_WITH_REASON`, never "fine".

**Contract-level risks**: none from the checks themselves. Any defect found is routed as separate
work, not fixed inside the check.

**Registry/SCP follow-through**: record each outcome as a dated addendum in roadmap §3.1. Region
ownership (FAC-010) stays on its own track.

**Background, non-binding**: incomplete scenario drafts from stopped exploratory agents sit on the
same local prototype branch. They are not evidence.

---

## Appendix — M1 ticket draft (background only, unreviewed, not binding)

An earlier session drafted an implementation ticket for Epic A's first workstream
(`TCK-20260927-NATURAL-AGING-OLD-AGE-DISPATCH-RACE`). It was withdrawn from `tickets/todos/` because
ticket creation belongs to the ticket planner; it remains in this branch's git history. In summary:
- **Title**: "An entity that dies of natural aging is deactivated with no recorded cause and no
  succession."
- **Tier**: proposed standard, P1.
- **Acceptance criteria**:
  1. Natural aging to max age yields an OLD_AGE record and heir effects.
  2. No silent inactive tick.
  3. Death timing pinned and documented.
  4. Existing death, inheritance and passive-decay tests pass unmodified.
  5. Verified and unverified death paths named.
  6. Registry and parity evidence updated.
- **Open questions**: the inactive-spawn behaviour, and the starvation sibling gap.

Use it or discard it; it carries no roadmap authority.

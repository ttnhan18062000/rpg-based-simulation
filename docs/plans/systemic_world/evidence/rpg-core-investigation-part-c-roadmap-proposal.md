---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated evidence snapshot supporting `docs/plans/systemic_world/roadmap.md`, copied from the local working file `rpg-core-investigation-part-c-roadmap-proposal.md` on 2026-09-27. Where the roadmap has since corrected a claim, the roadmap is authoritative.

# Part C — Roadmap Proposal: Closing the Entity-World Recognition Loop

**Source instruction:** `tmp/rpg-core-next-investigation-2-ext-ai.md`, Part C.
**Inputs:** Part A (`tmp/rpg-core-investigation-part-a-action-affordance.md`), Part B
(`tmp/rpg-core-investigation-part-b-recognition-standing-test.md`), Pass 1, Pass 2, and the
Recognition/Standing synthesis (all in `tmp/`), as corrected by Part B.
**Status of everything below:** `PROPOSED`, not `DECIDED`. No canonical Rule text or roadmap file
has been modified. This is a standalone document, not an edit to any existing roadmap.

---

## 0. Roadmap authority — genuinely ambiguous, reported rather than resolved

Candidates checked:

| Candidate | Status | Why it's not the right home |
|---|---|---|
| `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` (M1-M9) | **Fully closed** — M1-M6, M8, M9 confirmed `DONE`; M7 is an audit-only follow-up, not a feature milestone; M10 is a narrow 2-idea backlog (ideas 50, 64 specifically), not a general landing zone. | No natural slot for a new capability area this size. |
| `docs/plans/long_term_development_roadmap.md` | Active, but a different axis entirely — engine-infrastructure phases (CI, determinism, corpus tooling), dated 2026-06-19, pre-dates the World Rule Catalog. | Wrong shape — phase-numbered engine health, not RPG-feature capability sequencing. |
| `docs/world_rules/roadmap.md` | Frozen — Catalog-authoring sequencing only. | Explicitly not an implementation roadmap (roadmap's own governance section). |
| `docs/plans/simulation_semantic_control_plane/roadmap.md` (M0-M4) | Active, in flight. | Scoped to Rule↔Mechanism *mapping*, not new capability implementation — explicitly out of scope per that roadmap's own Stage boundaries. |
| `docs/plans/render_and_art_program_roadmap.md` / `hud_delivery_roadmap.md` / `live_map_scaling_roadmap.md` | Active, unrelated axis. | The source instruction explicitly warned not to confuse this proposal with these. |

**Conclusion:** this proposal is deliberately standalone. Whoever accepts it should decide its
permanent home (see Decision Request #2 below) — likely either a new file alongside the others in
`docs/plans/`, or eventual promotion into `rpg_design_roadmap.md` as an M11, given M1-M9's own
established pattern of one roadmap doc + milestone epics.

---

## 1. Consolidated findings (full detail in Part A/Part B's own reports — this is the roadmap-relevant summary)

**The loop, evidence-graded, end to end:**

| Capability | Status | First failed/unproven edge |
|---|---|---|
| 1. Opportunity discovery | `PROVEN CURRENT`, real, live — but `CONFLICTING`: `AGENCY-03`'s own Repository Finding confirms opportunity generation reads raw/omniscient world state, not perception-gated | Not absent — a wiring defect against an already-correct Rule |
| 2. Decision → valid attempt → world change | `PROVEN CURRENT` strongly for Combat (rigorously validated, recently hardened, 6.3%→93.7% coverage fix) and Harvest (live via generic `INTERACT`); cleanest single-writer pattern of the whole investigation is Quest reward's Objective Reward stage | Shared, unproven upstream edge across **all three families**: how a selected `ActionIntent` becomes an `ActionRouter` payload — `UNKNOWN`, not traced by either pass. Also `UNKNOWN`: whether `ResourceTransferIntent(source_kind="NODE")` resolves cleanly, given the sibling `"CHEST"` source_kind is confirmed broken in the same resolver. |
| 3. Consequences persist as history/evidence | `PROVEN CURRENT` for participant-scoped history (`TurningPointState`; `SocialComponent`'s `bonds`/`trust_history` — real, directed, deliberately separated from global reputation per `SOC-193`) | Recordable evidence for a **non-participant third party** — confirmed absent |
| 4. Information reaches specific observers, no omniscient injection | `PROVEN CURRENT`, narrow — direct-interaction propagation into `SocialComponent` genuinely works and is already correctly consumed | **The confirmed single narrowest bottleneck in the entire investigation**: propagation from a witnessed-but-uninvolved observer's perspective has no producer at all. `BeliefCycleSystem.process_rumor()` is already generic enough to carry this — its only production caller just never feeds it an entity subject (only ever a region) |
| 5. Knowledge/standing changes treatment | `PROVEN CURRENT` for individuals (`appraisal.py` already prioritizes private bond → trust_history → global reputation, in that order) | `MISSING` entirely for institutions — `IP-S17` re-confirmed, no per-(organization, individual) record of any kind |
| 6. Treatment changes future opportunity | `MISSING` as an input category | `opportunity_providers_contract.md`'s `RequirementsFilter` is a closed 4-category list; reputation/standing was never a 5th |

**Corrections this investigation made to earlier claims in this same track** (per the source
instruction's own requirement to report these explicitly):
- The Recognition/Standing synthesis's central claim — "no directed standing record exists" — is
  **wrong for the individual case**. `SocialComponent`'s `bonds`/`trust_history` already is that
  record, already correctly consumed. The synthesis over-generalized from the institutional case
  (where it's right) to the individual case (where it's wrong).
- Pass 2 characterized `BeliefCycleSystem.process_rumor()` as inherently region-scoped. It isn't —
  the function is fully generic; only its one caller (`GuildIntelSystem`) happens to only feed it
  regions. This is a wiring gap, not a mechanism limitation.
- The synthesis folded all of `ME-S12`/`politics-authority.md`'s wealth/reputation/office findings
  into "downstream of standing." Part B split this: wealth→coercive-capacity and office→resource-
  access are `INDEPENDENT CAUSAL EDGE`s, unrelated to standing; only reputation→leverage is
  standing-adjacent.
- `ActionProposal`/`ActionType` (`TCK-20260422`) — a real, documented "authoritative action proposal
  model" — is confirmed `SYMBOL`-only, zero consumers. Neither prior pass surfaced this; production
  action dispatch runs entirely on raw string keys instead.
- Two named harvest mechanisms (`HarvestAction`, `HarvestSystem`) are confirmed dead code; the real,
  live harvest path runs through generic `INTERACT`.

**Full architecture-decision tables** (Action question, Recognition question) are in Part A §"A3"/
"Architecture decision table" and Part B §"Architecture decision table" respectively — not
reproduced here in full; both conclude, independently, toward **wiring/repair over new abstraction**.

---

## 2. Proposed slices

Organized around the six causal capabilities above, sequenced by real dependency, not by
milestone-number tradition.

### Slice 0 — Groundwork repairs (no new capability; removes evidence gaps blocking everything else)

- **World capability proved:** none directly — this closes `UNKNOWN`s that block confidently
  building on top of the pipeline.
- **Mechanism candidates:** `WIRE` — verify `ResourceTransferIntent(source_kind="NODE")` resolves
  cleanly (or fix it, given the sibling `"CHEST"` bug is confirmed broken in the same resolver);
  `TUNE` — close `AGENCY-03`'s confirmed perception-bypass in opportunity generation; `RETIRE` (or,
  if Decision Request #3 below goes the other way, `EXTEND`) — `ActionProposal`/`ActionType`.
- **Verification level:** source trace + a passing unit test per fix — no new scenario needed.
- **Dependencies:** none. Can proceed immediately, independently, in parallel with everything else.
- **Exit criteria:** all three `UNKNOWN`s above resolved to a concrete status (fixed, or confirmed
  already-fine).
- **Deferred:** the shared upstream `ActionIntent`→`ActionRouter` payload edge (real, but no evidence
  yet that it's actually broken — trace it, don't redesign around an unconfirmed problem).

### Slice 1 — Close the propagation bottleneck (the thin end-to-end proof of changed life trajectory)

This is the single most load-bearing slice — Part B's own calibrated verdict names this the
narrowest real gap in the whole loop, and it is cheaper than the synthesis originally proposed: a
wiring change to an existing, already-correct mechanism, not a new architectural primitive.

- **World capability proved:** an ordinary entity's deed, witnessed by one observer but not another,
  produces genuinely different, causally-explained treatment from each — the exact loop the whole
  investigation was chartered to test.
- **Seeded scenario, two divergent outcomes:** a hunter completes a deed. Shopkeeper A was
  physically present (perception-gated, per `PerceptionGate`'s own existing channel) and directly
  learns of it; Shopkeeper B was not present and never learns of it (or, as a second run of the same
  scenario, receives a deliberately mis-attributed account — testing whether the system can
  represent a *wrong* belief, not just an absent one). Both later evaluate a contract offer from the
  hunter. A's evaluation differs from B's, sourced from real perception/propagation evidence, not
  from reading a global scalar.
- **First failed/unproven edge, evidenced:** `BeliefCycleSystem.process_rumor()` (`src/systems/
  strategic_systems/belief.py:127-158`) is generic-capable (`rumor_subject: str` — any entity or
  region) but has exactly one production caller (`GuildIntelSystem.update()`), which only ever
  passes a region. No producer feeds it an entity subject today.
- **Existing Rules defining target behavior:** `AGENCY-02`/`AGENCY-03` (opportunity/affordance
  distinct from desire; motivation influences, doesn't determine), `KNOW-01/02` (belief distinct
  from truth, memory distinct from declarative belief), `SOC-01` (structural relation vs. subjective
  attitude). **Proposed clarification, not a new Rule:** none of these currently states explicitly
  that social standing specifically must follow the perception-mediated, non-omniscient pattern —
  Pass 2 already flagged this as worth an explicit Inherited-entry citation when real work touches
  this area (small, non-blocking documentation action).
- **Mechanism candidates:** `INTRODUCE` a minimal witness-detection producer (event + `PerceptionGate`
  check at the moment of a notable action) that calls the *existing* `process_rumor()` with an
  entity subject; `WIRE` that rumor content into whatever consumer Decision Request #1 below settles
  on (extend `SocialComponent`'s existing dicts, or a new secondhand-belief tier).
- **Dependencies:** Slice 0's `ActionIntent`→payload trace helps but doesn't block this — the
  witnessing detector can be built independently of that edge. Gated on Decision Request #1.
- **Verification level:** scenario runtime — a deterministic, seeded scenario proving A's and B's
  treatment diverge, sourced from the propagation path, not from a global-scalar read.
- **Exit criteria:** the seeded scenario above passes, with an explicit assertion that removes any
  path to the result via `public_reputation` alone (i.e., the test must fail if propagation is
  stubbed out but the global scalar is left unchanged).

### Slice 2 — Institutional standing

- **World capability proved:** `IP-S17`'s own already-frozen scenario, made real: an organization
  records a non-HERO individual's repeated meaningful actions and changes access/hostility/role
  toward that individual specifically.
- **Seeded scenario, two divergent outcomes:** two otherwise-identical individuals interact
  repeatedly with the same guild; one consistently delivers, one consistently fails or betrays.
  Their standing with that guild diverges, and each receives different guild-mediated opportunities
  as a result.
- **First failed/unproven edge:** no per-(institution, individual) record of any kind exists —
  confirmed `MISSING`, not partially built.
- **Existing Rules:** `IP-S17` states the target shape precisely already — no new Rule needed, a
  realization gap under existing content.
- **Mechanism candidates:** `INTRODUCE` an institution-scoped standing record — **design shape
  deliberately not fixed here** (see Decision Request #4: specialize `FactionSentiment` downward, or
  a distinct type).
- **Dependencies:** should follow Slice 1, not run in parallel with it — reusing whatever
  propagation/consumption shape Slice 1 establishes avoids building two divergent "standing" shapes
  in the same release.
- **Verification level:** scenario runtime, same bar as Slice 1.
- **Exit criteria:** the two-individual guild scenario passes with genuinely divergent, guild-
  specific treatment.

### Slice 3 — Wire standing into opportunity generation

- **World capability proved:** a renowned or notorious entity's future opportunity set differs from
  an anonymous, identical-stat entity's — closing the loop back into changed trajectory.
- **Seeded scenario:** the same hunter from Slice 1, now with an established (positive or negative)
  standing with a specific observer, is offered a different opportunity set by that observer than an
  otherwise-identical stranger would be.
- **First failed/unproven edge:** `RequirementsFilter`'s four gate categories (inventory/skill/
  faction/quest-state) are a closed list — Pass 2's own direct read of the contract doc.
- **Mechanism candidates:** `EXTEND` `RequirementsFilter` with a fifth category reading standing
  (individual from Slice 1, institutional from Slice 2, whichever is relevant to the specific
  opportunity provider).
- **Dependencies:** Slice 1 (individual case) and, for institution-gated opportunities specifically,
  Slice 2.
- **Verification level:** scenario runtime.
- **Exit criteria:** the opportunity pool itself, not just a price or dialogue outcome, differs
  between the two evaluated entities.

### Slice 4 — Power-conversion edges (independent of standing, per Part B's correction)

- **4a — Wealth→coercive-capacity, office→resource-access.** `INDEPENDENT CAUSAL EDGE`s per Part B
  — **do not gate these on Slices 1-3.** Can proceed immediately, in parallel with Slice 0.
  - World capability: `politics-authority.md`'s own already-stated Rule — "a specific, declared
    edge, never a universal score" — realized for at least one concrete case (`ME-S12`'s own
    `PROTECTION` contract path, currently zero production call sites outside certification
    scenarios, is the most evidenced starting candidate).
  - Verification: scenario runtime once a concrete edge is chosen (not chosen here).
- **4b — Reputation→leverage.** `MAY CONSUME STANDING` — gated on Slice 1 at minimum.
  - Sequenced after Slice 1, can run parallel to Slice 2/3.

### Life-Chronicle validation lens (not authoritative state — explicit constraint honored)

Once Slices 1-3 land, a read-only projection over the real causal events they produce (turning
points, propagated rumors, standing changes, opportunity-set differences) can validate the whole
loop end-to-end by generating a biography-shaped trace — **this is a validation/reporting tool, not
new simulation state**, per the source instruction's explicit "do not turn biography output into
authoritative state" constraint. Not scheduled as its own slice; a natural follow-on once Slice 3
exits.

---

## 3. Sequencing summary

```
Slice 0 (repairs)  ──┐
                      ├──> Slice 1 (propagation) ──> Slice 2 (institutional) ──> Slice 3 (opportunity)
Slice 4a (wealth/office, independent) ──────────────────────────────────────────> Slice 4b (reputation→leverage)
```

Semantic Control Plane M3 stays exactly what it already is — an ongoing, non-blocking ingestion
stream. Nothing in this proposal is gated on M3, and M3 should keep triaging findings from whichever
of these slices land, the same way it already picked up the `combat_engagement` staleness finding
this session found earlier.

---

## 4. Decision requests for the owner

Only questions this investigation's own evidence cannot settle — not implementation details
resolvable locally.

1. **Slice 1's write target.** Should witnessed/secondhand propagation write into `SocialComponent`'s
   *existing* `bonds`/`trust_history` dicts — which would mean widening `SOC-196`'s own "trust/
   sentiment changes through interaction evidence" invariant to also cover witnessed-but-not-
   participated evidence — or into a new, separate, lower-confidence "secondhand belief" tier that
   keeps `SOC-196`'s current meaning intact? Real tradeoff: the first is cheaper (existing consumers
   already work correctly) but changes what an existing, named invariant means; the second is
   architecturally cleaner but requires `appraisal.py` and any other consumer to learn a new input.
2. **This proposal's permanent home**, given §0's ambiguity finding: a new standalone `docs/plans/`
   file, or eventual promotion into `rpg_design_roadmap.md` as an M11 once accepted?
3. **`ActionProposal`/`ActionType`** (`TCK-20260422`, confirmed dead) — retire now (Part A's own lean,
   low cost, clears a naming-collision risk), or adopt it as Slice 0/1's typed intent shape now that
   this work will touch the action-dispatch layer anyway? Not blocking, but worth a decision rather
   than leaving it dangling indefinitely.
4. **Slice 2's institutional standing shape** — specialize `FactionSentiment` downward to
   institution-to-individual, or build a distinct type? Part B flagged this as open; no repo evidence
   settles it either way.

Nothing else in this proposal requires owner judgment beyond ordinary implementation-ticket scoping
once these four are answered.

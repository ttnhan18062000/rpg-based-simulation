---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
last_verified: "2026-09-28"
---

# Systemic World — First-Wave Epic Plan — PROPOSED / FOR REVIEW

**Status: `PROPOSED / FOR REVIEW`. Not owner-approved.** The frontmatter `status: active` is the
repository's "live working document" value. The schema has no "proposed" value, and `active` does
not mean approved. Only the visible status above does.

**What this document is.** The epic-level first-wave plan for the direction proposed in
`roadmap.md` §8: a **bounded reachability-first** wave (owner memo decision 1). It defines epics,
their outcomes and boundaries, cross-epic dependencies, proof gates, failure branches, and what
stays outside the wave. Companion documents in this folder:
- `ticket_planner_handoff.md`: one card per item, for the downstream ticket planner;
- `owner_decision_memo.md`: owner-level choices only.

**What it is not.** A ticket list, or a prescription of code changes, schemas, tests or APIs. The
ticket planner decomposes approved epics, and two implementation agents implement and verify them.
Nothing here starts before the owner accepts this package.

---

## 1. What the first wave claims

The roadmap's four proof claims, and what this wave does with each:

| # | Proof claim | This wave |
|---|---|---|
| 1 | **World correctness.** | **Establishes bounded findings** for three named mechanisms (Epic J) and one authority boundary (Epic C1). Each finding says what does and does not act in ordinary runs, and why. |
| 2 | **Evidence-path design.** | **Establishes feasibility only** (Epic B0): whether one ordinary-run event yields a trace a situated observer could legitimately encounter, and whether perception is live at runtime. The full observer-contract design stays in portfolio Epic B. |
| 3 | **Player inference.** | **Not claimed.** At most, B0 identifies a clue a formative blinded-proxy review could later use (owner memo decision 6). |
| 4 | **Changed life trajectory.** | **Future.** |

**Hypothesis, not a promise.** Better behaviour in ordinary runs is a hypothesis this wave *tests*.
An outcome of "legitimately rare or conditional" is a valid result, not a failure. Where a mechanism
does act, visible change is a bonus, not an exit requirement.

---

## 2. First-wave epics

### Epic J — Bounded mechanism reachability

**Outcome.** Each of exactly **three named mechanisms** gets a finite, evidence-backed answer about
whether and how it acts in ordinary runs. No other mechanism is in scope; expanding the set is a
separate, later decision.

**Semantic contract.** A mechanism the registry calls `done` should either act in the conditions
the world intends, or carry an honest label describing when it does. "Rare" is not "broken".

**The four levels answered for each mechanism** (roadmap §11 item 5):
1. **Trigger reachability**: can the precondition arise in ordinary play?
2. **Feasible run horizon**: does it arise within a run length we can afford?
3. **Actual state effects**: when triggered, does it change authoritative state as declared?
4. **Observer evidence**: recorded if found, never required.

**Exit claim per mechanism — exactly one of**:
- acts in ordinary runs;
- legitimately rare or conditional, with the condition stated;
- defect (routed to separate work);
- registry label corrected;
- `BLOCKED_WITH_REASON`.

**The three mechanisms and the finite outcome sought for each:**

| # | Mechanism | Domain owner | Existing evidence | Linked existing ticket (not duplicated) | Outcome sought |
|---|---|---|---|---|---|
| J1 | `calamity_intensity` | world dynamics | `verified: {instrument: corpus_run, verdict: contradicted}`. The value stayed 0.0 in every region for a 5000-tick run | `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` (open) | Which level fails: the trigger never arising, the horizon, or the producer effect. Then one exit claim. |
| J2 | `regional_trauma` | world dynamics | `contradicted`. In the one corpus world with a lair, the lair's region records zero deaths across 5000 ticks. Trauma accrues per death elsewhere | `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` (open) | Whether this is a trigger-reachability condition (nobody goes there) that may be legitimately conditional, or a defect. Then one exit claim. |
| J3 | `aging_death` / `succession` (natural path) | lifecycle / lineage | Acts only when ages are staged. Natural-aging death is recorded silently (runtime-reproduced defect, roadmap §7.1). The default lifespan is about 20M ticks; corpus runs are 1k–5k | None yet. The defect is tracked as a ready-for-planning item, not duplicated (§3) | Level 2: record that it is unreachable within the feasible horizon under current world-time semantics. Level 3: record that its state effect is defective when reached. **Fixing that defect is not part of J3's exit claim** (§3). |

**J1 and J2 are two of the three mechanisms.** Their existing tickets become Epic J's workstreams
for them. The ticket planner reconciles their scope with the four-level outcome rather than opening
new tickets.

**Completion evidence (finite).**
- Three exit claims, each with its four-level record and evidence source.
- Registry labels corrected where needed, through the registry's normal process.
- Defects routed to separate work, not fixed inside J.

**Failure branch.** If a mechanism's investigation grows beyond answering its four levels, stop,
record `BLOCKED_WITH_REASON`, and return a scoping decision to the roadmap.

### Epic B0 — Situated-observation feasibility check

**Outcome.** Two bounded answers:
1. Is perception live in production at runtime?
2. Does **one selected consequential event in ordinary runs** produce evidence that a situated
   observer could legitimately encounter?

This is a feasibility finding, **not a player-experience proof**. It is the bounded precursor to
portfolio Epic B, the full observer contract.

**Semantic contract.** The epistemic principle (roadmap §2): viewpoint-scoped evidence only; no
omniscient surface; private events may stay private.

**Domain owners.** Perception/observation, plus the selected event's own domain.

**Selected event.** Default: **an ordinary-run death**, such as a combat death. It is consequential,
occurs within feasible run horizons (unlike old-age death), and already has one in-world effect: the
location-independent grief trigger (roadmap §7.2). The ticket planner may choose a different
consequential event if it is better evidenced, and must record why.

**Known evidence.**
- A grep found no production caller for the perception update phase. That is `UNKNOWN` at runtime
  and must not be treated as a finding until a run confirms it.
- For inheritance, no in-world carrier or provenance signal exists (read-only inspection,
  roadmap §7.2).

**Completion evidence (finite).**
- A runtime answer on perception: live, inactive, or `BLOCKED_WITH_REASON`.
- For the selected event: the evidence that exists, who could encounter it and from where, what
  stays hidden, and whether any path leaks hidden truth.
- Each result labelled with its evidence level.

**Failure branch: perception inactive at runtime.**
- Record it as an **engine foundation finding**.
- Close B0 with that result, and propose a **separate perception-foundation epic** to the roadmap,
  with its dependency implications. It would precede the full Epic B, individual history
  propagation (D), and any player-inference claim.
- Do **not** expand this wave.

### Epic C1 — Entity-death authority boundary check

**Outcome.** The entity-death boundary (`alive_set` written by combat and by hazard damage in the
same tick) resolves to one of:
- `CONFIRMED_FINE_WITHIN_SCOPE`;
- `DEFECT_CONFIRMED` (routed separately);
- `BLOCKED_WITH_REASON`.

**Why this boundary is in the wave.** It shares death semantics with J3 and with B0's default
event. Knowing whether same-tick deaths resolve under a declared rule keeps those findings honest.

**Semantic contract.** A persistent fact has one canonical authority, and concurrent effects
resolve under a declared rule (roadmap §3.1).

**Domain owners.** Combat, and world dynamics.

**Completion evidence (finite).** One bounded outcome, with its reason and evidence source, recorded
back in roadmap §3.1. A harness limitation is never reported as fine.

---

## 3. Tracked outside the wave, with owners and revisit triggers

| Item | Status | Owner | Scheduled when (revisit trigger) |
|---|---|---|---|
| **Natural-aging OLD_AGE/succession defect** (roadmap §7.1) | Confirmed at runtime; **ready for ticket planning**; not scheduled | lifecycle/lineage; engine apply | Any one of three triggers: (i) owner memo decision 5 chooses compressed world time, longer runs, or declared initial conditions for lineage claims; (ii) a first-wave or later proof needs natural deaths from aging; (iii) portfolio Epic A is scheduled. Its confirmed status alone does not give it first-wave priority. |
| **Faction-diplomacy boundary** (`diplomatic_relations_set`) | `UNKNOWN_WITH_REASON` | faction | When faction or diplomacy code is next changed, or when an epic starts relying on diplomatic relations as input (e.g. portfolio E). |
| **Public-reputation boundary** (`reputation_set`) | `UNKNOWN_WITH_REASON` | social | When owner memo decision 4 (`public_reputation`'s meaning) is decided, or when an epic reads or surfaces reputation (portfolio D or E). |
| **Region ownership / FAC-010** | Known, tracked on its existing track | faction / world | Unchanged by this wave. |

---

## 4. Cross-epic dependencies

```text
Epic J  : J1 · J2 · J3, each independent          (world side: reachability findings)
Epic B0 : perception runtime check ─┐
          selected-event evidence  ─┴─ both needed for B0's exit   (player side: feasibility)
Epic C1 : entity-death boundary                    (foundation)

No hard edges between J, B0 and C1. They can run in any order or in parallel.
No world-side item waits on B0.

Returned to the roadmap, not expanded in the wave:
  B0 finds perception inactive    ──> proposal: a perception-foundation epic
  J finds a defect                ──> routed as separate work
  decision 5 or a proof trigger   ──> schedules the natural-aging defect (§3)
```

---

## 5. Why this shape, and the tradeoffs

- **It tests the "done but doesn't fire" pattern directly** (roadmap §11 item 5), on a finite set,
  instead of building new capability on possibly inert mechanisms.
- **It keeps one situated-observation check in the wave**, so the player-side direction is not
  silently dropped. It uses an event that occurs in runs we can afford, rather than old-age death.
- **The costs:**
  - the lineage story is delayed;
  - the natural-aging fix waits for a scheduling trigger;
  - two authority checks move outside the wave, with owners and triggers.
- **Rejected alternatives:** A + B + C (no visible test of real behaviour), and A + C (no
  player-side progress at all). Both are recorded in the memo under decision 1.

---

## 6. Feeding results back

- J's exit claims and C1's outcome are recorded in the roadmap: §3.1 (the audit) and §8 (the
  portfolio evidence column).
- B0's findings are recorded in §7.2 and §11 item 3.
- Registry labels change only through the registry's own process. SCP mappings change only through
  SCP validation.

After this package is accepted, these documents change for new evidence, new decisions, or material
corrections, not for further wording passes. Implementer findings arrive through the ticket planner.

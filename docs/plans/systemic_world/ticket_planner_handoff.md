---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
last_verified: "2026-09-28"
---

# Systemic World First Wave — Ticket-Planner Handoff

**Status: ready for ticket planning.** The first-wave scope was accepted on 2026-09-28 (owner memo
decision 1). That acceptance covers ticket-planning scope only.
Frontmatter `status: active` means "live working document", not approval.

**Audience.** The ticket planner who decomposes approved epics into tickets for the implementation
agents. One card per first-wave item, plus one card for a ready-but-unscheduled item. Outcomes,
contracts, boundaries and exit claims live in `first_wave_plan.md` §2–§3 and are not repeated here.

**What this does not contain.** Classes to edit, schemas, test filenames, or a chosen fix. Ticket
granularity, technical investigation, acceptance tests and assignment are yours.

---

## Card J — Bounded mechanism reachability (J1, J2, J3)

**Where it is defined:** plan §2, Epic J.

**Scope.** Exactly three mechanisms, each answered on four levels:
1. trigger reachability;
2. feasible run horizon;
3. actual state effects;
4. observer evidence (recorded, never required).

Each ends with one exit claim. No fourth mechanism.

**Existing tickets to adopt, not duplicate:**
- J1 `calamity_intensity`: `tickets/todos/TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES.md`.
- J2 `regional_trauma`: `tickets/todos/TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES.md`. This
  ticket already frames the problem as a region that records zero deaths, not a wrong threshold.
  That is a trigger-reachability question, and it may be legitimately conditional.
- J3 `aging_death`/`succession`: no ticket. J3 **assesses reachability and classifies the finding
  only**. Fixing the known natural-aging defect is outside this wave: see Card R, which is scheduled
  only by the run-horizon decision or a specific proof dependency.

**Verified evidence (sources):**
- **Registry:** `registries/mechanisms.yaml` entries for `calamity_intensity`, `regional_trauma`,
  `aging_death` and `succession`. Their `verified` blocks were checked on 2026-09-27; the first two
  are `contradicted` by corpus runs.
- **Probe:** `evidence/2026-09-27-candidate-trajectory-search-findings.md`.
- **J3's horizon arithmetic:** the default lifespan is 70 fantasy years, about 20M ticks
  (`src/core/state.py:165`). Corpus runs are 1k–5k ticks.

**Questions for the ticket planner / implementers:**
1. For J1 and J2, which of the four levels actually fails? Is the answer a condition, a defect, or a
   mislabel?
2. How does each linked ticket's existing scope map onto the four levels? Tell us where it doesn't
   fit.
3. What is the minimum evidence that answers level 2 (feasible horizon) without an open-ended long
   run?
4. For J3, can levels 2 and 3 be recorded from existing evidence plus the reproduction, without
   fixing the defect?

**Contract-level risks.** Re-labelling a mechanism can change what other plans assume is live.
Record each label change in the registry, with its evidence, not only in these documents.

**Registry/SCP follow-through.**
- Update each mechanism's `verified` evidence and any corrected label through the registry process.
- None of the three is SCP-mapped; no SCP change is required.

---

## Card B0 — Situated-observation feasibility check

**Where it is defined:** plan §2, Epic B0.

**Scope.** Three separately reported answers, all needed to close B0:
1. **Perception**: is it live in production at runtime?
2. **Trace existence**: which world-state changes or events does the specified event leave behind?
3. **Situated encounterability**: can a specified co-located or bonded observer legitimately receive
   any of those traces, from where, and when?

A trace that exists but cannot be encountered is a valid, separately reported outcome. This is not
a player-experience proof.

**Specified event.** A combat death in an ordinary corpus run: an entity killed in combat and
recorded with death reason `COMBAT`. It does not depend on natural aging. If ordinary runs produce no
combat death, the event question closes `BLOCKED_WITH_REASON`. Do not substitute another event; a
replacement is a scoping decision returned to the roadmap.

**Verified evidence (sources):**
- `evidence/2026-09-27-inheritance-observer-encounter-findings.md`. Read-only inspection found:
  - the perceived-entity record has no item fields;
  - the perception update phase has no production caller, per a grep;
  - knowledge assimilates only paid information facts;
  - the grief trigger is location-independent.
- Roadmap §7.2.

**Evidence limits.** "Perception not live" comes from a grep and is `UNKNOWN` until a run confirms
it. Perception may run through another path.

**Questions for the ticket planner / implementers:**
1. At runtime, does any production path update what entities perceive about each other? If so,
   which one?
2. Do combat deaths occur in an ordinary corpus run, and which traces does one leave (answer 2)?
   Separately, which of those traces could a co-located or bonded entity legitimately receive
   (answer 3)?
3. Which surfaces are developer-only and must be excluded? Examples: event logs, inspectors, API
   presenters.
4. Does any existing path leak hidden truth? For example, `cognition.motivation.named_intention`,
   `strategic.blockers`, or location-independent reads.

**If perception is inactive at runtime:**
- Record it as an engine foundation finding and close B0 with that result.
- The roadmap then proposes a separate perception-foundation epic.
- Do not expand B0 into building perception.

**Contract-level risks.** Any runtime check must not turn on or change perception in production.
This is observation of current behaviour only.

**Registry/SCP follow-through.** If a perception mechanism's real state differs from its registry
entry, correct it through the registry process. Record B0's findings in roadmap §7.2 and §11
item 3.

**Never** record them against SCP rows `PERC-01`/`KNOW-01`. Those rows map only Combat's
`tactical_decision`, and observer evidence there would corrupt Combat's mapping.

---

## Card C1 — Entity-death authority boundary

**Where it is defined:** plan §2, Epic C1.

**Invariant.** Same-tick deaths from combat and hazard damage resolve under a declared rule.

**Verified evidence (sources):**
- `evidence/2026-09-27-authority-boundary-audit-findings.md`, boundary 2.
- Precedence comments at `src/systems/world_systems/groups.py:99` and
  `src/engine/pipeline_phases/clan_lifecycle.py:19`.

**Questions for the ticket planner / implementers:**
1. Is a same-tick combat + hazard kill on one entity reachable in production, or only in a harness?
2. What is the committed state and the recorded cause, and is the death processed exactly once?
3. Does the commented precedence actually hold?

**Exit.** One of:
- `CONFIRMED_FINE_WITHIN_SCOPE`;
- `DEFECT_CONFIRMED` (routed separately);
- `BLOCKED_WITH_REASON`.

A harness limitation is never reported as fine.

**Registry/SCP follow-through.** Record the outcome as a dated addendum in roadmap §3.1.

**Contract-level risks and sequencing**:
- C1 is a check. `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION` is out of its scope.
  - That ticket already carries a verified comparison of the two ownership writers; do not
    re-derive it.
  - The consolidation is determinism-sensitive: a naive consolidation delays death-driven ownership
    changes by one tick.
  - Any fix C1 routes that touches the ordering between world dynamics and lifecycle must be
    sequenced with it.
- The SCP rows `LIFE-01`/`LIFE-02` cite `combat_resolution`. Any change that alters who decides
  alive/dead must be followed by `make semantic-control-plane-drift-check`, a report-only check.

**Background, non-binding.** An incomplete scenario draft from a stopped exploratory agent sits on
the local branch `natural-aging-old-age-dispatch-fix-unreviewed`. It is not evidence.

---

## Card R — Natural-aging OLD_AGE/succession defect (ready; not scheduled in this wave)

**Status.** Confirmed at runtime. Ready for ticket planning. **Schedule it only when a trigger in
plan §3 fires:**
- owner memo decision 5 makes natural aging relevant (compressed world time, longer runs, or
  declared initial conditions);
- a proof needs natural aging deaths;
- portfolio Epic A is scheduled.

**Invariant.** A death reached through ordinary aging is recorded under one declared authority,
with a cause and a time, and its lineage consequences follow.

**Verified evidence (sources):**
- `evidence/2026-09-27-lineage-composition-probe-findings.md`.
- Roadmap §7.1.
- The runtime reproduction: seed 42, `PROD_SMALL`. The subject ages from 0 to max age 3 with a
  designated heir. From tick 3 it is inactive, with no death reason and no succession, and it never
  recovers.
- The existing lineage tests stage age past the maximum, so they miss the defect.

**Known gaps by evidence level:**
- Silent natural-aging death: runtime-confirmed.
- Starvation/sleep-debt death may be equally silent: `UNKNOWN`, inspection only.
- Spawns created inactive may rely on the same code path to become active: `UNKNOWN`, inspection
  only.

**Questions for when it is scheduled:**
1. Which path is the declared authority for old-age deactivation, and what is the resolution rule?
2. Does the correction shift the tick on which death is recorded? How is that pinned?
3. Is the inactive-spawn behaviour intended? If answering needs a world-meaning decision, return it
   to the roadmap.
4. Is the starvation path silent at runtime?

**Contract-level risks.** Changing how active/alive state is decided can affect:
- combat and hazard death;
- passive-decay consumers;
- group/clan lifecycle phases;
- economy vacancy signals.

**Registry/SCP follow-through.** Dated evidence notes on `aging_death`/`succession`, and the
matching parity-ledger entry.

**Background, non-binding.**
- The M1 ticket draft is summarized in the Appendix. It is unreviewed.
- Local branch `natural-aging-old-age-dispatch-fix-unreviewed` (not pushed) holds a prototype
  change and a natural-aging scenario. The scenario failed 3/3 against current code. The prototype
  was never run against the suite and does not address the inactive-spawn question. Inspect it or
  discard it; it is not an approved fix.

---

## Outside this wave (tracked, no cards)

The diplomacy and reputation authority checks and region ownership (FAC-010) are listed in plan
§3, with owners and revisit triggers. They need no ticket-planning work in this wave.

---

## Appendix — M1 ticket draft (background only, unreviewed, not binding)

An earlier session drafted an implementation ticket for the natural-aging defect,
`TCK-20260927-NATURAL-AGING-OLD-AGE-DISPATCH-RACE`. It was withdrawn from `tickets/todos/` because
ticket creation belongs to the ticket planner; it remains in this branch's git history. In summary:
- **Title:** "An entity that dies of natural aging is deactivated with no recorded cause and no
  succession."
- **Proposed classification:** standard tier, P1.
- **Acceptance criteria:**
  1. natural aging to max age yields an OLD_AGE record and heir effects;
  2. no silent inactive tick;
  3. death timing pinned and documented;
  4. existing death, inheritance and passive-decay tests pass unmodified;
  5. verified and unverified death paths are named;
  6. registry and parity evidence updated.
- **Open questions:** inactive-spawn behaviour; the starvation sibling gap.

Use it or discard it. It carries no roadmap authority.

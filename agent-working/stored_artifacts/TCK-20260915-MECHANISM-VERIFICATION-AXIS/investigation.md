---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260915-MECHANISM-VERIFICATION-AXIS
artifact_type: investigation
tags: [architecture, documentation, schema]
---

# Investigation — TCK-20260915-MECHANISM-VERIFICATION-AXIS

## Current Behavior

`docs/brainstorm/mechanisms.yaml` (built by `TCK-20260915-MECHANISM-REGISTRY-FOUNDATION`, this
ticket's own dependency) has no `verified` block on any of its 75 mechanisms — only `id`, `layer`,
`depends_on`, `state`. No verification view exists anywhere. `tools/mechanism_registry.py`'s
`MechanismRegistry` reader has no accessor for verification data.

## Mechanics / Engine Constraints

Same as the Foundation ticket: this is tracking tooling, not a simulation mechanic. No
`docs/mechanics/` or `docs/engine/` contract governs its shape.

## Real Mechanism Ids For The Three Sample Texts (exact ownership, not assumed)

Located directly in the atlas JSON (`id="card-sections-data"`), not guessed:

| Atlas text | Card | My registry id | Current `state` |
|---|---|---|---|
| "Succession never triggers" | `entity-profile#6` ("Aging, Natural Death & Succession") | `succession` | `orphan` |
| "Built correctly, OFF by default" | `entity-cognition#0` ("Self-Model") | `self_model` | `gated` |
| "Built correctly, OFF by default" | `entity-cognition#10` ("Information Sourcing, Trust & Deception Detection") | `information_trust_deception` | `gated` |
| "Built correctly, OFF by default" | `world-layer#2` ("Opportunity & Rumor Seeds") | `opportunity_rumor_seeds` | `gated` |
| "Proven mechanic, narrow trigger" | `design-ideas#6` ("7. Extend Grief/Nemesis past episode boundaries") | `cross_episode_grief_nemesis` | `done` |

The "Built correctly, OFF by default" text appears on **3 different cards**, not 1 — migrating it
means 3 separate `verified` blocks, one per mechanism, not one shared value.

**`combat_judgement` naming note**: the ticket's own worked example (and
`docs/plans/mechanism_registry_initiative.md`'s §3 shape example) both use the id `combat_judgement`
for this worked example. The Foundation ticket's real seed does not have that id — the atlas's own
card is titled "Combat Engagement (Pre-Combat Assessment)", seeded as `combat_engagement`, and that
is the mechanism `tests/mechanic_scenarios/test_combat_judgement_withdrawal.py` actually exercises
(the posture-veto gate in `action_router.py`'s `ATTACK`/`SKILL` dispatch, set by Combat Engagement's
own posture-selection logic). Using the real seeded id (`combat_engagement`), not inventing a
second, redundant `combat_judgement` entry that would never resolve any `depends_on` edge pointing
at it.

## Real Finding: the `instrument` enum does not cover the dominant verification method

**Flagged to peer before implementation** (not silently resolved): all three sample texts above are
direct code-trace/investigation confirmations — "heir_entity_id never populated" (a repo-wide
search confirming a field write path doesn't exist), "confirmed live, called from the Campaign
orchestrator" (a direct call-site trace) — not output from an automated instrument run. None fit
`instrument: census | scenario | corpus_run | null` as literally specified in the ticket's own
Request Summary. This is not narrow to these three texts: direct code tracing (confirmed zero
callers, confirmed call chains, confirmed a field is never written) is the dominant verification
method across this entire arc's own ticket history — most of this session's own findings this week
used exactly this method, not one of the three automated instruments.

**Resolved (peer review, 2026-09-16): add `code_trace` as a 4th `instrument` value, with a hard
distinction from the other three, not a flat peer.** `code_trace` is **static** evidence — it
proves what the code *says* (this is called, this field is never populated, this has zero
callers). `census`/`scenario`/`corpus_run` are **runtime** evidence — they prove what the
simulation actually *does*. This distinction is the single most expensive lesson of this whole
arc: combat judgement passed a code trace cleanly (real code, reachable, called — all true, all
confirmable statically) and was write-only; only a runtime instrument (the 1960→837 corpus
measurement) caught that. A `code_trace`/`observed` row must never render as equally strong as a
runtime-confirmed one. Carried two ways, deliberately minimal — no numeric confidence/strength
field (invented precision) — (1) documented on the value itself: `code_trace` establishes
*structure*, never that reachable code has its intended runtime effect; (2) the view groups/orders
static evidence separately from runtime evidence so a reader scanning the table sees which kind of
evidence they're looking at, per plan.md.

**Second resolution (peer review): not all three sample texts are pure verification statements —
one decomposes across two fields.** "Built correctly, OFF by default" is mostly a *state* claim
(`gated` already covers "OFF by default" — 3 of the 6 state classes exist for exactly this) with
only "built correctly" left over as an actual verdict. Migrated as `state: gated` (already true in
the registry, unchanged) plus a `code_trace`/`observed` verified block whose note covers only the
"built correctly" claim, not restating the OFF-by-default fact a second time. This is itself a
second, real instance of Gap 2's own claim: the atlas texts were overloaded across *two* missing
fields (verification here, but the pre-existing `state` field already absorbed half the original
text), not one — strengthens the epic's own framing rather than just confirming it.

**Third resolution — Assumption/Open Question #2 (verdict:contradicted vs state:orphan) settled
with real data, not in the abstract, per peer's explicit request:** `succession`'s own case is the
deciding example. `state: orphan` already carries the claim "built but never fires." The
`heir_entity_id`-never-populated code trace *confirms* that claim is true — it does not contradict
it. So this is `verified: {instrument: code_trace, verdict: observed, ...}`, not `contradicted` —
`verdict` and `state` **compose** (both independently point the same direction here) rather than
collapsing into one field. They stay genuinely separate fields answering different questions
(`state`: is it built and reachable; `verified.verdict`: does the evidence match that claim), and
the case that would actually produce `contradicted` is the historically expensive one — `state:
done` with a *runtime* instrument finding the claimed behavior doesn't actually happen (exactly
combat judgement's own near-miss, had it not been caught). No real `contradicted` example exists
in the current 75-mechanism seed; not fabricated to fill the enum — recorded as still open for a
future mechanism that actually needs it.

## Prior Work

- `staging_artifacts/TCK-20260915-MECHANISM-REGISTRY-FOUNDATION/` — the Foundation ticket's own
  investigation/plan/test_plan; this ticket extends that schema, reader, and test file rather than
  building anything from scratch.
- `tests/mechanic_scenarios/test_combat_judgement_withdrawal.py` — the real, differential scenario
  verdict for `combat_engagement` (posture risk-rejected → 0 attacks; no posture recorded → attack
  proceeds, everything else identical). Confirmed this file still exists and still passes (part of
  this same branch's earlier work, not re-verified from scratch here — already covered by CI's
  `perf-cert-arena` fast lane).
- The corpus-scale 1960 → 837 measurement for the same mechanism: cited in
  `docs/plans/mechanic_verification_scenarios_proposal.md` §4 and this ticket's own Request
  Summary; not independently re-run here (a re-run of a 3000-tick corpus scenario is out of this
  ticket's own scope — Out of Scope explicitly excludes "automatically ingesting scenario or census
  output," and re-deriving the number from scratch is not required to record the verdict that
  already exists and is cited in two prior tickets' own Implementation Notes).

## Docs Requiring Update

None beyond `docs/brainstorm/mechanisms.yaml` itself and the new verification-view output file
(location decided in plan.md). The atlas HTML's own three badge texts are migrated (copied into the
registry), not deleted or edited — Scope explicitly says "leave genuine per-card colour as prose,"
and the three sample texts, once the real verification claim moves to `verified`, may still carry
real per-card color the atlas itself uses for its own presentation; not touching the atlas HTML in
this ticket unless review finds a specific reason to (kept as a possible follow-up, not assumed
necessary).

## Parity Ledger Overlap

None. No logic change.

## Final Verdicts To Seed (5 real entries, 4 mechanisms + combat_engagement)

| Mechanism | `state` (unchanged) | `instrument` | `verdict` | Note (one line) |
|---|---|---|---|---|
| `combat_engagement` | `done` | `scenario` | `observed` | Corpus: posture gate moved attacks 1960→837. Scenario: risk-rejected posture→0 attacks vs no posture→attack proceeds, all else identical. |
| `succession` | `orphan` (unchanged) | `code_trace` | `observed` | `heir_entity_id` confirmed never populated by any write path (repo-wide search) — confirms the orphan claim, does not contradict it. |
| `self_model` | `gated` (unchanged) | `code_trace` | `observed` | Code read confirms the mechanism is correctly built; currently flag-gated off (see `state`). |
| `information_trust_deception` | `gated` (unchanged) | `code_trace` | `observed` | Code read confirms the mechanism is correctly built; currently flag-gated off (see `state`). |
| `opportunity_rumor_seeds` | `gated` (unchanged) | `code_trace` | `observed` | Code read confirms the mechanism is correctly built; currently flag-gated off (see `state`). |
| `cross_episode_grief_nemesis` | `done` (unchanged) | `code_trace` | `observed` | Confirmed live, called from Campaign orchestrator (dead ally → grief concern; repeated betrayal → party-formation blocker); narrow trigger. |

`combat_engagement` is the only `scenario`-instrument (runtime) verdict; the other 5 are
`code_trace` (static). This 1-runtime-vs-5-static split is itself informative for the view's own
grouping — worth preserving in the rendered output, not flattening into one undifferentiated list.

The remaining 69 mechanisms keep `verified: null` (unverified, per AC #2 rendered visibly, never
omitted).

## Assumptions / Open Questions

1. **The `instrument` enum gap above** — the load-bearing open item, pending peer confirmation
   before implementation.
2. Per the ticket's own Assumption #2: is `verdict: contradicted` (built, observed not working)
   distinct from `state: orphan` (a structural fact)? Checked against the three real texts: none of
   them is a clean `contradicted` case — "Succession never triggers" is closer to `state: orphan`
   already carrying the claim (the mechanism doesn't work), with the verified block adding *how* we
   know (a code trace found the missing write path), not a separate live-observation-that-failed.
   `combat_engagement`'s own verdict IS a clean `observed` case (a real differential test showed the
   gate does what it claims). No real example of `contradicted` surfaced in this pass — recorded as
   still open, not fabricated to fill the enum.
3. Per the ticket's own Assumption #1: `corpus_run` is treated as a real, current instrument (it
   produced the 1960 → 837 measurement), not deprecated in favor of `scenario` — both remain valid,
   distinct instruments (a scenario proves a claim under staged conditions; a corpus run measures
   real-world-scale frequency).

---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap]
---

> Dated evidence snapshot supporting `docs/plans/systemic_world/roadmap.md`, copied from the local working file `candidate-trajectory-search-findings.md` on 2026-09-27. Where the roadmap has since corrected a claim, the roadmap is authoritative.

# Second candidate trajectory search — findings

**Task**: find a second delivery-trajectory candidate with a causal shape genuinely different from
lineage (family/succession/history) and from economy/wealth (confirmed `BLOCKED` — no conversion
mechanism registered anywhere).

**Scope searched**: `registries/mechanisms.yaml`, grepped whole-file for
`calamity|trauma|environmental|feud|displac|office|institution|drought|famine|disaster|fire|flood|blight`,
then read the `state:`/`verified:` block of every match directly. That is the full scope searched —
a bounded keyword sweep of one registry file, not a repo-wide or full-Catalog search.

## Candidate 1 — Environmental threat / calamity

Two entries: `regional_trauma` (`registries/mechanisms.yaml:1948`, implemented by
`src/world/consequences.py::RegionalConsequenceService`) and `calamity_intensity`
(`registries/mechanisms.yaml:2114`, implemented by `src/world/calamity.py::CalamityService`). Both
are `state: done`, but both carry `verified: {instrument: corpus_run, verdict: contradicted}` —
meaning a real run was executed and it disproved the mechanism firing, not merely "untested":

- `regional_trauma`: real accumulation/decay code exists and is read by `camp.py`, `boss.py`,
  `creature_territory.py`, `threat.py` — but a direct measurement found the Lair region's
  `trauma_score` never actually accumulates in real play (open ticket
  `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`).
- `calamity_intensity`: real producer code (`+0.05 per hero death` in a hazardous region) — but an
  instrumented 5000-tick `Kernel.tick_once()` run against the `frontier_living_world` corpus found
  the value stayed `0.0` in every region for the entire run (open ticket
  `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`).

**Verdict**: disqualified — and arguably in worse shape than economy, since economy simply has no
mechanism registered, while this domain has one that was built, wired, and then directly falsified
by a real run.

## Candidate 2 — Displaced family / feud

No mechanism with `id: displacement` or `id: feud` exists anywhere in the registry. The only
occurrence of "displacement" is a dead code-comment cited inside `calamity_intensity`'s own note
(`registries/mechanisms.yaml:2137`: "a comment in `displacement.py`, never a real call"). The
roadmap already treats feud/displacement as part of the *same* mechanism family as lineage ("feud
inheritance, dying wishes, displacement, heirloom transfer, leadership succession" all under
`succession`/`aging_death`).

**Verdict**: not independent — this is a lineage variant, not a second causal shape.

## Candidate 3 — Institutional/office consequences (`IP-S17`)

No `institutional_standing`, `office`, or `political_office` mechanism id exists in the registry.
The one institution-adjacent entry, `belief_institution` (`registries/mechanisms.yaml:2548`), is
`state: partial`, `verified: {instrument: code_trace, verdict: observed}` — real for the
belief-export/import half, but its own note says the assimilation half has "no general writer
anywhere, only a compile-time seed for one scenario." This is belief/culture propagation, not
institutional standing or office succession, and it's `partial` with a known dead half, not
`done`+`observed` end-to-end like lineage.

**Verdict**: disqualified — `IP-S17`'s prior `MISSING` finding is reconfirmed.

## Overall result

No second candidate found that qualifies at lineage's evidence tier (`state: done`,
`verified: observed`, a real passing test through a real game tick, genuinely different causal
domain). Economy/wealth remains the only inspected comparison and it is `BLOCKED`. The honest status
to record in the roadmap: **comparative experiential clarity = `UNKNOWN`, bounded search exhausted**
(scope: the three keyword families above, in one registry file — not a full sweep).

## Comparison table (lineage vs. the two disqualified alternatives)

| Axis | Lineage | Environmental/calamity | Economy/wealth |
|---|---|---|---|
| Real causal sequence | Real, single-transition, `verified: observed` | Real code, but a run directly contradicts it firing | No mechanism to seed a run against |
| Authority/history continuity | Untested at multi-tick scale, but the single-tick mechanism is real | Precondition never arises in real play — nothing to test continuity of | Moot — nothing exists |
| Legitimate observer traces | Unchecked, but a real state change exists to project from | No real state change exists to project from | Same — none exists |
| Missing simulation work | None — mechanism already real | Needs a producer-side fix for why the precondition never fires | Needs the conversion mechanism built from scratch |
| Integration/proof cost | Cheapest of the three | Requires production code changes before any product-side work | Requires production code changes before any product-side work |

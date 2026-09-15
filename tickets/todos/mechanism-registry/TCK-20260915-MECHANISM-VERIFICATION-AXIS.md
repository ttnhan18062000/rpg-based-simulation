---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260915-MECHANISM-VERIFICATION-AXIS
phase: open
date: 2026-09-15
tags: [architecture, documentation, schema]
---

# TCK-20260915-MECHANISM-VERIFICATION-AXIS

## Title
Record whether each mechanism has been *observed working*, by which instrument, and when — the axis
no artifact currently has

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Every status in every brainstorm artifact answers one question: *is it built?* None answers *has it
been observed working?*

That gap produced this arc's most expensive miss. Combat judgement was correctly marked implemented
and was write-only: four conditions — flag off, flag on, output neutered, phase stubbed — all
produced exactly 1960 attacks. Nothing in the artifacts was wrong; the question was never asked.

Add a `verified` block to each mechanism in the registry:

```yaml
verified:
  instrument: scenario        # census | scenario | corpus_run | null
  verdict: observed           # observed | contradicted | inconclusive
  date: 2026-09-15
  note: "one line, what was actually seen"
```

Worked example, real as of 2026-09-15 — combat judgement is now verified at two scales: at corpus
scale the posture gate moved attacks 1960 → 837, and at scenario scale
`tests/mechanic_scenarios/test_combat_judgement_withdrawal.py` shows risk-rejected posture → 0
attacks vs no posture → attack proceeds, with legality, range and readiness identical. Four fields
hold that. Nothing in the current artifacts can express it.

## Scope
1. **Schema extension** — `verified` on each mechanism, nullable.
2. **The unverified-visible rule** — a mechanism with `verified: null` renders in the verification
   view as `unverified`, never omitted. This is the ticket's most important requirement, see below.
3. **A verification view** — rendered section listing every mechanism with instrument, verdict, date.
4. **Volume cap, enforced not just documented** — one row per mechanism, never per test; latest
   verdict only, no history (history lives in git).
5. **Migrate the overloaded atlas badge texts.** `"Built correctly, OFF by default"`, `"Proven
   mechanic, narrow trigger"`, `"Succession never triggers"` are verification statements sitting in a
   build-status field. Move them here; leave genuine per-card colour as prose.

## Out of Scope
- Adding badge classes to carry verification. That is what this field is for.
- Per-test result feeds. The scenario component emits one verdict per mechanism.
- Automatically ingesting scenario or census output. Verdicts are written deliberately at first;
  automate only once the producers are stable.
- Verification history or trend analysis.

## Acceptance Criteria
1. Every mechanism in the registry appears in the verification view, including unverified ones.
2. A mechanism with no verdict renders as `unverified` — proven by a test that adds an unverified
   mechanism and asserts it appears. **Assert presence, not absence**: an omission bug is invisible
   to a test that only checks the verified rows look right.
3. `instrument` is constrained to the known set; an unknown instrument fails validation.
4. The view is one row per mechanism; a fixture with multiple results for one mechanism collapses to
   the latest rather than emitting several rows.
5. At least the migrated atlas texts are present as real verdicts, so the view ships non-empty.

## Related Tickets
- `TCK-20260915-EPIC-MECHANISM-REGISTRY` — parent
- `TCK-20260915-MECHANISM-REGISTRY-FOUNDATION` — dependency
- `TCK-20260915-COMBAT-RISK-EVALUATION-ACCEPTABLE-AT-3X-MISMATCH` — a finding surfaced *by* scenario
  verification; the kind of result this axis exists to hold

## Related Docs
- `docs/plans/mechanism_registry_initiative.md` §2 Gap 4
- `docs/plans/mechanic_verification_scenarios_proposal.md` — the primary verdict producer

## Related Stored Artifacts
None yet.

## Related Code Areas
- `docs/brainstorm/rpg_feature_atlas.html` — source of the overloaded badge texts
- `tests/mechanic_scenarios/` — the scenario component's own verdicts

## Assumptions / Open Questions
1. Is `corpus_run` a durable instrument or an interim one that the scenario component replaces? It
   produced the 1960 → 837 measurement, so it is real today.
2. Should `verdict: contradicted` (built, observed *not* working) be distinct from a `state` of
   `orphan`? They are different claims — one is an observation, the other a structural fact — and
   keeping them separate is probably right, but confirm while migrating.
3. How stale may a verdict be before it is shown as aged? Deferred; a date is recorded so the policy
   can be added later without schema change.

## Implementation Notes
The unverified-visible rule is the whole point. If unverified mechanisms are simply absent from the
view, this artifact reproduces the exact failure the arc was about: a real state rendered as silence.
Build the default state loud.

## Test Summary
To be completed during implementation.

## Files Changed
To be completed during implementation.

## Completion Summary
Open.

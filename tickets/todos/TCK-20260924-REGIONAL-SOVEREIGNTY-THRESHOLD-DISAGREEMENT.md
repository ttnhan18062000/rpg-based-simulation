---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT
phase: open
date: 2026-09-24
tags: [world, documentation, determinism]
---

# TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT

## Title

Regional sovereignty ownership threshold is ±50 in one code path and ±100 in another, with the two
governing docs disagreeing the same way

## Status

OPEN

## Tier

standard

## Type

bug

## Priority

P1

## Request Summary

Four sources define when a region changes owner. They do not agree, and the split is **2-versus-2
across both docs and code** — so this is not documentation drift behind a single implementation, it
is two live implementations each backed by one doc.

| # | Source | Threshold | Verified at |
|---|---|---|---|
| 1 | `docs/mechanics/regional_sovereignty.md` — **Mechanics Bible, authoritative** | Control at influence **> +100.0 / < −100.0**; "Contested" between −50 and 50 | `:22-24` |
| 2 | `docs/world/regional_sovereignty_runtime_contract.md` | Sovereignty / conquest / liberation at **±50** | `:24`, `:51`, `:80`, `:85`, `:109` |
| 3 | `src/world/influence.py::FactionInfluenceService` | `CONQUEST_THRESHOLD = -50.0`, `LIBERATION_THRESHOLD = 50.0` | `:29-30`, applied `:65`, `:69` |
| 4 | `src/engine/world_dynamics.py::WorldDynamicsSystem` | Ownership change at `>= 100.0` / `<= -100.0` | `:82`, `:86` |

So (1) agrees with (4), (2) agrees with (3), and **both pairs are live**. Two independent code paths
can each transfer region ownership, on different evidence, at different thresholds.

**Why this is P1 rather than a tidy-up.** The Mechanics Bible is the authoritative source for
simulation law and this repo requires 100% semantic parity between it and source. Here one live path
contradicts it outright. Worse, the two code paths are not alternatives behind a flag — both run, so
the observable ownership rule depends on which path reaches a region first, which is a
consistency hazard in a simulation whose determinism is a hard guarantee.

**Provenance.** Surfaced by `TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE` while mapping TERR-02,
and correctly recorded rather than fixed there (out of that slice's scope). It is already cited as
one of the two gaps holding TERR-02 at `PARTIAL` rather than `SUPPORTED` in
`registries/rule_classifications.yaml`. Every line citation in the table above was independently
re-verified while filing this ticket.

**Note on a related subtlety, not itself the bug:** `influence.py:59` clamps influence to
`[-100.0, +100.0]`. The Mechanics Bible's "> 100.0" is therefore unreachable as written — only
`>= 100.0` (what `world_dynamics.py` actually tests) can ever fire. Whichever threshold wins, the
Bible's strict-inequality phrasing needs to be reconciled with the clamp.

## Scope

- Decide the single canonical ownership threshold, with a rationale. This is a **simulation-balance
  decision, not a mechanical one** — ±50 and ±100 produce materially different conquest rates.
- Make all four sources agree with that decision: both docs and both code paths.
- Resolve whether two independent ownership-transfer paths should exist at all, or whether one
  should defer to the other. If both remain, state explicitly which is authoritative and why the
  other is not a duplicate authority.
- Reconcile the strict-inequality/clamp interaction noted above.
- Update the parity ledger entry for regional sovereignty (`docs/parity_ledger/substrate.yaml` or
  `world_dynamics.yaml` — locate the real entry) with the new `status` and `v2_evidence`. If no
  entry exists, add one. A P0/P1 entry requires a passing `test_path`.
- Add a regression test asserting the chosen threshold in **both** code paths, so they cannot drift
  apart again silently.

## Out of Scope

- Any other sovereignty behavior: influence accrual rates, trauma, taxation cadence, stronghold
  spawn/removal, town-access locking.
- Re-classifying TERR-02 in `registries/rule_classifications.yaml`. That classification is correct
  as written *today*; revisiting it belongs to a later control-plane review, not to this fix.
- The `owner_faction_id` overload that makes TERR-01/TERR-03 `CONFLICTING`. Different defect,
  different fix, deliberately untouched here.

## Acceptance Criteria

1. One canonical threshold is chosen and the rationale is recorded, including why the alternative
   was rejected.
2. All four sources state that threshold: both docs and both code paths.
3. The authority relationship between `FactionInfluenceService` and `WorldDynamicsSystem` ownership
   transfer is explicit — either one path is removed/made to defer, or the doc states why two
   independent paths are correct.
4. The strict-inequality vs. clamp interaction is reconciled: the documented comparison is actually
   reachable given `influence.py:59`'s clamp.
5. A regression test asserts the threshold in both code paths and fails if either drifts.
6. The regional-sovereignty parity ledger entry is updated (or created) with `status` and
   `v2_evidence` pointing at that test.
7. If the chosen value changes observable behavior, it is recorded in
   `docs/guidelines/intentional_divergences.md` with a rationale class and verification path.

## Related Tickets

- `TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE` (DONE) — surfaced this; correctly recorded
  rather than fixed in scope.
- `TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC` — TERR-02's `PARTIAL` classification cites this
  disagreement as one of its two blocking gaps.

## Related Docs

- `docs/mechanics/regional_sovereignty.md` — authoritative, currently ±100
- `docs/world/regional_sovereignty_runtime_contract.md` — currently ±50
- `docs/world/threat_and_consequences_contract.md` — cited by the runtime contract as owning
  "influence threshold mechanics"; check it for a third statement before deciding
- `docs/parity_ledger/` — the entry to update
- `docs/guidelines/intentional_divergences.md` — if behavior changes

## Related Stored Artifacts

- `stored_artifacts/TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE/` — the mapping evidence that
  surfaced this

## Related Code Areas

- `src/world/influence.py:29-30,59,65,69` — `FactionInfluenceService`, ±50 plus the ±100 clamp
- `src/engine/world_dynamics.py:82,86` — `WorldDynamicsSystem`, ±100

## Assumptions / Open Questions

- **Open, and the real decision:** which threshold is correct? Not inferable from the code — both
  are deliberate, each matches one doc. The Mechanics Bible's precedence rule argues for ±100, but
  the Bible is also the source that is currently unreachable-as-written given the clamp, so
  precedence alone should not settle it without a balance judgment.
- **Open:** is `WorldDynamicsSystem`'s path the newer one? Check `git log -S` on both constants
  before assuming which drifted from which — do not assume the Bible-matching path is the original.
- **Assumption:** both paths genuinely execute in normal runs. If investigation finds one is
  effectively dead, that changes the fix from "reconcile" to "remove," and is a finding to report
  before implementing.
- Not assumed: that `threat_and_consequences_contract.md` agrees with either value. It is cited as
  owning these mechanics and was not checked while filing.

## Implementation Notes

_To be completed by the implementer._

## Test Summary

_To be completed by the implementer._

## Files Changed

_To be completed by the implementer._

## Completion Summary

_To be completed by the implementer._

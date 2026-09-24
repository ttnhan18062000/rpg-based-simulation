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

## Decision (2026-09-24, REVISED) — SUPERSEDED IN PART, read the revision below first

> **The original decision recorded in the next section has been REVISED by the user on 2026-09-24
> after new evidence.** Read `## Decision Revision` below before implementing. The threshold flipped
> from ±100 to **±50**, and the `world_dynamics.py` deletion is no longer a bare delete. The
> original section is kept verbatim for provenance — do not implement from it alone.

## Decision (2026-09-24) — original, superseded in part

Decided by the user via `world-rule-catalog-design`, after this ticket was raised to them twice
unanswered. **Explicitly scoped as a quick fix, not a balance investigation** — the user's stated
reasoning is that this project is still in its documentation/architecture-alignment phase, not its
balance-tuning phase. Three mechanical edits, no number-picking, no redesign.

**1. Threshold: ±100. The Mechanics Bible wins on precedence, full stop.**
- `src/world/influence.py`: `CONQUEST_THRESHOLD` / `LIBERATION_THRESHOLD` ±50 → ±100.
- `docs/world/regional_sovereignty_runtime_contract.md`: update to match.
- `docs/mechanics/regional_sovereignty.md`: `> 100.0` → `>= 100.0`, so the rule is reachable
  against the existing `[-100, 100]` clamp.
- **No balance investigation.** A future balance-driven move to ±50 is a *separate* ticket with its
  own `docs/guidelines/intentional_divergences.md` entry — not this one.

**2. Dual authority: structural fix, not a redesign.**
- `FactionInfluenceService` becomes the **sole writer** of `owner_faction_id` — it already holds
  the only symmetric conquest+liberation logic.
- **Delete** `WorldDynamicsSystem`'s own conquest block (`src/engine/world_dynamics.py:80-89`)
  rather than rewriting it. It becomes a pure reader of whatever `FactionInfluenceService` decided
  that tick, consistent with the trauma/hazard bookkeeping already surrounding it.
- **No new abstraction or service extraction.**

**3. The undefined 50–100 / −100–−50 Bible bands: fold into "Contested."**
- Since ±100 is now the only place ownership changes, widen the Bible's "Contested" range from
  "−50 to 50" to "anything short of ±100." Pure doc-gap closure — the gap existed only because of
  the ±50/±100 split. Zero balance judgment.

**Supersedes the two open questions previously recorded here** (which threshold is correct; whether
precedence alone should settle it without a balance judgment). Both are answered: ±100, and yes.

## Decision Revision (2026-09-24) — SETTLED BY THE USER, authoritative over the section above

Decided by the user via `rpg-feature-planning`, after `rpg-implementer (2)`'s investigation surfaced
two facts the original decision was made without. Both were independently re-verified against
`src/` and `docs/mechanics/` before escalating. This revision changes the threshold and the shape of
the `world_dynamics.py` change; everything else in the original section still holds.

### R1. Threshold: **±50**, not ±100. The Bible was split against itself.

"The Mechanics Bible wins on precedence" could not settle this, because the split is *inside* the
Bible — a fact not known when ±100 was chosen:

| Source | Says | Last changed |
|---|---|---|
| `docs/mechanics/05_world_evolution.md:62-69` | **±50**, and explicitly rebuts ±100 as "only the influence value's clamp bound, not itself a trigger", citing `influence.py:29-30,59` | **2026-09-02** |
| `docs/mechanics/regional_sovereignty.md:20-24` | `> 100.0` / `< -100.0` | **2026-05-18** (`Resource V2 Implementation`) |

The ±50 statement is 3.5 months **newer**, is code-cited, and was written as a deliberate correction
that anticipated exactly the reasoning used to pick ±100. The ±100 statement is older and its
strict-inequality phrasing is provably unreachable against the `[-100, 100]` clamp — the defect this
ticket already flagged in `## Request Summary`. Precedence applied with full information therefore
points to ±50.

**Consequences — the fix gets smaller, not bigger:**
- `src/world/influence.py`: **no constant change.** `CONQUEST_THRESHOLD = -50.0` /
  `LIBERATION_THRESHOLD = 50.0` are already correct and stay as they are.
- `docs/mechanics/regional_sovereignty.md:20-24`: corrected to ±50, with reachable comparisons
  (`>= +50.0` / `<= -50.0`).
- `docs/mechanics/05_world_evolution.md`: **no change.** Already correct.
- `docs/world/regional_sovereignty_runtime_contract.md`: **no change.** Already ±50.
- `docs/world/threat_and_consequences_contract.md`: **no change.** Already ±50.
- **The original decision's item 3 is VOID** — there is no 50–100 band to fold into "Contested",
  because ±50 is the ownership boundary. `regional_sovereignty.md`'s existing "Contested: between
  -50.0 and 50.0" becomes correct as written.

### R2. `world_dynamics.py`: preserve HERO_GUILD, do not bare-delete.

`FactionInfluenceService.process_influence_shift()` (`src/world/influence.py:64-70`) only ever writes
`MONSTER_HORDE` (conquest) or the `None`-sentinel (liberation) — it has **no HERO_GUILD branch**.
`WorldDynamicsSystem`'s block (`src/engine/world_dynamics.py:79-89`) is the only code that ever
grants `Faction.HERO_GUILD` ownership via an influence threshold. A literal delete would remove a
real game capability, not just restructure authority, and would break
`tests/integration/world/test_regional_sovereignty.py::test_regional_ownership_flip`, which
currently proves that capability exists.

- **Give `FactionInfluenceService` a real HERO_GUILD branch before the deletion lands.** This is new
  logic and stretches the original "delete, don't rewrite" instruction — that is accepted
  deliberately, because it keeps the change behavior-neutral, which is what the alignment-phase
  framing actually intended. "No new abstraction / no service extraction" still holds: a branch
  inside the existing method, nothing more.
- `FactionInfluenceService` still becomes the **sole writer** of `owner_faction_id`.
- `world_dynamics.py:91-100`'s `SOVEREIGNTY_SHIFT` emission reads `new_owner`, a local set only
  inside the deleted block, so the emission **must move** with whatever writes ownership. The block
  cannot be removed in isolation regardless of the HERO_GUILD question.
- Because HERO_GUILD conquest is preserved, **no second `intentional_divergences.md` entry for a
  capability loss is needed.** AC7's entry is still required only if the ±50 consolidation changes
  observable behavior — note that with ±50 retained in code, the observable change is the removal of
  the ±100 transfer path, not a threshold move.

### R3. Still open for the implementer, unchanged by this revision

`WORLD-107` in `docs/parity_ledger/world_dynamics.yaml` updated in place (rather than a new entry)
is the accepted approach. Both threshold paths were confirmed live-reachable every tick — neither is
dead code, so the ticket's "consistency hazard" framing was correct.

## Assumptions / Open Questions

- **Still worth checking during implementation:** is `WorldDynamicsSystem`'s path the newer one?
  `git log -S` on both constants. This no longer affects *which* threshold wins — that is settled —
  but it may affect how cleanly the block deletes.
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

---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT
phase: done
date: 2026-09-24
tags: [world, documentation, determinism]
---

# TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT

## Title

Regional sovereignty ownership threshold is ±50 in one code path and ±100 in another, with the two
governing docs disagreeing the same way

## Status

DONE

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

**Added scope item, decided by the user during PR #245's review, not part of the original
request:** `tools/semantic_control_plane/generate_territory_control_view.py`'s `_COMPARISON_TEXT`
(the M4 cross-domain view's hand-written comparison prose, lines ~203-238) hardcodes counts
(`0/4`, `10/10`, classification breakdowns) that this ticket's own fix invalidates the moment it
lands — this work moves `TERR-02` off `PARTIAL`. Compute those counts from the registries the same
way the view's own banner already does, rather than leaving them as a stale hand-authored literal
inside a file headed "Do not hand-edit." Scope guard: this is the counts in `_COMPARISON_TEXT`
only — not a rewrite of the generator, and not a broadening of `mapping_drift_check.py`'s own
drift classes (a "generated prose vs. computed banner" drift class is a real gap the M2 detector
doesn't cover, but that's a finding to report separately, not something this ticket builds).

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
3. ~~The authority relationship between `FactionInfluenceService` and `WorldDynamicsSystem` ownership
   transfer is explicit — either one path is removed/made to defer, or the doc states why two
   independent paths are correct.~~ **REVISED by R4 (2026-09-24): consolidation is deferred.**
   Satisfied instead by *documenting* that two ownership writers exist, that they now agree on the
   threshold, and that consolidation is deferred to
   `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION` — with a pointer to that ticket from
   `docs/world/regional_sovereignty_runtime_contract.md`. Do **not** remove or re-home either path in
   this ticket.
   3a. Both code paths read the threshold from the **same constants** —
   `WorldDynamicsSystem` imports `CONQUEST_THRESHOLD`/`LIBERATION_THRESHOLD` from
   `src/world/influence.py` rather than hardcoding literals, so they cannot drift apart numerically
   again even while two writers remain.
4. The strict-inequality vs. clamp interaction is reconciled: the documented comparison is actually
   reachable given `influence.py:59`'s clamp.
5. A regression test asserts the threshold in both code paths and fails if either drifts.
6. The regional-sovereignty parity ledger entry is updated (or created) with `status` and
   `v2_evidence` pointing at that test.
7. If the chosen value changes observable behavior, it is recorded in
   `docs/guidelines/intentional_divergences.md` with a rationale class and verification path.
8. **(Added scope, from #245's review.)** `generate_territory_control_view.py`'s
   `_COMPARISON_TEXT` computes its counts/classification-breakdown from the real registries
   (mirroring the banner's own existing computation) instead of hardcoding them, and a real
   assertion fails if the prose and the computed banner ever disagree — not merely relying on the
   existing regeneration test, which cannot catch this drift class (stale prose regenerates
   byte-for-byte identical to itself).

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

> **The original decision recorded in the next section has been REVISED by the user, twice.** Read
> `## Decision Revision` below — specifically **R1** and **R4** — before implementing. Net effect:
> the threshold flipped from ±100 to **±50**, and the `world_dynamics.py` deletion is **cancelled
> entirely** (R4 supersedes R2; no block is deleted and no HERO_GUILD branch is added). The scope is
> now: correct one Bible chapter, share one pair of constants between the two code paths, record the
> divergence, and fix the `_COMPARISON_TEXT` drift. The original section and R2 are kept verbatim for
> provenance — do not implement from either alone.

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

### R4. Authority consolidation is DEFERRED — R2's HERO_GUILD branch is VOID

Decided by the user 2026-09-24 (recorded 2026-09-25), after `rpg-implementer (2)` found R2's
"add a HERO_GUILD branch" instruction architecturally insufficient. All findings below were
independently re-verified before escalating.

**What R2 missed:** the two paths differ in *trigger* and *phase position*, not just in what they
write.
- `FactionInfluenceService.process_influence_shift` has exactly **one** production caller,
  `src/systems/lifecycle_systems/lifecycle.py:272`, gated behind `if recent_deaths:` — it only ever
  evaluates regions where a death occurred this tick.
- `WorldDynamicsSystem`'s block is an **unconditional sweep** over every region in
  `state.regions`, against final settled influence (stored value + any `influence_delta` written
  that tick), regardless of cause.
- `world_dynamics` runs at `src/engine/pipeline.py:348`; `lifecycle` at `:414` — **`world_dynamics`
  runs first.**
- The block also carries `is_protector`/`is_invader` faction-semantics guards
  (`world_dynamics.py:82,86`) preventing redundant re-flips to the side already holding a region.
  That is real logic which would have to be reproduced anywhere ownership moves to — not a bare
  threshold compare.
- **Consolidating onto a single sweep at `world_dynamics`'s position would delay death-driven
  ownership flips by one tick**, because death influence deltas are not written until the later
  `lifecycle` phase. Today `process_influence_shift` flips ownership same-tick. That is a
  determinism/ordering change and needs its own investigation, not a branch added in passing.
- `tests/integration/world/test_regional_sovereignty.py::test_regional_ownership_flip` injects a raw
  `WorldUpdate(influence_delta=10.0)` with no death at all and asserts a `HERO_GUILD` flip — proving
  the unconditional sweep is load-bearing for non-death influence sources.

**The decision: fix the threshold disagreement, defer the architecture.**
- **`WorldDynamicsSystem`'s ownership block is NOT deleted.** It stays where it is, at the same phase
  position, with its guards and its `SOVEREIGNTY_SHIFT` emission intact.
- **No HERO_GUILD branch is added to `FactionInfluenceService`.** R2's instruction is void; the
  capability was never at risk once the block survives.
- `world_dynamics.py:82,86` change from the hardcoded `100.0`/`-100.0` to the **imported**
  `LIBERATION_THRESHOLD`/`CONQUEST_THRESHOLD` constants from `src/world/influence.py`.
- Both writers remain, but they now agree numerically and share one constant, so **the P1 consistency
  hazard this ticket was filed for is resolved** — the hazard was the disagreement, not the plurality.
- Consolidation moves to `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`.

**Rationale, in the user's framing:** three successive verification rounds each found hidden
structure in what was scoped as a ten-line delete. Continuing would turn an alignment-phase quick fix
into a pipeline-ordering change. Stop at the defect actually filed.

**Behavior-change note for AC7, state it plainly:** lowering `world_dynamics`'s effective threshold
from ±100 to ±50 makes ownership flips occur *sooner and more often* via the unconditional sweep.
This is unavoidable — any direction that makes the sources agree changes behavior — and it must be
recorded in `docs/guidelines/intentional_divergences.md` with rationale class **Unified** and a
verification path. Do not describe this ticket as behavior-neutral.

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

**All of `plan.md`'s Steps 1-9 complete.** #245 (`semantic-control-plane-m4`) merged to `main` as
`022dfd1dd` on 2026-09-25; `origin/main` merged into this branch (`e9c623024`) to pick up
`generate_territory_control_view.py`'s cross-domain-view code before Steps 8-9 could proceed.
Pre-implementation architecture review (2 rounds) correctly held Steps 8-9 until that dependency
was real — confirmed via `git merge-base --is-ancestor 42fff7d52 HEAD`/`...origin/main` (both
false before the merge, both true after).

Steps 1-7 implement R1/R3/R4 exactly (threshold unified to ±50, `WorldDynamicsSystem`'s block
undeleted and importing shared constants, dual-writer documented + deferred to
`TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`).

Steps 8-9 (`_COMPARISON_TEXT` → `_render_comparison(view)`, AC8) surfaced a real, concrete instance
of the exact drift class AC8 exists to catch: the *original* hardcoded prose stated "Combat is
`10/10` verified," but the document's own per-domain banner convention (already established by M4)
uses `verified/total_rows` as the denominator — `10/12` (10 verified, 12 total Combat rows
including the 2 `UNKNOWN` ones) — not `10/10`. Computing the count instead of hand-typing it fixed
a real, pre-existing inaccuracy, not just future-proofed against one. Verified the new anti-drift
test actually catches this class of regression by temporarily reintroducing the stale `10/10`
literal and confirming `test_comparison_counts_match_the_computed_banner` fails with a clear
diff, then reverting.

## Test Summary

Full scoped regression, real venv:
```
pytest tests/unit/world/test_sovereignty_events.py \
       tests/unit/world/test_influence.py \
       tests/unit/world/test_stronghold.py \
       tests/integration/world/test_regional_sovereignty.py \
       tests/unit/tools/test_cross_domain_management_view.py \
       tests/unit/tools/test_territory_control_view.py \
       tests/unit/tools/test_semantic_control_plane_schema.py \
       tests/unit/tools/test_semantic_control_plane_drift_detector.py -v
```
**71 passed, 0 failed.** New tests: `test_world_dynamics_ownership_threshold_uses_shared_constants`,
`test_world_dynamics_flips_ownership_at_shared_threshold_boundary` (AC5), and
`test_comparison_counts_match_the_computed_banner` (AC8, proven to fail on a deliberately
reintroduced stale literal, then reverted). One existing test's fixture updated:
`test_no_sovereignty_event_when_influence_below_threshold` (`influence=50.0` → `30.0`, since 50.0
is now exactly the new threshold, not safely below it). `test_conquest_and_liberation_thresholds`,
both `test_stronghold.py` tests, and Territory's own regeneration test all confirmed unaffected,
unchanged. `test_regional_ownership_flip` (the integration test proving the real end-to-end flip)
still passes at the corrected magnitude.

Validator: `python3 tools/semantic_control_plane/registry.py` → `OK`. Drift check:
`make semantic-control-plane-drift-check` → `0 cited-code drift finding(s), 0 verdict drift
finding(s)`. Parity ledger `WORLD-107` validated directly against
`tools/parity_ledger_writer.py::validate_entry()` (no dedicated single-entry CLI found; reused the
same function the writer tool itself calls). Territory's own output confirmed byte-identical
(`--check` → `OK`) both before and after the `_render_comparison` refactor.

## Files Changed

- `docs/mechanics/regional_sovereignty.md` — §1.2 thresholds corrected to ±50, reachable
  comparisons; `last_verified` bumped.
- `src/engine/world_dynamics.py` — ownership block now imports and compares against
  `FactionInfluenceService.LIBERATION_THRESHOLD`/`CONQUEST_THRESHOLD` instead of hardcoded
  `100.0`/`-100.0`. No other line changed.
- `tests/unit/world/test_sovereignty_events.py` — module docstring corrected to ±50; one fixture
  value fixed (50.0 → 30.0); two new tests added.
- `docs/world/regional_sovereignty_runtime_contract.md` — new "Two independent ownership writers"
  section, pointing at `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`.
- `docs/parity_ledger/world_dynamics.yaml` — `WORLD-107` updated in place (text, v2_evidence,
  test_path).
- `docs/guidelines/intentional_divergences.md` — new §2.58 entry, rationale class Unified.
- `tools/semantic_control_plane/generate_territory_control_view.py` — `_COMPARISON_TEXT` (static
  literal) replaced with `_render_comparison(view)` (computed from the same `view` dict the
  banner already renders from) plus a new `_classification_breakdown_prose()` helper. Qualitative
  prose left hand-written per AC8's own scope guard.
- `docs/brainstorm/cross_domain_management_view.md` — regenerated; the `## Comparison` section's
  counts now match the rest of the document's own established denominator convention (the
  pre-existing `10/10`→`10/12` inaccuracy this fix caught and corrected).
- `tests/unit/tools/test_cross_domain_management_view.py` — new
  `test_comparison_counts_match_the_computed_banner` (AC8).
- `staging_artifacts/TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT/{investigation.md,test_plan.md,plan.md}`.

## Completion Summary

All 9 acceptance criteria met. Three rounds of investigation/escalation (R1: ±50, not ±100, since
the Mechanics Bible was split against itself and the newer chapter explicitly rebutted ±100; R2
voided: no `FactionInfluenceService` HERO_GUILD branch, since `WorldDynamicsSystem`'s block was
never actually at risk of deletion; R4: writer consolidation deliberately deferred, since the two
paths differ in trigger and phase position and naive consolidation risked a one-tick determinism
change) each changed the outcome before any code landed — the pre-implementation architecture-
review gate held at each round rather than letting an interpretation get implemented and later
reverted.

Net effect: `WorldDynamicsSystem` and `FactionInfluenceService` now share one threshold constant
pair and can no longer numerically disagree, resolving the P1 consistency hazard this ticket was
filed for. Both writers remain, documented and deliberately not consolidated
(`TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`, filed separately). This is explicitly
**not** behavior-neutral — `WorldDynamicsSystem`'s own unconditional per-tick sweep now triggers
sooner and more often — recorded in `intentional_divergences.md` §2.58 (rationale class Unified).
The added `_COMPARISON_TEXT` scope item (from PR #245's review) is also complete and, in the
process, fixed a real pre-existing inaccuracy in that generated view's own prose.

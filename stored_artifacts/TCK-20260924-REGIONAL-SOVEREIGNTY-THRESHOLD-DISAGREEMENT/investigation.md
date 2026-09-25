---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT
artifact_type: investigation
tags: [world, documentation, determinism]
---

# Investigation — TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT

**Scope note:** The settled `## Decision (2026-09-24)` (±100 everywhere; `FactionInfluenceService`
sole writer, `WorldDynamicsSystem`'s conquest block deleted; Bible "Contested" band widened) is
**not re-opened anywhere below.** Everything here is evidence in service of implementing that
decision correctly — including two consequences of the settled structural choice that were not
named in the decision text itself and that the planner needs to see before writing `plan.md`.

## Current Behavior

### `FactionInfluenceService` (`src/world/influence.py`)

- `CONQUEST_THRESHOLD = -50.0`, `LIBERATION_THRESHOLD = 50.0` (`:29-30`), `DEATH_INFLUENCE_SHIFT = 5.0`
  (`:28`).
- `process_influence_shift()` (`:32-74`): accumulates ±5.0 influence per protector/invader death
  into a per-region delta, clamps `new_influence` to `[-100.0, 100.0]` (`:59`), then:
  - Conquest (`:65-66`): only when `region.owner_faction_id is None` and `new_influence <=
    CONQUEST_THRESHOLD` → `owner_faction_id_set = Faction.MONSTER_HORDE`.
  - Liberation (`:69-70`): only when the current owner is an invader and `new_influence >=
    LIBERATION_THRESHOLD` → `owner_faction_id_set = -1` (sentinel for `None`).
  - **This method never sets `owner_faction_id_set = Faction.HERO_GUILD`.** Its only two outcomes
    are "assign to `MONSTER_HORDE`" or "clear to `None`." This is a real behavioral asymmetry, not
    just a threshold-value difference — see Risks below.
- `process_conquest_lifecycle()` (`:76-113`): reads the `StateUpdate` `process_influence_shift`
  just produced (not `world_dynamics.py`'s output) and spawns/removes a stronghold entity on
  conquest/liberation. Unaffected by anything in `world_dynamics.py`; safe from the planned
  deletion.
- **Call site**: `src/systems/lifecycle_systems/lifecycle.py:267-289`, inside
  `LifecycleSystem.resolve_lifecycle()`, gated on `if recent_deaths:`. `resolve_lifecycle` is
  invoked from the authoritative pipeline at `src/engine/pipeline.py:414`
  (`run_phase("lifecycle", update, lambda u: LifecycleSystem.resolve_lifecycle(state, u))`) —
  **unconditional, every tick that pipeline phase runs.** `process_influence_shift`/
  `process_conquest_lifecycle` themselves only do work when `recent_deaths` is non-empty that tick,
  but the call site is live, not dead code.
- Its own `w_upd_args`/`inf_update.world_updates` are merged into the tick's running
  `StateUpdate.world_updates` at `lifecycle.py:280-289` via `WorldUpdate.merge()` — see "Two live
  paths, ordering, and merge semantics" below for why this matters.

### `WorldDynamicsSystem` (`src/engine/world_dynamics.py`)

- `resolve_dynamics()` (`:22-281`) is invoked unconditionally every tick from the authoritative
  pipeline at `src/engine/pipeline.py:348`
  (`run_phase("world_dynamics", update, lambda u: WorldDynamicsSystem.resolve_dynamics(...))`) —
  **also live, not dead code**, and this call happens *earlier in the same tick's phase order* than
  the `lifecycle` phase above (line 348 vs. line 414).
- "2.2 Ownership & Calamity Progression" is a single loop over `state.regions.items()` (`:68-110`),
  not a self-contained 10-line block:
  - `:71-78` compute `current_trauma`/`current_influence` (region value + any pending
    `w_upd.trauma_delta`/`influence_delta` from earlier phases this tick) and `owner_fid`.
  - **The ticket's cited `:80-89` ("the conquest block") is exactly this sub-piece**:
    ```
    new_owner = None
    if current_influence >= 100.0 and (owner_fid is None or not _sem.is_protector(owner_fid)):
        world_upd = replace(world_upd, owner_faction_id_set=Faction.HERO_GUILD)
        new_owner = "HERO_GUILD"
        changed = True
    elif current_influence <= -100.0 and (owner_fid is None or not _sem.is_invader(owner_fid)):
        world_upd = replace(world_upd, owner_faction_id_set=Faction.MONSTER_HORDE)
        new_owner = "MONSTER_HORDE"
        changed = True
    ```
  - `:91-100` (SOVEREIGNTY_SHIFT `WorldEvent` emission, part of E52G/`TCK-20260628-E52G-SOVEREIGNTY-EVENTS`)
    **reads `new_owner`, set only by the block above**, and compares it against `owner_fid` to
    decide whether to emit the event. **This is a real dependency the ticket's own line range
    (`:80-89`) does not include** — a literal delete of just `:80-89` leaves `:91` referencing an
    undefined `new_owner`. A clean removal must also either delete/adapt `:91-100`, or rewrite it to
    read whatever `FactionInfluenceService` already wrote into `w_upd.owner_faction_id_set` this
    tick (see "Two live paths" below) instead of recomputing a threshold locally.
  - `:102-107` (hazard scaling from `current_trauma`) and `:109-110` (writing `world_upd` back) are
    independent of the ownership block — hazard scaling reads `current_trauma`, not
    `current_influence`/`new_owner`/`changed`-from-ownership (though `changed` is shared; hazard
    scaling can still set it to `True` on its own, so the flag survives ownership-block deletion).
  - **Nothing after line 110 in the rest of the function** (steps 2.3, 3, 3.1–3.10, 4, 5) reads
    `new_owner`, `owner_fid`, or anything else set only by `:80-89`. The deletion's blast radius is
    fully contained to `:80-100`.
- `WorldDynamicsSystem`'s own threshold (`>= 100.0` / `<= -100.0`) is **already** ±100 — no code
  change needed on this side per the settled decision; only the deletion.

### Two live paths, ordering, and merge semantics — confirms the "consistency hazard" framing

Both call sites are real and both run every tick (see above) — this directly answers the ticket's
own open question 2: **neither path is dead code.** `WorldDynamicsSystem.resolve_dynamics` runs
first in phase order (`pipeline.py:348`), `LifecycleSystem.resolve_lifecycle` (which invokes
`FactionInfluenceService`) runs second (`pipeline.py:414`), within the *same* tick.

`WorldUpdate.merge()` (`src/core/updates.py:867-893`) resolves a conflicting `owner_faction_id_set`
with `other.owner_faction_id_set if other.owner_faction_id_set is not None else self.owner_faction_id_set`
(`:881`). `lifecycle.py:282-286` calls `new_world_updates[r_id] = new_world_updates[r_id].merge(extra_upd)`
where `new_world_updates[r_id]` is `world_dynamics`'s (earlier) result and `extra_upd` is
`FactionInfluenceService`'s (later) result — so **when both fire for the same region in the same
tick, `FactionInfluenceService`'s decision always wins** (second-writer-wins via `merge()`), not
"whichever reaches the region first" in any spatial sense, but not necessarily whichever a caller
might assume either. When only one fires for a region in a given tick (e.g., no deaths there this
tick → `FactionInfluenceService` never runs for it), the other's decision stands uncontested. This
is concrete evidence for the ticket's "observable ownership rule depends on which path reaches a
region first" framing — confirmed, not merely asserted.

## Mechanics / Engine Constraints

- `docs/mechanics/regional_sovereignty.md` §1.2 (authoritative, P0): "Hero Guild Control: Influence
  > 100.0. Monster Horde Control: Influence < -100.0. Contested: Between -50.0 and 50.0." The
  strict inequalities are unreachable given `influence.py:59`'s `[-100.0, 100.0]` clamp — this is
  the reconciliation AC 4 requires (`> 100.0` → `>= 100.0`; by the same clamp-reachability logic,
  `< -100.0` should become `<= -100.0` to match what `world_dynamics.py:82,86` actually tests,
  though the ticket's decision text only names the `>` side explicitly — flagged, not decided,
  below).
- `docs/engine/kernel.md`'s 7-phase deterministic loop and `docs/engine/authoritative_pipeline.md`'s
  refinement-sequence contract govern why phase order (`world_dynamics` before `lifecycle`) and
  `StateUpdate` merge semantics, not "which system runs first in wall-clock terms," determine the
  outcome described above — the Authoritative Mutation Pipeline Contract's apply-path law is the
  reason `merge()`'s deterministic tie-break (not a race) is the correct frame for this bug.

## Docs Requiring Update

- `docs/world/regional_sovereignty_runtime_contract.md`: currently states ±50 as the runtime
  sovereignty threshold at `:24`, `:51`, `:80`, `:85`, `:109` (all five citations in the ticket
  confirmed present verbatim) — must be updated to ±100 to match the settled decision.
- `docs/mechanics/regional_sovereignty.md`: `:22-24` — `> 100.0` → `>= 100.0` per the settled
  decision; `< -100.0` should also become `<= -100.0` for the same clamp-reachability reason (the
  decision text names only the `>` side; flagged as a small consistency gap for the planner, not
  decided here — see Risks); `:24` "Contested: Between -50.0 and 50.0" → widen to "anything short
  of ±100" per decision item 3.
- `docs/mechanics/05_world_evolution.md` (chapter 05 of the CLAUDE.md-listed six-chapter Mechanics
  Bible, `authority: P0`, `status: authoritative`, `last_verified: 2026-09-04`): **not named in the
  ticket's Related Docs or Decision text, but found here** — its own "Ownership Thresholds" section
  (`:62-69`) states, verbatim: *"Conquest and liberation trigger at `CONQUEST_THRESHOLD = -50.0` /
  `LIBERATION_THRESHOLD = 50.0` (`influence.py:29-30`), **not ±100.0**... ±100.0 is only the
  influence value's clamp bound... it does not define a second, stricter ownership tier."* This is
  a second P0-authoritative Mechanics Bible chapter directly and explicitly contradicting
  `regional_sovereignty.md`'s own ±100 claim (and, after this ticket, will directly contradict the
  settled ±100 decision unless also updated). It carries its own dated "Corrected, 2026-09-02"
  narrative (in the adjacent Influence Shifts section, `:50-55`) describing a prior fix that
  re-verified against `influence.py` and asserted ±50/DEATH_SHIFT=5.0 was correct against a
  previously-wrong ±100/±1.0 claim — i.e., this chapter was deliberately re-verified against source
  *after* `regional_sovereignty.md` already stated ±100, and it "corrected" toward the value that
  is now the one being retired. This doc **must** be updated (delete/rewrite the "not ±100.0"
  section) as part of this ticket, or the Mechanics Bible will contain two mutually contradictory
  P0 chapters immediately after the fix lands.
- `docs/world/threat_and_consequences_contract.md`: answers investigation question 3 (see Prior
  Work / body below) — its own "Influence" section (`:89-101`) states verbatim: `` `influence <=
  −50`: conquest event... ``, `` `influence >= +50`: liberation event... `` (`:100-101`). This is
  not a *third* distinct value — it restates the ±50 side already known from `influence.py` and
  `regional_sovereignty_runtime_contract.md` — but it is a real, previously-unchecked doc surface
  (the runtime contract cites it, at its own `:24`, as the doc that "owns" influence threshold
  mechanics) that must also change to ±100.

## Parity Ledger Overlap

Searched both `docs/parity_ledger/substrate.yaml` and `docs/parity_ledger/world_dynamics.yaml`
(the ticket's own candidate files) for `sovereignty`/`conquest`/`liberation`/`owner_faction`/
`influence`.

- **`WORLD-107`** (`docs/parity_ledger/world_dynamics.yaml:1369-1393`) is the real, closest-matching
  entry: "Sovereignty shift WorldEvent (E52G): when a region's influence crosses +100 (HERO_GUILD
  takeover) or -100 (MONSTER_HORDE takeover), a `WorldEvent(category=SOVEREIGNTY_SHIFT, ...)` is
  emitted..." `status: verified`, `priority: P1`, `v2_evidence` cites exactly `src/engine/
  world_dynamics.py` — "step 2.2 collects sovereignty_events; step 2.2b flushes them" — the same
  code region this ticket restructures, `test_path:
  tests/unit/world/test_sovereignty_events.py::test_sovereignty_shift_event_emitted_on_hero_takeover`.
  **This entry's `v2_evidence` will go stale** as soon as the event-emission logic stops computing
  its own threshold check and instead reads a decision `FactionInfluenceService` already made —
  it needs a `v2_evidence` update (and possibly `test_path`, if the cited test itself changes
  shape — see test_plan.md) as part of this ticket's Scope bullet "Update the parity ledger entry
  for regional sovereignty... If no entry exists, add one."
  - `WORLD-107`'s `divergence_note` already states: "Previously, ownership changes produced
    `WorldUpdate.owner_faction_id_set` but no `WorldEvent` was emitted." This confirms the event
    mechanic itself (not the ownership decision) is what this entry actually certifies — a further
    argument for treating it as the entry to update, not a signal that a wholly separate new entry
    is needed.
- **No entry anywhere in either file specifically certifies the conquest/liberation threshold value
  itself** (i.e., no entry cites `CONQUEST_THRESHOLD`/`LIBERATION_THRESHOLD` or the dual-authority
  structure). `WORLD-024` (`world_dynamics.yaml:235-244`) is a false lead — it's about calamity
  spawn intervals, unrelated despite the ID's superficial proximity to "world."
  `registries/rule_classifications.yaml`'s `TERR-02` row (`:55-72`, `PARTIAL`, re-verified
  2026-09-24) already names this exact ±50-vs-±100 mismatch as one of two blocking gaps, but that
  file is the Semantic Control Plane's rule-classification registry, not a `docs/parity_ledger/`
  entry, and per Out of Scope is explicitly **not** to be touched by this ticket ("Re-classifying
  TERR-02... belongs to a later control-plane review, not to this fix").
- No P0-priority entry was found for this specific rule/fact (`WORLD-107` is P1), so the "P0 entries
  require a passing `test_path`" rule does not independently gate this ticket, though the Scope's
  own AC 5/6 already require a passing regression test regardless of priority tier.

## Prior Work

- `stored_artifacts/TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE/investigation.md` — the source
  of this ticket, independently re-derives the same ±50 (`FactionInfluenceService`) vs. ±100
  (`WorldDynamicsSystem`) split (`:82-90`) and the same "docs disagree with each other as well as
  with one code path each" framing, and explicitly deferred fixing it (out of that ticket's scope).
- `registries/rule_classifications.yaml`'s `TERR-02` row (re-verified 2026-09-24 by
  `TCK-20260924-M3-TERRITORY-COMBAT-FINDING-TRIAGE`) restates the same mismatch as one of two gaps
  keeping `TERR-02` at `PARTIAL`. Confirms this ticket's fix, once landed, is relevant evidence for
  a future (separate, out-of-scope-here) `TERR-02` re-classification pass — not something to act on
  in this ticket.
- `tests/unit/world/test_influence.py` and `tests/unit/world/test_stronghold.py` are the existing
  regression surface for `FactionInfluenceService`'s ±50 constants (see test_plan.md).
  `tests/unit/world/test_sovereignty_events.py` and `tests/integration/world/test_regional_sovereignty.py`
  are the existing regression surface for `WorldDynamicsSystem`'s ownership block and event
  emission — both call patterns are described in detail below since they interact directly with
  the planned deletion.

## Risks and Open Questions

- **The dual-authority fix removes the only code path that ever assigns `HERO_GUILD` ownership.**
  `FactionInfluenceService.process_influence_shift()` never sets `owner_faction_id_set =
  Faction.HERO_GUILD` — its only two outcomes are "assign `MONSTER_HORDE`" (conquest) or "clear to
  `None`" (liberation). Only `WorldDynamicsSystem`'s block (`:82-84`) ever assigns `HERO_GUILD`.
  The settled decision's own justification — "`FactionInfluenceService`... already holds the only
  symmetric conquest+liberation logic" — is true in the sense that it handles both directions
  (gain a MONSTER_HORDE owner / lose one), but it is **not symmetric with `WorldDynamicsSystem`'s
  own behavior**, which actively assigns *both* enemy factions as owner on their respective
  thresholds. **Confirmed by an existing, currently-passing test**:
  `tests/integration/world/test_regional_sovereignty.py::test_regional_ownership_flip` (`:9-71`)
  drives influence to ≥100 through the *full* authoritative pipeline (`AuthoritativeApplyPipeline.refine`)
  and asserts `final_state.regions["forest"].owner_faction_id == Faction.HERO_GUILD` (`:71`) — this
  assertion currently passes *only* because of the `WorldDynamicsSystem` block being deleted. This
  is a genuine behavioral consequence of the settled structural decision, not a re-litigation of
  it: **the planner needs to decide whether `FactionInfluenceService` gains HERO_GUILD-assignment
  logic (making it a true drop-in replacement) or whether this is an accepted, intentional
  narrowing of behavior** (regions could conquer to MONSTER_HORDE or become ownerless via influence,
  but never become HERO_GUILD-owned via influence after this fix). Not deciding this before
  implementation risks either silently breaking `test_regional_ownership_flip` or silently changing
  observable game behavior without anyone having chosen to.
- **The SOVEREIGNTY_SHIFT event-emission code (`world_dynamics.py:91-100`) depends on `new_owner`,
  set only by the block slated for deletion** (see Current Behavior above). A literal "delete lines
  80-89" is not self-contained; the planner must specify how event emission is adapted — most
  naturally, by having `resolve_dynamics` read `w_upd.owner_faction_id_set` (now set upstream by
  `FactionInfluenceService`, since `lifecycle` still runs later in the same tick and the *next*
  tick's `world_dynamics` pass will see the committed `region.owner_faction_id`) rather than
  recomputing a threshold decision locally. This has a second-order consequence: because
  `world_dynamics` (phase `:348`) runs *before* `lifecycle` (phase `:414`) in the same tick, a
  conquest/liberation decided by `FactionInfluenceService` this tick would not be visible to
  `world_dynamics`'s own event-emission read until the update merge later in the same tick
  (`lifecycle.py:280-289`) — the ordering means `resolve_dynamics` cannot simply read
  `update.world_updates` for "this tick's decision so far" before lifecycle has run and expect it
  to already be there for a same-tick death-triggered conquest. This is exactly the kind of
  ordering subtlety AC 4/5 exist to catch — flagged for the planner, not resolved here.
- **`docs/mechanics/05_world_evolution.md` contradicting the settled decision was not named in the
  ticket's Decision text or Related Docs at all.** It must be added to the doc-update list (see
  above) or the fix leaves two Mechanics-Bible-authoritative chapters (05 and `regional_sovereignty.md`)
  disagreeing immediately after this ticket closes — the exact defect class this ticket exists to
  fix, reintroduced one level up.
- **`git log -S` shows both threshold definitions were introduced in the exact same commit**
  (`562116889`, "Resource V2 Implementation", 2026-05-18) — confirmed for `CONQUEST_THRESHOLD`
  (`influence.py`) and the `>= 100.0` literal (`world_dynamics.py`) via `git log --format='%h %ad
  %s' --date=short -S "<token>" -- <path>` on the current branch's real history (no `--all`).
  Neither path is newer; the split was baked in from day one, not introduced by later drift. (A
  `--all` search also surfaced an unrelated, non-ancestor commit `6e5c28992` dated 2026-04-26 on
  what appears to be a different, non-linear branch history — not chased further, out of scope, and
  does not change the "same commit on mainline" finding.) What *is* newer, and does complicate a
  clean deletion, is the SOVEREIGNTY_SHIFT event-emission code (E52G,
  `TCK-20260628-E52G-SOVEREIGNTY-EVENTS`, dated well after the original commit) — this is the real
  source of the "how cleanly the block deletes" complication the ticket asked about, not a
  chronology difference between the two thresholds themselves.
- **`docs/world/regional_sovereignty.py`'s `RegionalSovereigntyService` (taxation, debuffs) does
  not itself hardcode a ±50/±100 threshold** — `apply_sovereignty_debuffs()` (`:77-103`) and
  `process_taxation()` (`:23-75`) both gate purely on the already-committed `region.owner_faction_id`,
  never on a raw influence comparison. This rules out a feared fourth live threshold path; it is a
  pure downstream consumer of whatever `FactionInfluenceService`/`WorldDynamicsSystem` decided, and
  needs no code change. The runtime contract's own ±50 prose describing "when sovereignty holds"
  still needs updating (already listed above), but the service itself is unaffected.

## Anti-Drift Hazards

- Do not delete only `world_dynamics.py:80-89` and call it done — `:91-100`'s event emission reads
  `new_owner` from that exact block and will raise `NameError` (or silently emit nothing, depending
  on how it's rewritten) unless explicitly adapted.
- Do not treat `HERO_GUILD`-assignment as something `FactionInfluenceService` already does — it
  does not, today. If the planner decides `FactionInfluenceService` should gain this behavior to
  stay a faithful sole writer, that is new logic to write, not a refactor of existing logic.
- Do not update `docs/mechanics/regional_sovereignty.md`'s `> 100.0` → `>= 100.0` while leaving
  `docs/mechanics/05_world_evolution.md`'s "not ±100.0" section untouched — both are P0 Mechanics
  Bible chapters and must agree.
- Do not treat `tests/unit/world/test_influence.py::test_conquest_and_liberation_thresholds` or
  `tests/unit/world/test_stronghold.py`'s two tests as unrelated regressions when they fail after
  the ±50 → ±100 constant change — updating their fixture influence values (and, for
  `test_stronghold.py`, the death counts needed to cross ±100 instead of ±50) is required, in-scope
  work for this ticket, not a side effect to avoid touching.
- Do not widen the Bible's "Contested" band language in a way that implies a third, intermediate
  ownership tier exists in code — decision item 3 is pure prose (nothing in either code path
  currently branches on a "contested" state beyond "no owner assigned yet").

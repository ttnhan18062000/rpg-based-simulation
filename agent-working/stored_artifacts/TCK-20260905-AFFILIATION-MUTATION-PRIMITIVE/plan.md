---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE
artifact_type: plan
tags: [core, faction]
---

# Implementation Plan — TCK-20260905-AFFILIATION-MUTATION-PRIMITIVE

## Summary

The write-side primitive (`IdentityUpdate.faction_set` → `patches.py:209` → `apply.py:321`) is
already real, correct, and idle — this plan does not touch it. The only missing piece is a real,
live producer. Per the investigation's own recommendation, this plan extends
`PartyLifecycleService.check_defection()` (`src/systems/social_systems/party_lifecycle.py:143`,
SOC-230) — the single most evidence-grounded live, pipeline-wired trigger — so that a defecting
entity's `identity.faction` is set to `Faction.NEUTRAL` (`src/core/enums.py:28`) via
`IdentityUpdate(faction_set=Faction.NEUTRAL)`. This avoids inventing a "which rival faction"
design (no `GroupRecord.faction` field exists — confirmed absent at `src/core/state.py:659-679`)
and gives idea 56 (Drifting Loyalty) a real consumer to later request a *specific* destination
faction instead of bare neutrality, without this ticket depending on idea 56 existing first.

Mid-tick legality semantics (AC #3) resolve to **next-tick-boundary by construction of existing
phase order**, not a new code guard: `AuthoritativeApplyPipeline.refine()` runs `"action_routing"`
(`src/engine/pipeline.py:297`, which is where `LegalityServiceV2.verify_attack_legality()` is
actually evaluated and combat outcomes resolved, via `src/engine/domain/combat_actions.py:50` and
`src/engine/combat.py:143/265/348/482`) strictly *before* `"groups"`
(`src/engine/pipeline.py:402`, where the defection/`faction_set` trigger lives). Both phases read
against the same frozen `state` argument and accumulate into the same `update`/
`refined_entity_updates`, so an entity that defects during the `"groups"` phase cannot retroactively
affect any attack this same tick's `"action_routing"` phase already legality-checked and resolved —
those decisions were made against the pre-defection faction. The new faction becomes visible to
`legality.py`'s live reads (all 6 cited sites read `entity.identity.faction` fresh, no local
caching found beyond `apply.py:321`'s `pass_hostile`/`_has_hostiles_or_dead_cache`, which
`apply.py:321` already invalidates whenever `faction_set is not None`) starting with the *next*
tick's `"action_routing"` pass. No `legality.py` code change is required — this is a documentation
+ regression-test deliverable, not a new guard.

This plan also fixes the `src/replay/fingerprint.py` gap disclosed in Investigate (per-entity
fingerprint string omits both `role` and `faction`, `fingerprint.py:56-72`) as part of this
ticket's own AC #6, not a separate follow-up ticket — reasoning under Acceptance Criteria Map.

Groups.py's existing entity-update merge plumbing (`src/engine/pipeline_phases/groups.py:159-160`,
`existing_upd.merge(entity_upd)`) and `EntityUpdate.merge()` (`src/core/updates.py:756`,
`if other.identity: changes["identity"] = self.identity.merge(other.identity) ...`) already
correctly thread a new `identity=IdentityUpdate(faction_set=...)` returned by `check_defection()`
through to the final `StateUpdate` with zero changes needed to `groups.py` or `updates.py` itself.

## Steps

### Step 1 — Fix `StateFingerprinter` to cover `role`/`faction`

**Files:** `src/replay/fingerprint.py`

**Change:** `StateFingerprinter.get_fingerprint()`'s per-entity f-string (`fingerprint.py:56-72`)
currently includes `kind`, `pos`, `hp`, `gold`, `current_project`, `current_objective`,
`readiness`, `active`, `skills=len(...)`, `items=...`, `bonds=len(...)`, `reputation`,
`regional_reputation`, `strategic=...` — confirmed via direct read, **no `role` or `faction` term
anywhere in the string**. Add two terms to the f-string, immediately after `f"{ent.kind}:"`:
`f"role={ent.identity.role}:"` and `f"faction={ent.identity.faction}:"`. `IdentityComponent.role`
and `.faction` are both confirmed-real `int` fields (`src/core/state.py:578-579`).

**Other writers to this resource:** `StateFingerprinter.get_fingerprint()` is the sole writer of
its own return value (a pure function of `state`); it is not a shared mutable resource. It has two
known callers — `src/worldbuilding/compiler.py:730` and `src/core/state.py:1484-1485`
(`AuthoritativeState`'s own convenience method) — both read-only consumers of the returned
fingerprint, neither constructs or mutates it. Distinct from `CanonicalStateHasher`
(`src/engine/checkpoint.py:38`, fed by `IdentityComponent.to_canonical_dict()`,
`src/core/state.py:601-620`, which already includes `"faction": self.faction` at line 606) — that
hasher is a separate mechanism and is out of scope for this step (it already covers faction; no
change needed).

**Do NOT touch:** `CanonicalStateHasher`/`to_canonical_dict()` (already correct, per
`state.py:606`). Do not add any other new fields to the fingerprint string beyond `role`/`faction`
— this step is scoped exactly to the gap AC #6 names, not a general fingerprint audit.

**Verify:** `test_fingerprint_changes_when_faction_changes` (new,
`tests/unit/replay/test_fingerprint_identity_coverage.py`) — per test_plan.md item 6, write this
test first so it FAILS against current code, then confirm it PASSES after this step's change.

---

### Step 2 — Extend `check_defection()` to populate `faction_set`

**Files:** `src/systems/social_systems/party_lifecycle.py`

**Change:** In `PartyLifecycleService.check_defection()` (`party_lifecycle.py:143-198`), the
current `entity_update` construction (`party_lifecycle.py:194-197`) is:
```python
entity_update = EntityUpdate(
    entity_id=entity.id,
    social=SocialUpdate(notoriety_delta=2.0),
)
```
Add `identity=IdentityUpdate(faction_set=Faction.NEUTRAL)` alongside the existing `social=` kwarg.
Add `from src.core.enums import Faction` and `IdentityUpdate` to the existing local-import block at
`party_lifecycle.py:165-166` (which already locally imports `BetrayalDesertionEvent`,
`EntityUpdate`, `SocialUpdate` in this same function — follow that established local-import
pattern, do not add a module-level import). `Faction.NEUTRAL` is confirmed `= 3`
(`src/core/enums.py:28`, `class Faction(IntEnum)`).

**Other writers to this resource:** `check_defection()`'s returned `EntityUpdate` is merged at
exactly one call site — `src/engine/pipeline_phases/groups.py:159-160`
(`refined_entity_updates[m_id] = existing_upd.merge(entity_upd)`) — inside `GroupPhase.resolve()`'s
"Defection pass," which the file's own comment confirms runs "at most one defection per group per
tick" (`groups.py:132`, loop `break` at end). `refined_entity_updates` is seeded from
`update.entity_updates` (whatever `"action_routing"` and earlier phases already produced for the
same entity, `pipeline.py:297` runs before `"groups"` at `pipeline.py:402`) and merged via
`EntityUpdate.merge()` (`updates.py:741-771`), which for `identity` calls
`self.identity.merge(other.identity) if self.identity else other.identity`
(`updates.py:756`) — additive/non-destructive if an earlier phase this same tick already set a
different `IdentityUpdate` field (e.g. `role_set`) for this entity; `IdentityUpdate.merge()`
(`updates.py:254-259`) itself uses last-write-wins semantics per field (`if other.faction_set is
not None: changes["faction_set"] = other.faction_set`) with no conflict detection — confirmed no
other producer of `faction_set` exists in `src/` before this step (investigation's `grep -rn
"faction_set" src/` found only the 4 non-producer hits), so no actual collision is possible today;
this last-write-wins behavior is exactly what test_plan.md's Anti-Drift Test Guards section flags
as worth a guard test (see Step 3's architecture-guard note). No other pipeline phase reads or
writes `GroupRecord` in a way that races with this change — `check_defection()` remains a pure
function of its 3 arguments (`group`, `entity`, `tick`) per its own docstring contract.

**Do NOT touch:** `GroupRecord` (no `faction` field is added — this plan deliberately uses the
NEUTRAL-sentinel design specifically to avoid needing one). Do NOT touch
`SocialContractSystem.resolve_contract_outcome()` (`contracts.py:184`, confirmed dormant per
investigation — its `betrayal=True` path is never reached by `process_active_contracts()` and this
plan does not wire it live). Do NOT add any loyalty/pressure-accumulation field to
`IdentityComponent`/`EntityState` (that is idea 56's own scope). Do NOT change
`effective_defection_threshold()` or the grievance-log mechanics themselves — only the
`entity_update` return value changes.

**Verify:** New test in `tests/unit/social/test_party_lifecycle.py`, following the existing
`test_betrayal_desertion_fires_on_high_grievance` (`party_lifecycle.py:405`) setup pattern —
`test_defection_produces_faction_set_neutral_via_apply_path`: asserts `check_defection()`'s
returned `entity_update.identity.faction_set == Faction.NEUTRAL` when the grievance threshold is
met, and `entity_update.identity is None` (or unset) when it is not met. Also assert
`entity.identity.faction` is unchanged by calling `check_defection()` directly (pure function, no
mutation) — only changes once the returned update is run through `ApplyPath`/`patches.py:209`, per
AC #1's own required assertion.

**Depends on:** none (independent of Step 1).

---

### Step 3 — Confirm `entity_faction_changed` fires from the real trigger

**Files:** `tests/unit/observability/test_event_extractor_identity.py` only — no `src/` change.

**Change:** `event_extractor.py:410-416`'s `entity_faction_changed` emission is a plain
before/after diff (`if _is_real_number(ident.faction, prior_ident.faction) and ident.faction !=
prior_ident.faction:`) — already correct and already covered by the existing
`test_entity_faction_changed_fires_on_real_delta` test (`test_event_extractor_identity.py:48`,
hand-built `replace(prior_ent.identity, faction=prior_ent.identity.faction + 1)`). That existing
test is NOT modified. Add one new test,
`test_entity_faction_changed_fires_once_on_real_defection_trigger`, that runs Step 2's real
`check_defection()` → `ApplyPath` → `event_extractor` sequence end-to-end (construct a `GroupRecord`
at/above `effective_defection_threshold()`, call `check_defection()`, apply the returned
`EntityUpdate` via the real apply-path, then run the event extractor over prior/post state) and
asserts exactly one `entity_faction_changed` event with `payload["faction"] ==
Faction.NEUTRAL` and `payload["previous_faction"]` equal to the entity's original faction.

**Other writers to this resource:** `event_extractor.py`'s identity-event block
(`event_extractor.py:395-420`) also emits `entity_role_changed`, `recipe_learned`, and
`skill_cooldown_started` from the same prior/post diff pass — none of those are touched by this
step; the new test must not assert on their absence/presence beyond what's already covered by
`test_no_event_on_zero_delta` (`test_event_extractor_identity.py:105`), which remains unmodified.

**Do NOT touch:** `event_extractor.py` itself (confirmed already correct, per investigation and
this plan's own re-verification of lines 410-416). Do NOT touch
`test_event_shapers_deferred_instrumentation.py`'s `faction_extinct` coverage
(`event_shapers.py:1392`) — unrelated event, already reads `faction_set` defensively, no change
needed.

**Verify:** `test_entity_faction_changed_fires_once_on_real_defection_trigger` (new); existing
`test_entity_faction_changed_fires_on_real_delta` and `test_no_event_on_zero_delta` must still
pass unmodified.

**Depends on:** Step 2 (needs the real trigger to exist to test the end-to-end path; the isolated
event-extractor logic itself needs no change).

---

### Step 4 — Regression test for next-tick-boundary legality semantics

**Files:** `tests/unit/engine/test_legality_faction_mutation.py` (new) — no `src/engine/legality.py`
or `src/engine/pipeline.py` change.

**Change:** Add an integration-style test proving the ordering claim made in this plan's Summary:
construct a tick where (a) an attack against/by an entity is proposed and resolved during
`"action_routing"` using that entity's pre-tick faction, and (b) the same entity defects during
`"groups"` later in the same `refine()` pass. Assert: the action_routing-phase attack's legality
outcome reflects the OLD (pre-defection) faction (i.e., unaffected by the same-tick defection),
while a legality check performed against the POST-apply state (next tick, or directly against the
applied `AuthoritativeState`) reflects the NEW (`Faction.NEUTRAL`) faction. This directly exercises
the phase-order guarantee: `pipeline.py:297` (`"action_routing"`) precedes `pipeline.py:402`
(`"groups"`), both reading the same frozen `state` argument, so `"groups"`'s
`IdentityUpdate(faction_set=...)` cannot retroactively change an already-resolved
`"action_routing"` legality decision within that same tick.

**Other writers to this resource:** N/A — this is a new test file, not a shared resource. The
behavior it tests (phase ordering in `AuthoritativeApplyPipeline.refine()`) is fixed by existing
`run_phase(...)` call order (`pipeline.py:212-402`, confirmed by direct read) and is not modified
by this plan — Step 4 adds test coverage for existing, already-correct ordering, it does not change
the ordering itself.

**Do NOT touch:** `LegalityServiceV2` (`legality.py`) itself — no code change; all 6 cited call
sites (`legality.py:269,451,521,530,543,556`) already read `entity.identity.faction` fresh with no
local caching, confirmed by direct read. Do NOT touch `apply.py:321`'s existing
`pass_hostile`/`_has_hostiles_or_dead_cache` invalidation logic — it is already correct for the
next-tick read case this step documents. Do NOT attempt to re-verify all 31 call sites found in
Investigate individually — this step scopes to proving the phase-order guarantee once, which
covers every site's staleness question structurally (none of the other 25 sites were found to
cache `identity.faction` across ticks beyond what `apply.py:321` already invalidates); a full
per-site re-audit is not required by any AC and is explicitly flagged as unnecessary scope in the
investigation's own Risks section.

**Verify:** `test_faction_change_mid_tick_legality_semantics` (or the name above) — asserts the
specific ordering-derived behavior, not merely "does not crash," per test_plan.md item 3's own
requirement.

**Depends on:** Step 2 (needs the real `faction_set` producer to construct the scenario).

---

### Step 5 — Architecture guard: single authoritative writer for `faction_set`

**Files:** `tests/architecture/test_faction_mutation_write_paths.py` (new)

**Change:** Follow the exact precedent of `tests/architecture/test_social_write_paths.py`
(confirmed pattern via direct read: `_WRITE_PATTERN = re.compile(r'\b(...)\s*=')` scanning all
`src/**/*.py`, an `ALLOWED_FILES` frozenset, one test asserting no file outside the allowlist
contains the write pattern). **Correction, found during architecture review:** `IdentityComponent`
is a frozen dataclass (`src/core/state.py:576`), so a literal `identity.faction = X` attribute
assignment cannot be written against it at all — that pattern can never match anything and would
give false confidence. The realistic bypass this guard must actually catch is a bare `faction=`
keyword argument inside `dataclasses.replace(entity.identity, faction=X, ...)`, exactly the shape
`test_social_write_paths.py`'s own precedent guards against for `public_reputation`/
`regional_reputation` with a bare-field-name pattern. Scan for `faction_set\s*=` and, separately, a
bare `\bfaction\s*=` (NOT `identity\.faction\s*=`) — mirroring
`\b(public_reputation|regional_reputation)\s*=` exactly. `ALLOWED_FILES` must contain exactly:
`src/core/updates.py` (field declaration + `merge()`, `updates.py:227,259`), `src/engine/patches.py`
(the sole authoritative consumer, `patches.py:209`), `src/core/builder.py` (initial-construction
seeding — confirmed real via direct read: `builder.py:171,193` sets `faction` as a constructor
kwarg, not a live mutation), and `src/systems/social_systems/party_lifecycle.py` (this plan's new
trigger, Step 2). Also add `src/replay/fingerprint.py` to the allowlist for the bare `faction`
pattern (Step 1's f-string interpolation reads `entity.identity.faction`, which the bare-word regex
would otherwise flag as a false positive — follow `test_social_write_paths.py`'s own precedent,
which already allowlists `fingerprint.py` for the same reason on `public_reputation`).

**Other writers to this resource:** This step's entire purpose is to enumerate every writer — the
allowlist above IS that enumeration, confirmed via the investigation's `grep -rn "faction_set"
src/` (4 total hits, all accounted for) plus this plan's own re-verification. No other file in
`src/` was found constructing `IdentityUpdate(faction_set=...)` or a bare `faction=` kwarg against
`IdentityComponent`.

**Do NOT touch:** `test_social_write_paths.py` itself (different field, must keep passing
unmodified). Do NOT add `src/engine/apply.py` to the allowlist for a write pattern — it only reads
`u.identity.faction_set is not None` (a comparison, not an assignment) at `apply.py:321`, which the
regex `faction_set\s*=` does not match (`is not None` is not `=`); confirm this during
implementation and do not add it defensively.

**Verify:** `test_faction_set_write_restricted_to_authoritative_writer` (new, per test_plan.md item
7).

**Depends on:** Step 2 (the allowlist is only final once `party_lifecycle.py` is the confirmed
sole trigger file).

---

### Step 6 — Contract doc

**Files:** `docs/world/affiliation_mutation.md` (new)

**Change:** Document, as a `docs/world/` contract doc (per ticket AC #4 and investigation's Docs
Requiring Update section, which confirms no Mechanics Bible chapter exists yet to add this to —
`TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER` owns that separately): (1) the write-path contract
(`IdentityUpdate.faction_set` → `patches.py:209` → `apply.py:321`, pre-existing and unchanged by
this ticket), (2) the trigger — defection via `check_defection()` sets `faction_set =
Faction.NEUTRAL` (Step 2), explicitly noting this is a NEUTRAL-sentinel design, not a
rival-faction-selection design, and that idea 56 (Drifting Loyalty) is the anticipated future
consumer for a non-neutral destination, (3) the `entity_faction_changed` observability event
(pre-existing, unchanged), (4) the mid-tick/next-tick-boundary legality semantics established in
Step 4's Summary reasoning, with the concrete `pipeline.py:297`/`pipeline.py:402` phase-order
citation, (5) a cross-reference to `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER` as the eventual
Bible-chapter home rather than duplicating chapter-level content here.

**Other writers to this resource:** N/A — new doc file, no other writer.

**Do NOT touch:** Do not author Mechanics Bible chapter content (`docs/mechanics/0N_*.md`) — that
chapter does not exist yet and is out of this ticket's scope per its own Out of Scope section.

**Verify:** No pytest coverage required (doc existence is a `done-checker` static check per
test_plan.md item 4). Manually confirm the doc's semantics section matches Step 4's actual tested
behavior before marking this step complete.

**Depends on:** Steps 2 and 4 (must document the actual chosen trigger and actual tested
semantics, not a planned/hypothetical version).

---

### Step 7 — Parity ledger entries

**Files:** `docs/parity_ledger/social_narrative.yaml`, `docs/parity_ledger/combat_movement.yaml`,
`docs/parity_ledger/substrate.yaml`

**Change:** Using `tools/parity_ledger_writer.py` (per repo convention — never a raw YAML edit for
ledger files, per the "Parity-updater full-file YAML rewrite risk" pattern):
- `social_narrative.yaml`: add a new entry (next `SOC-XXX` id) with `text` describing
  "Defection sets defector's `identity.faction` to `Faction.NEUTRAL` via `IdentityUpdate.
  faction_set`", `status: verified`, `test_path` pointing at Step 2's and Step 3's new tests,
  priority `P2` (this is a new mechanic, not a P0 correctness law).
- `combat_movement.yaml`: add a new entry documenting the mid-tick-vs-next-tick-boundary legality
  semantics (Step 4), `test_path` pointing at Step 4's new test.
- `substrate.yaml`: amend `SUB-378`'s `v2_evidence` (existing entry for
  `entity_role_changed`/`entity_faction_changed` wiring) to note a real producer now exists
  (Step 2/3), rather than adding a new entry — this is the same event, now actually firing; do not
  duplicate the entry.

**Other writers to this resource:** These 3 YAML files are also written by `parity-updater` agent
runs from *other* tickets over time (append-only entry additions keyed by unique IDs) and read by
`tools/parity_ledger_writer.py`'s own schema validator plus `done-checker`'s P0 `test_path`
verification. This step does not touch any entry outside `SUB-378` and the 2 newly-added entries —
no other in-flight ticket in this session's working tree touches these 3 files (confirmed via
`git status` at session start: no `docs/parity_ledger/*.yaml` files are currently modified). Do NOT
touch `strategic_cognition.yaml` or `faction.yaml` — per investigation, `intelligence.py`'s 4
`identity.faction` read sites have no behavior change from this ticket (they read fresh, same as
before) and `faction.yaml`'s 15 entries are all `FactionState`-level, not entity-level; adding
entries there would misrepresent what this ticket actually changed. Do NOT touch
`world_dynamics.yaml`'s existing "Spawned entity faction is valid" entry — construction-time only,
unaffected by this ticket's mutation-time change.

**Do NOT touch:** Any ledger file/entry not named above. Do not re-run the "5 of 8" vs "5 of 9"
epic-doc reconciliation here — that is the epic doc's own housekeeping (flagged in investigation,
not this ticket's AC).

**Verify:** `python3 tools/parity_ledger_writer.py` (or its validate mode) confirms schema
validity; `done-checker`'s P0 check (n/a here, all P2) is not blocking, but every `test_path` added
must actually pass when run.

**Depends on:** Steps 2, 3, 4 (test paths must exist and pass before being cited).

## Scope Guards

- Do NOT modify `patches.py:209` or `apply.py:321` — both are already correct and fully wired;
  this ticket's entire job is supplying a real producer, not changing the apply-path.
- Do NOT add a `faction` field to `GroupRecord` (`state.py:659-679`) — the NEUTRAL-sentinel design
  deliberately avoids needing a "destination faction" concept.
- Do NOT wire `SocialContractSystem.resolve_contract_outcome(betrayal=True)` live — confirmed
  dormant, and making it live is a separate, larger decision not implied by this ticket.
- Do NOT touch `FactionInfluenceService.process_conquest_lifecycle()` (`src/world/influence.py`)
  or `FactionDecisionPhase` (`src/engine/faction_decision.py`) — both operate at the
  `FactionState`/region level; connecting them to entity-level `identity.faction` is out of scope.
- Do NOT introduce any loyalty/pressure-accumulation field or logic (idea 56's scope,
  `TCK-20260905-DRIFTING-LOYALTY-SIGNAL`).
- Do NOT touch idea 59/65 scope (`TCK-20260905-HOME-EXILE-REFUGEE-THREADS`).
- Do NOT author the Mechanics Bible chapter (`TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER`'s own
  scope) — only the minimum-viable `docs/world/` contract doc (Step 6).
- Do NOT add any `src/api/` surface for affiliation changes.
- Do NOT re-verify all 31 call sites individually — Step 4's phase-order proof covers the
  staleness question structurally; do not turn this into a 31-site manual audit.
- Do NOT touch `strategic_cognition.yaml` or `faction.yaml` (see Step 7 reasoning).
- Do NOT modify `check_defection()`'s grievance-threshold math, `GroupPhase.resolve()`'s
  leadership-election pass, or any other part of `groups.py` beyond what already correctly merges
  the new `EntityUpdate.identity` field with zero code change.

## Dependency Map

```
Step 1 (fingerprint fix)        — independent
Step 2 (check_defection trigger) — independent
Step 3 (event confirmation test) — depends on Step 2
Step 4 (legality semantics test) — depends on Step 2
Step 5 (architecture guard)      — depends on Step 2
Step 6 (contract doc)            — depends on Steps 2, 4
Step 7 (parity ledger)           — depends on Steps 2, 3, 4
```
Steps 1 and 2 can be implemented in either order or in parallel; everything else sequences after
Step 2 because it needs the real trigger to exist.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — real trigger populates `faction_set` through the authoritative apply-path only | Step 2 | `test_defection_produces_faction_set_neutral_via_apply_path` |
| AC #2 — `entity_faction_changed` fires exactly once per real faction change | Step 3 (no `src/` change; confirmation test only) | `test_entity_faction_changed_fires_once_on_real_defection_trigger` |
| AC #3 — combat/action-legality interaction has documented, tested semantics | Step 4 (test) + Step 6 (doc) | `test_faction_change_mid_tick_legality_semantics` |
| AC #4 — documented in a real, citable doc | Step 6 | N/A (doc-existence, `done-checker` static check) |
| AC #5 — parity-ledger entries added, each with a real `test_path` | Step 7 | validated via the `test_path`s cited (Steps 2/3/4's tests) |
| AC #6 — `src/replay/fingerprint.py` coverage confirmed | Step 1 | `test_fingerprint_changes_when_faction_changes` |

Also: Step 5's architecture guard (`test_faction_set_write_restricted_to_authoritative_writer`) is
not itself an AC but is required by test_plan.md as the anti-drift guard backing AC #1's "never via
direct mutation" clause.

## Anti-Drift Notes

- **`src/replay/fingerprint.py` gap (AC #6) is genuinely this ticket's own scope, not a follow-up
  ticket.** Reasoning: the ticket's own AC #6 text names `src/replay/fingerprint.py` explicitly and
  frames it as "exactly the failure class PR #128's own architecture review caught... do not repeat
  it" — this is a direct instruction to fix it here, not merely disclose it. The investigation
  confirms it is a small, isolated, two-line f-string change (Step 1) with no dependency on the
  trigger design chosen in Step 2, so there is no scope-creep risk in doing it within this ticket.
- **`IdentityUpdate.merge()`'s last-write-wins semantics for `faction_set`
  (`updates.py:258-259`) has no conflict detection.** Since this plan introduces the only real
  producer, no collision exists today — but if a future ticket adds a second producer in the same
  tick, `merge()` will silently take whichever was merged last with no warning. This plan does not
  add conflict detection (out of scope, no second producer exists to make it observable/testable
  today) but the reasoning is recorded here for whoever eventually adds ticket 2 of the epic.
- **Phase-order dependency is load-bearing and undocumented today.** The next-tick-boundary
  legality semantics this plan relies on (`pipeline.py:297` before `pipeline.py:402`) is currently
  an implicit consequence of call order in `refine()`, not an enforced invariant. Step 4's test is
  a regression guard for this ordering, but if `refine()`'s phase order is ever refactored,
  `test_faction_change_mid_tick_legality_semantics` is the test that will catch a semantics change
  — flag this explicitly in the doc (Step 6) so a future phase-reordering change knows to re-check
  it.
- **`check_defection()` remains a pure function** (per its own docstring contract, unchanged by
  Step 2) — the new `identity=IdentityUpdate(...)` in its return value must not cause it to read or
  mutate anything beyond its existing 3 arguments (`group`, `entity`, `tick`).
- **Do not let Step 6's doc content drift from Step 4's actual tested behavior** — write Step 6
  after Step 4's test is green, not from this plan's own predicted semantics, in case
  implementation reveals a nuance this plan's Investigate-time read of `pipeline.py` missed.

## Deviations

- **Step 5's bare `\bfaction\s*=` regex, as literally specified, does not work and had to be
  narrowed further during implementation.** Running it against the real `src/` tree (not just
  the files this plan's own re-verification happened to check) produced 19 false-positive files:
  `\bfaction\s*=` also matches `faction ==` equality comparisons (`src/engine/cognition.py`,
  `src/engine/combat.py`, `src/engine/legality.py`, `src/systems/world_systems/intake.py`,
  `src/world/environment.py` — a regex bug, `=` inside `==` is matched), local read-only
  variables coincidentally named `faction` (`src/api/presenters/state_presenter.py`,
  `src/observability/understanding/balance/engine.py`,
  `src/observability/warehouse/provenance_lookup.py`), an f-string label
  (`src/entities/identity_resolver.py`, same shape as `fingerprint.py`'s own accepted exception),
  and — the real finding — dozens of legitimate `V2EntityBuilder(...).identity(faction=...)`
  construction-time builder-DSL calls scattered across world-generation/assembly files
  (`src/certification/scenarios.py`, `src/perf/scenarios.py`,
  `src/systems/world_systems/generator.py`, `src/worldgeneration/generator.py`,
  `src/worldbuilding/compiler.py`, `src/worldassembly/resolver.py`,
  `src/worldassembly/entity_spawner.py`, `src/entities/archetype_factory.py`,
  `src/lab/workflows/generate_simulation_setup.py`, `src/core/state.py`). Unlike
  `public_reputation`/`regional_reputation` (rare, concentrated identifiers), "faction" is a
  common word/kwarg name used constantly across construction-time entity-building code that has
  nothing to do with a live mutation bypass of the frozen `IdentityComponent` dataclass — this
  plan's own investigation grep evidence for this step was scoped too narrowly (it checked only a
  handful of files by direct read, not a full `grep -rn "faction\s*=" src/`) and did not surface
  this before Plan was approved.
- **Fix applied:** narrowed the second guard to the actual realistic bypass shape the plan's own
  text already named — `dataclasses.replace(<identity-component-expr>, faction=X, ...)` — via
  `replace\([^)]*?faction\s*=(?!=)`, plus a `(?!=)` fix so `==` no longer matches. Verified via
  direct read that this exact shape occurs nowhere in `src/` outside
  `src/engine/patches.py::IdentityPatch.apply()`'s own authoritative
  `replace(new_id, ..., faction=fac, ...)` construction. `IDENTITY_REPLACE_BYPASS_ALLOWED_FILES`
  is therefore just `{"src/engine/patches.py"}`, not the originally-planned
  `BARE_FACTION_ALLOWED_FILES` set (which would have needed all 19 false-positive files added,
  defeating the guard's purpose). The renamed test is
  `test_identity_replace_faction_bypass_restricted_to_allowlist` (was
  `test_bare_faction_keyword_restricted_to_allowlist` in this plan's original Step 5 text). The
  first guard (`faction_set\s*=`, `FACTION_SET_ALLOWED_FILES`) matched the plan exactly with zero
  false positives and required no change.
- **SUB-378's amendment also updated `support_boundary`, not only `v2_evidence` as Step 7's text
  named.** The existing `support_boundary` field contained a now-factually-false claim
  ("`entity_role_changed`/`entity_faction_changed` cannot fire in ANY current code path") that
  this ticket's own change directly contradicts for `entity_faction_changed`; leaving it
  unamended would have left the ledger self-contradictory against the new `v2_evidence` note and
  the new SOC-273 entry. Both amendments were made via `tools/parity_ledger_writer.py::
  write_entry`, never a raw YAML edit.

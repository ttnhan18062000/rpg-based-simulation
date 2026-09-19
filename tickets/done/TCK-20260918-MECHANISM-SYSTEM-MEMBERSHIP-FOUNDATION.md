---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION
phase: done
date: 2026-09-18
tags: [architecture, documentation, schema]
---

# TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION

## Title
Revive the `system` tier as declared membership on mechanisms — a managed registry, many-to-many, with
missing-system and orphan-system validation

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The `system` tier was rejected **as designed** —
`TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION` found that deriving membership from a
declared root's `depends_on` ancestors produced sets nobody would recognise, because **`depends_on`
encodes *prerequisite* while a system encodes *collaboration*.**

**This is a different mechanism, not a retry of that one.** A system becomes a **membership declared on the
mechanism**. No roots, no traversal, no use of `depends_on` at all — which removes all three of the
investigation's blockers: bad thematic fits (membership is declared by intent), unaudited edges
(edges are not consulted), and non-unique roots (there are none).

**Why it is needed**, in the user's framing: to review what features the simulation actually has, and
which are loose versus deep, **without reading all 93 mechanisms individually.** A mechanism must stay
the smallest unit and cannot be made more abstract, so the grouping belongs in a layer above it.

The motivating case, run by hand during scoping: entity progression spans **15 mechanisms** —
`xp_leveling`, `evolution`, `progression_conversion`, `breakthrough_bonuses`, `attributes_biology`,
`derived_stats`, `skill_unlocks`, `class_assignment`, `race_archetype`, `genetics_aptitude`,
`aging_death`, `strategic_learning_bias`, `build_diversity`, `readiness_speed_scaling`,
`status_effects`. That list was **hand-typed in a shell command** — unreproducible, unreviewed, and
different for whoever types it next. That is the gap this ticket closes.

## Scope

### 1. A managed `systems` registry — extensible, not frozen
Systems are registered and validated, **but new systems can be added.** The original map will not be
correct forever, so a frozen vocabulary is wrong; an unmanaged free-text field is equally wrong,
because it drifts into `combat` / `combat_system` / overlapping names within weeks.

Follow the repo's existing registry pattern (`registries/tag_registry.jsonl`,
`layer_registry.jsonl`), with the difference that entries may be **added** as understanding improves.

### 2. `systems: []` on each mechanism — many-to-many
Declared on the mechanism, not held as a list in the systems registry. A mechanism may belong to
several systems.

**Declared-on-mechanism, not list-in-registry, is deliberate:** a separate membership list is a second
place holding mechanism ids, and a renamed mechanism leaves a dangling reference. A reference on the mechanism cannot
dangle, and adding a mechanism forces the question *"which system?"* at the point of creation.

### 3. Two validation invariants
- **No missing system** — every value in any `systems: []` resolves to a registered system.
- **No orphan system** — every registered system has at least one mechanism declaring it. A
  declared system with zero members is dead vocabulary and should fail rather than accumulate.

### 4. Mechanisms with no system render as `unassigned`
A mechanism in no system appears explicitly as unassigned, never omitted — the same rule as
`unverified`. A review surface that silently drops mechanisms with no system under-reports exactly what it
exists to show.

### 5. Initial membership pass — large to small
Assign all 93 mechanisms. **Start with few broad systems that cover everything, then split.**

Coverage before granularity: starting small-and-precise risks whole areas having no system at all,
whereas splitting a too-broad system later is safe and loses nothing. Do not aim for a target count —
if a system turns out to contain two unrelated things, that is a split to make later, not a reason to
pre-fragment now.

## Out of Scope
- **Rollup views and counts.** Deferred to a follow-up plan once the mapping and registry exist.
  Noted below because the eventual constraint is already known.
- **Computing anything from system membership.** Priority stays derived from `depends_on`; verification
  stays per mechanism. See Assumptions #2.
- **The `axis` tier.** Separate, and already carried by
  `TCK-20260917-MECHANISM-AXIS-ATTACHMENT-POINT-MECHANISMS-NOT-SYSTEMS`.
- **Reviving derived membership** in any form, including multi-root.
- **Splitting systems finer** than the initial broad pass. That is the expected follow-up, not this
  ticket.

## Acceptance Criteria
1. Systems are registered, validated, and **addable** — adding a new system is a supported operation,
   not a schema change.
2. `systems: []` exists on mechanisms and accepts multiple values.
3. Both invariants fail on deliberately invalid fixtures — an unregistered system reference, and a registered
   system with no members. **Not** proven by a clean pass on valid data.
4. All 93 mechanisms have a declared system, or explicitly listed as `unassigned` with a reason.
5. A mechanism with no system is proven to render by a test that **asserts its presence**, not by checking
   the assigned rows look right — an omission bug is invisible to the latter.
6. Nothing derives a ranking, verdict or priority from system membership.

## Related Tickets
- `TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-INVESTIGATION` — done; found the value/cost case
  for building this real (2 of 3 test systems cleared the value bar against baseline) and seeded
  the initial 7-system, 93-mechanism vocabulary this ticket's own §5 pass should start from
- `TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION` — rejected the derived design; this
  supersedes its conclusion **for the declared-membership mechanism only**, not for derivation
- `TCK-20260917-EPIC-MECHANISM-TIER-MODEL` — closed; this reopens the tier by a different route
- `TCK-20260917-MECHANISM-AXIS-ATTACHMENT-POINT-MECHANISMS-NOT-SYSTEMS` — the tier above
- `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT` — **no dependency**; membership does not use edges

## Related Docs
- `docs/plans/mechanism_tier_model_initiative.md` — **needs updating**, see Implementation Notes
- `docs/plans/mechanism_identity_and_change_taxonomy.md` — the identity rule keeping mechanisms atomic

## Related Stored Artifacts
- `stored_artifacts/TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION/` — the four derived
  candidate sets and why each failed; read before assigning membership, since they show what a bad grouping looks
  like

## Related Code Areas
- `registries/mechanisms.yaml`
- `tools/mechanism_registry/registry.py` — validation lives here
- `tools/mechanism_registry/mechanism_registry_completeness_check.py` — already enumerates
  mechanisms; the natural place for an unassigned check

## Assumptions / Open Questions
1. **System membership has no mechanical backing, and that is accepted deliberately.** Nothing in the code
   says "this belongs to progression." The cost reasoning is the user's and it is sound: the
   code→mechanism mapping is far larger than mechanism→system, so automate the first and hand-author
   the second. State the absence of backing where systems are defined, so it is visible rather than
   forgotten — the same disclosure axes carry.
2. **Membership must remain read-only to every computation.** The moment a ranking or verdict derives from
   membership, unbacked judgement becomes load-bearing. Systems are a review lens.
3. **The known follow-up constraint:** when rollups are built, they must report **counts, never a
   single badge** — *progression: 15 mechanisms, 5 verified, 1 contradicted, 2 gated off, 10
   unverified*. A summary status would destroy the loose-versus-deep signal that is the entire
   purpose. Recorded now so the follow-up does not have to rediscover it.
4. How many systems the broad pass yields is unknown and deliberately not targeted. If it lands very
   high, that is a signal the grouping is not working — report it rather than forcing a number.
5. **Hard requirement for any rollup/review view, found by
   `TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-INVESTIGATION`: report every per-system rate
   against the whole-registry baseline, never in isolation.** That investigation's own `faction`
   test case looked like a real finding (77% unverified, 23% `implemented_by`) until compared
   against the corpus-wide baseline (74% / 30%) and found statistically indistinguishable from
   average — a raw rate without a baseline isn't a finding, it's the corpus average wearing a
   system's name. **This generalizes past this one rollup**: it is the same failure shape as the
   attribution ratchet reporting a percentage with no comparison and firing on legitimate
   activity, and SimQ reporting green because it measured at a scale where the real change
   couldn't appear — a number presented without the context that makes it mean something. Any
   future report built on top of declared membership must carry this requirement, not just the
   first rollup view.
6. **Multi-membership is real but rare (8/93 = 8.6%, per the same investigation), and that is the
   argument to keep the declared-on-mechanism list field as-is, not to simplify it away.** A
   single-valued field plus a hand-maintained exception list for the 8 that don't fit would put
   membership in two places — the field and the exception list — which is exactly the
   second-source-of-truth pattern this ticket's own §2 rationale already rejects for a
   registry-side membership list. The list field already handles 0, 1, or many memberships
   without needing a second mechanism; 8.6% is small enough to keep, not small enough to special-
   case.
7. **The investigation's own progression assignment (independently arriving at exactly 15
   mechanisms before re-reading this ticket's own worked example) is real corroborating evidence,
   not just a nice coincidence** — it is what makes the investigation's other six system
   assignments (including the two, `combat` and `economy`, that passed the value test) credible
   rather than fitted to a known answer.

## Implementation Notes
**`docs/plans/mechanism_tier_model_initiative.md` must be updated, not duplicated.** Its current
status block (on the `mechanism-tier-model-disposition` branch) says the tier was rejected and the
doc is kept "not as a live implementation plan." That becomes wrong once this lands: the tier is
live again by a different mechanism.

Rewrite the block so the doc reads as one narrative — the model, the derived approach and why it
failed, and the declared-membership approach now adopted. **Do not create a second plan doc for the system tier**;
that would put one subject in two documents, which is the duplication rule this effort exists to
enforce. The rejected-derivation finding is expensive and must survive the rewrite.

## Test Summary
- New: `tests/unit/tools/test_system_registry.py` (18 tests, mirrors `test_layer_registry.py`),
  11 new tests in `tests/unit/tools/test_mechanism_registry.py` (invariants 9/10, both directions
  each, plus `mechanisms_by_system()`'s own grouping and unassigned-presence tests).
- New: `tests/unit/tools/conftest.py` — autouse fixture isolating the new orphan-system invariant
  from every pre-existing fixture-based test (see `staging_artifacts/.../investigation.md` for
  why this is structurally necessary, not a workaround).
- Regression: `tests/unit/tools/` filtered to `mechanism or system_registry` — 202/202 passed.
- `make mechanism-registry-validate` — `OK: ... valid, 93 mechanisms`.
- Full detail in `staging_artifacts/TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION/test_plan.md`.

## Files Changed
- `registries/system_registry.jsonl` — new, 7 systems registered.
- `tools/mechanism_registry/system_registry.py` — new, mirrors `tools/layer_registry.py`.
- `registries/mechanisms.yaml` — `systems: []` added to all 93 mechanisms.
- `tools/mechanism_registry/registry.py` — invariants 9/10 (missing/orphan system), new
  `mechanisms_by_system()` query, `_load_system_registry` import, docstring invariant-count fix.
- `tools/mechanism_registry/__init__.py` — re-export `mechanisms_by_system`.
- `tests/unit/tools/conftest.py` — new.
- `tests/unit/tools/test_mechanism_registry.py` — 11 new tests, 2 existing tests updated to
  restore the real system registry via `monkeypatch`.
- `tests/unit/tools/test_system_registry.py` — new, 18 tests.
- `docs/plans/mechanism_tier_model_initiative.md` — status block updated (not duplicated) to
  record the foundation landing and the value investigation's own "proceed with a required
  change" verdict.
- `staging_artifacts/TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION/{plan,investigation,test_plan}.md` — new.

## Completion Summary
**All 6 acceptance criteria met.** Systems are registered, validated, and addable (AC #1) via
`registries/system_registry.jsonl` + `system_registry.py`, mirroring the established
`layer_registry`/`tag_registry` pattern exactly. `systems: []` exists on every mechanism and
accepts multiple values (AC #2, exercised by 8 real multi-system mechanisms and a dedicated
test). Both new invariants are proven failing on deliberately invalid fixtures, never merely
passing on clean data (AC #3). All 93 mechanisms declare a real system — zero unassigned,
confirmed by a pinned regression test, not just a clean validate() pass (AC #4). A mechanism
with no system is proven to render under `mechanisms_by_system()`'s own `"unassigned"` key by a
test asserting its own presence in the output (AC #5). Nothing derives a ranking, verdict, or
priority from system membership — the two new invariants only check structural consistency, and
`mechanisms_by_system()` is a pure, read-only query (AC #6).

**The one real, unanticipated finding**: the orphan-system invariant is not fixture-testable the
same way every prior invariant in this file was, because its subject (a registered system having
zero real members) is a whole-corpus property — it needs a CLOSED universe (every system it can
see has a member within that same universe), not necessarily the real, complete mechanism set. A
small synthetic fixture works fine as long as it's complete and self-contained on its own terms;
what actually broke was the pre-existing tests' shared 2-3-mechanism fixtures being a PARTIAL slice
of the real 93-mechanism/7-system registry rather than a closed universe of their own — 18
pre-existing tests broke as a direct, immediate signal of this before any fix was written, not
discovered later. Solved with a scoped, autouse test fixture rather than either weakening the
invariant or forcing every unrelated test to carry full-registry weight.

**Generalizable lesson for the next invariant author**: every invariant in `registry.py::validate()`
before this one was compositional — a self-contained property of the `data` dict already passed
in, true or false on any arbitrary valid subset of it. The orphan-system invariant is the first
whole-corpus invariant added to this function (a property of the full mechanism-x-system universe,
not of any one mechanism or slice). That distinction, not just "add a fixture," is the reusable
takeaway — see the comment block directly above invariants 9/10 in `tools/mechanism_registry/registry.py`
for the full reasoning, and `tests/unit/tools/conftest.py` for the fix shape (autouse empty-registry
default, explicit opt-in restoration per test). A future whole-corpus-shaped invariant should expect
the same non-compositionality rather than assuming it will behave like every invariant before it.
Coverage for invariant 10 is not limited to the two real-registry tests (`test_real_registry_passes_validation`,
`test_real_registry_systems_all_resolve`) — `test_validator_rejects_registered_system_with_zero_members`
and its sibling accept-side tests exercise it directly on synthetic data, because each defines its
own complete, self-contained registered-systems/mechanism-list pair via `_fixture_registry()` --
a closed universe in its own right, not a partial slice of the real 93-mechanism/7-system one --
which is exactly what makes a small synthetic fixture usable here despite the property's own
non-compositionality.

`docs/plans/mechanism_tier_model_initiative.md` updated in place, not duplicated, per this
ticket's own Implementation Notes instruction — the rejected-derivation history and the revived
declared-membership design now read as one coherent narrative including this ticket's own landing.

---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED
phase: done
date: 2026-09-13
tags: [cognition, social]
---

# TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED

## Title
Dissolved groups are removed from state outright — nothing captures whether the recruitment that formed them worked out

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Filed while implementing `TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING` (contract →
group reverse lookup), per peer's explicit instruction to disclose this as a real, separate gap
rather than leave it in that PR's description.

`GroupSystem.update_groups()` (`src/systems/world_systems/groups.py`) removes a group from
`state.groups` entirely (`groups_remove`) the moment it drops below 2 members — confirmed via
grep: no code path anywhere retains a dissolved group in a queryable form afterward.
`GroupRecord.dissolution_tick` (`src/core/state.py`) is a declared field that no write site ever
sets — dead at the data-model level, not just unused.

This means `GroupSystem.find_group_for_contract()` (the function this ticket's origin added) can
only ever answer "is this contract's recruitment currently a live group" — the moment the group
dissolves (recruit dies, contract expires, cohesion breaks, betrayal, whatever), the record is
gone and the question "did this recruitment ever produce a group, and how did it end" becomes
unanswerable after the fact. That is the real blocker for any future contract-outcome
differentiation (e.g. distinguishing "recruit died in the field" from "recruit betrayed the
contract" from "contract simply expired") — durable event history, not a live-state query, is
what that kind of work would need.

## Scope
This ticket is scoped as **the question, not a mechanism**: should group dissolution capture a
durable outcome record, and if so, what should it contain and where should it live? The right
shape (a lightweight terminal-state event, a `dissolution_tick` + `dissolution_reason` populated
in place before removal, a separate durable log, something else) depends on what the eventual
contract-outcome/differentiation work actually needs to query — which is not designed yet. Do not
build a specific mechanism speculatively; investigate what durable-state precedents exist elsewhere
in the codebase for "an entity/record left the active set but its outcome still matters"
(e.g. how entity death outcomes are recorded, if at all) and bring options back before implementing.

## Out of Scope
- Any specific persistence mechanism, chosen without first confirming what the differentiation
  work needs.
- Re-deriving outcomes retroactively from other logs (chronicle/event history) as an alternative
  to capturing it at dissolution time — that's a legitimate option to weigh, not a foregone
  conclusion, and should be evaluated alongside the others during investigation.
- Actually building contract-outcome differentiation (betrayal vs. death vs. expiry) — this ticket
  only unblocks that by making the outcome observable, it doesn't do the differentiation itself.

## Acceptance Criteria
- [x] Investigation surveys existing durable-outcome precedents in the codebase (if any) before
      proposing a shape. Done: ClanState.dissolved_tick and CampState.active surveyed and
      confirmed as the two real, live precedents; WorldEventCategory.CAMP_CLEARED/PARTY_ABANDONED
      checked and found to be dead schema with no real producer.
- [x] A concrete design question (not yet a decision) is brought to peer/user: what to capture at
      dissolution, and where it should live, with real options and a recommendation. Done: 3
      options with a recommendation (Option 1), sent for review.
- [x] No implementation proceeded until that design question was answered. Honored: investigation
      and design-question phase made zero source/test changes; implementation began only after
      peer approved Option 1 with 2 explicit conditions (per-consumer audit, outcome-semantics
      kept separate).

## Related Tickets
- `TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING` (origin — implementing the
  contract→group reverse lookup surfaced this as the boundary of what that lookup can answer)

## Related Docs
None yet.

## Related Stored Artifacts
`staging_artifacts/TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED/investigation.md` — full
precedent survey (Clan/Camp both retain-with-terminal-marker, real and live;
`WorldEventCategory.CAMP_CLEARED`/`PARTY_ABANDONED` initially looked usable but verified to have no
real producer anywhere — corrected before it became a recommendation), 3 options with a
recommendation, and a Resolution section recording peer's approval of Option 1 plus the 2 real
consumer hazards the audit found. `plan.md` has the full 11-consumer audit table. `test_plan.md`
has the complete test breakdown.

## Related Code Areas
- `src/systems/world_systems/groups.py` (`GroupSystem.update_groups()`, where `groups_remove`
  drops a dissolved group from `state.groups` with no trace left behind)
- `src/core/state.py` (`GroupRecord.dissolution_tick` — a declared, never-written field)

## Assumptions / Open Questions
- **Resolved**: the real capture mechanism is retain-with-terminal-marker (Option 1), approved by
  peer/user and built.
- **Still open, deliberately deferred to a separate future ticket**: what a dissolution *outcome*
  should actually capture beyond timing (e.g. distinguishing "recruit died" from "betrayed the
  contract" from "contract simply expired") — `dissolution_tick` alone answers "when," not "why."
  Peer's own explicit condition: bring this back separately, don't decide it inside this ticket.

## Implementation Notes
**Phase 1 (2026-09-14): investigation, blocked on design review — no code changed.** Summary (full
detail in staging_artifacts/investigation.md):
- Surveyed 2 real, live durable-state precedents for "record left the active set but its outcome
  still matters": `ClanState.dissolved_tick` and `CampState.active` — both use the same shape:
  **stop deleting the record, set an in-place terminal field, keep it forever.**
- Initially treated `WorldEventCategory.CAMP_CLEARED`/`PARTY_ABANDONED` as an existing, ready-made
  mechanism (both declared in the schema, `PARTY_ABANDONED` even has an orchestrator weight-table
  entry) — **verified directly and found neither has a real producer anywhere in `src/`**;
  `CampService.resolve_camp_clearing()` only sets `active_set=False`, no event emitted. Corrected
  before it became a recommendation, not after.
- Found that `GroupSystem.find_group_for_contract()`'s own docstring already names this exact
  ticket and already assumes the fix looks like "stop removing dissolved groups" — a strong,
  pre-existing signal for which option fits.
- 3 options laid out, **Option 1 (retain-with-terminal-marker) recommended**, per this ticket's own
  acceptance criteria calling for a recommendation. Design question sent to peer/user for review.

**Phase 2 (2026-09-14): Option 1 approved and built**, with peer's 2 explicit conditions honored:
- `GroupSystem.update_groups()`'s 2 dissolution branches now append
  `dataclasses.replace(group, dissolution_tick=state.tick)` to `groups_add_or_update` instead of
  `g_id` to `groups_remove` — reuses the existing whole-record replace-in-place mechanism, no new
  `StateUpdate` schema. Added a top-of-loop guard skipping already-dissolved groups, required to
  protect against `get_relevant_group_ids()`'s own `force_full_scan`/no-dirty-set fallback (which
  returns ALL of `state.groups.keys()`, including every retained dissolved group).
- **Full per-consumer audit of all 11 `state.groups` readers, individually, per peer's explicit
  condition** (not just assumed safe): 2 real hazards found and fixed —
  `GroupPhase.resolve()` (`src/engine/pipeline_phases/groups.py`) builds its own relevant-group-id
  set directly from `state.groups.keys()`, bypassing dirty-tracking entirely, running leadership-
  election and defection checks against every group found there; `CooperationPhase.execute()`
  (`src/domains/cooperation/phase.py`) iterates all groups with no liveness check, applying an
  "abandoned" trust/grudge social penalty to a dissolved group's former members. Both fixed with
  the same `dissolution_tick is not None: continue` guard. The remaining 9 consumers were checked
  and confirmed safe with no change needed (2 improved for free — checkpoint/fingerprint now
  correctly preserve dissolved-group history instead of losing it); full table with per-file
  reasoning in plan.md.
- `find_group_for_contract()`'s own docstring updated to reflect that it now answers the question
  after dissolution too.
- Outcome-semantics (what `dissolution_tick`/a future reason field should actually mean) kept as a
  separate question, per peer's second condition — not decided inside this ticket.

## Test Summary
See staging_artifacts (→ stored_artifacts) `test_plan.md` for the full breakdown. 5 new tests
(mechanism retention, force-full-scan guard, `find_group_for_contract()` post-dissolution, both
consumer-hazard regressions), 4 existing tests updated from asserting delete-on-dissolve to
retain-with-marker. Full group/cooperation/faction regression: 604 passed. Full fast-tier sweep
(`tests/unit tests/integration tests/architecture -m "not slow and not extra_slow"`): 6523 passed,
9 skipped, 95 deselected, 7 failed — the same 7 pre-existing, unrelated failures already documented
in the cognition-hazard ticket's own closure this batch (`tests/unit/domains/progression/` recipe/
material-lookup tests, zero relation to group dissolution, confirmed passing in isolation there).

## Files Changed
- `src/systems/world_systems/groups.py` — retain-with-terminal-marker mechanism +
  `force_full_scan` guard + `find_group_for_contract()` docstring update.
- `src/engine/pipeline_phases/groups.py` — dissolved-group skip in both leadership-election and
  defection passes.
- `src/domains/cooperation/phase.py` — dissolved-group skip in cohesion evaluation.
- `tests/unit/social/test_groups.py` — 2 new tests.
- `tests/unit/social/test_domain_7_social.py` — 1 new test.
- `tests/unit/social/test_group_lifecycle_fields.py` — 2 new tests.
- `tests/unit/social/test_social_phase7.py`, `test_party_agency.py`, `test_phantom_leader.py` —
  updated assertions (delete-on-dissolve → retain-with-marker).
- `staging_artifacts/TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED/{investigation,plan,test_plan}.md`.

## Completion Summary
Decided and built Option 1 (retain-with-terminal-marker, mirroring `ClanState.dissolved_tick`/
`CampState.active`) for dissolved-group outcome capture, after a peer/user review cycle that
corrected an initial wrong assumption (that `WorldEventCategory.CAMP_CLEARED`/`PARTY_ABANDONED`
were usable existing mechanisms) before it shipped as a recommendation. The per-consumer audit
peer required found 2 real hazards the mechanism alone would not have caught — both fixed. Groups
are now retained forever with `dissolution_tick` set rather than deleted, and
`find_group_for_contract()` (the function this whole investigation traces back to) now correctly
answers "did this recruitment ever produce a group, and how did it end" after dissolution, closing
the gap the origin ticket first surfaced. Outcome-semantics (what "how did it end" should actually
capture beyond timing) remains open, by design, as a separate future question.

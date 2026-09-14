# Test Plan — TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED

## New tests

- `tests/unit/social/test_groups.py::test_group_system_retains_dissolved_groups_with_terminal_marker_not_deleted` — `GroupSystem.update_groups()` marks `dissolution_tick` in place via `groups_add_or_update`, never populates `groups_remove`, and the record survives `ApplyPath.apply_generation()` still present in `state.groups`.
- `tests/unit/social/test_groups.py::test_group_system_skips_already_dissolved_groups_under_force_full_scan` — direct regression for the most structural hazard: an already-dissolved group present under `force_full_scan=True` is untouched (no re-write, no entity updates for its now-absent members).
- `tests/unit/social/test_domain_7_social.py::test_find_group_for_contract_answers_the_question_after_dissolution` — the origin ticket's own real need: dissolve a group tied to a real contract, apply, then confirm `find_group_for_contract()` returns the dissolved record (not `None`) with `dissolution_tick` set — proving the fix's actual value, not just the mechanism.
- `tests/unit/social/test_group_lifecycle_fields.py::test_group_phase_skips_already_dissolved_group_in_leadership_and_defection_passes` — regression for the most severe consumer hazard found (`GroupPhase.resolve()` builds its own group id set directly from `state.groups.keys()`, bypassing dirty-tracking entirely).
- `tests/unit/social/test_group_lifecycle_fields.py::test_cooperation_phase_skips_already_dissolved_group_cohesion_evaluation` — regression proving a dissolved group's former (still-alive) member no longer receives the "abandoned" trust/grudge penalty every tick.

## Updated tests (asserted the old delete-on-dissolve behavior; now assert retain-with-marker)

- `tests/unit/social/test_social_phase7.py::test_contract_expiration_resolves_and_dissolves`
- `tests/unit/social/test_party_agency.py::test_party_leadership_loss_dissolution`
- `tests/unit/social/test_party_agency.py::test_party_member_abandonment_on_distance`
- `tests/unit/social/test_phantom_leader.py::test_phantom_leader_bug`

`tests/unit/social/test_groups.py::test_group_dissolution` was NOT changed — it exercises
`ApplyPath.apply_generation()`'s general-purpose `groups_remove` mechanism directly (a raw
`StateUpdate(groups_remove=[...])`), which is untouched by this change; only
`GroupSystem.update_groups()` stopped using it for this specific cause.

## Regression

Ran under `.venv313` (CI parity), `-m "not slow and not extra_slow"`:
- Full group/cooperation/faction-related suite (`tests/unit/social/`,
  `tests/unit/domains/cooperation/`, `tests/unit/movement/`,
  `tests/integration/campaigns/`, `tests/integration/domains/cooperation/`,
  `tests/integration/optimization/`,
  `tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py`,
  `tests/unit/domains/faction/`, `tests/simulation_quality/test_clan_reputation_witnessed_betrayal.py`,
  `tests/simulation_quality/test_clan_membership_and_defection_corpus.py`,
  `tests/architecture/test_clan_reputation_write_paths.py`): **604 passed**.
- Full fast-tier sweep (`tests/unit tests/integration tests/architecture -m "not slow and not
  extra_slow"`): **6523 passed, 9 skipped, 95 deselected, 7 failed** — the same 7 pre-existing,
  unrelated failures already documented in the cognition-hazard ticket's own closure this batch
  (`tests/unit/domains/progression/` recipe/material-lookup tests, zero relation to group
  dissolution, confirmed passing in isolation there).

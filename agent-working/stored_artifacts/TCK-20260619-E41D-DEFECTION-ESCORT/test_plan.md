# Test Plan — TCK-20260619-E41D-DEFECTION-ESCORT

## Scope
Unit tests for defection mechanics and escort route scoring. Integration smoke test for 600-tick narrative ledger presence.

## Unit Tests (tests/unit/social/test_party_lifecycle.py, appended)

### AC1 — test_betrayal_desertion_fires_on_high_grievance
- Build a GroupRecord with 3 grievances in grievance_log for entity 11
- Call `PartyLifecycleService.check_defection(group, entity_11, tick=50)`
- Assert: returns updated_group with 11 removed from member_ids
- Assert: returns BetrayalDesertionEvent with event_type="betrayal_desertion", entity_id=11, group_id=group.id
- Assert: returns EntityUpdate with social.notoriety_delta == 2.0

### AC2 — test_betrayal_desertion_no_fire_below_threshold
- Build GroupRecord with 2 grievances (threshold is 3)
- Call check_defection
- Assert all returns are None (no defection)

### AC3 — test_betrayal_desertion_dissolution_on_single_member
- Group starts with 2 members; one defects
- After defection updated_group should have dissolution_tick set (not None)

### AC4 — test_escort_target_route_scores_above_survival
- Build entity with group where escort_target_id is set and entity is NOT the target
- Score a PROTECT_TARGET route and an OWN_SURVIVAL route
- Assert: PROTECT_TARGET score > OWN_SURVIVAL score (by at least the +3.0 vs -1.0 delta)

### AC5 — test_escort_scoring_skipped_for_escort_target_itself
- Build entity == escort_target_id
- Score PROTECT_TARGET and OWN_SURVIVAL routes
- Assert: no escort bonus/penalty applied (target doesn't protect itself)

### AC6 — test_escort_scoring_skipped_when_no_escort_target
- Group exists but escort_target_id = None
- Assert: PROTECT_TARGET scores normally without bonus

## Commands
```bash
pytest tests/unit/social/test_party_lifecycle.py -x -v
pytest tests/integration/scenarios/test_party_lifecycle.py -x -v -m slow  # if exists
```

## Edge Cases
- Empty grievance_log → no defection
- Leader defecting: ticket says "remove entity from group.member_ids" — leader can defect (leader election from E41B handles the next tick; or dissolution)
- Defecting entity not in state.entities → skip gracefully
- Group with 1 member → dissolution_tick set immediately on defection

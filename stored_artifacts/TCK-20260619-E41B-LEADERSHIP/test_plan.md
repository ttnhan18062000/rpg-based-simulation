---
ticket_id: TCK-20260619-E41B-LEADERSHIP
phase: test_plan
date: 2026-06-21
---

# Test Plan — TCK-20260619-E41B-LEADERSHIP

## Test File

`tests/unit/social/test_party_lifecycle.py`

---

## Required Tests

### AC1 — Leadership election picks highest sociability (diff ≥ 0.2)

**`test_leadership_election_picks_highest_sociability`** (required by ticket)
- Group with leader (sociability=0.3) and one member (sociability=0.6).
- Diff = 0.3 ≥ 0.2 threshold.
- `check_leadership()` at interval boundary returns a new `GroupRecord` with `leader_id` changed to the high-sociability member.
- Returned event is a `LeadershipChangedEvent` with correct old/new leader IDs.

### AC2 — No election when sociability diff < 0.2

**`test_leadership_no_election_when_diff_below_threshold`**
- Leader sociability=0.5, best member sociability=0.65. Diff=0.15 < 0.2.
- `check_leadership()` returns updated `GroupRecord` with same `leader_id`, updated `last_leadership_check_tick`.
- No event returned.

### AC3 — Interval gate: skip when not enough ticks have passed

**`test_leadership_skips_before_interval`**
- `last_leadership_check_tick=50`, current tick=100, `LEADERSHIP_CHECK_INTERVAL=100`.
- `check_leadership()` returns `None` (no update needed yet).

### AC4 — Leader's own sociability is included in candidate pool

**`test_leadership_current_leader_is_candidate`**
- Leader (sociability=0.9) vs member (sociability=0.6). Leader still has highest.
- No leader change; check tick updated.

### AC5 — Members absent from state.entities are skipped

**`test_leadership_skips_missing_members`**
- `member_ids` includes an entity ID not in the provided member list.
- Should not raise; missing entity is silently skipped.

### AC6 — LeadershipChangedEvent has correct payload

**`test_leadership_event_payload`**
- Verify event has `group_id`, `old_leader_id`, `new_leader_id`, `morale_delta` in payload.
- `event_type == "leadership_changed"`, `event_category == "social"`.

---

## Run Command

```bash
pytest tests/unit/social/test_party_lifecycle.py -x -v
```

---

## Regression Tests

Existing tests that must remain passing:
```bash
pytest tests/unit/social/test_group_lifecycle_fields.py -x -v
pytest tests/unit/social/test_party_coordination.py -x -v
pytest tests/unit/social/test_groups.py -x -v
```

# Test Plan — TCK-20260913-RAID-MOB-PERMANENT-PROJECT-CAPACITY-EXCLUSION

**Blocked, same reason as plan.md — no implementation to test yet.** If Option 2 or 3
(investigation.md) is chosen, the ticket's own acceptance criteria already names the minimum real
coverage required: "real test coverage that a surviving raid mob's project capacity is restored,
not just that it starts at zero" — i.e. a test must drive a raid mob through spawn → whatever the
chosen "concluded" signal is → assert `max_active_projects` is back to its class default, not just
assert the spawn-time value is 0 (already covered by existing tests). Filled in once a direction is
picked.

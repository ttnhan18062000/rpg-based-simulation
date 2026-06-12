---
ticket_id: TCK-20260612-QUESTS-CONTRACT
phase: investigation
---

# Investigation: Quests Contract

## Key Findings
- No Compliance IDs in src/quests/ files
- QuestStatus: ACTIVE(1), COMPLETED(2), REWARDED(3), REWARD_PENDING(4)
- QuestKind: HUNT, GATHER, EXPLORE, LIBERATE, BOUNTY
- QuestState extends ProjectState (frozen dataclass); stored on EntityState
- QuestService: all @staticmethod, returns new QuestState via dataclasses.replace()
- No expiry logic — quests stay ACTIVE until completed or removed
- QuestGenerator.generate() is deterministic: DeterministicRNG(seed)
- Phase 14 = Objective Reward (PROG-084) applies rewards — quest system itself does not mutate state
- templates.py: per-kind template dict with subject_options for name generation

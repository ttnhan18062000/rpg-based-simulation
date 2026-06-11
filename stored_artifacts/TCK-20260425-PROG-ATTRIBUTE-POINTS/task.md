---
content_type: doc
status: historical
layer: core
authority: P2
audience: agent
tags: [prog, attribute, points]
---

# Tasks

- [x] Brainstorming PH8 M5: Attribute Points and Manual Growth
    - [x] Explore project context
    - [x] Ask clarifying questions
    - [x] Propose 2-3 approaches
    - [x] Present design
    - [x] Write design doc
- [x] Create implementation plan
- [x] Implement PH8 M5: Attribute Points and Manual Growth
    - [x] Add AttributeComponent to state.py
    - [x] Add AttributeUpdate to updates.py
    - [x] Update builder.py to persist attributes
    - [x] Implement deterministic stat recalculation in leveling.py
    - [x] Update ApplyPath for AttributeUpdate and unspent_ap
    - [x] Implement AllocateAttributeAction with aptitude scaling
- [x] Verify PH8 M5
    - [x] Create and run tests/progression/test_attribute_growth.py
    - [x] Verify Hybrid model (Monsters scale, Heroes don't)
    - [x] Verify Aptitude multipliers (PROG-015)
    - [x] Verify Attribute caps (PROG-046)

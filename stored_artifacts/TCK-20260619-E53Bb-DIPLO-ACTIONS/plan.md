---
ticket_id: TCK-20260619-E53Bb-DIPLO-ACTIONS
phase: plan
date: 2026-06-22
---

# Plan — TCK-20260619-E53Bb-DIPLO-ACTIONS

## Changes

1. `src/engine/faction_decision.py` — add 5 diplomatic action subclasses (slots=True, all new fields have defaults)
2. `src/domains/faction/__init__.py` — create empty (module registration)
3. `src/domains/faction/diplomatic_actions.py` — DiplomaticActionHandler with pure handle() function
4. `tests/unit/faction/test_diplomacy.py` — add E53Bb acceptance criteria tests

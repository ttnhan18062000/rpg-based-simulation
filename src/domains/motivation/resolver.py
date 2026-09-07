"""
src/domains/motivation/resolver.py
───────────────────────────────────────────────────────────────────────────────
DoctrineResolver for Phase 14.

CONFIRMED DEAD LEGACY CODE (TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE, 2026-09-07):
`DoctrineResolver.resolve()` has zero real (non-test) callers anywhere in `src/` — the only two
`identity(class_id=...)` construction sites in the whole codebase
(`src/testing/scenario_runner.py`, `src/domains/campaigns/runner.py`) are test/single-episode-
analysis utilities, not the real corpus-world entity population path, so every real entity's
`class_id` stays at the bare default and this resolver never produces a meaningfully-differentiated
`IdentityDoctrine` in production. It is superseded by `AdventureRouteScorer.score()`'s own
already-live `personality_bias` mechanism (`src/domains/adventure/scoring.py`), which does the same
conceptual job (personality/context → route-family bias) with real, populated per-entity trait data
instead. Deliberately NOT revived or deleted — see `docs/guidelines/intentional_divergences.md`
§2.53 for the full disclosure and rationale.
"""

from __future__ import annotations
from typing import Mapping
from src.core.cognition import IdentityDoctrine

class DoctrineResolver:
    """Resolves actor types to unique IdentityDoctrines."""

    @staticmethod
    def resolve(class_id: str) -> IdentityDoctrine:
        class_id_lower = class_id.lower()
        if class_id_lower == "warrior":
            return IdentityDoctrine(
                class_id="warrior",
                preferred_route_tags={"melee": 0.5, "heavy_armor": 0.4, "combat": 0.3},
                avoided_route_tags={"ranged": 0.5, "spells": 0.6, "flee": 0.3},
                combat_style_bias={"melee": 0.5, "aggressive": 0.3},
                cooperation_bias={"solo": -0.1, "party": 0.2}
            )
        elif class_id_lower == "ranger":
            return IdentityDoctrine(
                class_id="ranger",
                preferred_route_tags={"ranged": 0.6, "scouting": 0.5, "stealth": 0.4},
                avoided_route_tags={"heavy_armor": 0.5, "melee": 0.2},
                combat_style_bias={"ranged": 0.5, "tactical": 0.4},
                cooperation_bias={"solo": 0.3, "party": -0.1}
            )
        elif class_id_lower == "mage":
            return IdentityDoctrine(
                class_id="mage",
                preferred_route_tags={"spells": 0.7, "intel": 0.5, "mana": 0.4},
                avoided_route_tags={"heavy_armor": 0.7, "melee": 0.5},
                combat_style_bias={"spellcasting": 0.6, "backline": 0.4},
                cooperation_bias={"solo": 0.0, "party": 0.3}
            )
        else:
            return IdentityDoctrine(class_id=class_id)

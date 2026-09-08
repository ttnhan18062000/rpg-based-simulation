"""
src/domains/motivation/__init__.py
───────────────────────────────────────────────────────────────────────────────
Exposing motivation-related services.

TCK-20260908-DEAD-DOCTRINE-VALUES-CHAIN-RETIREMENT (2026-09-08): DoctrineResolver and
MotivationBiasService (formerly exported here) were deleted -- confirmed dead in production
(zero real callers), superseded by AdventureRouteScorer.score()'s personality_bias mechanism.
See docs/guidelines/intentional_divergences.md §2.53 for the full disclosure.
"""

from src.domains.motivation.evaluator import RoleFitEvaluator

__all__ = ["RoleFitEvaluator"]

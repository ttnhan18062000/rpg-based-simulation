"""
src/domains/progression/phase.py
───────────────────────────────────────────────────────────────────────────────
Phase 6 — ProgressionConversionPhase

The bounded authoritative engine phase that runs the progression loop.
"""

from __future__ import annotations
from dataclasses import asdict, replace

from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate, EntityUpdate
from src.domains.progression.possession import PossessionUnderstandingService
from src.domains.progression.gaps import GrowthGapEvaluator
from src.domains.progression.schema import RewardLedgerComponent
from src.domains.progression.interpretation import RewardInterpretationService
from src.domains.progression.generator import ConversionOptionGenerator
from src.domains.progression.selector import ConversionDecisionService
from src.domains.progression.resolver import ConversionIntentResolver


class ProgressionConversionPhase:
    """
    Integrates all progression conversion services into a single execution boundary.
    """

    @staticmethod
    def execute(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        # Check feature flag or run constraints
        # Skip if not enabled in state context
        feature_flag = getattr(state, "progression_conversion_enabled", True)
        if not feature_flag:
            return update

        new_entity_updates = dict(update.entity_updates)

        # Process entities with inventory/reward/XP dirty marks
        for entity_id, entity in state.entities.items():
            # Coarse checks: skip if entity is inactive or dead
            if not entity.lifecycle.active or not entity.combat.alive:
                continue

            # Load or initialize reward ledger
            properties = getattr(entity.identity, "properties", {}) or {}
            ledger = properties.get("reward_ledger")
            if ledger is None:
                ledger = RewardLedgerComponent()

            # 1. Update possession understanding
            possession = PossessionUnderstandingService.evaluate(entity, state)

            # 2. Evaluate growth gaps
            gaps = GrowthGapEvaluator.evaluate(entity, possession, state)

            # 3. Interpret rewards
            interpretation = RewardInterpretationService.interpret(entity, ledger, possession, gaps, state)

            # 4. Generate options
            options = ConversionOptionGenerator.generate(entity, interpretation, gaps, state)

            # 5. Choose decision
            decision = ConversionDecisionService.select(entity, options, state)

            # 6. Map to executable intent / updates
            entity_update = new_entity_updates.get(entity_id)
            if not entity_update:
                entity_update = EntityUpdate(entity_id=entity_id)

            resolved_upd = ConversionIntentResolver.resolve(entity, decision, state)
            
            # Merge resolved updates back
            merged_upd = entity_update.merge(resolved_upd)
            
            # Store trace / properties for observation
            prop_upd = dict(merged_upd.property_updates)
            # asdict(): property_updates flows into entity.identity.properties, which
            # CanonicalStateHasher.to_canonical_json() serializes via plain json.dumps() with
            # no custom encoder -- the raw dataclass instance is not JSON-serializable.
            prop_upd["last_progression_decision"] = asdict(decision)
            
            merged_upd = replace(
                merged_upd,
                property_updates=prop_upd
            )

            new_entity_updates[entity_id] = merged_upd

        return replace(
            update,
            entity_updates=new_entity_updates
        )

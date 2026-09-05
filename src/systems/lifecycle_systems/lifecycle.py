from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
from dataclasses import replace
from src.core.updates import StateUpdate, EntityUpdate, LifecycleUpdate, InventoryUpdate, IdentityUpdate
from src.core.state import LifeStage
from src.core.enums import EntityRole
from src.ai.life_stage import LifeStageService
from src.ai.coming_of_age import choose_archetype, is_excluded_no_birth_record
from src.domains.demographics.cohort import compute_elder_attribute_update
import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState

class LifecycleSystem:
    """
    Handles entity lifecycle transitions: Aging, Death, Succession, and Heirlooms.
    Phase 9: Hero Lifecycle.
    """

    # Idea 55 (Feuds Outlive the Feuders): the heir's inherited hostility is weaker
    # than the deceased's own -- a starting grudge, not a full transfer.
    INHERITED_NEMESIS_SEVERITY_MULTIPLIER = 0.5

    @staticmethod
    def _transfer_inherited_feud(deceased: EntityState, heir_upd: EntityUpdate) -> EntityUpdate:
        """Idea 55 (Feuds Outlive the Feuders, TCK-20260904-LINEAGE-DEATH-DISPATCH):
        transfer a weakened version of the deceased's active Campaign-mode Nemesis
        blockers to the heir.

        Explicitly scoped to entity.strategic.blockers['nemesis_*'] -- the
        Campaign-mode signal populated by NemesisRelationImporter from
        CampaignState.nemesis_relations (src/domains/campaigns/grief_urgency.py) --
        NOT the always-live legacy SocialComponent.nemesis_ids/grudge_history
        mechanism, which this ticket does not touch (tracked separately by
        TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS). Most default single-episode
        Kernel runs never populate the Campaign-mode signal, so this handler is
        frequently a no-op -- an accepted, disclosed scope limit, not a bug.

        Uses a distinct "inherited_nemesis_{antagonist}" id (not "nemesis_
        {antagonist}") so this never silently overwrites a heir's own,
        independently-formed nemesis blocker against the same antagonist.
        """
        from src.core.strategic import BlockerState
        from src.core.updates import StrategicUpdate

        inherited = [
            replace(
                blocker,
                id=f"inherited_nemesis_{blocker.subject}",
                severity=blocker.severity * LifecycleSystem.INHERITED_NEMESIS_SEVERITY_MULTIPLIER,
                resolved=False,
                suppression_until_tick=0,
            )
            for bid, blocker in sorted(deceased.strategic.blockers.items(), key=lambda kv: kv[0])
            if bid.startswith("nemesis_")
        ]
        if not inherited:
            return heir_upd
        strat_upd = heir_upd.strategic or StrategicUpdate()
        return replace(
            heir_upd,
            strategic=replace(
                strat_upd,
                blockers_add_or_update=list(strat_upd.blockers_add_or_update) + inherited,
            ),
        )

    @staticmethod
    def _seed_dying_wish(
        deceased: EntityState, heir: EntityState, heir_upd: EntityUpdate, death_tick: int
    ) -> EntityUpdate:
        """Idea 58 (A Dying Wish, TCK-20260904-LINEAGE-DEATH-DISPATCH): seed one
        named, source-attributed intention onto the heir's MotivationModel at the
        moment heir_entity_id resolves.

        Honorable, ignorable, or rejectable -- nothing in this codebase reads
        NamedIntentionBundle.status to force an action, so seeding this bundle
        never auto-executes anything.

        Follows the codebase's established read-through-then-replace convention
        for entity.cognition (src/strategy/role_model_phase.py,
        src/domains/emotion/habit_phase.py, src/engine/quests.py): reads whatever
        cognition_bundle_set an earlier same-tick phase already staged on this
        heir_upd (falling back to heir.cognition) before replacing, so a same-tick
        collision with another cognition_bundle_set writer never silently clobbers
        either write.

        Wish text is deterministic, not narratively generated: if the deceased has
        an active Campaign-mode Nemesis blocker, the wish names that same
        antagonist (coherent with idea 55's feud transfer above); otherwise it
        falls back to a generic remembrance wish. No new decision-making/narrative
        subsystem is introduced -- a Plan-phase-equivalent scope decision, since no
        existing precedent selects among multiple wish templates.
        """
        from src.core.cognition import NamedIntentionBundle

        nemesis_ids = sorted(bid for bid in deceased.strategic.blockers if bid.startswith("nemesis_"))
        if nemesis_ids:
            antagonist = deceased.strategic.blockers[nemesis_ids[0]].subject
            text = f"avenge me against {antagonist}"
        else:
            text = "honor my memory"

        base_cognition = (
            heir_upd.cognition_bundle_set if heir_upd.cognition_bundle_set is not None else heir.cognition
        )
        new_intention = NamedIntentionBundle(
            text=text,
            source_entity_id=deceased.id,
            created_tick=death_tick,
            status="PENDING",
        )
        new_motivation = replace(base_cognition.motivation, named_intention=new_intention)
        new_cognition = replace(base_cognition, motivation=new_motivation)
        return replace(heir_upd, cognition_bundle_set=new_cognition)

    @staticmethod
    def _select_default_heir(state: AuthoritativeState, deceased: EntityState) -> Optional[int]:
        candidates = []
        for target_id, bond in deceased.social.bonds.items():
            if target_id == deceased.id:
                continue
            candidate = state.entities.get(target_id)
            if candidate is None or not candidate.lifecycle.active:
                continue
            score = 0.6 * bond.familiarity + 0.4 * ((bond.sentiment + 1.0) / 2.0)
            candidates.append((score, bond.last_interaction_tick, target_id))
        if not candidates:
            return None
        candidates.sort(key=lambda c: (-c[0], -c[1], c[2]))
        return candidates[0][2]

    @staticmethod
    def resolve_lifecycle(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        """
        Identify entities that have died and process succession/permadeath.
        """
        refined_entity_updates = dict(update.entity_updates)
        
        # Collect deaths for influence processing (Task 11.4)
        recent_deaths: List[EntityState] = []
        
        for e_id, entity in state.entities.items():
            if not entity.lifecycle.active:
                continue
            
            ent_upd = refined_entity_updates.get(e_id)

            # Age-based life-stage transition (TCK-20260824-LIFE-STAGE-TRANSITIONS). Monotonic
            # forward-only: every world-generated entity starts at age_ticks=0 with life_stage=ADULT
            # already correct (construction default, not a "just born" fact) -- an unconditional
            # recompute-and-overwrite would misclassify every entity as CHILD at tick 1.
            target_stage = LifeStageService.get_stage_for_age(entity.lifecycle.age_ticks)
            if LifeStageService.is_forward_transition(entity.identity.life_stage, target_stage):
                ent_upd = ent_upd or EntityUpdate(entity_id=e_id)
                existing_identity = ent_upd.identity or IdentityUpdate()
                ent_upd = replace(ent_upd, identity=replace(existing_identity, life_stage_set=target_stage))

                if target_stage == LifeStage.ELDER:
                    elder_update = compute_elder_attribute_update(
                        e_id, entity.attributes, entity.lifecycle.age_ticks
                    )
                    if elder_update is not None:
                        ent_upd = ent_upd.merge(elder_update)

                # Coming of Age archetype-choice roll (TCK-20260902-COMING-OF-AGE-ARCHETYPE-
                # CHOICE, idea 34). The entity.identity.role == EntityRole.CITIZEN gate is
                # required, not optional: without it this branch would also fire for a
                # MONSTER-role CHILD from the flag-gated Natural-Creature reproduction path
                # (spawn_natural_creature_offspring(), src/systems/world_systems/generator.py),
                # whose is_excluded_no_birth_record() check alone does NOT exclude it (it is
                # parentless but carries a real nonzero birth_tick) -- overwriting role_set there
                # would produce an incoherent MONSTER_HORDE-faction entity with a citizen
                # occupation.
                if (
                    target_stage == LifeStage.ADULT
                    and entity.identity.life_stage == LifeStage.CHILD
                    and entity.identity.role == EntityRole.CITIZEN
                ):
                    if not is_excluded_no_birth_record(entity):
                        archetype_role = choose_archetype(entity, state)
                        ent_upd = replace(ent_upd, identity=replace(ent_upd.identity, role_set=archetype_role))

                refined_entity_updates[e_id] = ent_upd

            # Check for natural death (old age)
            is_dead = False
            death_reason = None
            
            if entity.lifecycle.age_ticks >= entity.lifecycle.max_age_ticks:
                is_dead = True
                death_reason = "OLD_AGE"
            
            # Check for combat death -- PERMADEATH (a rebirth-eligible Hero at generation cap,
            # src/engine/combat.py) is a more final outcome than KILL, not a separate one; it must
            # route through the same deactivation path or the entity never actually deactivates
            # and keeps acting despite being narratively permanently dead (TCK-20260826-HOTFIX-
            # PERMADEATH-LIFECYCLE-FIX).
            if ent_upd and ent_upd.combat and ent_upd.combat.outcome_kind in ("KILL", "PERMADEATH"):
                is_dead = True
                death_reason = "COMBAT"
            
            if is_dead:
                ent_upd = ent_upd or EntityUpdate(entity_id=e_id)
                recent_deaths.append(entity)
                # Mark as inactive and record death truth
                life_upd = ent_upd.lifecycle or LifecycleUpdate()
                refined_entity_updates[e_id] = replace(ent_upd,
                    active=False,
                    lifecycle=replace(life_upd,
                        is_permadeath_set=True,
                        death_tick_set=state.tick,
                        death_reason_set=death_reason
                    )
                )
                
                # Process Succession / Heirlooms
                heir_id = entity.lifecycle.heir_entity_id
                if heir_id is None:
                    heir_id = LifecycleSystem._select_default_heir(state, entity)
                    if heir_id is not None:
                        life_upd2 = refined_entity_updates[e_id].lifecycle or LifecycleUpdate()
                        refined_entity_updates[e_id] = replace(refined_entity_updates[e_id],
                            lifecycle=replace(life_upd2, heir_entity_id_set=heir_id)
                        )
                if heir_id is not None:
                    heir = state.entities.get(heir_id)
                    if heir:
                        heir_upd = refined_entity_updates.get(heir_id, EntityUpdate(entity_id=heir_id))

                        # On-death lineage dispatch (ideas 55+58): one dispatch point, two
                        # thin handlers, both firing here -- right after heir_id resolution,
                        # before the heirloom transfer below (TCK-20260904-LINEAGE-DEATH-
                        # DISPATCH).
                        heir_upd = LifecycleSystem._transfer_inherited_feud(entity, heir_upd)
                        heir_upd = LifecycleSystem._seed_dying_wish(entity, heir, heir_upd, state.tick)

                        # Transactional Heirloom Transfer
                        from src.core.updates import ResourceTransferIntent
                        from src.core.state import ItemStack

                        # Combine inventory and specific heirlooms. entity.inventory.items is a
                        # list on a live/authoritative entity but a tuple when entity is a
                        # to_readonly() view (src/core/state.py's immutability optimization) --
                        # normalize to list before concatenating with heirloom_stacks (always a
                        # list) so this works for either source (TCK-20260829-LIFECYCLE-HEIRLOOM-
                        # INVENTORY-TUPLE-TYPEERROR).
                        heirloom_stacks = [ItemStack(item_id=hid, quantity=1) for hid in entity.lifecycle.heirlooms]
                        all_transfer_items = list(entity.inventory.items) + heirloom_stacks

                        if all_transfer_items:
                            intent = ResourceTransferIntent(
                                source_id=entity.id,
                                source_kind="CHEST", # Use CHEST or similar source kind that allows items
                                items_add=all_transfer_items,
                                transfer_kind="AUTO"
                            )
                            heir_upd = replace(heir_upd,
                                resource_transfers=heir_upd.resource_transfers + [intent]
                            )

                        refined_entity_updates[heir_id] = heir_upd

        # Apply Influence Shifts and Conquest Lifecycle
        if recent_deaths:
            from src.world.influence import FactionInfluenceService
            from src.economy.vacancy import EconomicVacancyService
            # Influence Shift
            inf_update = FactionInfluenceService.process_influence_shift(state, recent_deaths)
            # Conquest/Stronghold Lifecycle (Requires generator)
            from src.systems.world_systems.generator import EntityGenerator
            generator = EntityGenerator(state.seed + state.tick)
            inf_update = FactionInfluenceService.process_conquest_lifecycle(state, inf_update, generator)
            # Economic Vacancy Signal (TCK-20260903-ECONOMIC-VACANCY-SIGNAL)
            vac_update = EconomicVacancyService.check_and_emit(state, recent_deaths)

            # Merge world updates and new entities
            new_world_updates = dict(update.world_updates)
            for r_id, extra_upd in inf_update.world_updates.items():
                if r_id in new_world_updates:
                    new_world_updates[r_id] = new_world_updates[r_id].merge(extra_upd)
                else:
                    new_world_updates[r_id] = extra_upd

            update = replace(update,
                world_updates=new_world_updates,
                entities_add=list(update.entities_add) + list(inf_update.entities_add),
                entities_remove=list(update.entities_remove) + list(inf_update.entities_remove),
                world_events_add=list(update.world_events_add) + list(vac_update.world_events_add),
            )
                        
        return replace(update, entity_updates=refined_entity_updates)

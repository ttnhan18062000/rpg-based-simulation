from __future__ import annotations
import time
import logging
from typing import Any, List, Optional
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.events import (
    SimulationEvent, CombatDamageEvent, CombatKillEvent,
    GoldTransactionEvent, QuestEvent, MovementEvent, LifecycleEvent
)

logger = logging.getLogger(__name__)

_NEAR_DEATH_THRESHOLD = 0.2


class EventExtractor:
    """Extracts curated low-volume SimulationEvents from state changes and committed updates."""
    @staticmethod
    def extract(
        prior_state: AuthoritativeState,
        current_state: AuthoritativeState,
        update: Any,
        mode: ObservabilityMode = ObservabilityMode.LIGHT
    ) -> List[SimulationEvent]:
        """Compares state transitions to produce semantic events matching volume policies."""
        if mode == ObservabilityMode.OFF:
            return []

        tick = current_state.tick
        now = time.time()
        events: List[SimulationEvent] = []

        # Optimization: Scoped comparison using dirty entity IDs
        dirty_entity_ids = update.entity_updates.keys() if (update and hasattr(update, "entity_updates")) else []
        if not dirty_entity_ids:
            dirty_entity_ids = current_state.entities.keys()

        for eid in dirty_entity_ids:
            entity = current_state.entities.get(eid)
            prior_ent = prior_state.entities.get(eid)

            # Despawn lifecycle
            if entity is None:
                if prior_ent is not None:
                    events.append(LifecycleEvent(
                        tick=tick, timestamp=now, entity_id=eid,
                        action="despawn", details={"kind": prior_ent.kind, "position": prior_ent.navigation.position}
                    ))
                    # Demographic mortality — despawn without a combat attacker
                    e_upd = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
                    has_attacker = bool(e_upd and getattr(e_upd, "combat_upd", None) and e_upd.combat_upd.attacker_id)
                    if not has_attacker:
                        events.append(SimulationEvent(
                            event_type="demographic_mortality", event_category="lifecycle",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"kind": prior_ent.kind},
                        ))
                continue

            # Spawn lifecycle
            if prior_ent is None:
                events.append(LifecycleEvent(
                    tick=tick, timestamp=now, entity_id=eid,
                    action="spawn", details={"kind": entity.kind, "position": entity.navigation.position}
                ))
                events.append(SimulationEvent(
                    event_type="demographic_birth", event_category="lifecycle",
                    tick=tick, entity_id=eid, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"kind": entity.kind},
                ))
                continue

            # Movement (exclusively low-volume for non-LIGHT/LONG_RUN modes)
            if prior_ent.navigation.position != entity.navigation.position:
                if mode not in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):
                    events.append(MovementEvent(
                        tick=tick, timestamp=now, entity_id=eid,
                        start_pos=prior_ent.navigation.position,
                        end_pos=entity.navigation.position
                    ))

            # Combat damage event
            hp_diff = entity.combat.hp - prior_ent.combat.hp
            if hp_diff < 0:
                is_lethal = (entity.combat.hp <= 0 or not entity.lifecycle.active)
                # Volumization rule: skip routine damage inside LIGHT or LONG_RUN mode unless lethal
                if is_lethal or mode not in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):
                    attacker_id = None
                    e_upd = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
                    if e_upd and getattr(e_upd, "combat_upd", None):
                        attacker_id = e_upd.combat_upd.attacker_id

                    events.append(CombatDamageEvent(
                        tick=tick, timestamp=now, entity_id=eid,
                        attacker_id=attacker_id, damage=int(-hp_diff),
                        is_lethal=is_lethal
                    ))

            # Kill events
            if prior_ent.lifecycle.active and not entity.lifecycle.active:
                killer_id = None
                e_upd = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
                if e_upd and getattr(e_upd, "combat_upd", None):
                    killer_id = e_upd.combat_upd.attacker_id

                events.append(CombatKillEvent(
                    tick=tick, timestamp=now, entity_id=eid,
                    killer_id=killer_id
                ))

            # Combat initiated — entity was at full HP prior tick, now taking damage
            if (entity.lifecycle.active
                    and prior_ent.combat.hp == prior_ent.combat.max_hp
                    and entity.combat.hp < entity.combat.max_hp):
                e_upd = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
                attacker_id = None
                if e_upd and getattr(e_upd, "combat_upd", None):
                    attacker_id = e_upd.combat_upd.attacker_id
                events.append(SimulationEvent(
                    event_type="combat_initiated", event_category="combat",
                    tick=tick, entity_id=eid, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"attacker_id": attacker_id},
                ))

            # Near-death survival — HP crosses below 20% threshold while entity survives
            near_death_hp = prior_ent.combat.max_hp * _NEAR_DEATH_THRESHOLD
            if (entity.lifecycle.active
                    and entity.combat.hp < near_death_hp
                    and prior_ent.combat.hp >= near_death_hp):
                events.append(SimulationEvent(
                    event_type="near_death_survival", event_category="combat",
                    tick=tick, entity_id=eid, severity="WARNING",
                    source_system="event_extractor", message="",
                    payload={"hp": entity.combat.hp, "max_hp": entity.combat.max_hp},
                ))

            # XP granted and level-up (via IdentityComponent)
            if hasattr(entity, "identity") and hasattr(prior_ent, "identity"):
                xp_delta = entity.identity.evolution_points - prior_ent.identity.evolution_points
                if xp_delta > 0:
                    events.append(SimulationEvent(
                        event_type="xp_granted", event_category="lifecycle",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"amount": xp_delta},
                    ))
                if entity.identity.evolution_level > prior_ent.identity.evolution_level:
                    events.append(SimulationEvent(
                        event_type="level_up", event_category="lifecycle",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"new_level": entity.identity.evolution_level},
                    ))

            # Economy/Gold events (exclusively meaningful changes)
            gold_diff = entity.inventory.gold - prior_ent.inventory.gold
            if gold_diff != 0:
                # Volumization rule: ignore micro-trades (< 5.0 gold) in LIGHT mode
                if abs(gold_diff) >= 5.0 or mode not in (ObservabilityMode.LIGHT, ObservabilityMode.LONG_RUN):
                    kind = "gain" if gold_diff > 0 else "loss"
                    events.append(GoldTransactionEvent(
                        tick=tick, timestamp=now, entity_id=eid,
                        amount=float(abs(gold_diff)), transaction_kind=kind
                    ))

            # Agency and cognition events — derived from EntityUpdate fields
            e_upd_ext = update.entity_updates.get(eid) if update and hasattr(update, "entity_updates") else None
            if e_upd_ext is not None:
                prop = getattr(e_upd_ext, "property_updates", None) or {}

                # Agency: route_selected / action_executed
                routing_family = prop.get("last_routing_family")
                if routing_family:
                    events.append(SimulationEvent(
                        event_type="route_selected", event_category="strategy",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"family": routing_family},
                    ))
                    events.append(SimulationEvent(
                        event_type="action_executed", event_category="strategy",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"family": routing_family},
                    ))

                # Cognition: self_model_updated (PP-03)
                if getattr(e_upd_ext, "self_model_bundle_set", None) is not None:
                    events.append(SimulationEvent(
                        event_type="self_model_updated", event_category="strategy",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={},
                    ))

                # Information: belief_assimilated + belief_updated (PP-04)
                if prop.get("last_assimilated_tick") == tick:
                    subject = prop.get("last_assimilated_subject", "unknown")
                    events.append(SimulationEvent(
                        event_type="belief_assimilated", event_category="strategy",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"subject": subject},
                    ))
                    events.append(SimulationEvent(
                        event_type="belief_updated", event_category="strategy",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"subject": subject},
                    ))

                # Economy + Information events from intent_results (resource_transfers cleared by PP-27)
                _GOLD_SINK_KINDS = frozenset(("REPAIR_FEE", "SERVICE_FEE", "TAX"))
                for ir in (getattr(e_upd_ext, "intent_results", None) or []):
                    if not getattr(ir, "accepted", False):
                        continue
                    src_kind = getattr(ir, "source_kind", None)
                    if src_kind == "NODE":
                        events.append(SimulationEvent(
                            event_type="resource_harvested", event_category="economy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"node_id": str(getattr(ir, "source_id", ""))},
                        ))
                    elif src_kind == "CRAFTING":
                        events.append(SimulationEvent(
                            event_type="item_crafted", event_category="economy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"source_id": str(getattr(ir, "source_id", ""))},
                        ))
                    elif src_kind in ("SHOP_BUY", "SHOP_SELL"):
                        events.append(SimulationEvent(
                            event_type="shop_transaction", event_category="economy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"kind": src_kind},
                        ))
                        events.append(SimulationEvent(
                            event_type="trade_executed", event_category="economy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"kind": src_kind},
                        ))
                    elif src_kind == "QUEST":
                        events.append(SimulationEvent(
                            event_type="quest_reward_dispensed", event_category="economy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"source_id": str(getattr(ir, "source_id", ""))},
                        ))
                    elif src_kind in _GOLD_SINK_KINDS:
                        events.append(SimulationEvent(
                            event_type="gold_sink_fired", event_category="economy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"mechanism": src_kind},
                        ))
                    elif src_kind == "INFORMATION_PURCHASE":
                        events.append(SimulationEvent(
                            event_type="paid_information_transaction", event_category="economy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"source_id": str(getattr(ir, "source_id", ""))},
                        ))

                # World: hazard_drain_applied (WorldDynamicsSystem sets outcome_kind="HAZARD")
                combat_upd = getattr(e_upd_ext, "combat", None)
                if combat_upd and getattr(combat_upd, "outcome_kind", None) == "HAZARD":
                    hp_delta = getattr(combat_upd, "hp_delta", 0)
                    if hp_delta < 0:
                        events.append(SimulationEvent(
                            event_type="hazard_drain_applied", event_category="combat",
                            tick=tick, entity_id=eid, severity="WARNING",
                            source_system="event_extractor", message="",
                            payload={"damage": int(-hp_delta)},
                        ))

            # Cognition: lead_certainty_changed (PP-30 side effect — state diff)
            if hasattr(entity, "strategic") and hasattr(prior_ent, "strategic"):
                curr_leads = getattr(entity.strategic, "leads", None) or {}
                prior_leads = getattr(prior_ent.strategic, "leads", None) or {}
                for lid, lead in curr_leads.items():
                    prior_lead = prior_leads.get(lid)
                    if prior_lead is not None and lead.certainty != prior_lead.certainty:
                        events.append(SimulationEvent(
                            event_type="lead_certainty_changed", event_category="strategy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={
                                "lead_id": lid,
                                "from_certainty": str(prior_lead.certainty),
                                "to_certainty": str(lead.certainty),
                            },
                        ))

            # Social: group_joined / group_expelled (PP-34 group membership state diff)
            curr_group = getattr(entity, "group_id", None)
            prior_group = getattr(prior_ent, "group_id", None)
            if curr_group != prior_group:
                if curr_group is not None:
                    events.append(SimulationEvent(
                        event_type="group_joined", event_category="social",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"group_id": str(curr_group)},
                    ))
                else:
                    events.append(SimulationEvent(
                        event_type="group_expelled", event_category="social",
                        tick=tick, entity_id=eid, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"prior_group_id": str(prior_group)},
                    ))

            # Social: contract lifecycle events (PP-35 contracts state diff)
            if hasattr(entity, "strategic") and hasattr(prior_ent, "strategic"):
                curr_contracts = getattr(entity.strategic, "contracts", None) or {}
                prior_contracts = getattr(prior_ent.strategic, "contracts", None) or {}
                for cid, cs in curr_contracts.items():
                    prior_cs = prior_contracts.get(cid)
                    if prior_cs is None:
                        continue
                    curr_status = getattr(getattr(cs, "status", None), "name", str(getattr(cs, "status", "")))
                    prior_status = getattr(getattr(prior_cs, "status", None), "name", str(getattr(prior_cs, "status", "")))
                    if curr_status == prior_status:
                        continue
                    if prior_status == "OFFERED" and curr_status == "ACTIVE":
                        events.append(SimulationEvent(
                            event_type="contract_offer_accepted", event_category="social",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"contract_id": cid},
                        ))
                    elif curr_status == "COMPLETED":
                        events.append(SimulationEvent(
                            event_type="contract_completed", event_category="social",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"contract_id": cid},
                        ))
                    elif curr_status == "EXPIRED":
                        events.append(SimulationEvent(
                            event_type="contract_lapsed", event_category="social",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={"contract_id": cid},
                        ))

            # Quest progress lifecycle events
            prior_projects = prior_ent.strategic.projects
            current_projects = entity.strategic.projects
            for qid, qstate in current_projects.items():
                prior_qstate = prior_projects.get(qid)
                if prior_qstate is None:
                    events.append(QuestEvent(
                        tick=tick, timestamp=now, entity_id=eid,
                        quest_id=qid, status="started"
                    ))
                elif prior_qstate.status != qstate.status:
                    events.append(QuestEvent(
                        tick=tick, timestamp=now, entity_id=eid,
                        quest_id=qid, status=str(qstate.status)
                    ))

        # Resource node depletion and regeneration
        if hasattr(current_state, "resource_nodes") and hasattr(prior_state, "resource_nodes"):
            for node_id, node in current_state.resource_nodes.items():
                prior_node = prior_state.resource_nodes.get(node_id)
                if prior_node is None:
                    continue
                if prior_node.remaining_charges > 0 and node.remaining_charges == 0:
                    events.append(SimulationEvent(
                        event_type="resource_node_depleted", event_category="resource",
                        tick=tick, entity_id=None, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"node_id": node_id, "charges": 0, "max_charges": node.max_charges},
                    ))
                elif prior_node.remaining_charges == 0 and node.remaining_charges > 0:
                    events.append(SimulationEvent(
                        event_type="resource_node_regenerated", event_category="resource",
                        tick=tick, entity_id=None, severity="INFO",
                        source_system="event_extractor", message="",
                        payload={"node_id": node_id, "charges": node.remaining_charges, "max_charges": node.max_charges},
                    ))

        # World dynamics events — from StateUpdate world_updates and entities_add
        for rid, w_upd in (getattr(update, "world_updates", None) or {}).items():
            if getattr(w_upd, "trauma_delta", 0.0) != 0.0:
                events.append(SimulationEvent(
                    event_type="region_trauma_delta", event_category="region",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"region_id": rid, "delta": w_upd.trauma_delta},
                ))
            if getattr(w_upd, "owner_faction_id_set", None) is not None:
                events.append(SimulationEvent(
                    event_type="region_ownership_changed", event_category="region",
                    tick=tick, entity_id=None, severity="WARNING",
                    source_system="event_extractor", message="",
                    payload={"region_id": rid, "new_owner": str(w_upd.owner_faction_id_set)},
                ))
            if getattr(w_upd, "kind_set", None) is not None:
                events.append(SimulationEvent(
                    event_type="region_transformed", event_category="region",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"region_id": rid, "new_kind": w_upd.kind_set},
                ))

        if getattr(update, "last_calamity_tick_set", None) == tick:
            events.append(SimulationEvent(
                event_type="calamity_spawned", event_category="lifecycle",
                tick=tick, entity_id=None, severity="CRITICAL",
                source_system="event_extractor", message="",
                payload={"tick": tick},
            ))

        _BOSS_KINDS = frozenset(("world_boss", "ancient_sentinel"))
        for new_ent in (getattr(update, "entities_add", None) or []):
            kind = getattr(new_ent, "kind", None)
            if kind in _BOSS_KINDS:
                events.append(SimulationEvent(
                    event_type="boss_spawned", event_category="lifecycle",
                    tick=tick, entity_id=getattr(new_ent, "id", None), severity="WARNING",
                    source_system="event_extractor", message="",
                    payload={"kind": kind},
                ))
            elif kind == "goblin_raider":
                events.append(SimulationEvent(
                    event_type="raid_party_spawned", event_category="lifecycle",
                    tick=tick, entity_id=getattr(new_ent, "id", None), severity="WARNING",
                    source_system="event_extractor", message="",
                    payload={"kind": kind},
                ))

        return events

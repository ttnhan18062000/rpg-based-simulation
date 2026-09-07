from __future__ import annotations
from dataclasses import replace
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState
    from src.core.updates import StateUpdate
    from src.observability.events import LeadershipChangedEvent, BetrayalDesertionEvent


class GroupPhase:
    """
    Pipeline phase responsible for coordinating group formation, updates, and removals.

    Also runs PartyLifecycleService leadership elections each tick (E41B) and
    defection checks each tick (E41D).
    """

    # Accumulated leadership events from the most recent resolve() call.
    # Cleared at the start of every resolve() call. Used by tests and by the
    # kernel's _event_listeners dispatch chain.
    last_tick_events: List["LeadershipChangedEvent"] = []

    # Accumulated defection events from the most recent resolve() call.
    last_tick_defection_events: List["BetrayalDesertionEvent"] = []

    @staticmethod
    def resolve(state: AuthoritativeState, update: StateUpdate) -> StateUpdate:
        from src.systems.world_systems.groups import GroupSystem
        from src.systems.social_systems.party_lifecycle import PartyLifecycleService
        from src.systems.social_systems.clan_lifecycle import (
            ClanLifecycleService,
            CLAN_REPUTATION_MISCONDUCT_DELTA,
        )
        from src.core.updates import ClanUpdate, EntityUpdate

        # Clear per-tick event buffers
        GroupPhase.last_tick_events = []
        GroupPhase.last_tick_defection_events = []

        # Optimization: Pass state and update directly, let GroupSystem handle sliding positions
        group_update = GroupSystem.update_groups(state, update)

        # Merge group additions/updates
        new_groups_add = list(update.groups_add_or_update)
        group_ids = {g.id for g in new_groups_add}

        for g in group_update.groups_add_or_update:
            if g.id in group_ids:
                new_groups_add = [
                    existing if existing.id != g.id else g
                    for existing in new_groups_add
                ]
            else:
                new_groups_add.append(g)

        # Merge group removals
        new_groups_remove = list(
            set(list(update.groups_remove) + list(group_update.groups_remove))
        )

        # --- E41B: Leadership election pass ---
        # Run over all surviving groups (those not being removed this tick).
        removed_ids = set(new_groups_remove)
        tick = state.tick

        # Build a combined view: groups already in state PLUS groups being added/updated
        groups_being_updated = {g.id: g for g in new_groups_add}
        all_relevant_group_ids = (
            set(state.groups.keys()) | set(groups_being_updated.keys())
        ) - removed_ids

        for g_id in sorted(all_relevant_group_ids):
            group = groups_being_updated.get(g_id) or state.groups.get(g_id)
            if group is None:
                continue

            # Collect live members from state.entities for sociability scoring
            members = [
                state.entities[m_id]
                for m_id in group.member_ids
                if m_id in state.entities
            ]

            updated_group, event = PartyLifecycleService.check_leadership(
                group, members, tick
            )

            if updated_group is not None:
                # Replace (or insert) the group in the accumulated list
                replaced = False
                for i, existing in enumerate(new_groups_add):
                    if existing.id == g_id:
                        new_groups_add[i] = updated_group
                        replaced = True
                        break
                if not replaced:
                    new_groups_add.append(updated_group)

            if event is not None:
                GroupPhase.last_tick_events.append(event)

        # --- E41D: Defection pass ---
        # Re-build the combined group view after the leadership pass has potentially
        # updated groups in new_groups_add.
        groups_being_updated = {g.id: g for g in new_groups_add}

        # Merge side-effect entity updates from group logic (e.g. leadership changes)
        refined_entity_updates = dict(update.entity_updates)
        for eid, eupd in group_update.entity_updates.items():
            existing = refined_entity_updates.get(eid, EntityUpdate(entity_id=eid))
            refined_entity_updates[eid] = existing.merge(eupd)

        new_clan_updates: List["ClanUpdate"] = list(update.clan_updates)

        for g_id in sorted(all_relevant_group_ids):
            group = groups_being_updated.get(g_id) or state.groups.get(g_id)
            if group is None:
                continue

            # TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE: read idea 56's bridged loyalty-pressure
            # signal for this group's real region, instead of always defaulting to 0.0.
            # Resolved from the group's own anchor position (real geometry, recomputed every call)
            # rather than a member's cached NavigationComponent.region_id -- avoids depending on
            # that per-entity cache's own freshness for a group-level (not per-entity) decision.
            # None-safe: 0.0 (no-op, byte-identical to the pre-bridge behavior) when the group's
            # anchor isn't inside any region, or that region has no region_cultures entry yet.
            from src.engine.spatial_query import SpatialQueryService

            group_region = SpatialQueryService.get_region_at(state, group.anchor)
            loyalty_pressure = (
                state.region_loyalty_pressure.get(group_region.id, 0.0)
                if group_region is not None else 0.0
            )

            # Only run defection on groups that still have multiple members
            # and whose grievance_log is at threshold or above.
            if len(group.grievance_log) < PartyLifecycleService.effective_defection_threshold(group, loyalty_pressure):
                continue

            # Collect live members eligible to defect (those present in state.entities)
            live_member_ids = [
                m_id for m_id in sorted(group.member_ids)
                if m_id in state.entities
            ]

            # At most one defection per group per tick — take the first eligible member.
            for m_id in live_member_ids:
                member_entity = state.entities[m_id]
                updated_group, def_event, entity_upd = PartyLifecycleService.check_defection(
                    group, member_entity, tick, loyalty_pressure
                )

                if updated_group is None:
                    # Threshold not met (shouldn't happen given the guard above, but be safe)
                    continue

                # Apply the group update
                replaced = False
                for i, existing in enumerate(new_groups_add):
                    if existing.id == g_id:
                        new_groups_add[i] = updated_group
                        replaced = True
                        break
                if not replaced:
                    new_groups_add.append(updated_group)

                # Refresh groups_being_updated so subsequent iterations see the pruned group
                groups_being_updated[g_id] = updated_group

                if def_event is not None:
                    GroupPhase.last_tick_defection_events.append(def_event)

                if entity_upd is not None:
                    existing_upd = refined_entity_updates.get(m_id, EntityUpdate(entity_id=m_id))
                    refined_entity_updates[m_id] = existing_upd.merge(entity_upd)

                    clan_id = ClanLifecycleService.find_clan_id_for_entity(state, m_id)
                    if clan_id is not None:
                        new_clan_updates.append(
                            ClanUpdate(
                                clan_id=clan_id,
                                clan_reputation_delta=CLAN_REPUTATION_MISCONDUCT_DELTA,
                            )
                        )

                # One defection per group per tick
                break

        return replace(
            update,
            groups_add_or_update=new_groups_add,
            groups_remove=new_groups_remove,
            entity_updates=refined_entity_updates,
            clan_updates=new_clan_updates,
        )

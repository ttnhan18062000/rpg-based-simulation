from __future__ import annotations

import hashlib
from typing import Any, Dict

from src.core.state import AuthoritativeState


class StateFingerprinter:
    """
    Produces deterministic, domain-specific fingerprints for authoritative state.

    This fingerprint is intentionally lightweight. It is not a full canonical
    save-state serializer. For full replay/certification hashing, use
    CanonicalStateHasher.

    Scope:
        The fingerprint must change when replay-visible gameplay state changes.

    Important:
        Strategic state is replay-visible. Adding/removing projects, blockers,
        leads, directives, concerns, contracts, or changing the current project
        must affect the fingerprint.

    Fraud this catches:
        - strategic changes are applied but invisible to fingerprint
        - replay parity misses project/detour/blocker changes
        - state hash only tracks scalar entity fields
        - group/social/tactical changes are silently ignored
    """

    @staticmethod
    def get_fingerprint(state: AuthoritativeState) -> Dict[str, Any]:
        """
        Produce a deterministic fingerprint of the current state.

        Included domains:
            - entity identity and spatial state
            - combat/readiness/lifecycle state
            - inventory shape
            - strategic projects/blockers/leads/directives/concerns/contracts
            - global resources
            - resource nodes
            - regions
            - local scars
            - group coordination
            - macro world state
        """
        entity_parts = []

        for eid in sorted(state.entities.keys()):
            ent = state.entities[eid]

            strategic_ident = StateFingerprinter._strategic_identity(ent)

            entity_parts.append(
                f"{eid}:"
                f"{ent.kind}:"
                f"pos={ent.navigation.position}:"
                f"hp={ent.combat.hp}:"
                f"gold={ent.inventory.gold}:"
                f"current_project={ent.strategic.current_project_id}:"
                f"current_objective={ent.strategic.current_objective_id}:"
                f"readiness={ent.combat.readiness}:"
                f"active={ent.lifecycle.active}:"
                f"skills={len(ent.identity.learned_skills)}:"
                f"items={StateFingerprinter._inventory_identity(ent)}:"
                f"bonds={len(ent.social.bonds)}:"
                f"reputation={ent.social.public_reputation:.3f}:"
                f"strategic={strategic_ident}"
            )

        entity_ident = "|".join(entity_parts)

        resource_ident = "|".join(
            f"{k}:{v}"
            for k, v in sorted(state.global_resources.items())
        )

        node_ident = "|".join(
            f"{nid}:{node.remaining_charges}:{node.cooldown_remaining}"
            for nid, node in sorted(state.resource_nodes.items())
        )

        region_ident = "|".join(
            f"{rid}:{region.owner_faction_id}:{region.influence:.3f}:"
            f"{region.hazard_level:.3f}"
            for rid, region in sorted(state.regions.items())
        )

        scar_ident = "|".join(
            f"{scar_id}:{scar.severity}"
            for scar_id, scar in sorted(state.local_scars.items())
        )

        group_ident = StateFingerprinter._group_identity(state)

        macro_ident = (
            f"maturity={state.maturity}:"
            f"last_calamity_tick={state.last_calamity_tick}:"
            f"movement_count={state.movement_count}"
        )

        raw_data = (
            f"tick={state.tick}|"
            f"seed={state.seed}|"
            f"entities={entity_ident}|"
            f"resources={resource_ident}|"
            f"nodes={node_ident}|"
            f"regions={region_ident}|"
            f"scars={scar_ident}|"
            f"groups={group_ident}|"
            f"macro={macro_ident}"
        )

        state_hash = hashlib.md5(raw_data.encode("utf-8")).hexdigest()

        return {
            "state_hash": state_hash,
            "tick": state.tick,
            "seed": state.seed,
            "entity_count": len(state.entities),
            "resource_count": len(state.global_resources),
            "maturity": state.maturity,
        }

    @staticmethod
    def _inventory_identity(entity) -> str:
        """
        Return deterministic inventory identity.

        Count-only inventory fingerprints are too weak because replacing one
        item with another could preserve len(items). Include item IDs and
        quantities.
        """
        item_parts = []

        for stack in sorted(
            entity.inventory.items,
            key=lambda item: (
                item.item_id if hasattr(item, "item_id") else str(item)
            ),
        ):
            if hasattr(stack, "item_id"):
                item_parts.append(f"{stack.item_id}:{stack.quantity}")
            else:
                item_parts.append(str(stack))

        return ",".join(item_parts)

    @staticmethod
    def _strategic_identity(entity) -> str:
        """
        Return deterministic strategic identity for replay-visible planning
        state.

        This intentionally includes IDs and core fields instead of only counts.
        A project with ID p1 and a project with ID p2 are different replay
        states even if both have the same count.
        """
        strategic = entity.strategic

        project_ident = "|".join(
            f"{project_id}:"
            f"{project.kind}:"
            f"{project.status}:"
            f"{project.active_objective_id}:"
            f"objectives={','.join(str(obj.id) for obj in project.objectives)}"
            for project_id, project in sorted(strategic.projects.items())
        )

        blocker_ident = "|".join(
            f"{blocker_id}:"
            f"{blocker.kind}:"
            f"{blocker.subject}:"
            f"{blocker.severity:.3f}:"
            f"{blocker.resolved}"
            for blocker_id, blocker in sorted(strategic.blockers.items())
        )

        lead_ident = "|".join(
            f"{lead_id}:"
            f"{lead.kind}:"
            f"{lead.subject}:"
            f"{lead.certainty}:"
            f"{lead.tested}"
            for lead_id, lead in sorted(strategic.leads.items())
        )

        directive_ident = "|".join(
            f"{directive_id}:"
            f"{directive.kind}:"
            f"{directive.priority}"
            for directive_id, directive in sorted(strategic.directives.items())
        )

        concern_ident = "|".join(
            f"{concern_id}:"
            f"{concern.kind}:"
            f"{concern.source}:"
            f"{concern.urgency:.3f}"
            for concern_id, concern in sorted(strategic.concerns.items())
        )

        contract_ident = "|".join(
            f"{contract_id}:"
            f"{contract.kind}:"
            f"{contract.status}:"
            f"{contract.target_id}"
            for contract_id, contract in sorted(strategic.contracts.items())
        )

        boredom_ident = "|".join(
            f"{kind}:{value:.3f}"
            for kind, value in sorted(strategic.boredom.items())
        )

        return (
            f"projects=[{project_ident}];"
            f"blockers=[{blocker_ident}];"
            f"leads=[{lead_ident}];"
            f"directives=[{directive_ident}];"
            f"concerns=[{concern_ident}];"
            f"contracts=[{contract_ident}];"
            f"boredom=[{boredom_ident}]"
        )

    @staticmethod
    def _group_identity(state: AuthoritativeState) -> str:
        """
        Return deterministic group coordination identity.

        Important:
            Current GroupRecord does not have the legacy field goal_id.
            Use current fields such as leader_id, member_ids, shared_target_id,
            shared_target_kind/shared_intent if available, and contract_id.
        """
        group_parts = []

        for group_id in sorted(state.groups.keys()):
            group = state.groups[group_id]

            member_ids = ",".join(
                str(member_id)
                for member_id in sorted(group.member_ids)
            )

            shared_target_id = getattr(group, "shared_target_id", None)
            shared_target_kind = getattr(group, "shared_target_kind", None)
            shared_intent = getattr(group, "shared_intent", None)

            if hasattr(shared_intent, "value"):
                shared_intent = shared_intent.value

            group_parts.append(
                f"{group_id}:"
                f"leader={group.leader_id}:"
                f"members={member_ids}:"
                f"target={shared_target_kind}:{shared_target_id}:"
                f"intent={shared_intent}:"
                f"contract={getattr(group, 'contract_id', None)}"
            )

        return "|".join(group_parts)
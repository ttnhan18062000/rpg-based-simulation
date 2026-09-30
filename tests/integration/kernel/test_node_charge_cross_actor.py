"""Cross-actor node-charge accounting through the authoritative pipeline (Mechanics Bible ch03 §1, §3).

Parity ``TOWN-122``: two actors completing the same node charge in one tick cannot duplicate the
yield. Resolver-level branches are covered in ``tests/unit/resource/test_node_charge_accounting.py``;
this test proves the pipeline accumulates the reservation across the two actors' intents.
"""

import pytest

from src.core.models.inventory import ItemStack
from src.core.update_models.resources import ResourceTransferIntent
from src.core.updates import EntityUpdate, StateUpdate
from src.engine.pipeline import AuthoritativeApplyPipeline
from tests.helpers.entities import make_entity
from tests.helpers.resources import make_resource_node, make_resource_state

pytestmark = [pytest.mark.domain("substrate"), pytest.mark.domain("economy"), pytest.mark.level("kernel_integration")]

_NODE_ID = 101


def test_two_actors_on_the_last_charge_yield_exactly_once():
    actors = [make_entity(1), make_entity(2)]
    node = make_resource_node(_NODE_ID, remaining_charges=1, max_charges=1)
    state = make_resource_state(entities=actors, nodes=[node])
    update = StateUpdate(
        entity_updates={
            actor.id: EntityUpdate(
                entity_id=actor.id,
                resource_transfers=[
                    ResourceTransferIntent(
                        transaction_id=f"txn-{actor.id}",
                        source_id=_NODE_ID,
                        source_kind="NODE",
                        items_add=[ItemStack("iron_ore", 1)],
                        transfer_kind="HARVEST",
                    )
                ],
            )
            for actor in actors
        }
    )

    refined = AuthoritativeApplyPipeline.refine(state, update)

    yields = [u for u in refined.entity_updates.values() if u.inventory is not None]
    assert len(yields) == 1
    assert refined.node_updates[_NODE_ID].charges_delta == -1

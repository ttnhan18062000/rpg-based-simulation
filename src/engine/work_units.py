# Compliance IDs: INFRA-005, RES-025
"""Reference-millisecond work model for the Canonical signal contract (PERF-D1).

``tick_cost`` models what a tick costs on the reference host from deterministic counts of the demand placed on the engine, never from a clock.
This module imports no clock, no host module and no thread module, and a static guard test keeps it that way.

The weights are constants of a named, versioned model. Changing one is a new version, like a hash scheme: never edit a weight in place.
``WORK_MODEL_V1`` was calibrated on 2026-10-08 (``TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY``, step 1) and is PROVISIONAL:
it leaves out the ``combat_engagement`` bucket (open defect ``TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP``), so V2 refits with combat included.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState

WORK_MODEL_VERSION = "WORK_MODEL_V1"
WORK_MODEL_STATUS = "PROVISIONAL"
ENTITY_MS = 0.68  # reference-ms per active entity
LEAD_MS = 7.42  # reference-ms per lead held by an active entity


@dataclass(frozen=True, slots=True)
class WorkDemand:
    """Pre-policy demand counts, read from authoritative state before the mode's scan policy, cadence or budgets act."""

    entities_active: int = 0
    leads: int = 0


def count_demand(state: AuthoritativeState) -> WorkDemand:
    """Count the demand in ``state``. Pure and order-independent: it reads entity fields and nothing else."""
    entities_active = 0
    leads = 0
    for entity in state.entities.values():
        if entity.lifecycle.active:
            entities_active += 1
            leads += len(entity.strategic.leads)
    return WorkDemand(entities_active=entities_active, leads=leads)


def tick_cost_ref_ms(demand: WorkDemand) -> float:
    """Modelled cost of one tick, in reference-milliseconds, under ``WORK_MODEL_VERSION``."""
    return ENTITY_MS * demand.entities_active + LEAD_MS * demand.leads

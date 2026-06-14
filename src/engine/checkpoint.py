# Compliance IDs: INFRA-119, INFRA-120, INFRA-121, INFRA-122, INFRA-123, INFRA-124, INFRA-125, INFRA-126, INFRA-127, INFRA-128, INFRA-129, INFRA-130, INFRA-133
# Compliance IDs: INFRA-196
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, Optional

from src.config.optimization_profiles import SubsystemBudget, SubsystemPressureReport, DEFAULT_HASHING_BUDGET
from src.core.state import AuthoritativeState

logger = logging.getLogger(__name__)


class CanonicalStateHasher:
    """
    Deterministic hasher for AuthoritativeState.
    """

    @staticmethod
    def get_hash(state: AuthoritativeState) -> str:
        """
        Produce a SHA256 hash of the compact canonical JSON representation.
        """
        compact_json = CanonicalStateHasher.to_canonical_json(state, pretty=False)
        return hashlib.sha256(compact_json.encode("utf-8")).hexdigest()

    @staticmethod
    def to_canonical_json(state: AuthoritativeState, pretty: bool = False) -> str:
        """
        Convert AuthoritativeState into a canonical JSON representation.
        """
        data = CanonicalStateHasher.to_canonical_data(state)
        
        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def to_canonical_data(state: AuthoritativeState) -> Dict[str, Any]:
        """
        Convert AuthoritativeState into a sortable dictionary structure.
        """
        # 1. Scalar fields
        data = {
            "tick": state.tick,
            "seed": state.seed,
            "world_time": state.world_time,
            "movement_count": state.movement_count,
            "maturity": state.maturity,
            "last_calamity_tick": state.last_calamity_tick,
            "town_center": state.town_center
        }
        
        # 2. Entities (Sorted by ID)
        sorted_entities = {}
        for eid in sorted(state.entities.keys()):
            sorted_entities[str(eid)] = state.entities[eid].to_canonical_dict()
        data["entities"] = sorted_entities
        
        # 3. Global collections (All sorted by key/id)
        data["regions"] = {k: v.to_canonical_dict() for k, v in sorted(state.regions.items())}
        data["local_scars"] = {str(k): v.to_canonical_dict() for k, v in sorted(state.local_scars.items())}
        data["resource_nodes"] = {str(k): v.to_canonical_dict() for k, v in sorted(state.resource_nodes.items())}
        data["buildings"] = {str(k): v.to_canonical_dict() for k, v in sorted(state.buildings.items())}
        data["corpses"] = {str(k): v.to_canonical_dict() for k, v in sorted(state.corpses.items())}
        data["ground_items"] = {str(k): v.to_canonical_dict() for k, v in sorted(state.ground_items.items())}
        data["chests"] = {str(k): v.to_canonical_dict() for k, v in sorted(state.chests.items())}
        data["groups"] = {str(k): v.to_canonical_dict() for k, v in sorted(state.groups.items())}
        data["home_storage"] = {str(k): v.to_canonical_dict() for k, v in sorted(state.home_storage.items())}
        data["camps"] = {k: v.to_canonical_dict() for k, v in sorted(state.camps.items())}
        
        data["global_resources"] = dict(sorted(state.global_resources.items()))
        data["periodic_due_ticks"] = dict(sorted(state.periodic_due_ticks.items()))
        data["work_debt"] = dict(sorted(state.work_debt.items()))
        
        data["blocked_tiles"] = sorted([str(t) for t in state.blocked_tiles])
        data["town_tiles"] = sorted([str(t) for t in state.town_tiles])
        data["building_tiles"] = {str(k): v for k, v in sorted(state.building_tiles.items(), key=lambda x: str(x[0]))}
        
        # 4. RNG Checkpoint
        data["rng_checkpoint"] = state.rng_checkpoint

        return data


class BudgetedCanonicalHasher:
    """
    Rate-limited wrapper around CanonicalStateHasher.

    Tracks the number of full-hash calls within a 100-tick sliding window.
    When the call count reaches the budget ceiling, a WARNING is logged and
    the last known (stale) hash is returned instead of computing a new one.

    Note: callers must handle the case where get_hash() is called before any
    successful hash has been computed (first call at or above the limit); in
    that case the stale hash fallback delegates to CanonicalStateHasher.get_hash()
    to avoid returning None.

    This class does NOT modify CanonicalStateHasher (INFRA-119–130 unaffected).
    degradation_action "returning_stale_hash" is advisory — the Governor decides
    how to react.
    """

    def __init__(self, budget: SubsystemBudget | None = None) -> None:
        self._budget: SubsystemBudget = budget or DEFAULT_HASHING_BUDGET
        self._call_count: int = 0
        self._window_start_tick: int = 0
        self._last_known_hash: Optional[str] = None

    def get_hash(self, state: AuthoritativeState, current_tick: int = 0) -> str:
        """
        Return a canonical hash of *state*, subject to the rate budget.

        Window resets every 100 ticks.  Over-budget calls return the last
        known hash (stale).  The hash value itself is bit-identical to
        CanonicalStateHasher.get_hash() on the normal path.
        """
        # Window reset: start a new 100-tick counting window.
        if current_tick - self._window_start_tick >= 100:
            self._call_count = 0
            self._window_start_tick = current_tick

        max_h = self._budget.max_full_hashes_per_100_ticks
        if max_h is not None and self._call_count >= max_h:
            logger.warning(
                "BudgetedCanonicalHasher: rate limit reached (%d/%d per 100 ticks)"
                " — returning stale hash",
                self._call_count,
                max_h,
            )
            # Return stale hash; fall back to a fresh hash if none is cached yet
            # (first call over-budget, e.g. budget=0).
            return self._last_known_hash or CanonicalStateHasher.get_hash(state)

        self._call_count += 1
        self._last_known_hash = CanonicalStateHasher.get_hash(state)
        return self._last_known_hash

    def pressure_report(self) -> SubsystemPressureReport:
        """
        Advisory pressure snapshot for the hashing subsystem.

        Returns WARN when call_count exceeds max_full_hashes_per_100_ticks
        (i.e. the rate limiter is active and stale hashes are being returned).
        Returns OK when within budget or when budget is unlimited (None).
        """
        max_h = self._budget.max_full_hashes_per_100_ticks
        if max_h is None:
            return SubsystemPressureReport(
                subsystem="hashing",
                current_usage=float(self._call_count),
                budget=None,
                pressure_state="OK",
                degradation_action=None,
            )
        pct = self._call_count / max_h
        if pct < 0.8:
            state, action = "OK", None
        elif pct < 1.0:
            state, action = "WARN", "reduce_hash_frequency"
        else:
            state, action = "DEGRADED", "returning_stale_hash"
        return SubsystemPressureReport(
            subsystem="hashing",
            current_usage=float(self._call_count),
            budget=float(max_h),
            pressure_state=state,
            degradation_action=action,
        )

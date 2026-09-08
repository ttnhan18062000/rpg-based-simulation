# Compliance IDs: INFRA-119, INFRA-120, INFRA-121, INFRA-122, INFRA-123, INFRA-124, INFRA-125, INFRA-126, INFRA-127, INFRA-128, INFRA-129, INFRA-130, INFRA-133
# Compliance IDs: INFRA-196, INFRA-197
from __future__ import annotations

import dataclasses
import hashlib
import json
import logging
from enum import Enum
from typing import Any, Dict, Optional

from src.config.optimization_profiles import SubsystemBudget, SubsystemPressureReport, DEFAULT_HASHING_BUDGET
from src.core.state import AuthoritativeState

logger = logging.getLogger(__name__)


class HashMode(str, Enum):
    """Controls whether a full or light canonical hash is computed.

    FULL  — delegates to CanonicalStateHasher.get_hash(); expensive, deterministic proof.
            Only allowed at sanctioned boundaries (see CanonicalHashScheduler.allow_full_hash_at).
    LIGHT — hashes (tick, seed, entity_count, region_count) via MD5; fast dirty signal only,
            NOT a cryptographic proof and NOT suitable for determinism verification.
    """
    FULL = "full"
    LIGHT = "light"


class HashScheduleViolation(RuntimeError):
    """Raised when a FULL canonical hash is requested outside a sanctioned boundary.

    INFRA-197: Full canonical hashing must only occur at start-of-run (tick=0),
    end-of-run (shutdown), or when an explicit sanctioned reason is provided
    ("certification", "audit", "replay"). Any other FULL hash call is a violation.
    """


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
        data["places"] = {k: v.to_canonical_dict() for k, v in sorted(state.places.items())}  # Idea 66
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

        # 5. Dormant Mechanism Closure epic bridge fields
        # (TCK-20260907-CAMPAIGN-BRIDGE-FIELDS-STATE-HASH-COVERAGE): confirmed via direct test
        # that two states differing ONLY in one of these 6 fields previously produced identical
        # hashes -- a real determinism-verification gap, not benign (personality_bias's own
        # contribution from these fields is not guaranteed to flip any entity's resulting
        # decision/state on the same tick it changes, so a real divergence here could silently
        # escape detection at a certification/replay checkpoint).
        data["region_loyalty_pressure"] = dict(sorted(state.region_loyalty_pressure.items()))
        data["region_culture_states"] = {
            k: v.to_dict() for k, v in sorted(state.region_culture_states.items())
        }
        data["entity_legend_facts"] = {
            k: v.to_dict() for k, v in sorted(state.entity_legend_facts.items())
        }
        # List[InformationSourceProfile], not keyed -- sort by (source_id, source_kind) for a
        # stable canonical order independent of insertion order.
        data["information_source_profiles"] = sorted(
            (dataclasses.asdict(p) for p in state.information_source_profiles),
            key=lambda d: (str(d.get("source_id")), str(d.get("source_kind"))),
        )
        data["entity_belief_institutions"] = {
            str(k): [
                inst.to_dict()
                for inst in sorted(v, key=lambda i: (i.origin_event_id, i.clan_id))
            ]
            for k, v in sorted(state.entity_belief_institutions.items())
        }
        data["event_fidelity"] = dict(sorted(state.event_fidelity.items()))

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


# Sanctioned reasons that permit a FULL canonical hash outside tick 0 / run-end.
_SANCTIONED_REASONS: frozenset = frozenset({"certification", "audit", "replay"})


class CanonicalHashScheduler:
    """Enforces that FULL canonical hashing only occurs at sanctioned boundaries.

    INFRA-197: Full canonical hashing is expensive (sorts and JSON-serialises all
    collections). It must only occur at:
      - tick == 0  (start-of-run baseline)
      - tick == run_end_tick  (end-of-run final hash)
      - reason in {"certification", "audit", "replay"}  (explicit sanctioned call)

    All other full-hash attempts raise HashScheduleViolation.

    LIGHT hashing hashes (tick, seed, entity_count, region_count) via MD5 — a cheap
    dirty signal. It is NOT a determinism proof and must not be used for certification.
    """

    def __init__(self, run_end_tick: int = -1) -> None:
        self._run_end_tick = run_end_tick

    def allow_full_hash_at(self, tick: int, reason: str) -> bool:
        """Return True if a FULL hash is sanctioned at the given tick and reason."""
        if tick == 0:
            return True
        if self._run_end_tick >= 0 and tick == self._run_end_tick:
            return True
        if reason in _SANCTIONED_REASONS:
            return True
        return False

    def compute_hash(
        self,
        state: AuthoritativeState,
        tick: int,
        mode: HashMode = HashMode.LIGHT,
        reason: str = "",
    ) -> str:
        """Compute a canonical hash according to *mode*.

        FULL:  delegates to CanonicalStateHasher.get_hash(state). Raises
               HashScheduleViolation if tick/reason is not sanctioned.
        LIGHT: hashes (tick, seed, entity_count, region_count) via MD5.
               Always allowed; no state-walk or JSON serialisation.
        """
        if mode is HashMode.FULL:
            if not self.allow_full_hash_at(tick, reason):
                raise HashScheduleViolation(
                    f"Full canonical hash requested at tick={tick} reason={reason!r} "
                    f"but this is not a sanctioned boundary. "
                    f"Use reason='certification'|'audit'|'replay', or tick=0/run_end."
                )
            return CanonicalStateHasher.get_hash(state)
        # LIGHT: fast non-cryptographic dirty signal
        payload = f"{tick}:{state.seed}:{len(state.entities)}:{len(state.regions)}"
        return hashlib.md5(payload.encode("utf-8"), usedforsecurity=False).hexdigest()

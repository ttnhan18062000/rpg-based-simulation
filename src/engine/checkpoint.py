# Compliance IDs: INFRA-119, INFRA-120, INFRA-121, INFRA-122, INFRA-123, INFRA-124, INFRA-125, INFRA-126, INFRA-127, INFRA-128, INFRA-129, INFRA-130, INFRA-133
# Compliance IDs: INFRA-196, INFRA-197
from __future__ import annotations

import dataclasses
import hashlib
import json
from enum import Enum
from typing import Any, Dict, Optional

from src.core.state import AuthoritativeState

# PERF-D5 point 2: the proof digest is named and versioned. A stored or emitted digest of a
# different scheme is never compared with this one.
PROOF_DIGEST_SCHEME = "flat-sha256-v1"


class DigestStatus(str, Enum):
    """Whether a proof digest was computed, and if not, why. Replaces the bare string "SKIPPED"."""
    COMPUTED = "computed"
    NOT_COMPUTED_UNSANCTIONED_BOUNDARY = "not_computed_unsanctioned_boundary"
    NOT_COMPUTED_LIVE_POLICY = "not_computed_live_policy"  # the kernel's replay-richness skip


@dataclasses.dataclass(frozen=True, slots=True)
class ProofDigest:
    """A proof digest (or the report that none was computed) with its scheme, tick and status.

    `value` is None exactly when `status` is not COMPUTED. A value is never served stale.
    """
    scheme: str
    tick: int
    status: DigestStatus
    value: Optional[str] = None

    def __post_init__(self) -> None:
        if (self.value is None) == (self.status is DigestStatus.COMPUTED):
            raise ValueError("ProofDigest.value must be set if and only if status is COMPUTED")

    def require_value(self) -> str:
        """The digest value, for a caller at a boundary that is always sanctioned. Raises if it was not computed."""
        if self.value is None:
            raise ValueError(f"proof digest at tick {self.tick} was not computed ({self.status.value})")
        return self.value


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


# Sanctioned reasons that permit a FULL canonical hash outside tick 0 / run-end.
_SANCTIONED_REASONS: frozenset = frozenset({"certification", "audit", "replay"})


class CanonicalHashScheduler:
    """Enforces that FULL canonical hashing only occurs at sanctioned boundaries.

    INFRA-197: Full canonical hashing is expensive (sorts and JSON-serialises all
    collections). It must only occur at:
      - tick == 0  (start-of-run baseline)
      - tick == run_end_tick  (end-of-run final hash)
      - reason in {"certification", "audit", "replay"}  (explicit sanctioned call)

    All other full-hash attempts raise HashScheduleViolation (`compute_hash`) or are reported as
    not computed (`compute_digest`). A digest is computed for the current state or reported as not
    computed; it is never served stale (PERF-D5 point 3).
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

    @staticmethod
    def not_computed_by_policy(tick: int) -> ProofDigest:
        """The digest record for a tick whose live policy does not hash (PERF-D5 point 4: the cadence is unchanged)."""
        return ProofDigest(PROOF_DIGEST_SCHEME, tick, DigestStatus.NOT_COMPUTED_LIVE_POLICY)

    def compute_digest(self, state: AuthoritativeState, tick: int, reason: str = "") -> ProofDigest:
        """Return the proof digest of *state* with its scheme, tick and status.

        An unsanctioned boundary is reported as NOT_COMPUTED_UNSANCTIONED_BOUNDARY, not raised.
        """
        if not self.allow_full_hash_at(tick, reason):
            return ProofDigest(PROOF_DIGEST_SCHEME, tick, DigestStatus.NOT_COMPUTED_UNSANCTIONED_BOUNDARY)
        return ProofDigest(PROOF_DIGEST_SCHEME, tick, DigestStatus.COMPUTED, CanonicalStateHasher.get_hash(state))

    def compute_hash(
        self,
        state: AuthoritativeState,
        tick: int,
        reason: str = "",
    ) -> str:
        """Compute the flat proof digest value of *state*.

        Delegates to CanonicalStateHasher.get_hash(state). Raises HashScheduleViolation if
        tick/reason is not sanctioned.
        """
        if not self.allow_full_hash_at(tick, reason):
            raise HashScheduleViolation(
                f"Full canonical hash requested at tick={tick} reason={reason!r} "
                f"but this is not a sanctioned boundary. "
                f"Use reason='certification'|'audit'|'replay', or tick=0/run_end."
            )
        return CanonicalStateHasher.get_hash(state)

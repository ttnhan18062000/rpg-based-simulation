"""Compare tactics' hostility predicate with legality's at every verify_attack_legality call.

usage: hostility_probe.py <root> <world> <ticks>

At each call (any caller) it recomputes, with the same RelationContext legality builds:
  tactical_pred   = is_hostile_compat(resolver ids)            (tactical.py:243-249 as written)
  legality_pred   = has_clean ? is_hostile_compat(get_faction_id_str ids) : raw legacy faction inequality
                                                                (legality.py:252-272 as written; hostile == not FRIENDLY_FIRE)
  has_clean forward / reverse (attacker->target, target->attacker), the raw ids, and each entity's
  EntityIdentityResolver source (clean_metadata = carries a catalog faction_id; compatibility_projection =
  legacy enum only, the shape of a runtime-spawned monster).
Counts calls (verdicts) and DISTINCT attacker/target entity pairs and DISTINCT faction-id pairs, plus the real
verdict reasons. Settings: audit_mode=True, max_tick_budget_ms=1e9, seed 42.
"""
import collections
import json
import sys

ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, ROOT)
import src  # noqa: E402
from src.config.profiles import PROD_SMALL  # noqa: E402
from src.content_semantics.faction import get_faction_id_str, get_faction_semantics_service, get_species_id_str  # noqa: E402
from src.content_semantics.relation import RelationContext  # noqa: E402
from src.engine.executor import LocalSequentialExecutor  # noqa: E402
from src.engine.kernel import Kernel  # noqa: E402
from src.engine.legality import LegalityServiceV2  # noqa: E402
from src.entities.identity_resolver import EntityIdentityResolver, IdentityResolutionError  # noqa: E402
from src.platform.rng import DeterministicRNG  # noqa: E402
from src.worldbuilding.compiler import WorldCompiler  # noqa: E402
from src.worldbuilding.repository import WorldRepository  # noqa: E402

assert src.__file__.startswith(ROOT), (src.__file__, ROOT)
RES = EntityIdentityResolver()
C = collections.Counter()
PAIRS = {}  # (att_id, tgt_id) -> dict
FACPAIRS = collections.Counter()
_vl = LegalityServiceV2.verify_attack_legality


def resolve(e):
    try:
        r = RES.resolve(e)
        return r.faction_id, r.source
    except IdentityResolutionError:
        return get_faction_id_str(e), "legacy_fallback"


def has_clean(svc, source, target):
    for p in svc.repo.perspectives.values():
        if p.chosen_faction == source or p.id == source:
            return True
    for rel in svc.repo.faction_relationships.values():
        if rel.source_faction == source and rel.target_faction == target:
            return True
    return False


def vl(attacker, target, state, *a, **k):
    res = _vl(attacker, target, state, *a, **k)
    try:
        svc = get_faction_semantics_service()
        af, tf = get_faction_id_str(attacker), get_faction_id_str(target)
        (rtaf, asrc), (rttf, tsrc) = resolve(attacker), resolve(target)
        dist = LegalityServiceV2.get_manhattan_dist(attacker.navigation.position, target.navigation.position)
        engaged = attacker.task.payload.get("target_id") == target.id or target.task.payload.get("target_id") == attacker.id
        ctx = RelationContext(distance=float(dist), combat_engaged=engaged,
                              source_species=get_species_id_str(attacker), target_species=get_species_id_str(target))
        fwd, rev = has_clean(svc, af, tf), has_clean(svc, tf, af)
        tactical_pred = bool(svc.is_hostile_compat(rtaf, rttf, ctx))
        legality_pred = bool(svc.is_hostile_compat(af, tf, ctx)) if fwd else (attacker.identity.faction != target.identity.faction)
        # the same pair seen from the other side (the asymmetry the ticket suspects)
        fwd_r_pred = bool(svc.is_hostile_compat(tf, af, ctx)) if rev else (attacker.identity.faction != target.identity.faction)
        key = (attacker.id, target.id)
        C["calls"] += 1
        reason = str(res[1]).replace("ReasonCode.", "")
        C[f"verdict.{reason}"] += 1
        disagree = tactical_pred != legality_pred
        if disagree:
            C["calls.predicates_disagree"] += 1
            if reason == "FRIENDLY_FIRE_ILLEGAL":
                C["calls.disagree_and_friendly_fire"] += 1
        if reason == "FRIENDLY_FIRE_ILLEGAL":
            C["calls.friendly_fire"] += 1
            if tactical_pred:
                C["calls.friendly_fire_but_tactics_says_hostile"] += 1
        if not fwd:
            C["calls.has_clean_false_forward"] += 1
        if fwd != rev:
            C["calls.has_clean_asymmetric"] += 1
        if legality_pred != fwd_r_pred:
            C["calls.legality_pred_differs_by_direction"] += 1
        if rtaf != af or rttf != tf:
            C["calls.resolver_id_differs_from_get_faction_id_str"] += 1
        p = PAIRS.setdefault(key, {"calls": 0, "disagree": 0, "ff": 0})
        p["calls"] += 1
        p["disagree"] += int(disagree)
        p["ff"] += int(reason == "FRIENDLY_FIRE_ILLEGAL")
        FACPAIRS[(af, tf, asrc, tsrc, fwd, rev, tactical_pred, legality_pred, reason == "FRIENDLY_FIRE_ILLEGAL")] += 1
    except Exception as exc:  # the probe must never change the run
        C[f"probe_error.{type(exc).__name__}"] += 1
    return res


LegalityServiceV2.verify_attack_legality = staticmethod(vl)
repo = WorldRepository(f"{ROOT}/data/worlds")
spec, ctx_ = repo.load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, 42, context=ctx_)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
try:
    for _ in range(TICKS):
        k.tick_once()
finally:
    k.shutdown()
out = dict(sorted(C.items()))
out["distinct_entity_pairs"] = len(PAIRS)
out["distinct_pairs_disagree"] = sum(1 for p in PAIRS.values() if p["disagree"])
out["distinct_pairs_friendly_fire"] = sum(1 for p in PAIRS.values() if p["ff"])
out["distinct_faction_rows"] = len(FACPAIRS)
print("HOSTILITY-PROBE", WORLD, TICKS, json.dumps(out))
for row, n in FACPAIRS.most_common(12):
    print("ROW", n, "att,tgt,att_src,tgt_src,fwd,rev,tactical,legality,ff =", row)

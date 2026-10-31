"""Instrument helpers shared by profile_run.py and test_instrument.py (read-only mirrors of groups.py l.95-170 and a per-entity growth snapshot)."""
import dataclasses as _dc_unused, json, os
from src.core.strategic import ContractStatus
def _eff(cu, e_id):
    return cu.entity_updates.get(e_id) if cu is not None else None
def _alive(state, cu, e_id):
    u = _eff(cu, e_id)
    if u is not None and u.combat and u.combat.alive_set is False: return False
    e = state.entities.get(e_id); return e.combat.alive if e else False
def _active(state, cu, e_id):
    u = _eff(cu, e_id)
    if u is not None and u.active is False: return False
    e = state.entities.get(e_id); return e.lifecycle.active if e else False
def _pos(state, cu, e_id):
    u = _eff(cu, e_id)
    if u is not None and u.new_position: return u.new_position
    e = state.entities.get(e_id); return e.navigation.position if e else (0.0, 0.0)
def _reasons(state, cu, grp):
    """Mirror of groups.py l.95-170 on the pre-state: which branch ends this group. Read-only."""
    ldr = state.entities.get(grp.leader_id)
    if ldr is None or not _alive(state, cu, grp.leader_id) or not _active(state, cu, grp.leader_id): return ["l110_leader_dead_inactive_or_missing"]
    out = []; kept = 1
    for m in sorted(grp.member_ids):
        if m == grp.leader_id: continue
        if not _alive(state, cu, m) or not _active(state, cu, m): out.append("member_dead_or_inactive"); continue
        mp = _pos(state, cu, m); dx = mp[0] - grp.anchor[0]; dy = mp[1] - grp.anchor[1]
        dist = dx * dx + dy * dy > (grp.cohesion_radius * 2) ** 2
        cinv = None
        if grp.contract_id and ldr:
            c = None
            if cu is not None and grp.leader_id in cu.entity_updates:
                lu = cu.entity_updates[grp.leader_id]
                if lu.strategic: c = next((x for x in lu.strategic.contracts_add_or_update if x.id == grp.contract_id), None)
            if not c: c = ldr.strategic.contracts.get(grp.contract_id)
            if not c: cinv = "missing"
            elif c.status != ContractStatus.ACTIVE: cinv = "not_active:" + str(getattr(c.status, "value", c.status))
            elif c.expiry_tick != -1 and state.tick > c.expiry_tick: cinv = "expired"
        if dist and cinv: out.append("member_distance_and_contract_" + cinv)
        elif dist: out.append("member_distance")
        elif cinv: out.append("member_contract_" + cinv)
        else: kept += 1
    return out if kept < 2 and out else (["l170_fewer_than_2_members_no_cause_found"] if kept < 2 else [])

import dataclasses as _dc
GROWTH_TICKS = {int(x) for x in os.environ.get("GROWTH_TICKS", "500,1000,2000").split(",")}
def _growth(state):
    ents = [e for e in state.entities.values() if e.combat.alive]
    out = dict(living=len(ents), canon_json_bytes={}, entries={}, named={})
    for e in ents:
        cd = e.to_canonical_dict()
        for k, v in cd.items(): out["canon_json_bytes"][k] = out["canon_json_bytes"].get(k, 0) + len(json.dumps(v, default=str, sort_keys=True))
        for comp in ("strategic", "social", "self_model", "cognition"):
            c = getattr(e, comp, None)
            if c is None or not _dc.is_dataclass(c): continue
            for f in _dc.fields(c):
                v = getattr(c, f.name, None)
                if isinstance(v, (dict, list, tuple, set, frozenset)): out["entries"][comp + "." + f.name] = out["entries"].get(comp + "." + f.name, 0) + len(v)
        for nm, v in (("strategic.contracts", e.strategic.contracts), ("social.trust_history", e.social.trust_history), ("social.grudge_history", e.social.grudge_history),
                      ("social.fear_history", e.social.fear_history), ("social.familiarity_history", e.social.familiarity_history), ("social.salience_history", e.social.salience_history),
                      ("social.bonds", e.social.bonds), ("social.betrayal_records", e.social.betrayal_records), ("strategic.turning_points", e.strategic.turning_points),
                      ("strategic.beliefs", e.strategic.beliefs), ("strategic.source_trust", e.strategic.source_trust), ("strategic.hypotheses", e.strategic.hypotheses),
                      ("strategic.committed_intentions", e.strategic.committed_intentions)):
            out["named"][nm] = out["named"].get(nm, 0) + len(v)
    return out

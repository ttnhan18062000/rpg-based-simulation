"""Instrument proof (scratch): (1) the contract-invalid split on synthetic states, checked against the real update_groups; (2) the social/strategic growth fields read non-zero on a state with histories, and the cooperation penalty path writes fields that are in the list.
Run: cd <tree> && PYTHONPATH=. python test_instrument.py   (from the probe directory on sys.path)"""
import sys, os
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dataclasses import replace
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, GroupRecord
from src.core.strategic import ContractKind, ContractState, ContractStatus
from src.core.updates import EntityUpdate, SocialUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.systems.world_systems.groups import GroupSystem
from profile_helpers import _reasons, _growth

def state_with(contract, tick=10, cid="c1"):
    cs = {} if contract is None else {cid: contract}
    ents = {1: V2EntityBuilder(1).kind("actor").location(0.0, 0.0).strategic(contracts=cs).build(),
            2: V2EntityBuilder(2).kind("actor").location(0.5, 0.5).build()}
    g = GroupRecord(id=10000, leader_id=1, member_ids={1, 2}, anchor=(0.2, 0.2), contract_id=cid)
    return AuthoritativeState(tick=tick, seed=1, entities=ents, groups={10000: g})

def mk(status, expiry=-1): return ContractState(id="c1", kind=ContractKind.RECRUITMENT, source_id=1, target_id=2, status=status, expiry_tick=expiry)
cases = [("missing", None, "member_contract_missing"),
         ("not_active", mk(ContractStatus.FAILED), "member_contract_not_active:FAILED"),
         ("expired", mk(ContractStatus.ACTIVE, expiry=5), "member_contract_expired"),
         ("valid (control: no dissolution)", mk(ContractStatus.ACTIVE, expiry=-1), None),
         ("valid, expiry in the future (control)", mk(ContractStatus.ACTIVE, expiry=50), None)]
ok = True
for name, c, want in cases:
    st = state_with(c); grp = st.groups[10000]
    got = _reasons(st, None, grp)
    upd = GroupSystem.update_groups(st)
    dissolved = any(g.id == 10000 and g.dissolution_tick == st.tick for g in upd.groups_add_or_update)
    good = (got == [want] and dissolved) if want else (got == [] and not dissolved)
    ok &= good
    print(f"{'PASS' if good else 'FAIL'} {name}: mirror {got} | real update_groups dissolved {dissolved}")

# (2) growth fields read non-zero on a state with histories; the cooperation penalty path
e = V2EntityBuilder(1).kind("actor").location(0, 0).strategic(contracts={"c1": mk(ContractStatus.ACTIVE)}).build()
from src.core.state import SocialComponent
soc = replace(e.social, trust_history={2: 0.4, 3: 0.2}, grudge_history={2: 0.3}, fear_history={4: 0.1}, familiarity_history={2: 0.5}, salience_history={2: 0.1})
e = replace(e, social=soc)
st = AuthoritativeState(tick=1, seed=1, entities={1: e})
gr = _growth(st)["named"]
want = {"social.trust_history": 2, "social.grudge_history": 1, "social.fear_history": 1, "social.familiarity_history": 1, "social.salience_history": 1, "strategic.contracts": 1}
good = all(gr.get(k) == v for k, v in want.items()); ok &= good
print(("PASS" if good else "FAIL"), "growth fields read the seeded histories:", {k: gr.get(k) for k in want})
# the cooperation penalty writes SocialUpdate.trust_delta / grudge_delta, applied by relationships.py into social.trust_history / grudge_history
e2 = V2EntityBuilder(2).kind("actor").location(0, 0).build()
st2 = AuthoritativeState(tick=1, seed=1, entities={1: V2EntityBuilder(1).kind("actor").location(0, 0).build(), 2: e2})
before = _growth(st2)["named"]
new = ApplyPath.apply_generation(st2, StateUpdate(entity_updates={2: EntityUpdate(entity_id=2, social=SocialUpdate(trust_delta={1: -0.25}, grudge_delta={1: 0.3}))}))
after = _growth(new)["named"]
good = before["social.trust_history"] == 0 and after["social.trust_history"] == 1 and before["social.grudge_history"] == 0 and after["social.grudge_history"] == 1
ok &= good
print(("PASS" if good else "FAIL"), "applying the cooperation penalty's SocialUpdate (trust_delta -0.25, grudge_delta 0.3 toward the leader) moves:", {k: (before[k], after[k]) for k in ("social.trust_history", "social.grudge_history")})
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)

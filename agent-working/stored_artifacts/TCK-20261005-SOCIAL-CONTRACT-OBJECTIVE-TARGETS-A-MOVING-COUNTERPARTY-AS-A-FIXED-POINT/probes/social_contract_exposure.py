"""How live is the social-contract objective path in the corpus?  (TCK-20261005-SOCIAL-CONTRACT-OBJECTIVE-TARGETS-...)

usage: social_contract_exposure.py <root> <world> <ticks>   (cwd is set to <root>; content seeds from the cwd-relative data/content)
Settings: audit_mode=True, max_tick_budget_ms=1e9, seed 42, LocalSequentialExecutor.

Reports, per world: scorer calls and how many had an ACTIVE mapped contract candidate; contract statuses seen on entities; and for every
materialized contract project (id proj_contract_<contract id>_t<tick>): ticks it was the entity's ACTIVE project, ticks the objective's
captured target_position differed from the counterparty's live position (and the largest Manhattan gap), and ticks it stayed ACTIVE
while its contract was no longer ACTIVE (or gone)."""
import collections
import json
import os
import re
import sys

ROOT, WORLD, TICKS = sys.argv[1], sys.argv[2], int(sys.argv[3])
os.chdir(ROOT)
sys.path.insert(0, ROOT)
import src  # noqa: E402
from src.ai.goals.social_contract_scorer import SocialContractGoalScorer  # noqa: E402
from src.config.profiles import PROD_SMALL  # noqa: E402
from src.core.strategic import ContractStatus, ProjectStatus  # noqa: E402
from src.engine.executor import LocalSequentialExecutor  # noqa: E402
from src.engine.kernel import Kernel  # noqa: E402
from src.platform.rng import DeterministicRNG  # noqa: E402
from src.worldbuilding.compiler import WorldCompiler  # noqa: E402
from src.worldbuilding.repository import WorldRepository  # noqa: E402

assert src.__file__.startswith(ROOT), (src.__file__, ROOT)
C = collections.Counter()
KINDS = collections.Counter()
_score = SocialContractGoalScorer.score


def score(self, entity, state):
    out = _score(self, entity, state)
    C["scorer calls"] += 1
    if out.utility > 0:
        C["scorer calls with a mapped ACTIVE contract (utility > 0)"] += 1
    return out


SocialContractGoalScorer.score = score
repo = WorldRepository(f"{ROOT}/data/worlds")
spec, ctx = repo.load_world_with_context(WORLD)
state, _ = WorldCompiler.compile(spec, 42, context=ctx)
k = Kernel(profile=PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state=state, rng=DeterministicRNG(42),
           flags={"no_frame_pacing": True, "no_replay": True, "audit_mode": True}, executor=LocalSequentialExecutor())
PROJ = {}
STATUS_SEEN = collections.Counter()
try:
    for _ in range(TICKS):
        k.tick_once()
        st = k._state
        for e in st.entities.values():
            for c in e.strategic.contracts.values():
                STATUS_SEEN[f"{c.kind.name}/{c.status.name}"] += 1
            for pid, p in e.strategic.projects.items():
                if not pid.startswith("proj_contract_"):
                    continue
                rec = PROJ.setdefault((e.id, pid), {"start": st.tick, "ticks_active": 0, "diff_ticks": 0, "max_gap": 0,
                                                    "active_after_contract_gone": 0, "counterparty": None, "kind": None})
                if p.status != ProjectStatus.ACTIVE:
                    continue
                rec["ticks_active"] += 1
                obj = next((o for o in p.objectives if o.id == p.active_objective_id), None)
                cid = re.sub(r"_t\d+$", "", pid[len("proj_contract_"):])
                contract = e.strategic.contracts.get(cid)
                rec["kind"] = contract.kind.name if contract else "(contract gone)"
                if contract is None or contract.status != ContractStatus.ACTIVE:
                    rec["active_after_contract_gone"] += 1
                if obj is not None and obj.target is not None:
                    try:
                        cp = st.entities.get(int(obj.target))
                    except ValueError:
                        cp = None
                    rec["counterparty"] = obj.target
                    if cp is not None and obj.target_position is not None:
                        gap = abs(cp.navigation.position[0] - obj.target_position[0]) + abs(cp.navigation.position[1] - obj.target_position[1])
                        if gap > 0:
                            rec["diff_ticks"] += 1
                            rec["max_gap"] = max(rec["max_gap"], gap)
finally:
    k.shutdown()
out = dict(sorted(C.items()))
out["contract status-ticks seen (entity-tick, by kind/status)"] = dict(sorted(STATUS_SEEN.items()))
out["materialized contract projects"] = len(PROJ)
out["projects"] = [dict(entity=e, project=p, **r) for (e, p), r in sorted(PROJ.items())][:12]
out["ticks active, summed"] = sum(r["ticks_active"] for r in PROJ.values())
out["ticks captured != live, summed"] = sum(r["diff_ticks"] for r in PROJ.values())
out["ticks active after contract not ACTIVE/gone, summed"] = sum(r["active_after_contract_gone"] for r in PROJ.values())
print("SOCIAL-CONTRACT-EXPOSURE", WORLD, TICKS, json.dumps(out))

"""P1 entity 10 path (scratch, read-only). PROBE_OUT=<jsonl> python probe5.py <scenario_key>: ScoreModifierSystem.apply_modifiers (raw -> modified) and evaluate_project_switch for entity 10, t105-113."""
import json, os, sys, runpy
sys.path.insert(0, ".")
OUT = open(os.environ["PROBE_OUT"], "w")
def log(**r): OUT.write(json.dumps(r, default=str, separators=(",", ":")) + "\n")
from src.ai.score_modifiers import ScoreModifierSystem as SM
om = SM.apply_modifiers
def am(entity, state, scores):
    res = om(entity, state, scores)
    if entity.id == 10 and 105 <= state.tick <= 113:
        log(k="mod", t=state.tick, raw=[[str(s.kind), round(s.utility, 4)] for s in sorted(scores, key=lambda s: -s.utility)[:5]],
            mod=[[str(s.kind), round(s.utility, 4)] for s in sorted(res, key=lambda s: -s.utility)[:5]],
            blockers=[[b.id, b.kind, b.subject, b.severity, b.resolved] for b in entity.strategic.blockers.values()],
            personality=str(entity.identity.personality), life_stage=str(entity.identity.life_stage), boredom=dict(entity.strategic.boredom))
    return res
SM.apply_modifiers = staticmethod(am)
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem as SI
oe = SI.evaluate_project_switch
def ev(entity, candidate_project, current_tick, state=None):
    res = oe(entity, candidate_project, current_tick, state=state)
    if entity.id == 10 and 105 <= current_tick <= 113:
        cur = entity.strategic.projects.get(entity.strategic.current_project_id)
        log(k="switch", t=current_tick, candidate=candidate_project.id, cand_score=candidate_project.score, current=(cur.id if cur else None),
            current_status=(str(cur.status) if cur else None), current_score=(cur.score if cur else None), lock_until=(cur.lock_until_tick if cur else None),
            result_current_project_id_set=(res.current_project_id_set if res else None), switched=bool(res))
    return res
SI.evaluate_project_switch = staticmethod(ev)
sys.argv = ["evaluate_simq", "--scenario", sys.argv[1]]
try: runpy.run_path("tools/evaluate_simq.py", run_name="__main__")
except SystemExit as ex: log(k="exit", code=str(ex.code))
OUT.close()

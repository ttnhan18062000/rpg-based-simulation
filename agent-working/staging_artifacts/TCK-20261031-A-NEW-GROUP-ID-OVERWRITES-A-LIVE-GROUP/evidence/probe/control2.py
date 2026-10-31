"""Probe v2 control for timers and work counts: calls the real phases on a known state. Expect phase_calls=1, coop_calls=1, work_phase=3 (3 stored ids), work_coop=3, work_relevant>=1."""
import sys, os
sys.path.insert(0, os.getcwd()); sys.path.insert(0, os.path.dirname(__file__))
import probe_groups2 as P
P.install()
exec(open(os.path.join(os.path.dirname(__file__), "control.py")).read().split("for collide in")[0].split("P.install()")[1])
from src.engine.pipeline_phases.groups import GroupPhase
from src.domains.cooperation.phase import CooperationPhase
from src.core.updates import StateUpdate
st = build(True)
GroupPhase.resolve(st, StateUpdate()); CooperationPhase.execute(st, StateUpdate())
s = P.summary(); print({k: s[k] for k in ("phase_calls","coop_calls","work_phase","work_coop","work_relevant","upd_calls")})

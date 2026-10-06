import ast
import dataclasses
import sys

sys.path.insert(0, "/mnt/data/Working/rpg-based-simulation/.claude/worktrees/attack-path-trace")
from src.core.enums import ReasonCode
from src.core.updates import EntityUpdate, NavigationUpdate

P = "/mnt/data/Working/rpg-based-simulation/.claude/worktrees/attack-path-trace/agent-working/staging_artifacts/TCK-20261005-ACTION-HANDLERS-MAY-RETURN-BARE-NO-OPS-THAT-HOLD-THE-TASK/probes/handler_exposure.py"
tree = ast.parse(open(P).read())
ns = {"dataclasses": dataclasses, "IGNORED": {"entity_id", "readiness_delta"}}
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == "classify":
        exec(compile(ast.Module([node], []), P, "exec"), ns)
c = ns["classify"]
print("bare       ->", c(EntityUpdate(entity_id=1, readiness_delta=0.0)))
print("bare -10   ->", c(EntityUpdate(entity_id=1, readiness_delta=-10.0)))
print("failure    ->", c(EntityUpdate(entity_id=1, navigation=NavigationUpdate(failure_reason=ReasonCode.UNSUPPORTED_ACTION))))
print("effect     ->", c(EntityUpdate(entity_id=1, readiness_delta=-100.0, navigation=NavigationUpdate(target_set=(1, 1)))))
print("none       ->", c(None))

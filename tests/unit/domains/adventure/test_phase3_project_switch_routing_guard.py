"""
tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py

Architecture guard: AdventureDecisionPhase.apply()'s project-commit branch must route
through StrategicIntelligenceSystem.evaluate_project_switch() rather than constructing
current_project_id_set directly. This fails loudly if a future edit reintroduces the
unconditional overwrite this ticket (TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION)
fixed, mirroring the project's "authoritative application path was used" architecture-test
pattern (CLAUDE.md Architecture Rule).
"""
import ast
import inspect
import textwrap

from src.domains.adventure import phase as phase_module
from src.domains.adventure.phase import AdventureDecisionPhase


def test_apply_commit_branch_does_not_construct_strategic_update_directly():
    """AST-level check: within AdventureDecisionPhase.apply()'s source, no `StrategicUpdate(`
    call site directly sets `current_project_id_set=` -- the only way to produce a
    StrategicUpdate assigned to `strat_upd` in the commit branch must be via
    `StrategicIntelligenceSystem.evaluate_project_switch(...)`."""
    source = textwrap.dedent(inspect.getsource(AdventureDecisionPhase.apply))
    tree = ast.parse(source)

    strategic_update_direct_calls = []
    evaluate_project_switch_calls = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            call_name = None
            if isinstance(func, ast.Name):
                call_name = func.id
            elif isinstance(func, ast.Attribute):
                call_name = func.attr

            if call_name == "StrategicUpdate":
                strategic_update_direct_calls.append(node)
            elif call_name == "evaluate_project_switch":
                evaluate_project_switch_calls.append(node)

    assert not strategic_update_direct_calls, (
        "AdventureDecisionPhase.apply() must not construct StrategicUpdate(...) directly for "
        "its project-commit branch -- it must go through "
        "StrategicIntelligenceSystem.evaluate_project_switch() so the lock-bypass gate is "
        "always enforced."
    )
    assert evaluate_project_switch_calls, (
        "AdventureDecisionPhase.apply() no longer calls "
        "StrategicIntelligenceSystem.evaluate_project_switch() -- the authoritative "
        "project-switch gate is not being used."
    )


def test_apply_module_imports_strategic_intelligence_system():
    """Guards against the import being silently removed while the call site is refactored
    into something that still bypasses the shared gate."""
    assert hasattr(phase_module, "StrategicIntelligenceSystem")

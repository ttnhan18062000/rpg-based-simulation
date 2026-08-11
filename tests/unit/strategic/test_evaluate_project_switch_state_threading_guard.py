"""
tests/unit/strategic/test_evaluate_project_switch_state_threading_guard.py

Architecture guard (TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION): all real production
call sites of StrategicIntelligenceSystem.evaluate_project_switch() must thread `state`
through, so the STRAT-236 threat-resolved early-release check can run wherever it's called.
Mirrors the AST-walk pattern already used in
tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py.
"""
import ast
import inspect
import textwrap

from src.domains.adventure.phase import AdventureDecisionPhase
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem


def _find_evaluate_project_switch_calls(source: str) -> list:
    tree = ast.parse(textwrap.dedent(source))
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        call_name = None
        if isinstance(func, ast.Name):
            call_name = func.id
        elif isinstance(func, ast.Attribute):
            call_name = func.attr
        if call_name == "evaluate_project_switch":
            calls.append(node)
    return calls


def test_three_production_call_sites_thread_state_argument():
    """Every evaluate_project_switch(...) call inside AdventureDecisionPhase.apply() and
    StrategicIntelligenceSystem.evaluate_strategic_intent() must carry a `state` argument
    (either a 4th positional arg or a `state=` keyword), and exactly 3 such call sites must
    exist total (1 in apply(), 2 in evaluate_strategic_intent()) -- guarding against both a
    missed site and a silently-added 4th site that forgets to thread state."""
    apply_calls = _find_evaluate_project_switch_calls(
        inspect.getsource(AdventureDecisionPhase.apply)
    )
    intent_calls = _find_evaluate_project_switch_calls(
        inspect.getsource(StrategicIntelligenceSystem.evaluate_strategic_intent)
    )

    all_calls = apply_calls + intent_calls
    assert len(all_calls) == 3, (
        f"Expected exactly 3 evaluate_project_switch(...) call sites across "
        f"AdventureDecisionPhase.apply() and evaluate_strategic_intent() combined, found "
        f"{len(all_calls)}. A missed or newly-added call site must be investigated."
    )

    for node in all_calls:
        carries_state = len(node.args) >= 4 or any(
            kw.arg == "state" for kw in node.keywords
        )
        assert carries_state, (
            "evaluate_project_switch(...) call at "
            f"line {node.lineno} does not thread a `state` argument."
        )

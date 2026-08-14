"""
tests/unit/strategic/test_evaluate_project_switch_state_threading_guard.py

Architecture guard (TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION): all real production
call sites of StrategicIntelligenceSystem.evaluate_project_switch() must thread `state`
through, so the STRAT-236 threat-resolved early-release check can run wherever it's called.
Mirrors the AST-walk pattern already used in
tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py.

Migrated by TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE (plan.md Step 5 item 3):
AdventureDecisionPhase.apply() no longer exists, so only evaluate_strategic_intent()'s own
2 call sites remain to guard (was 3: 1 in apply() + 2 in evaluate_strategic_intent()).
"""
import ast
import inspect
import textwrap

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


def test_two_production_call_sites_thread_state_argument():
    """Every evaluate_project_switch(...) call inside
    StrategicIntelligenceSystem.evaluate_strategic_intent() must carry a `state` argument
    (either a 4th positional arg or a `state=` keyword), and exactly 2 such call sites must
    exist total -- guarding against both a missed site and a silently-added 3rd site that
    forgets to thread state. Was 3 (1 in the now-deleted AdventureDecisionPhase.apply(), 2 here)
    before TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE removed the phase's own call site."""
    all_calls = _find_evaluate_project_switch_calls(
        inspect.getsource(StrategicIntelligenceSystem.evaluate_strategic_intent)
    )

    assert len(all_calls) == 2, (
        f"Expected exactly 2 evaluate_project_switch(...) call sites inside "
        f"evaluate_strategic_intent(), found {len(all_calls)}. A missed or newly-added call "
        f"site must be investigated."
    )

    for node in all_calls:
        carries_state = len(node.args) >= 4 or any(
            kw.arg == "state" for kw in node.keywords
        )
        assert carries_state, (
            "evaluate_project_switch(...) call at "
            f"line {node.lineno} does not thread a `state` argument."
        )

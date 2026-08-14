"""
tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py

Architecture guard: the tier-5 ADVENTURE_ROUTE materialization branch inside
StrategicIntelligenceSystem.evaluate_strategic_intent() must route the winning candidate
through StrategicIntelligenceSystem.evaluate_project_switch() rather than constructing
current_project_id_set directly. This fails loudly if a future edit reintroduces the
unconditional overwrite this ticket (TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION)
fixed, mirroring the project's "authoritative application path was used" architecture-test
pattern (CLAUDE.md Architecture Rule).

Migrated by TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE (plan.md Step 5 item 5): the
guarded property moved from the deleted AdventureDecisionPhase.apply() to
evaluate_strategic_intent()'s own `if best_candidate:` commit block (intelligence.py:1428+,
confirmed by direct read this session -- every `best_candidate.kind` branch, including
ADVENTURE_ROUTE, falls through to the same shared `evaluate_project_switch()` call; no
separate commit path exists for adventure routing). The AST walk is scoped to that single
`if` block, not the whole function, since evaluate_strategic_intent() legitimately constructs
bare `StrategicUpdate()`/`StrategicUpdate(boredom_delta=...)` no-op/completion updates
elsewhere (detour completion, hunger/fatigue completion, etc.) that are unrelated to
materializing a NEW winning candidate and must not trip this guard.
"""
import ast
import inspect
import textwrap

from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem


def _best_candidate_commit_block(tree: ast.AST) -> ast.If:
    """Locate the `if best_candidate:` block inside evaluate_strategic_intent()'s AST --
    the single commit block every best_candidate.kind branch (including ADVENTURE_ROUTE)
    shares."""
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == "best_candidate":
            return node
    raise AssertionError(
        "Could not locate `if best_candidate:` block in "
        "StrategicIntelligenceSystem.evaluate_strategic_intent()'s source -- the guarded "
        "commit block may have been renamed or restructured."
    )


def test_adventure_route_commit_block_does_not_construct_strategic_update_directly():
    """AST-level check: within evaluate_strategic_intent()'s `if best_candidate:` commit
    block, no `StrategicUpdate(` call site sets `current_project_id_set=` to a real value --
    the only way to commit a NEW winning candidate (ADVENTURE_ROUTE or otherwise) must be via
    `StrategicIntelligenceSystem.evaluate_project_switch(...)`."""
    source = textwrap.dedent(inspect.getsource(StrategicIntelligenceSystem.evaluate_strategic_intent))
    tree = ast.parse(source)
    commit_block = _best_candidate_commit_block(tree)

    strategic_update_direct_calls = []
    evaluate_project_switch_calls = []

    for node in ast.walk(commit_block):
        if isinstance(node, ast.Call):
            func = node.func
            call_name = None
            if isinstance(func, ast.Name):
                call_name = func.id
            elif isinstance(func, ast.Attribute):
                call_name = func.attr

            if call_name == "StrategicUpdate":
                if any(kw.arg == "current_project_id_set" for kw in node.keywords):
                    strategic_update_direct_calls.append(node)
            elif call_name == "evaluate_project_switch":
                evaluate_project_switch_calls.append(node)

    assert not strategic_update_direct_calls, (
        "evaluate_strategic_intent()'s `if best_candidate:` commit block must not construct "
        "StrategicUpdate(current_project_id_set=...) directly -- it must go through "
        "StrategicIntelligenceSystem.evaluate_project_switch() so the lock-bypass gate is "
        "always enforced, including for ADVENTURE_ROUTE candidates."
    )
    assert evaluate_project_switch_calls, (
        "evaluate_strategic_intent()'s `if best_candidate:` commit block no longer calls "
        "StrategicIntelligenceSystem.evaluate_project_switch() -- the authoritative "
        "project-switch gate is not being used."
    )


def test_evaluate_project_switch_still_exists_on_strategic_intelligence_system():
    """Guards against StrategicIntelligenceSystem.evaluate_project_switch() being silently
    renamed or removed while the commit block is refactored into something that still
    bypasses the shared gate -- the analogous risk to the pre-relocation test's "import wasn't
    silently removed" check, now that the caller and the shared gate live in the same class
    rather than across an import boundary."""
    assert hasattr(StrategicIntelligenceSystem, "evaluate_project_switch")
    assert callable(StrategicIntelligenceSystem.evaluate_project_switch)

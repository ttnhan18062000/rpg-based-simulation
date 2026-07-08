"""
Architecture guard: GuildAction.visit() must remain unreferenced by any dispatched
pipeline phase.

TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT investigation.md #4: GuildAction
(src/town/guild.py) independently reimplements the same region in res_def.source_region_tags
gating check as ResourceOpportunityProvider to compute a scarcity signal feeding
QuestGenerator, but is not wired into any dispatcher/pipeline-phase module under src/engine/
or src/domains/ today -- confirmed by grep -rln "GuildAction" . returning only its own
definition, a docstring mention in src/quests/generator.py, and a direct unit-test invocation.

If this test starts failing, GuildAction has gone live in a dispatched pipeline path -- the
dormant region-coverage risk documented in this ticket's disposition
(docs/simulation_quality/eval_matrix_results.md) has become active and needs its own
region-coverage evaluation, not silent inheritance of this ticket's "currently dormant"
conclusion.
"""
from __future__ import annotations

import re
from pathlib import Path

_SRC_ROOT = Path(__file__).parent.parent.parent / "src"
_LIVE_DISPATCH_ROOTS = (_SRC_ROOT / "engine", _SRC_ROOT / "domains")

_GUILD_ACTION_REFERENCE = re.compile(r"\bGuildAction\b")


def test_guild_action_not_referenced_by_any_dispatched_pipeline_module() -> None:
    violations: list[str] = []

    for root in _LIVE_DISPATCH_ROOTS:
        for py_file in sorted(root.rglob("*.py")):
            if py_file == _SRC_ROOT / "town" / "guild.py":
                continue
            try:
                source = py_file.read_text(encoding="utf-8")
            except OSError:
                continue
            for match in _GUILD_ACTION_REFERENCE.finditer(source):
                line_no = source.count("\n", 0, match.start()) + 1
                rel = py_file.relative_to(_SRC_ROOT.parent)
                violations.append(f"{rel}:{line_no}")

    assert not violations, (
        "GuildAction is now referenced from a dispatched pipeline module — its scarcity "
        "computation's source_region_tags gating gap (TCK-20260706-SIMQ-CORPUS-RESOURCE-"
        "REGION-COVERAGE-AUDIT #4) is no longer dormant and needs its own region-coverage "
        f"evaluation:\n" + "\n".join(f"  {v}" for v in violations)
    )

"""
Architecture guard: GuildAction.visit() references from dispatched pipeline modules must be
limited to the one, deliberate, tracked live-dispatch site.

TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT investigation.md #4 originally
documented GuildAction (src/town/guild.py) as dormant — it independently reimplements the same
region in res_def.source_region_tags gating check as ResourceOpportunityProvider to compute a
scarcity signal feeding QuestGenerator, but was not wired into any dispatched pipeline phase.
That audit's own explicit guidance: "if/when it is ever wired into a dispatched action... needs
its own region-coverage evaluation, not silent inheritance of this ticket's 'currently dormant'
conclusion."

TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING wired it live via
src/engine/pipeline_phases/guild_visit.py (GuildVisitPhase, gated behind
ENABLE_GUILD_QUEST_GENERATION, default OFF) — following that audit's own guidance, this is
disclosed explicitly here, not silently absorbed: the scarcity-computation gap is real and
active whenever the flag is ON, and its own region-coverage evaluation is tracked separately as
TCK-20260807-GUILD-SCARCITY-REGION-COVERAGE-GAP.

This guard now confirms the reference is limited to exactly that one expected site — if it ever
fails, either a NEW, unreviewed dispatch path has started calling GuildAction (investigate before
assuming it's fine), or the expected site itself has moved (update _EXPECTED_REFERENCES to match,
with the same disclosure discipline as this ticket's own change).
"""
from __future__ import annotations

import re
from pathlib import Path

_SRC_ROOT = Path(__file__).parent.parent.parent / "src"
_LIVE_DISPATCH_ROOTS = (_SRC_ROOT / "engine", _SRC_ROOT / "domains")

_GUILD_ACTION_REFERENCE = re.compile(r"\bGuildAction\b")

# The one deliberate, tracked live-dispatch site (TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING).
# Relative to _SRC_ROOT.parent, matching this test's own `rel` computation below.
_EXPECTED_REFERENCES = frozenset({"src/engine/pipeline_phases/guild_visit.py"})


def test_guild_action_referenced_only_by_the_one_deliberate_dispatch_site() -> None:
    found_files: set[str] = set()

    for root in _LIVE_DISPATCH_ROOTS:
        for py_file in sorted(root.rglob("*.py")):
            if py_file == _SRC_ROOT / "town" / "guild.py":
                continue
            try:
                source = py_file.read_text(encoding="utf-8")
            except OSError:
                continue
            if _GUILD_ACTION_REFERENCE.search(source):
                rel = py_file.relative_to(_SRC_ROOT.parent)
                found_files.add(str(rel))

    unexpected = found_files - _EXPECTED_REFERENCES
    missing = _EXPECTED_REFERENCES - found_files

    assert not unexpected, (
        "GuildAction is now referenced from an UNEXPECTED dispatched pipeline module beyond the "
        "one deliberate site tracked by TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING — its "
        "scarcity computation's source_region_tags gating gap (TCK-20260706-SIMQ-CORPUS-"
        "RESOURCE-REGION-COVERAGE-AUDIT #4, TCK-20260807-GUILD-SCARCITY-REGION-COVERAGE-GAP) is "
        f"active for this new site too, unevaluated:\n" + "\n".join(f"  {v}" for v in unexpected)
    )
    assert not missing, (
        "GuildAction's expected live-dispatch site "
        f"({', '.join(sorted(missing))}) no longer references it — either the wiring was "
        "removed/moved (update _EXPECTED_REFERENCES) or something regressed."
    )

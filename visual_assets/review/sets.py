"""The draft sets the review tools know, and the one generic evaluation (`python -m visual_assets.review evaluate --set <id>`).

Each set's definition is a small module of data (sizes, groups, which keys are proposed, the extra measurements its report carries): `icon_draft_set` (`icons-key-v1`), `icon_v2_draft_set` (`icons-v2`) and
`icon_owner_fixes_draft_set` (`icons-owner-fixes-v1`). This registry maps a set id to its evaluation so there is ONE command and ONE way to record a result: the report is the evidence the committed fixtures
`__fixtures__/icondraft*/rule_result.json` hold, byte for byte (`icon_draft_fixture --check`), and a test never decides a verdict on art.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from visual_assets.review import icon_draft_set, icon_owner_fixes_draft_set, icon_v2_draft_set
from visual_assets.review.sprites import DRAFTS

EVALUATORS: dict[str, Callable[[Path], dict]] = {
    icon_draft_set.SET_ID: lambda root: icon_draft_set.evaluate_draft_set(root, icon_draft_set.SET_ID),
    icon_v2_draft_set.SET_ID: icon_v2_draft_set.evaluate,
    icon_owner_fixes_draft_set.SET_ID: icon_owner_fixes_draft_set.evaluate,
}
SET_IDS = tuple(sorted(EVALUATORS))


class UnknownSet(Exception):
    """No evaluation is registered for this draft set id."""


def evaluate(set_id: str, root: Path = DRAFTS) -> dict:
    try:
        evaluator = EVALUATORS[set_id]
    except KeyError:
        raise UnknownSet(f"no evaluation is registered for the draft set {set_id!r}; known: {', '.join(SET_IDS)}") from None
    return evaluator(root)


def evaluation_json(set_id: str, root: Path = DRAFTS, *, recorded: bool = False) -> str:
    """Indented JSON and a trailing newline. Default: insertion order, exactly what the per-set modules used to print. `recorded=True`: sorted keys, the exact text committed as
    `__fixtures__/icondraft*/rule_result.json` (`icon_draft_fixture --check` compares it byte for byte)."""
    return json.dumps(evaluate(set_id, root), indent=1, sort_keys=recorded) + "\n"

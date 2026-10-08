"""The committed copy of the icon draft set's preview export, for the isolated icon preview page (`TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET`).

`frontend/src/visualAssets/__fixtures__/icondraft/` holds a real `draft export icons-key-v1` (14 PNG previews and `draft_preview_manifest.json`) plus `rule_result.json`, the recorded
result of child 3's sheet rule on that set (`icon_draft_set.evaluate_draft_set`). It is the only link between `visual_assets` and `frontend/` for the page (file level, no import either way).

Freshness is checked against a fresh export of the drafts **modulo the manifest's `registry_hash`**: the page never reads that field for a decision, and pinning it would break the copy at every
key registration (the tax rc-0006 cost). Everything else must be equal: set id, draft_set_hash, entries, details and every PNG byte.

    python -m tests.visual_assets.icon_draft_fixture --write    # refresh the committed copy (also re-records the rule result)
    python -m tests.visual_assets.icon_draft_fixture --check    # exit 1 if it differs from a fresh export
    ... --set icons-v2 --write | --check                        # the same for icon set v2 (icondraft_v2/)
    ... --set icons-owner-fixes-v1 --write | --check            # the same for the owner-fix revisions (icondraft_fixes/)
"""

from __future__ import annotations

import argparse
import filecmp
import json
import shutil
import sys
import tempfile
from pathlib import Path

from tests.visual_assets import icon_owner_fixes_draft_set, icon_v2_draft_set
from tests.visual_assets.icon_draft_set import SET_ID, evaluate_draft_set
from tests.visual_assets.pilot_colour_vision import REPO
from visual_assets.store import draftexport

COMMITTED = REPO / "frontend" / "src" / "visualAssets" / "__fixtures__" / "icondraft"
# Icon set v2 (`TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET`): a second copy beside the first, same rules, its own recorded rule result (the groups and shape-only rule of `icon_v2_groups`).
COMMITTED_V2 = REPO / "frontend" / "src" / "visualAssets" / "__fixtures__" / "icondraft_v2"
# The owner-fix revisions (`TCK-20261008-VISUAL-ASSETS-ICON-OWNER-FIXES`): six new revisions of adopted icons, shown on the preview page beside their adopted r0001.
COMMITTED_FIXES = REPO / "frontend" / "src" / "visualAssets" / "__fixtures__" / "icondraft_fixes"
MANIFEST = "draft_preview_manifest.json"
RESULT = "rule_result.json"


def export_fresh(out: Path, set_id: str = SET_ID) -> None:
    draftexport.export_draft_preview(set_id, out)


def masked(manifest_bytes: bytes) -> dict:
    data = json.loads(manifest_bytes)
    data["registry_hash"] = "MASKED"
    return data


def recorded_result_text() -> str:
    return json.dumps(evaluate_draft_set(), indent=1, sort_keys=True) + "\n"


def recorded_result_text_v2() -> str:
    return json.dumps(icon_v2_draft_set.evaluate(), indent=1, sort_keys=True) + "\n"


def recorded_result_text_fixes() -> str:
    return json.dumps(icon_owner_fixes_draft_set.evaluate(), indent=1, sort_keys=True) + "\n"


def differences(fresh: Path, committed: Path = COMMITTED, result_text=recorded_result_text) -> list[str]:
    problems = []
    names = sorted(p.name for p in fresh.iterdir())
    have = sorted(p.name for p in committed.iterdir() if p.name != RESULT)
    if names != have:
        problems.append(f"files differ: fresh {names} vs committed {have}")
        return problems
    for name in names:
        if name == MANIFEST:
            if masked((fresh / name).read_bytes()) != masked((committed / name).read_bytes()):
                problems.append(f"{name} differs (registry_hash ignored)")
        elif not filecmp.cmp(fresh / name, committed / name, shallow=False):
            problems.append(f"{name} differs")
    if (committed / RESULT).read_text() != result_text():
        problems.append(f"{RESULT} differs from a fresh evaluation of the rule")
    return problems


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--set", default=SET_ID, choices=[SET_ID, icon_v2_draft_set.SET_ID, icon_owner_fixes_draft_set.SET_ID])
    args = ap.parse_args()
    target, result_text = {
        icon_v2_draft_set.SET_ID: (COMMITTED_V2, recorded_result_text_v2),
        icon_owner_fixes_draft_set.SET_ID: (COMMITTED_FIXES, recorded_result_text_fixes),
    }.get(args.set, (COMMITTED, recorded_result_text))
    with tempfile.TemporaryDirectory() as tmp:
        fresh = Path(tmp) / "export"
        export_fresh(fresh, args.set)
        if args.write:
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(fresh, target)
            (target / RESULT).write_text(result_text())
            print(f"wrote {target}")
        problems = differences(fresh, target, result_text)
        print("\n".join(problems) or "identical (registry_hash ignored)")
        sys.exit(1 if problems and args.check else 0)

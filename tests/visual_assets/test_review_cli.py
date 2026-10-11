"""`python -m visual_assets.review evaluate|review-sheets --set <id>` (`TCK-20261008-VISUAL-ASSETS-REVIEW-TOOLING-IN-STORE-CLI`).

The recorded results are the committed `__fixtures__/icondraft*/rule_result.json`; the generic command must print exactly those bytes for the three sets (and exactly what the retired per-set modules printed
without `--recorded`: that comparison was made against a baseline taken before the move and is in the ticket's stored artifacts).
"""

from __future__ import annotations

import json

import pytest

from visual_assets.review import __main__ as cli
from visual_assets.review import sets
from visual_assets.review.pilot_colour_vision import REPO

FIXTURES = REPO / "frontend" / "src" / "visualAssets" / "__fixtures__"
RECORDED = {"icons-key-v1": "icondraft", "icons-v2": "icondraft_v2", "icons-owner-fixes-v1": "icondraft_fixes"}


@pytest.mark.parametrize("set_id", sorted(RECORDED))
def test_the_generic_evaluation_reproduces_the_committed_recorded_result_byte_for_byte(set_id):
    assert sets.evaluation_json(set_id, recorded=True) == (FIXTURES / RECORDED[set_id] / "rule_result.json").read_text()


def test_the_command_prints_the_recorded_text_with_the_flag_and_the_same_report_without_it(capsys):
    assert cli.main(["evaluate", "--set", "icons-v2", "--recorded"]) == 0
    recorded = capsys.readouterr().out
    assert recorded == (FIXTURES / "icondraft_v2" / "rule_result.json").read_text()
    assert cli.main(["evaluate", "--set", "icons-v2"]) == 0
    plain = capsys.readouterr().out
    assert json.loads(plain) == json.loads(recorded) and plain.endswith("}\n") and plain != recorded  # same facts, insertion order instead of sorted


def test_an_unknown_set_is_refused_with_the_known_ones_named_and_nothing_is_printed(capsys):
    assert cli.main(["evaluate", "--set", "no-such-set"]) == 2
    out = capsys.readouterr()
    assert out.out == "" and "icons-key-v1" in out.err and "icons-owner-fixes-v1" in out.err and "icons-v2" in out.err


def test_review_sheets_writes_the_six_images_and_the_readme(tmp_path, capsys):
    out = tmp_path / "folder"
    assert cli.main(["review-sheets", "--set", "icons-v2", "--out", str(out)]) == 0
    assert sorted(p.name for p in out.iterdir()) == ["01_overview.png", "02_before_after.png", "03_groups.png", "04_colour_vision.png", "05_map_markers.png", "06_silhouettes.png", "README.txt"]
    assert "wrote" in capsys.readouterr().out


def test_every_registered_set_has_a_committed_draft_set_and_the_registry_matches_the_fixtures():
    assert sets.SET_IDS == tuple(sorted(RECORDED))
    for set_id in sets.SET_IDS:
        assert (REPO / "visual_assets" / "drafts" / set_id / "draft_set.json").is_file()

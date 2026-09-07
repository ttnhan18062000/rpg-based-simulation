"""Tests for tools/agent_replay/sampler.py (TCK-20260907-FILTERED-REPLAY-EVAL-PILOT, AC #1)."""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from agent_replay.sampler import (  # noqa: E402
    build_sample_manifest,
    load_manifest,
    write_manifest,
)

_DONE_DIR = _REPO_ROOT / "tickets" / "done"
_MONITORING_ROOT = _REPO_ROOT / "agent-monitoring"


def test_sampler_produces_valid_stratified_manifest():
    manifest = build_sample_manifest(_DONE_DIR, _MONITORING_ROOT, sample_size_range=(20, 40))

    assert 20 <= manifest.sample_size <= 40
    assert len(manifest.tickets) == manifest.sample_size

    real_ticket_ids = {p.stem for p in _DONE_DIR.glob("TCK-*.md")}
    seen_ids = set()
    for sampled in manifest.tickets:
        assert sampled.ticket_id in real_ticket_ids, f"{sampled.ticket_id} not a real done ticket"
        assert sampled.ticket_id not in seen_ids, f"{sampled.ticket_id} sampled more than once"
        seen_ids.add(sampled.ticket_id)
        assert sampled.split in {"dev", "validation", "holdout"}
        assert sampled.tier
        assert sampled.layer
        assert sampled.outcome_stratum in {"success", "failure", "unknown"}

        # strata fields must match the ticket's own real frontmatter/body fields, not fabricated
        ticket_path = _DONE_DIR / f"{sampled.ticket_id}.md"
        text = ticket_path.read_text(encoding="utf-8")
        assert f"layer: {sampled.layer}" in text or sampled.layer == "misc"

    split_counts = {"dev": 0, "validation": 0, "holdout": 0}
    for sampled in manifest.tickets:
        split_counts[sampled.split] += 1

    n = manifest.sample_size
    # reasonable band around 60/20/20 given rounding at small sample sizes
    assert split_counts["dev"] >= n * 0.4
    assert split_counts["validation"] >= 1
    assert split_counts["holdout"] >= 1


def test_sampler_persists_manifest_as_durable_artifact(tmp_path):
    manifest = build_sample_manifest(_DONE_DIR, _MONITORING_ROOT, sample_size_range=(20, 40))

    output_path = tmp_path / "sample_manifest.yaml"
    write_manifest(manifest, output_path)

    assert output_path.exists(), "manifest must be a real file on disk, not only a local variable"

    reloaded = load_manifest(output_path)
    assert reloaded.sample_size == manifest.sample_size
    assert {t.ticket_id for t in reloaded.tickets} == {t.ticket_id for t in manifest.tickets}

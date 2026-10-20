"""Score a saved run offline from its lossless ``simulation_events.jsonl`` (decision 80 C).

    python -m tools.simq_score_run RUN_DIR --out OUT_DIR [--profile NAME] [--require-host-independent]

Writes ``quality_report.json``, ``quality_scores.jsonl``, ``event_counts_by_type.json`` (the replayed file's count per event type) and the run's host-independence sidecar
(``quality_report.run_determinism.json``) into OUT_DIR. A run directory without ``simulation_events.jsonl`` is refused (exit 2). The report carries a fixed ``generated_at``,
so the same run directory gives a byte-identical ``quality_report.json`` on any host.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from src.simulation_quality.offline import RunNotReplayable, score_run_dir
from src.simulation_quality.weights import ScoringWeights
from tools.test_architecture.simq_run_record import write_sidecar


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--profile", default=os.environ.get("QUALITY_PROFILE", "default"))
    parser.add_argument("--require-host-independent", action="store_true", help="refuse a run whose manifest does not record signals_zeroed")
    args = parser.parse_args(argv)

    weights = ScoringWeights.load(
        "config/simulation_quality/scoring_weights.yaml",
        "config/simulation_quality/grade_thresholds.yaml",
        "config/simulation_quality/detection_params.yaml",
        args.profile,
    )
    args.out.mkdir(parents=True, exist_ok=True)
    try:
        report, replay = score_run_dir(args.run_dir, weights, args.out, require_host_independent=args.require_host_independent)
    except RunNotReplayable as exc:
        print(f"[simq_score_run] refused: {exc}", file=sys.stderr)
        return 2
    (args.out / "event_counts_by_type.json").write_text(json.dumps(replay.event_counts_by_type, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_sidecar(args.out, args.run_dir)
    print(f"[simq_score_run] {replay.event_count} events replayed ({replay.skipped_lines} unreadable lines skipped); overall={report.overall_grade}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

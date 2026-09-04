#!/usr/bin/env python3
"""Weight-sensitivity validation gate for `cost_proxy.py`'s W_BASH/W_AGENT/W_EDIT weights
(promoted from `experiments/cost_proxy_calibration/validate_rank_order.py`,
TCK-20260719-WEIGHT-SENSITIVITY-PROMOTE — the experiment that produced it is documented in
`experiments/cost_proxy_calibration/RESULTS.md`).

Recomputes `cost_proxy_score` for every real `(run_id, seq)` group in `agent-monitoring/
tools.jsonl` under two weight sets — the currently-shipped weights (by default, read directly
from `cost_proxy.py`, never a second hardcoded copy) and a candidate weight set supplied on the
CLI — then compares the resulting spend-by-phase / spend-by-agent RANK ORDER. This is the
required check before ever proposing a `cost_proxy.py` weight change: a candidate weight set that
doesn't materially reorder spend rankings isn't worth the churn of changing; one that does needs
that reordering to be a deliberate, reviewed decision, not a surprise discovered after the fact.

Read-only against `agent-monitoring/*.jsonl`. Never modifies `tools/agent-monitoring/cost_proxy.py`
— this tool informs a weight-change decision, it does not make one. Deliberately carries no
baked-in second weight set to compare against (the experiment's own Fit C numbers are not shipped
here as a default) — a candidate must always be supplied explicitly via `--candidate-weights`.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cost_proxy import W_AGENT, W_BASH, W_EDIT  # noqa: E402
from validate import load_data_glob  # noqa: E402

TOOLS_FILE = Path("agent-monitoring/data")
EVENTS_FILE = Path("agent-monitoring/data")

_EDIT_TOOLS = {"Read", "Edit", "Write", "MultiEdit"}

# The currently-shipped weights, read from cost_proxy.py's own module-level constants — never a
# second hardcoded literal copy. Used as the default baseline comparand.
SHIPPED_WEIGHTS = {"bash": W_BASH, "agent": W_AGENT, "edit": W_EDIT}


def _score_with_weights(tool_rows: list[dict], weights: dict) -> float:
    """Score one (run_id, seq) group's tool_rows under an arbitrary weights dict
    ({"bash": ..., "agent": ..., "edit": ...}). Deliberately a separate implementation from
    `cost_proxy.py::compute_cost_proxy_score` — that function hardcodes the module-level shipped
    constants by design (the real production write path, wired into `record_events.py`), while
    this tool needs to score the SAME group under two arbitrary, CLI-supplied weight sets for a
    real-time comparison. Formula is identical; only the weight source differs."""
    bash_ms = sum((r.get("duration_ms") or 0) for r in tool_rows if r.get("tool") == "Bash")
    agent_count = sum(1 for r in tool_rows if r.get("tool") == "Agent")
    edit_count = sum(1 for r in tool_rows if r.get("tool") in _EDIT_TOOLS)
    return weights["bash"] * bash_ms + weights["agent"] * agent_count + weights["edit"] * edit_count


def _spearman_rank_correlation(rank_a: dict, rank_b: dict) -> float | None:
    """Pure-Python Spearman rank correlation (no numpy dependency — this directory's other
    modules have none, and tools/agent-monitoring/*.py scripts run via bare `python3`, not
    guaranteed a numpy-equipped interpreter). Both `rank_a`/`rank_b` are {key: rank_int} dicts
    covering the same key set with no ties (ranks are a 0..n-1 permutation by construction, via
    Python's stable sort), so the tie-free closed-form formula applies exactly:
    rho = 1 - (6 * sum(d_i^2)) / (n * (n^2 - 1)). Returns None for fewer than 2 keys (undefined)."""
    keys = list(rank_a)
    n = len(keys)
    if n < 2:
        return None
    d_squared_sum = sum((rank_a[k] - rank_b[k]) ** 2 for k in keys)
    return 1 - (6 * d_squared_sum) / (n * (n**2 - 1))


def _group_report(scores_by_key: dict, baseline_key: str, candidate_key: str) -> dict:
    """Build one bucket-comparison report (phase-keyed or agent-keyed) from
    {bucket: {"baseline": [scores...], "candidate": [scores...]}}."""

    def mean(xs):
        return sum(xs) / len(xs) if xs else 0.0

    baseline_means = {k: mean(v[baseline_key]) for k, v in scores_by_key.items()}
    candidate_means = {k: mean(v[candidate_key]) for k, v in scores_by_key.items()}
    baseline_rank = {k: i for i, k in enumerate(sorted(baseline_means, key=lambda k: -baseline_means[k]))}
    candidate_rank = {k: i for i, k in enumerate(sorted(candidate_means, key=lambda k: -candidate_means[k]))}

    rows = [
        {
            "bucket": k,
            "n": len(scores_by_key[k][baseline_key]),
            "baseline_mean": round(baseline_means[k], 2),
            "baseline_rank": baseline_rank[k],
            "candidate_mean": round(candidate_means[k], 2),
            "candidate_rank": candidate_rank[k],
            "rank_delta": candidate_rank[k] - baseline_rank[k],
        }
        for k in sorted(baseline_means, key=lambda k: baseline_rank[k])
    ]

    spearman = _spearman_rank_correlation(baseline_rank, candidate_rank)
    return {"rows": rows, "spearman": round(spearman, 4) if spearman is not None else None}


def compute_weight_sensitivity_report(
    tool_rows_by_group: dict[tuple, list[dict]],
    phase_of: dict[tuple, str],
    agent_of: dict[tuple, str],
    baseline_weights: dict,
    candidate_weights: dict,
) -> dict:
    """Pure computation, no file I/O — the testable core this module exports.

    `tool_rows_by_group`: {(run_id, seq): [tools.jsonl row dicts]}, already filtered to groups
    with a real run_id/seq (the caller's responsibility, matching the CLI's own file-reading
    behavior below).
    `phase_of`/`agent_of`: {(run_id, seq): phase/agent string}, from events.jsonl — a group with
    no matching event is skipped (mirrors the pre-promotion script's own behavior).
    `baseline_weights`/`candidate_weights`: {"bash": float, "agent": float, "edit": float}.

    Returns {"n_groups_scored": int, "by_phase": {...}, "by_agent": {...}} — each `by_*` value
    shaped by `_group_report()`.
    """
    phase_scores = defaultdict(lambda: {"baseline": [], "candidate": []})
    agent_scores = defaultdict(lambda: {"baseline": [], "candidate": []})

    n_groups_scored = 0
    for key, rows in tool_rows_by_group.items():
        if key not in phase_of:
            continue
        n_groups_scored += 1
        s_baseline = _score_with_weights(rows, baseline_weights)
        s_candidate = _score_with_weights(rows, candidate_weights)
        phase_scores[phase_of[key]]["baseline"].append(s_baseline)
        phase_scores[phase_of[key]]["candidate"].append(s_candidate)
        agent_scores[agent_of[key]]["baseline"].append(s_baseline)
        agent_scores[agent_of[key]]["candidate"].append(s_candidate)

    return {
        "n_groups_scored": n_groups_scored,
        "by_phase": _group_report(phase_scores, "baseline", "candidate"),
        "by_agent": _group_report(agent_scores, "baseline", "candidate"),
    }


def _load_tool_rows_and_events(tools_path: Path, events_path: Path):
    """Real-file reader — kept separate from compute_weight_sensitivity_report() so that function
    stays testable with plain fixture dicts, no file I/O."""
    tool_rows_by_group: dict[tuple, list[dict]] = defaultdict(list)
    for r in load_data_glob(tools_path, "tools"):
        if r.get("run_id") is None or r.get("seq") is None:
            continue
        tool_rows_by_group[(r["run_id"], r["seq"])].append(r)

    phase_of: dict[tuple, str] = {}
    agent_of: dict[tuple, str] = {}
    for e in load_data_glob(events_path, "events"):
        run_id = e.get("run_id")
        seq = e.get("seq")
        if run_id is None or seq is None:
            continue
        key = (run_id, seq)
        phase_of[key] = e.get("phase", "?")
        agent_of[key] = e.get("agent", "?")

    return tool_rows_by_group, phase_of, agent_of


def _print_report(label: str, report: dict) -> None:
    print(f"\n=== {label} — mean score per bucket, baseline weights vs candidate weights ===")
    print(f"{'bucket':<28} {'n':>5} {'baseline_mean':>14} {'baseline_rank':>14} {'candidate_mean':>15} {'candidate_rank':>15} {'rank_delta':>11}")
    for row in report["rows"]:
        print(
            f"{row['bucket']:<28} {row['n']:>5} {row['baseline_mean']:>14} {row['baseline_rank']:>14} "
            f"{row['candidate_mean']:>15} {row['candidate_rank']:>15} {row['rank_delta']:>11}"
        )
    if report["spearman"] is not None:
        print(f"Spearman rank correlation (baseline vs candidate): {report['spearman']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare cost_proxy_score rank order under two weight sets — the required "
        "check before proposing any cost_proxy.py weight change."
    )
    parser.add_argument(
        "--candidate-weights",
        required=True,
        help='JSON object, e.g. \'{"bash": 0.0127, "agent": 7032.11, "edit": 2393.55}\' — '
        "the weight set being evaluated. No default — must always be supplied explicitly.",
    )
    parser.add_argument(
        "--baseline-weights",
        default=None,
        help="JSON object, same shape as --candidate-weights. Defaults to the currently-shipped "
        "cost_proxy.py weights if omitted.",
    )
    args = parser.parse_args()

    try:
        candidate_weights = json.loads(args.candidate_weights)
    except json.JSONDecodeError as e:
        print(f"ERROR: --candidate-weights is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    baseline_weights = SHIPPED_WEIGHTS
    if args.baseline_weights is not None:
        try:
            baseline_weights = json.loads(args.baseline_weights)
        except json.JSONDecodeError as e:
            print(f"ERROR: --baseline-weights is not valid JSON: {e}", file=sys.stderr)
            sys.exit(1)

    for label, weights in (("--candidate-weights", candidate_weights), ("--baseline-weights", baseline_weights)):
        missing = {"bash", "agent", "edit"} - set(weights)
        if missing:
            print(f"ERROR: {label} is missing required key(s): {sorted(missing)}", file=sys.stderr)
            sys.exit(1)

    tool_rows_by_group, phase_of, agent_of = _load_tool_rows_and_events(TOOLS_FILE, EVENTS_FILE)
    report = compute_weight_sensitivity_report(
        tool_rows_by_group, phase_of, agent_of, baseline_weights, candidate_weights
    )

    print(f"Groups scored (real (run_id,seq) with a matching event): {report['n_groups_scored']}")
    _print_report("Spend by PHASE", report["by_phase"])
    _print_report("Spend by AGENT", report["by_agent"])


if __name__ == "__main__":
    main()

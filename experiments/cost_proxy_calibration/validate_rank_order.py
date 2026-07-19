"""Validation gate (PROPOSAL.md Section 4, step 4): recompute cost_proxy_score for every real
(run_id, seq) group in agent-monitoring/tools.jsonl under both the shipped weights and the
session-aggregate regression-derived weights (Fit C from fit_regression.py), then compare the
resulting spend-by-phase / spend-by-agent RANK ORDER. Read-only against agent-monitoring/*.jsonl.
Does not modify tools/agent-monitoring/cost_proxy.py.
"""

import json
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_PATH = REPO_ROOT / "agent-monitoring" / "tools.jsonl"
EVENTS_PATH = REPO_ROOT / "agent-monitoring" / "events.jsonl"

W_SHIPPED = {"bash": 0.001, "agent": 50, "edit": 1}
# Fit C (session-level aggregate regression, n=31 sessions, R^2=0.93) from fit_regression.py.
W_FITC = {"bash": 0.012707, "agent": 7032.11, "edit": 2393.5493}

_EDIT_TOOLS = {"Read", "Edit", "Write", "MultiEdit"}


def score(tool_rows: list[dict], w: dict) -> float:
    bash_ms = sum((r.get("duration_ms") or 0) for r in tool_rows if r.get("tool") == "Bash")
    agent_count = sum(1 for r in tool_rows if r.get("tool") == "Agent")
    edit_count = sum(1 for r in tool_rows if r.get("tool") in _EDIT_TOOLS)
    return w["bash"] * bash_ms + w["agent"] * agent_count + w["edit"] * edit_count


def main() -> None:
    tool_rows_by_group: dict[tuple, list[dict]] = defaultdict(list)
    with open(TOOLS_PATH, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("run_id") is None or r.get("seq") is None:
                continue
            tool_rows_by_group[(r["run_id"], r["seq"])].append(r)

    phase_of: dict[tuple, str] = {}
    agent_of: dict[tuple, str] = {}
    with open(EVENTS_PATH, encoding="utf-8") as f:
        for line in f:
            e = json.loads(line)
            run_id = e.get("run_id")
            seq = e.get("seq")
            if run_id is None or seq is None:
                continue
            key = (run_id, seq)
            phase_of[key] = e.get("phase", "?")
            agent_of[key] = e.get("agent", "?")

    phase_scores = {"shipped": defaultdict(list), "fitc": defaultdict(list)}
    agent_scores = {"shipped": defaultdict(list), "fitc": defaultdict(list)}

    n_groups_scored = 0
    for key, rows in tool_rows_by_group.items():
        if key not in phase_of:
            continue
        n_groups_scored += 1
        s_shipped = score(rows, W_SHIPPED)
        s_fitc = score(rows, W_FITC)
        phase_scores["shipped"][phase_of[key]].append(s_shipped)
        phase_scores["fitc"][phase_of[key]].append(s_fitc)
        agent_scores["shipped"][agent_of[key]].append(s_shipped)
        agent_scores["fitc"][agent_of[key]].append(s_fitc)

    print(f"Groups scored (real (run_id,seq) with a matching event): {n_groups_scored}")

    def mean(xs):
        return sum(xs) / len(xs) if xs else 0.0

    def report(label, scores_dict):
        print(f"\n=== {label} — mean score per bucket, shipped weights vs Fit C weights ===")
        shipped_means = {k: mean(v) for k, v in scores_dict["shipped"].items()}
        fitc_means = {k: mean(v) for k, v in scores_dict["fitc"].items()}
        shipped_rank = {k: i for i, k in enumerate(sorted(shipped_means, key=lambda k: -shipped_means[k]))}
        fitc_rank = {k: i for i, k in enumerate(sorted(fitc_means, key=lambda k: -fitc_means[k]))}

        print(f"{'bucket':<28} {'n':>5} {'shipped_mean':>14} {'shipped_rank':>13} {'fitc_mean':>14} {'fitc_rank':>10} {'rank_delta':>11}")
        for k in sorted(shipped_means, key=lambda k: shipped_rank[k]):
            n = len(scores_dict["shipped"][k])
            sr = shipped_rank[k]
            fr = fitc_rank[k]
            print(f"{k:<28} {n:>5} {shipped_means[k]:>14.2f} {sr:>13} {fitc_means[k]:>14.2f} {fr:>10} {fr - sr:>11}")

        # Spearman rank correlation between the two rank orderings.
        import numpy as np
        keys = list(shipped_means)
        sr_arr = np.array([shipped_rank[k] for k in keys])
        fr_arr = np.array([fitc_rank[k] for k in keys])
        if len(keys) > 1:
            spearman = np.corrcoef(sr_arr, fr_arr)[0, 1]
            print(f"Spearman rank correlation (shipped vs Fit C): {spearman:.4f}")

    report("Spend by PHASE", phase_scores)
    report("Spend by AGENT", agent_scores)


if __name__ == "__main__":
    main()

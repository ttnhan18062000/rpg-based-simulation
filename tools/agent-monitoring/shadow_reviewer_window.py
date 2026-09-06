#!/usr/bin/env python3
"""Bounded shadow-reviewer sample window + collision-free negative-seq assignment
(TCK-20260904-SHADOW-REVIEWER-LOGGING). Two independent counting scopes, never conflated:
  - is_shadow_window_open(): counts prior shadow samples ACROSS ALL run_ids, for the
    bounded-sample stop condition (AC #4). Not the promotion/"enough evidence" decision —
    purely a mechanical cap on how many candidate calls this pilot ever makes.
  - compute_shadow_seq(): counts prior shadow samples for THIS run_id only, for negative-seq
    collision avoidance across resumed sessions (mirrors seq_offset.py's own resume-lookup
    precedent, scoped further to one reviewer's own agent literal).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import load_data_glob  # noqa: E402

DATA_DIR = Path("agent-monitoring/data")

# Pilot-window sizes (TCK-20260904-SHADOW-REVIEWER-LOGGING plan.md Judgment Call 4): sized from
# real corpus volume (478 historical Architecture-Verify events vs. 14 Security-Review events,
# confirmed by direct count against agent-monitoring/data/*/events.jsonl at plan time) — NOT a
# promotion/statistical-significance threshold, purely a cap on total candidate model calls this
# pilot ever makes. Adjust here only — never duplicate this literal at any call site.
SHADOW_MAX_SAMPLES = {
    "architecture-reviewer": 50,
    "security-reviewer": 10,
}

# Disjoint negative-seq base per reviewer (Judgment Call 5) — keeps the two reviewers' shadow
# ranges apart from each other AND from INFRA-299's own small -1..-5 shadow-packet range, even
# though the actual uniqueness key everywhere seq is consumed is (run_id, seq), not seq alone.
SHADOW_SEQ_BASE = {
    "architecture-reviewer": 100,
    "security-reviewer": 200,
}


def _shadow_agent_name(reviewer: str) -> str:
    return f"{reviewer}-shadow"


def count_prior_shadow_samples(reviewer: str) -> int:
    """Across ALL run_ids -- bounds the total pilot sample window (AC #4), never scoped to one
    run_id. Pure/read-only."""
    agent_name = _shadow_agent_name(reviewer)
    return sum(
        1 for e in load_data_glob(DATA_DIR, "events") if e.get("agent") == agent_name
    )


def is_shadow_window_open(reviewer: str, max_samples: int) -> bool:
    """True if fewer than max_samples prior shadow events exist for this reviewer, across all
    run_ids. False means: skip the candidate call entirely for this run (AC #4)."""
    return count_prior_shadow_samples(reviewer) < max_samples


def count_prior_shadow_samples_for_run(reviewer: str, run_id: str) -> int:
    """Scoped to ONE run_id -- for negative-seq collision avoidance across resumed sessions of
    the SAME ticket, never for the sample-window gate above. Pure/read-only."""
    agent_name = _shadow_agent_name(reviewer)
    return sum(
        1
        for e in load_data_glob(DATA_DIR, "events")
        if e.get("agent") == agent_name and e.get("run_id") == run_id
    )


def compute_shadow_seq(reviewer: str, run_id: str) -> int:
    """seq = -(SHADOW_SEQ_BASE[reviewer] + prior_count_this_run_this_reviewer). Always <= -100,
    provably disjoint from the real per-phase seq range (>= 1) for any run length/resume count,
    and from the other reviewer's own range (bases 100 vs. 200 apart)."""
    base = SHADOW_SEQ_BASE[reviewer]
    return -(base + count_prior_shadow_samples_for_run(reviewer, run_id))


if __name__ == "__main__":
    reviewer, run_id = sys.argv[1], sys.argv[2]
    result = {
        "window_open": is_shadow_window_open(reviewer, SHADOW_MAX_SAMPLES[reviewer]),
        "shadow_seq": compute_shadow_seq(reviewer, run_id),
    }
    print("SHADOW_WINDOW_JSON:" + json.dumps(result))

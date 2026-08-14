"""Step 3 (one-off) — line-scoped `final_status` casing fix for 7 `agent-monitoring/runs.jsonl` records.

TCK-20260718-STATUS-DRIFT-REPAIR plan.md Step 3. Pure line-scoped string substitution — never a
`json.loads`/`json.dumps` round trip — so every byte of every non-target line, and every field
other than `final_status` on the 7 target lines, is preserved exactly. Confirms each target line's
`run_id` before touching it (defensive check against a stale line-number assumption), and asserts
exactly one substitution occurs per target line.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNS_FILE = REPO_ROOT / "agent-monitoring" / "runs.jsonl"

EXPECTED_LINE_COUNT = 641

# 0-indexed line number -> (expected run_id, old substring, new substring)
TARGETS = {
    73: ("TCK-20260610-WORKER-SINGLETON-GUARD", '"final_status":"done"', '"final_status":"DONE"'),
    247: ("run-e51d-renderer-20260622", '"final_status":"success"', '"final_status":"DONE"'),
    248: ("run-e51e-rest-api-20260622", '"final_status":"success"', '"final_status":"DONE"'),
    249: ("TCK-20260619-E52A-COHORT-MODEL-run1", '"final_status":"success"', '"final_status":"DONE"'),
    250: ("TCK-20260619-E52B-MIGRATION-run1", '"final_status":"success"', '"final_status":"DONE"'),
    251: ("TCK-20260619-E52C-AGE-ADVANCEMENT-001", '"final_status":"success"', '"final_status":"DONE"'),
    252: ("TCK-20260619-E52D-DENSITY-SIGNAL-001", '"final_status":"success"', '"final_status":"DONE"'),
}


def main():
    lines = RUNS_FILE.read_text().splitlines(keepends=True)

    if len(lines) != EXPECTED_LINE_COUNT:
        print(
            f"FAIL: expected {EXPECTED_LINE_COUNT} lines, found {len(lines)} — "
            f"runs.jsonl has grown/shrunk since scoping, do not trust fixed line numbers",
            file=sys.stderr,
        )
        sys.exit(1)

    for idx, (expected_run_id, old_substr, new_substr) in TARGETS.items():
        line = lines[idx]
        rec = json.loads(line)
        if rec.get("run_id") != expected_run_id:
            print(
                f"FAIL: line {idx} run_id={rec.get('run_id')!r} != expected {expected_run_id!r}",
                file=sys.stderr,
            )
            sys.exit(1)
        count = line.count(old_substr)
        if count != 1:
            print(
                f"FAIL: line {idx} ({expected_run_id}) has {count} occurrences of "
                f"{old_substr!r}, expected exactly 1",
                file=sys.stderr,
            )
            sys.exit(1)
        lines[idx] = line.replace(old_substr, new_substr)

    tmp_path = RUNS_FILE.with_suffix(".jsonl.tmp")
    tmp_path.write_text("".join(lines))
    tmp_path.replace(RUNS_FILE)

    print(f"Fixed {len(TARGETS)} records in {RUNS_FILE}.")
    for idx, (run_id, _old, _new) in TARGETS.items():
        print(f"  line {idx}: {run_id}")


if __name__ == "__main__":
    main()

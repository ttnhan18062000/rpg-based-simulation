"""Search quality evaluation: Recall@5, Recall@10, MRR@10 against live knowledge index."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_QUERIES_PATH = _REPO_ROOT / "tools" / "eval" / "queries.json"
_KS_PATH = _REPO_ROOT / "tools" / "knowledge_search.py"
_DB_PATH = _REPO_ROOT / "knowledge-index" / "knowledge.db"
_REPORTS_DIR = _REPO_ROOT / "reports"


def _run_query(query: str, top_k: int = 10) -> list[str]:
    """Run knowledge_search.py query and return list of doc_ids (ordered)."""
    result = subprocess.run(
        [sys.executable, str(_KS_PATH), "query", query, "--top-k", str(top_k)],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
    )
    doc_ids = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if parts:
            doc_ids.append(parts[0])
    return doc_ids


def _reciprocal_rank(results: list[str], expected: set[str]) -> float:
    for rank, doc_id in enumerate(results):
        if doc_id in expected:
            return 1.0 / (rank + 1)
    return 0.0


def _hit(results: list[str], expected: set[str], k: int) -> bool:
    return any(d in expected for d in results[:k])


def evaluate(queries: list[dict], top_k: int = 10, threshold: float = 0.80) -> int:
    total = len(queries)
    hits5 = 0
    hits10 = 0
    rr_sum = 0.0
    zero_results = 0
    per_query = []

    for item in queries:
        query = item["query"]
        expected = set(item.get("expected_doc_ids", []))
        category = item.get("category", "?")

        results = _run_query(query, top_k)
        is_zero = len(results) == 0
        if is_zero:
            zero_results += 1

        h5 = _hit(results, expected, 5) if expected else None
        h10 = _hit(results, expected, 10) if expected else None
        rr = _reciprocal_rank(results, expected) if expected else None

        if h5:
            hits5 += 1
        if h10:
            hits10 += 1
        if rr is not None:
            rr_sum += rr

        top1 = results[0] if results else "(no results)"
        per_query.append({
            "query": query,
            "category": category,
            "expected": list(expected),
            "top1": top1,
            "results": results[:10],
            "hit5": h5,
            "hit10": h10,
            "rr": rr,
            "zero_results": is_zero,
        })

    recall5 = hits5 / total if total else 0.0
    recall10 = hits10 / total if total else 0.0

    queries_with_expected = sum(1 for q in per_query if q["rr"] is not None)
    mrr10 = rr_sum / queries_with_expected if queries_with_expected else 0.0

    _print_table(per_query)
    print()
    print(f"Recall@5: {recall5:.2f} | Recall@10: {recall10:.2f} | MRR@10: {mrr10:.2f} | Zero-result: {zero_results}")
    print(f"Queries: {total} | With expected: {queries_with_expected}")
    print(f"Threshold: Recall@5 >= {threshold:.2f} → {'PASS' if recall5 >= threshold else 'FAIL'}")

    _save_report(per_query, recall5, recall10, mrr10, zero_results, threshold)

    return 0 if recall5 >= threshold else 1


def _print_table(per_query: list[dict]) -> None:
    header = f"{'#':>3}  {'Cat':10}  {'R5':>3}  {'RR':>5}  {'Top-1 doc_id':<40}  Query"
    print(header)
    print("-" * len(header))
    for i, row in enumerate(per_query, 1):
        cat = row["category"][:10]
        h5 = "Y" if row["hit5"] else ("N" if row["hit5"] is not None else "-")
        rr_str = f"{row['rr']:.3f}" if row["rr"] is not None else "  -  "
        top1 = row["top1"][:40]
        query_short = row["query"][:60]
        print(f"{i:>3}  {cat:10}  {h5:>3}  {rr_str:>5}  {top1:<40}  {query_short}")


def _save_report(per_query: list[dict], recall5: float, recall10: float, mrr10: float,
                 zero_results: int, threshold: float) -> None:
    _REPORTS_DIR.mkdir(exist_ok=True)
    date_str = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
    report_path = _REPORTS_DIR / f"eval_search_{date_str}.json"
    report = {
        "date": datetime.now(tz=timezone.utc).isoformat(),
        "metrics": {
            "recall_at_5": round(recall5, 4),
            "recall_at_10": round(recall10, 4),
            "mrr_at_10": round(mrr10, 4),
            "zero_result_count": zero_results,
            "total_queries": len(per_query),
            "threshold": threshold,
            "pass": recall5 >= threshold,
        },
        "per_query": per_query,
    }
    report_path.write_text(json.dumps(report, indent=2))
    try:
        display_path = report_path.relative_to(_REPO_ROOT)
    except ValueError:
        display_path = report_path
    print(f"Report saved: {display_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Search quality evaluation (Recall@5, MRR@10)")
    parser.add_argument("--queries", default=str(_QUERIES_PATH), metavar="PATH",
                        help="Path to queries.json (default: tools/eval/queries.json)")
    parser.add_argument("--top-k", type=int, default=10, metavar="K",
                        help="Retrieve top-K candidates per query (default: 10)")
    parser.add_argument("--threshold", type=float, default=0.80, metavar="F",
                        help="Recall@5 threshold for pass/fail (default: 0.80)")
    args = parser.parse_args()

    if not _DB_PATH.exists():
        print(
            f"ERROR: knowledge index not found at {_DB_PATH}\n"
            "Run `make knowledge-index` to build it first.",
            file=sys.stderr,
        )
        return 1

    queries_path = Path(args.queries)
    if not queries_path.exists():
        print(f"ERROR: queries file not found: {queries_path}", file=sys.stderr)
        return 1

    with open(queries_path) as f:
        queries = json.load(f)

    print(f"Running {len(queries)} queries against {_DB_PATH.name} ...")
    print()
    return evaluate(queries, top_k=args.top_k, threshold=args.threshold)


if __name__ == "__main__":
    sys.exit(main())

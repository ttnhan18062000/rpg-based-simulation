"""
Real, one-off measurement script for TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT.

Data source: agent-monitoring/events.jsonl, phase == "Investigate" events (one real Investigate-phase
summary per ticket run, produced by the investigator agent during normal ticket work — real
production telemetry, not synthetic).

Method (mirrors proposal §11.2's conservative multi-signal approach — normalize -> extract stable
identifiers -> classify intent -> compare identity+intent agreement; explicitly NOT raw-string-only,
NOT embedding-only):

1. Normalize: lowercase, strip punctuation-heavy formatting.
2. Extract stable identifiers per summary:
   - subsystem-topic tags: reuses the real, existing `candidate_tags_from_text()` from
     tools/registry_query.py (the same seed-vocabulary substring matcher create-tickets.js and the
     investigator agent already use for prior-work lookup) against registries/tag_registry.jsonl.
   - CamelCase symbol-shaped tokens (e.g. AuthoritativeState, ContextPacket) via regex.
   - repo-relative file paths (src/..., docs/..., tools/...) via regex.
   - referenced ticket IDs (TCK-........-...) via regex.
3. Classify intent into one of 6 buckets via keyword rules, informed by (but not copying, since no
   free-text classifier exists in this repo for arbitrary prose) the 7 real ROUTING_SHAPES already
   used throughout Phase 0-4 (tools/knowledge_gateway_router.py ROUTING_TABLE / kgmcp_baseline_corpus
   ROUTING_SHAPES) collapsed into: mechanism_explanation, root_cause_debugging,
   completeness_verification, feasibility_evaluation, location_lookup, other.
4. Compare: two DIFFERENT tickets' Investigate summaries count as "repeated demand" only if
   (a) same intent bucket AND (b) at least one overlapping specific extracted identifier (CamelCase
   symbol, file path, or referenced ticket ID) -- NOT subsystem-topic tag alone, since tags like
   "mcp"/"cognition" are far too coarse (dozens of unrelated tickets share a tag). Subsystem-tag-only
   overlap is reported separately as a weaker, non-counted signal.
"""
import json
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "/home/u24desktop/Working/rpg-based-simulation/tools")
from registry_query import candidate_tags_from_text  # noqa: E402

REPO = "/home/u24desktop/Working/rpg-based-simulation"

# Requires an actual lowercase LETTER (not just a digit) between two uppercase letters, so bare
# ALL-CAPS acronyms (INFRA, STRAT, TOWN, TCK) and digit-joined pseudo-camel tokens (E2E, S3) never
# match here -- those are handled separately by PARITY_ID_RE / TICKET_RE, or excluded entirely,
# since a bare acronym/digit-joined token is a coarse category signal, not a specific entity.
# Minimum total length 6 further suppresses short incidental matches.
CAMEL_RE = re.compile(r"\b[A-Z][a-z][a-zA-Z0-9]*[A-Z][a-zA-Z0-9]*\b")
_CAMEL_MIN_LEN = 6
PATH_RE = re.compile(r"\b(?:src|docs|tools|tests)/[\w./-]+\.(?:py|md|yaml|json|csv)\b")
TICKET_RE = re.compile(r"\bTCK-\d{8}-[A-Z0-9-]+\b")
# A specific parity-ledger entry ID (e.g. INFRA-206, STRAT-227, TOWN-173) is a strong, specific
# identifier -- much stronger than its bare category prefix alone.
PARITY_ID_RE = re.compile(r"\b(?:[A-Z]{2,}-)?[A-Z]{3,}-\d{2,4}\b")

INTENT_KEYWORDS = {
    "mechanism_explanation": [
        "how does", "how the", "traced", "trace ", "flow is", "pipeline", "confirmed", "call chain",
        "calls into", "invoked", "understand", "how it works", "mechanism", "works by",
    ],
    "root_cause_debugging": [
        "bug", "fail", "failing", "failed", "error", "root cause", "broken", "regression",
        "incorrect", "wrong", "mismatch", "crash", "exception", "why is", "why was", "unexpected",
    ],
    "completeness_verification": [
        "implemented", "not yet implemented", "gap", "missing", "verify", "parity", "complete",
        "coverage", "already exists", "already satisfied", "unimplemented", "status of",
    ],
    "feasibility_evaluation": [
        "evaluate", "recommend", "should we", "worth", "compare", "measure", "economics",
        "justify", "warranted", "advantage", "feasibility", "net-positive", "net positive",
    ],
    "location_lookup": [
        "found in", "located", "file is", "defined in", "lives in", "site", "sites found",
        "is in ", "found at",
    ],
}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def classify_intent(text: str) -> str:
    lower = text.lower()
    scores = {}
    for bucket, kws in INTENT_KEYWORDS.items():
        scores[bucket] = sum(1 for kw in kws if kw in lower)
    best = max(scores.items(), key=lambda kv: kv[1])
    if best[1] == 0:
        return "other"
    return best[0]


def extract_identifiers(text: str) -> dict:
    ticket_ids = set(TICKET_RE.findall(text))
    # Exclude the current ticket's own TCK-... token accidentally matched as a parity ID lookalike,
    # and exclude any parity-id match that is actually a substring of an already-captured TCK id.
    parity_ids = {m for m in PARITY_ID_RE.findall(text) if not m.startswith("TCK-")}
    return {
        "camel": {m for m in CAMEL_RE.findall(text) if len(m) >= _CAMEL_MIN_LEN},
        "path": set(PATH_RE.findall(text)),
        "ticket": ticket_ids,
        "parity": parity_ids,
    }


def load_investigate_events():
    seen = {}
    with open(f"{REPO}/agent-monitoring/events.jsonl") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            if d.get("phase") != "Investigate":
                continue
            run_id = d.get("run_id")
            summary = d.get("summary") or ""
            if not run_id or not summary:
                continue
            if run_id in seen:
                continue  # keep first Investigate event per run_id
            seen[run_id] = {"run_id": run_id, "summary": normalize(summary), "ts": d.get("ts")}
    return list(seen.values())


def main():
    events = load_investigate_events()
    print(f"Total distinct tickets with an Investigate-phase summary: {len(events)}")

    records = []
    for e in events:
        text = e["summary"]
        ids = extract_identifiers(text)
        tags = candidate_tags_from_text(text, root=REPO)
        intent = classify_intent(text)
        records.append({**e, "ids": ids, "tags": tags, "intent": intent})

    intent_counts = Counter(r["intent"] for r in records)
    print("\nIntent bucket distribution:")
    for k, v in intent_counts.most_common():
        print(f"  {k}: {v}")

    # Pairwise conservative comparison: same intent + overlapping specific identifier, different tickets.
    repeated_pairs = []
    tag_only_pairs = 0
    n = len(records)
    for i in range(n):
        ri = records[i]
        for j in range(i + 1, n):
            rj = records[j]
            if ri["intent"] != rj["intent"]:
                continue
            if ri["intent"] == "other":
                continue  # too weak a bucket to count as a real intent match
            shared_camel = ri["ids"]["camel"] & rj["ids"]["camel"]
            shared_path = ri["ids"]["path"] & rj["ids"]["path"]
            shared_ticket = ri["ids"]["ticket"] & rj["ids"]["ticket"]
            shared_parity = ri["ids"]["parity"] & rj["ids"]["parity"]
            shared_specific = shared_camel | shared_path | shared_ticket | shared_parity
            shared_tags = ri["tags"] & rj["tags"]
            if shared_specific:
                repeated_pairs.append(
                    {
                        "a": ri["run_id"],
                        "b": rj["run_id"],
                        "intent": ri["intent"],
                        "shared_identifiers": sorted(shared_specific),
                        "shared_camel_or_path": sorted(shared_camel | shared_path),
                        "shared_ticket_or_parity_id": sorted(shared_ticket | shared_parity),
                        "a_summary": ri["summary"],
                        "b_summary": rj["summary"],
                    }
                )
            elif shared_tags:
                tag_only_pairs += 1

    print(f"\nConservative repeated-demand pairs (same intent + shared specific identifier, different tickets): {len(repeated_pairs)}")
    strong_pairs = [p for p in repeated_pairs if p["shared_camel_or_path"]]
    ref_only_pairs = [p for p in repeated_pairs if not p["shared_camel_or_path"] and p["shared_ticket_or_parity_id"]]
    print(f"  of which share a real code symbol or file path (strongest signal): {len(strong_pairs)}")
    print(f"  of which share only a referenced ticket/parity-entry ID (weaker signal): {len(ref_only_pairs)}")
    print(f"Tag-only overlap pairs (same intent, shared subsystem-topic tag, NO specific identifier overlap -- NOT counted): {tag_only_pairs}")
    n_tickets_involved = set()
    for p in repeated_pairs:
        n_tickets_involved.add(p["a"])
        n_tickets_involved.add(p["b"])
    print(f"Distinct tickets involved in >=1 conservative repeated-demand pair: {len(n_tickets_involved)} / {n} ({100*len(n_tickets_involved)/n:.1f}%)")

    print("\n--- Sample of up to 15 conservative repeated-demand pairs ---")
    for p in repeated_pairs[:15]:
        print(f"\n[{p['intent']}] shared={p['shared_identifiers']}")
        print(f"  A ({p['a']}): {p['a_summary'][:160]}")
        print(f"  B ({p['b']}): {p['b_summary'][:160]}")

    with open("/tmp/claude-1000/-home-u24desktop-Working-rpg-based-simulation/f3ce1493-682f-4e72-95ae-d2c6ad2943f4/scratchpad/kgmcp_p5_repeated_pairs.json", "w") as f:
        json.dump(
            {
                "total_tickets": n,
                "intent_distribution": intent_counts,
                "conservative_repeated_pair_count": len(repeated_pairs),
                "tag_only_pair_count": tag_only_pairs,
                "distinct_tickets_in_repeated_pairs": len(n_tickets_involved),
                "pairs": repeated_pairs,
            },
            f,
            indent=2,
            default=list,
        )


if __name__ == "__main__":
    main()

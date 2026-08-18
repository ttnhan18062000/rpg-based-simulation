"""Fixed, versioned representative-query corpus for the Knowledge Gateway MCP Phase 0
measurement baseline (TCK-20260814-KGMCP-MEASUREMENT-BASELINE).

This module is pure data plus one pure helper function — no live tool call, no file I/O, no
import of `tools/search_mcp.py` or any subprocess call. It is safe to import in every test run.
The real, recorded-from-a-real-run baseline lives in the committed fixture
`tests/tools/fixtures/kgmcp_measurement_baseline_corpus_results.json`, produced once by
`tools/agent-monitoring/kgmcp_baseline_runner.py` (a separate, one-time script, never wired into
this module or into any recurring cadence).

`CORPUS` has exactly 7 entries, one per `docs/plans/knowledge-gateway-mcp-proposal.md` §8's Query
Routing table row (confirmed 7 rows, not 8, by direct read during Plan). 5 of the 7 entries also
carry one of the 5 `use_case` IDs from §22's Representative Use Cases section — the other 2 carry
`use_case=None`, since §22 lists only 5 use cases against 7 routing shapes.
"""

from __future__ import annotations

import math

CORPUS_VERSION: int = 1

ROUTING_SHAPES: frozenset[str] = frozenset(
    {
        "definition_terminology_architecture",
        "symbol_lookup_callers_references",
        "requirement_completeness_verification",
        "ticket_historical_rationale",
        "test_impact_of_change",
        "ticket_work_status",
        "broad_task_context",
    }
)

USE_CASES: frozenset[str] = frozenset(
    {
        "authoritative_state_ownership",
        "feature_completeness_check",
        "historical_removal_rationale",
        "test_impact_of_change",
        "negative_knowledge_kafka",
    }
)

CORPUS: list[dict] = [
    {
        "id": "Q1_authoritative_state",
        "query_text": "What is AuthoritativeState, and who may mutate it?",
        "routing_shape": "definition_terminology_architecture",
        "use_case": "authoritative_state_ownership",
    },
    {
        "id": "Q2_symbol_lookup",
        "query_text": "Where is compute_search_investigation_trend defined, and what functions "
        "call it?",
        "routing_shape": "symbol_lookup_callers_references",
        "use_case": None,
    },
    {
        "id": "Q3_requirement_completeness",
        "query_text": "Is the read_count_correlation feature fully implemented?",
        "routing_shape": "requirement_completeness_verification",
        "use_case": "feature_completeness_check",
    },
    {
        "id": "Q4_historical_rationale",
        "query_text": "Why was WorldTemplateExpander removed?",
        "routing_shape": "ticket_historical_rationale",
        "use_case": "historical_removal_rationale",
    },
    {
        "id": "Q5_test_impact",
        "query_text": "What tests must run if tools/agent-monitoring/generate_retro.py changes?",
        "routing_shape": "test_impact_of_change",
        "use_case": "test_impact_of_change",
    },
    {
        "id": "Q6_ticket_status",
        "query_text": "What is the current status of "
        "TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING?",
        "routing_shape": "ticket_work_status",
        "use_case": None,
    },
    {
        "id": "Q7_negative_knowledge",
        "query_text": "Is Kafka currently used in this repository?",
        "routing_shape": "broad_task_context",
        "use_case": "negative_knowledge_kafka",
    },
]


def kgmcp_char_heuristic_v1_token_count(text: str) -> int:
    """The `kgmcp_char_heuristic_v1` token-counting method, implemented as a callable for the
    first time by this ticket (previously documented-only,
    docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md:144-181, which
    explicitly deferred its callable form to "a future ticket" — this is that future ticket, for
    this one formula only).

    `redaction_retention_policy.md` is drafted, not ratified (§11); this method's ±20% tolerance
    against a true tokenizer count is documented there, not re-derived here.
    """
    return math.ceil(len(text.encode("utf-8")) / 4)

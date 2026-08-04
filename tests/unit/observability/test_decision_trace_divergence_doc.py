"""
tests/unit/observability/test_decision_trace_divergence_doc.py
───────────────────────────────────────────────────────────────────────────────
Docs-consistency guard for TCK-20260702-OBSISO-TRACE-ASYNC Step 9: the accepted
crash-loss/queue-overflow-drop windows introduced by the async drain worker must
stay documented in docs/guidelines/intentional_divergences.md.
"""
import os


def test_intentional_divergences_documents_decision_trace_async_ticket():
    doc_path = "docs/guidelines/intentional_divergences.md"
    assert os.path.exists(doc_path), f"{doc_path} does not exist"

    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "TCK-20260702-OBSISO-TRACE-ASYNC" in content, (
        "intentional_divergences.md must reference TCK-20260702-OBSISO-TRACE-ASYNC"
    )
    assert "Crash-loss window" in content
    assert "Queue-overflow-drop window" in content

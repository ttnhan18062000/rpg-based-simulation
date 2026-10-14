---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261013-HARNESS-LLM-SECURITY-MAPPING
artifact_type: investigation
tags: [ai, governance]
---

# investigation — TCK-20261013-HARNESS-LLM-SECURITY-MAPPING

- Read: settings.json hooks and permissions, write_path_guard.py, retrieval_cache.py (grep for redaction use), agent_codex_posttool_adapter/redaction.py, post_tool_hook.py, sessions/guard.py and boundary.py, gate_ledger.py, search_shared.py, search_mcp.py, start_search_mcp.sh, requirements-knowledge.txt, pyproject.toml, .mcp.json, .github/.
- Result: see the doc's section 1 'Candidate controls' table for what each candidate really is.

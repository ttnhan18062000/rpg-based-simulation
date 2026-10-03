---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-MCP-TOOLS
artifact_type: test_plan
tags: [architecture, mcp, testing, documentation]
---

# Test plan — TCK-20261002-VISUAL-ASSETS-STORE-MCP-TOOLS

## Proof Plan

| Level | Proof kind | Oracle source | Expected effect | Selected commands |
|---|---|---|---|---|
| unit | read model: bounded, shaped, no absolute path, byte-identical tree, every kind and id form | ticket acceptance list | summaries only, nothing written | `pytest tests/visual_assets/store/unit/test_readmodel.py` |
| unit | handoff lookup: exact id pattern, unknown, path-like, `..`, bare candidate id refused | ticket acceptance list | refused, nothing written | `pytest tests/visual_assets/drawing/unit/test_handoff_unit.py` |
| stdio | exact tool set (19), no gate tool or parameter, gates stated in the instructions | ticket scope item 3 | tool-surface test green | `pytest tests/visual_assets/drawing/test_server_stdio.py` |
| stdio + Aseprite | `export_handoff` then `submit_candidate` gives PASSED for a real revision; a tampered package gives QUARANTINED with findings | ticket acceptance list | verdict and findings returned, only the quarantine written | `pytest tests/visual_assets/drawing/integration/test_server_stdio.py` |
| architecture | the server may import only the allowlisted store layers; planted violations fail for their rule | ticket scope item 2 | boundary test green | `pytest tests/visual_assets/test_boundaries.py` |
| docs | every command in the store contract's command table exists in the CLI parser and vice versa | ticket acceptance list | one comparison test | `pytest tests/visual_assets/store/unit/test_docs_commands.py` |
| tools | `.mcp.json` registration and launcher hardening still hold | ticket acceptance list | green | `pytest tests/tools/test_mcp_json_registration.py tests/tools/test_mcp_launcher_hardening.py` |
| mutation | hand-applied mutants of the new guards | n/a | each fails the intended test | scratch script (not committed) |

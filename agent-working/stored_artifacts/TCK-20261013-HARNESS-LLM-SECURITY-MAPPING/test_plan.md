---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261013-HARNESS-LLM-SECURITY-MAPPING
artifact_type: test_plan
tags: [ai, governance]
---

# test_plan — TCK-20261013-HARNESS-LLM-SECURITY-MAPPING

## Cases
- all 10 OWASP rows present; every present control cites a line or test that was read
- threat model covers four threats with entry point, impact, mitigation, gap
- search MCP checklist has five items each marked done/partial/open
- frontmatter valid

## Proof Plan
- level: documentation review against the code
- proof kind: reading cited files and tests; frontmatter validator
- oracle source: ticket acceptance criteria AC1-AC5
- expected effect: an honest record of present, advisory and missing controls
- selected commands: `python3 tools/validate_frontmatter.py docs/plans/agent_infrastructure/llm_security_mapping.md`

---
ticket_id: TCK-20260618-AUDIT-D12-PATTERNS
type: investigation
date: 2026-06-18
---
# D12 Investigation

## Patterns Checked
1. reason/metadata as storage: 41 reason=f"..." (mostly ok); 1 metadata={} case
2. Typed return annotations: 3 of 8 domain phases missing (world_emergence, perception, memory)
3. Untyped dict from domain: commitment/abandonment.py returns {"is_betrayal": ..., "penalty": ..., "reason": "greedy_desertion"}
4. Unstable sorts: 8 cases in non-test code; generator.py and selector.py on simulation path
5. Direct mutation: kernel.py:770 entity.timeline.append(event) outside pipeline
6. design_patterns.md: describes V1 GoalScorer/AIBrain patterns; V2 uses domain phases
7. Presenter pattern: 2 presenter files; route handlers mostly clean; behavior.py returns {} (intentional)
8. metadata={}: 1 case in scenarios.py — nearly clean

## Well-followed patterns
- Domain Phase class: 8/8 consistent
- Domain→core boundary: domains don't mutate AuthoritativeState
- Presenter layer: API routes use DTOs/presenters
- Metadata blobs: nearly clean (1 case)
- Authoritative pipeline: domains return typed records (mostly)

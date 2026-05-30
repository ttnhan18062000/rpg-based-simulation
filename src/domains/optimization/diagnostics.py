from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass(frozen=True, slots=True)
class DiagnosticIssue:
    category: str
    entity_id: Optional[int]
    message: str
    evidence_event_ids: List[str]

class DeveloperDiagnostics:
    """Aggregates optimization, budget skip, and cognition failure diagnostics."""
    def __init__(self) -> None:
        self._issues: List[DiagnosticIssue] = []

    def record_issue(self, issue: DiagnosticIssue) -> None:
        self._issues.append(issue)

    def generate_report(self) -> Dict[str, Any]:
        return {
            "issues": [
                {
                    "category": issue.category,
                    "entity_id": issue.entity_id,
                    "message": issue.message,
                    "evidence_event_ids": issue.evidence_event_ids
                }
                for issue in self._issues
            ]
        }

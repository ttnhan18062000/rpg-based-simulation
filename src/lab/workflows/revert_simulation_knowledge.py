import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Optional, List

from src.lab.results import RevertSimulationKnowledgeResult

# Core package imports
from src.lab.session import LabSessionStore
from src.lab.audit import LabAuditTrail

logger = logging.getLogger(__name__)

class LabKnowledgeRevertError(Exception):
    """Raised when a knowledge-store revert cannot be safely performed."""
    pass


class RevertSimulationKnowledgeWorkflow:
    """
    Reverts the most recent knowledge sync recorded for a session: removes exactly the
    insight/known-issue/rule files and decision-log line that
    UpdateSimulationKnowledgeWorkflow.run() wrote and recorded in the paired
    files_written/knowledge_sync_result audit events, rejecting the revert if a later
    sync has since modified any target file.
    """
    def __init__(self, workspace_root: Optional[str | Path] = None):
        if workspace_root is None:
            self.workspace_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.workspace_root = Path(workspace_root).resolve()

        sessions_dir = self.workspace_root / "data" / "lab_sessions"
        self.session_store = LabSessionStore(sessions_dir)
        self.knowledge_root = self.workspace_root / "data" / "lab_knowledge"

    def run(self, session_id: str) -> RevertSimulationKnowledgeResult:
        logger.info(f"Running RevertSimulationKnowledgeWorkflow for session '{session_id}'")
        from src.lab.audit import LabAuditTrail
        trail = LabAuditTrail(self.workspace_root)
        log = trail.read_log(session_id)

        # 2. Locate the most recent knowledge_sync_result and its immediately preceding
        # files_written event (both logged back-to-back by run(), so adjacency is a safe match).
        sync_result_event = None
        files_written_event = None
        for idx in range(len(log) - 1, -1, -1):
            event = log[idx]
            if event.get("event_type") == "knowledge_sync_result":
                sync_result_event = event
                if idx > 0 and log[idx - 1].get("event_type") == "files_written":
                    files_written_event = log[idx - 1]
                break

        if sync_result_event is None or sync_result_event["details"].get("status") == "NO_INSIGHTS":
            return {"status": "NOTHING_TO_REVERT", "session_id": session_id, "removed_files": []}

        # 2b. Legacy-log guard: pre-Step-1 audit logs don't carry file_hashes/decision_log_entry.
        file_hashes = files_written_event["details"].get("file_hashes") if files_written_event else None
        decision_log_entry = sync_result_event["details"].get("decision_log_entry")
        if file_hashes is None or decision_log_entry is None:
            raise LabKnowledgeRevertError(
                "this sync predates hash-tracking support and cannot be safely reverted"
            )

        # 3. Build the target file list, excluding report_path (absolute) and the decision log
        # (handled separately below).
        target_paths = [
            p for p in files_written_event["details"].get("files", [])
            if p != "decisions/decision_log.jsonl" and not Path(p).is_absolute()
        ]

        # Supersede pre-flight: check every target file's live content hash against the recorded
        # one before deleting anything, so a rejected revert never partially deletes files.
        for rel_path in target_paths:
            abs_path = self.knowledge_root / rel_path
            if not abs_path.is_file():
                continue
            current_hash = hashlib.sha256(abs_path.read_bytes()).hexdigest()
            recorded_hash = file_hashes.get(rel_path)
            if recorded_hash is not None and current_hash != recorded_hash:
                raise LabKnowledgeRevertError(
                    f"target file has been modified by a later operation and cannot be safely "
                    f"reverted: {rel_path}"
                )

        # 4. Delete target files, treating an already-absent file as already-reverted/idempotent.
        removed_files = []
        for rel_path in target_paths:
            abs_path = self.knowledge_root / rel_path
            if abs_path.is_file():
                abs_path.unlink()
                removed_files.append(rel_path)

        # 5. Remove exactly the matching decision-log line via temp-file + os.replace.
        decision_file = self.knowledge_root / "decisions" / "decision_log.jsonl"
        lines: List[str] = []
        if decision_file.is_file():
            with open(decision_file, "r", encoding="utf-8") as f:
                lines = [line for line in f if line.strip()]

        matching_indices = [
            i for i, line in enumerate(lines) if json.loads(line) == decision_log_entry
        ]
        if len(matching_indices) != 1:
            raise LabKnowledgeRevertError(
                "decision log entry match is ambiguous or already absent; cannot safely revert"
            )

        match_idx = matching_indices[0]
        remaining_lines = lines[:match_idx] + lines[match_idx + 1:]
        tmp_file = decision_file.with_name(decision_file.name + ".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            for line in remaining_lines:
                f.write(line if line.endswith("\n") else line + "\n")
        os.replace(tmp_file, decision_file)
        removed_files.append("decisions/decision_log.jsonl")

        # 6. Audit the revert action itself.
        trail.log_event(session_id, "knowledge_reverted", {"removed_files": removed_files})

        return {"status": "REVERTED", "session_id": session_id, "removed_files": removed_files}

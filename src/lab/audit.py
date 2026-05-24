import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Literal

from src.lab.session import LabSessionStore, LabSessionManifest, LabSessionError

def safe_path_resolution(base_dir: Path, target_path_str: str) -> Path:
    """Safely resolves target path within base directory, preventing traversal breakouts."""
    resolved_base = Path(base_dir).resolve()
    target_path = Path(target_path_str)
    
    # If target is absolute, check if it starts with resolved_base
    if target_path.is_absolute():
        resolved_target = target_path.resolve()
    else:
        resolved_target = (resolved_base / target_path).resolve()
        
    try:
        if not resolved_target.is_relative_to(resolved_base):
            raise PermissionError(f"Path traversal detected: {target_path_str} is outside of {base_dir}")
    except ValueError as e:
        raise PermissionError(f"Path traversal attempt blocked: {e}") from e
    return resolved_target


class LabApprovalGate:
    """
    Manages human-gated approval records, permissions, and gates.
    """
    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root).resolve()
        self.sessions_dir = self.workspace_root / "data" / "lab_sessions"
        self.session_store = LabSessionStore(self.sessions_dir)

    def record_approval(
        self,
        session_id: str,
        stage: str,
        approved_artifacts: List[str],
        approved_by: str,
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        Creates and stores a human-gated approval record for a session stage.
        """
        # Validate path safety for all artifacts
        session_dir = self.session_store.resolve_session_dir(session_id)
        
        # Enforce no unsafe paths in approvals
        for art in approved_artifacts:
            # Check if artifact references parent traversal
            if ".." in art or art.startswith("/") or art.startswith("\\"):
                raise ValueError(f"Approval artifact path cannot reference unsafe traversal: {art}")
            try:
                safe_path_resolution(session_dir, art)
            except PermissionError as e:
                raise ValueError(f"Approval artifact path is unsafe: {e}")
                
        # Load manifest and update status
        manifest = self.session_store.load_session(session_id)
        stage_lower = stage.lower()
        if stage_lower not in manifest.approval_status:
            manifest.approval_status[stage_lower] = "APPROVED"
        else:
            manifest.approval_status[stage_lower] = "APPROVED"
            
        self.session_store.save_session(manifest)
        
        # Create approval record
        approval_id = f"approval_{len(list((session_dir / 'generation').glob('approval_*.json'))) + 1:04d}"
        record = {
            "approval_id": approval_id,
            "session_id": session_id,
            "stage": stage.upper(),
            "approved_artifacts": approved_artifacts,
            "approved_by": approved_by,
            "approved_at": datetime.now(timezone.utc).isoformat(),
            "notes": notes
        }
        
        # Save record file
        records_dir = session_dir / "generation"
        records_dir.mkdir(parents=True, exist_ok=True)
        record_file = records_dir / f"{approval_id}.json"
        
        with open(record_file, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
            
        # Log to audit trail
        trail = LabAuditTrail(self.workspace_root)
        trail.log_event(session_id, "approval_recorded", {
            "approval_id": approval_id,
            "stage": stage.upper(),
            "approved_by": approved_by
        })
        
        return record

    def check_approval(self, session_id: str, stage: str) -> bool:
        """
        Returns whether a given session stage has been human-gated approved.
        """
        try:
            manifest = self.session_store.load_session(session_id)
            return manifest.approval_status.get(stage.lower()) == "APPROVED"
        except Exception:
            return False


class LabAuditTrail:
    """
    Maintains append-only audit logging for human-gated workflows.
    """
    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root).resolve()
        self.sessions_dir = self.workspace_root / "data" / "lab_sessions"
        self.session_store = LabSessionStore(self.sessions_dir)

    def log_event(self, session_id: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Appends a structured event line to the session's audit log.
        """
        session_dir = self.session_store.resolve_session_dir(session_id)
        audit_file = session_dir / "audit_log.jsonl"
        
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "details": details
        }
        
        # Append-only write
        with open(audit_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
            
        return entry

    def read_log(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Reads the full log for a given session.
        """
        session_dir = self.session_store.resolve_session_dir(session_id)
        audit_file = session_dir / "audit_log.jsonl"
        
        if not audit_file.is_file():
            return []
            
        events = []
        with open(audit_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line.strip()))
        return events

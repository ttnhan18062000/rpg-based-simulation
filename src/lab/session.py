from __future__ import annotations

import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Literal, List, Dict
from pydantic import BaseModel, Field, ConfigDict, field_validator

class LabSessionError(Exception):
    """Base exception for LabSession operations."""
    pass

class LabSessionManifest(BaseModel):
    """Pydantic model representing the human-gated lab session manifest."""
    model_config = ConfigDict(frozen=False, extra="allow")

    session_id: str = Field(..., pattern="^[a-zA-Z0-9_-]+$", description="Unique session identifier")
    status: Literal["ACTIVE", "WAITING_FOR_USER", "COMPLETED", "FAILED", "ARCHIVED"] = Field("ACTIVE")
    created_at: str = Field(..., description="ISO 8601 UTC timestamp of creation")
    updated_at: str = Field(..., description="ISO 8601 UTC timestamp of last update")
    current_stage: Literal["GENERATION", "EXECUTION_SUPPORT", "REGISTRATION", "INVESTIGATION", "ENHANCEMENT", "KNOWLEDGE_UPDATE"] = Field("GENERATION")
    
    linked_lab_runs: List[str] = Field(default_factory=list)
    linked_worlds: List[str] = Field(default_factory=list)
    linked_scenarios: List[str] = Field(default_factory=list)
    linked_experiments: List[str] = Field(default_factory=list)
    
    approval_status: Dict[str, Literal["PENDING", "APPROVED", "REJECTED"]] = Field(
        default_factory=lambda: {
            "generation": "PENDING",
            "execution_support": "PENDING",
            "enhancement": "PENDING"
        }
    )

class LabSessionStore:
    """
    File-based store for managing Phase 14 Lab Sessions under data/lab_sessions/.
    Enforces strict directory-level security and absolute scoping path guards.
    """
    STAGES = {
        "GENERATION": "generation",
        "EXECUTION_SUPPORT": "execution_support",
        "MANUAL_EXECUTION": "manual_execution",
        "REGISTRATION": "registration",
        "INVESTIGATION": "investigation",
        "ENHANCEMENT": "enhancement",
        "KNOWLEDGE_UPDATE": "knowledge_update"
    }

    def __init__(self, lab_sessions_dir: str | Path):
        self.lab_sessions_dir = Path(lab_sessions_dir).resolve()

    def _validate_session_id(self, session_id: str) -> None:
        """Enforces safe identifier formats to prevent directory traversal or malformed input."""
        if not session_id:
            raise LabSessionError("session_id cannot be empty")
        if not re.match(r"^[a-zA-Z0-9_-]+$", session_id):
            raise LabSessionError(
                f"Invalid session_id: '{session_id}'. Must be alphanumeric plus hyphens/underscores."
            )

    def resolve_session_dir(self, session_id: str) -> Path:
        """Safely resolves session directory, preventing any path traversal escapes."""
        self._validate_session_id(session_id)
        resolved = (self.lab_sessions_dir / session_id).resolve()
        try:
            if not resolved.is_relative_to(self.lab_sessions_dir) or resolved == self.lab_sessions_dir:
                raise PermissionError(
                    f"Path traversal detected or invalid access outside base directory: '{session_id}'"
                )
        except ValueError as e:
            raise PermissionError(
                f"Path traversal attempt blocked: '{session_id}' is outside '{self.lab_sessions_dir}': {e}"
            ) from e
        return resolved

    def create_session(self, session_id: str) -> LabSessionManifest:
        """
        Creates a new session root, sets up subdirectories, and registers its manifest.
        Raises LabSessionError if the session already exists or directory creation fails.
        """
        session_dir = self.resolve_session_dir(session_id)
        manifest_path = session_dir / "session_manifest.json"

        if manifest_path.is_file():
            raise LabSessionError(f"Session '{session_id}' already exists.")

        # Create session root and all required subdirectories
        try:
            session_dir.mkdir(parents=True, exist_ok=True)
            for sub_dir in self.STAGES.values():
                (session_dir / sub_dir).mkdir(parents=True, exist_ok=True)
                
            # Create sub-subdirectories for nested structures
            (session_dir / "generation" / "draft_specs").mkdir(parents=True, exist_ok=True)
            (session_dir / "generation" / "validation_reports").mkdir(parents=True, exist_ok=True)
            (session_dir / "enhancement" / "proposed_patches").mkdir(parents=True, exist_ok=True)
            (session_dir / "enhancement" / "next_experiment_drafts").mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise LabSessionError(f"Failed to initialize session directories: {e}") from e

        now_str = datetime.now(timezone.utc).isoformat()
        manifest = LabSessionManifest(
            session_id=session_id,
            status="ACTIVE",
            created_at=now_str,
            updated_at=now_str,
            current_stage="GENERATION"
        )
        self.save_session(manifest)
        return manifest

    def load_session(self, session_id: str) -> LabSessionManifest:
        """
        Loads the LabSessionManifest from the session manifest file.
        Raises FileNotFoundError if the session or manifest does not exist.
        """
        session_dir = self.resolve_session_dir(session_id)
        manifest_path = session_dir / "session_manifest.json"

        if not session_dir.is_dir():
            raise FileNotFoundError(f"Session directory not found: '{session_id}'")
        if not manifest_path.is_file():
            raise FileNotFoundError(f"Session manifest not found: '{manifest_path}'")

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return LabSessionManifest(**data)
        except json.JSONDecodeError as e:
            raise LabSessionError(f"Failed to parse session manifest: {e}") from e
        except Exception as e:
            raise LabSessionError(f"Failed to load session manifest: {e}") from e

    def save_session(self, manifest: LabSessionManifest) -> None:
        """
        Saves the LabSessionManifest model back to disk, updating the updated_at timestamp.
        """
        session_dir = self.resolve_session_dir(manifest.session_id)
        manifest_path = session_dir / "session_manifest.json"

        session_dir.mkdir(parents=True, exist_ok=True)
        manifest.updated_at = datetime.now(timezone.utc).isoformat()

        try:
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest.model_dump(), f, indent=2)
        except Exception as e:
            raise LabSessionError(f"Failed to save session manifest: {e}") from e

    def list_sessions(self) -> list[str]:
        """
        Lists all valid alphanumeric session IDs that contain a session manifest.
        """
        if not self.lab_sessions_dir.is_dir():
            return []

        session_ids = []
        for child in self.lab_sessions_dir.iterdir():
            if child.is_dir():
                manifest_path = child / "session_manifest.json"
                if manifest_path.is_file():
                    try:
                        self._validate_session_id(child.name)
                        session_ids.append(child.name)
                    except LabSessionError:
                        continue
        return sorted(session_ids)

    def get_stage_dir(self, session_id: str, stage: str) -> Path:
        """
        Returns the resolved safe subdirectory Path for a specific stage in a session.
        Raises LabSessionError if the stage is unrecognized.
        """
        session_dir = self.resolve_session_dir(session_id)
        upper_stage = stage.upper()
        if upper_stage not in self.STAGES:
            raise LabSessionError(f"Unknown or invalid workflow stage: '{stage}'")
        
        sub_dir = self.STAGES[upper_stage]
        resolved_sub = (session_dir / sub_dir).resolve()
        
        # Security double-check
        if not resolved_sub.is_relative_to(session_dir) or resolved_sub == session_dir:
            raise PermissionError(f"Stage directory escape blocked: '{sub_dir}'")
            
        return resolved_sub

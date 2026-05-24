from __future__ import annotations

import yaml
from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator

class WorkflowSkill(BaseModel):
    """Pydantic model representing a dynamic workflow or skill contract."""
    model_config = ConfigDict(frozen=True, extra="allow")

    name: str
    purpose: str = Field("", description="The core purpose or description of the contract")
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    allowed_actions: List[str] = Field(default_factory=list)
    forbidden_actions: List[str] = Field(default_factory=list)
    output_artifacts: List[str] = Field(default_factory=list)
    approval_required: bool = Field(False)
    context_budget: Dict[str, Any] = Field(default_factory=dict)
    failure_behavior: str = Field("STOP")

    @model_validator(mode="before")
    @classmethod
    def populate_purpose(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Map description -> purpose if purpose is missing
            if "purpose" not in data and "description" in data:
                data["purpose"] = data["description"]
        return data

class WorkflowRegistry:
    """
    Dynamic scanner and registry for Antigravity workflows and skills.
    Parses YAML frontmatter directly from .agents/workflows/*.md and .agents/skills/*/SKILL.md.
    """
    def __init__(self, workflows_dir: str | Path, skills_dir: str | Path):
        self.workflows_dir = Path(workflows_dir).resolve()
        self.skills_dir = Path(skills_dir).resolve()
        self._workflows: Dict[str, WorkflowSkill] = {}
        self._skills: Dict[str, WorkflowSkill] = {}

    def _parse_frontmatter(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parses the YAML frontmatter enclosed in '---' from a markdown file."""
        if not file_path.is_file():
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            
            if not content.startswith("---"):
                return None
                
            parts = content.split("---", 2)
            if len(parts) < 3:
                return None
                
            yaml_text = parts[1]
            data = yaml.safe_load(yaml_text)
            if isinstance(data, dict):
                return data
        except Exception:
            return None
        return None

    def scan_and_register(self) -> None:
        """Dynamically scans workflows and skills directories, loading all valid contracts."""
        self._workflows.clear()
        self._skills.clear()

        # Scan workflows (.agents/workflows/*.md)
        if self.workflows_dir.is_dir():
            for child in self.workflows_dir.glob("*.md"):
                data = self._parse_frontmatter(child)
                if data and "name" in data:
                    try:
                        contract = WorkflowSkill(**data)
                        self._workflows[contract.name] = contract
                    except Exception:
                        continue

        # Scan skills (.agents/skills/*/SKILL.md)
        if self.skills_dir.is_dir():
            for child_dir in self.skills_dir.iterdir():
                if child_dir.is_dir():
                    skill_md = child_dir / "SKILL.md"
                    if skill_md.is_file():
                        data = self._parse_frontmatter(skill_md)
                        if data and "name" in data:
                            try:
                                contract = WorkflowSkill(**data)
                                self._skills[contract.name] = contract
                            except Exception:
                                continue

    def get_workflow(self, name: str) -> WorkflowSkill:
        """Fetches the workflow contract by name. Raises ValueError if unknown."""
        if name not in self._workflows:
            raise ValueError(f"Unknown or unregistered workflow command: '{name}'")
        return self._workflows[name]

    def get_skill(self, name: str) -> WorkflowSkill:
        """Fetches the skill contract by name. Raises ValueError if unknown."""
        if name not in self._skills:
            raise ValueError(f"Unknown or unregistered skill: '{name}'")
        return self._skills[name]

    def list_workflows(self) -> list[str]:
        return sorted(list(self._workflows.keys()))

    def list_skills(self) -> list[str]:
        return sorted(list(self._skills.keys()))

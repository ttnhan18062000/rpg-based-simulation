# Compliance IDs: WORLD-CAT-006, WORLD-CAT-007
from __future__ import annotations

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from src.content.repository import CatalogRepository


class CatalogValidationError(Exception):
    """Exception raised when catalog validation discovers errors."""
    pass


class ValidationIssue(BaseModel):
    """Represents a specific semantic warning or error inside the catalog files."""
    severity: str = Field(..., description="Either 'ERROR' or 'WARNING'")
    rule_id: str = Field(..., description="Unique validation rule code")
    message: str = Field(..., description="Informative explanation of the validation constraint violation")
    target_id: Optional[str] = Field(None, description="Optional definition ID causing the violation")
    filename: Optional[str] = Field(None, description="Filename where the issue resides")


class CatalogValidator:
    """
    Independent validator for the static Content Catalog. 
    Catches relational, schema, mapping, and range errors across definition directories.
    """

    def __init__(self, repo: CatalogRepository):
        self.repo = repo

    def validate(self) -> List[ValidationIssue]:
        """
        Runs validation sweeps and returns a complete list of structured warnings and errors.
        """
        issues: List[ValidationIssue] = []

        # Validate relational linkages
        self._validate_role_relations(issues)
        self._validate_building_relations(issues)
        self._validate_defaults(issues)
        
        return issues

    def _validate_role_relations(self, issues: List[ValidationIssue]) -> None:
        """Verify referenced stats and inventory profiles exist in the loaded catalog repository."""
        for role_id, role in self.repo.roles.items():
            # Check stats profile reference
            if role.default_stats_profile:
                if not self.repo.get_stats_profile(role.default_stats_profile):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-001",
                        message=f"Role '{role_id}' references non-existent stats profile '{role.default_stats_profile}'",
                        target_id=role_id,
                        filename="roles.yaml"
                    ))
            
            # Check inventory profile reference
            if role.default_inventory_profile:
                if not self.repo.get_inventory_profile(role.default_inventory_profile):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-002",
                        message=f"Role '{role_id}' references non-existent inventory profile '{role.default_inventory_profile}'",
                        target_id=role_id,
                        filename="roles.yaml"
                    ))

            # Check cognition profile reference
            if role.default_cognition_profile:
                if not self.repo.get_cognition_profile(role.default_cognition_profile):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-003",
                        message=f"Role '{role_id}' references non-existent cognition profile '{role.default_cognition_profile}'",
                        target_id=role_id,
                        filename="roles.yaml"
                    ))

    def _validate_building_relations(self, issues: List[ValidationIssue]) -> None:
        """Verify referenced service profiles inside buildings exist."""
        for bld_id, bld in self.repo.buildings.items():
            if bld.service_profile_id:
                if not self.repo.get_service_profile(bld.service_profile_id):
                    issues.append(ValidationIssue(
                        severity="ERROR",
                        rule_id="CAT-REL-004",
                        message=f"Building '{bld_id}' references non-existent service profile '{bld.service_profile_id}'",
                        target_id=bld_id,
                        filename="buildings.yaml"
                    ))

    def _validate_defaults(self, issues: List[ValidationIssue]) -> None:
        """Verify that at least one global default compile profile exists."""
        if not self.repo.defaults:
            issues.append(ValidationIssue(
                severity="WARNING",
                rule_id="CAT-DEF-001",
                message="No global default compile profiles are configured inside the catalog.",
                filename="defaults.yaml"
            ))

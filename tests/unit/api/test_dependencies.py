"""Unit tests for src/api/dependencies.py's DI singleton pairs.

Ticket: TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT (added the CatalogRepository singleton pair).
"""
from __future__ import annotations

from src.content.repository import CatalogRepository
import src.api.dependencies as deps


def test_catalog_repository_di_wiring_loaded_once_at_startup():
    catalog = CatalogRepository()
    catalog.load_all()

    deps.set_catalog_repository(catalog)

    first = deps.get_catalog_repository()
    second = deps.get_catalog_repository()

    assert first is catalog
    assert first is second


def test_get_catalog_repository_returns_none_when_unset():
    deps.set_catalog_repository(None)
    assert deps.get_catalog_repository() is None

"""Disabled-mode infrastructure import smoke tests. [Cross-Cutting Track Task 1]

Proves that test collection and execution succeed with optional broker
packages (RabbitMQ/Kafka) disabled via environment flags.
"""
import os
import pytest
from unittest.mock import patch


class TestBrokerlessImport:
    """Verify that optional infrastructure modules do not crash import when disabled."""

    def test_rabbitmq_client_importable_when_disabled(self):
        """rabbitmq_client should import cleanly with DISABLE_RABBITMQ=1."""
        with patch.dict(os.environ, {"DISABLE_RABBITMQ": "1"}):
            import importlib
            import src.api.rabbitmq_client as mod
            importlib.reload(mod)
            assert mod.is_rabbitmq_disabled() is True
            assert mod.get_rabbitmq() is None

    def test_kafka_client_importable_when_disabled(self):
        """kafka_client should import cleanly with DISABLE_KAFKA=1."""
        with patch.dict(os.environ, {"DISABLE_KAFKA": "1"}):
            import importlib
            import src.api.kafka_client as mod
            importlib.reload(mod)
            assert mod.is_kafka_disabled() is True
            assert mod.get_kafka_producer() is None

    def test_rabbitmq_functions_noop_when_disabled(self):
        """All RabbitMQ public functions should return safely when disabled."""
        with patch.dict(os.environ, {"DISABLE_RABBITMQ": "1"}):
            from src.api.rabbitmq_client import is_rabbitmq_disabled, get_rabbitmq
            assert is_rabbitmq_disabled() is True
            conn = get_rabbitmq()
            assert conn is None

    def test_kafka_functions_noop_when_disabled(self):
        """All Kafka public functions should return safely when disabled."""
        with patch.dict(os.environ, {"DISABLE_KAFKA": "1"}):
            from src.api.kafka_client import is_kafka_disabled, get_kafka_producer
            assert is_kafka_disabled() is True
            producer = get_kafka_producer()
            assert producer is None


class TestDisabledModeRegression:
    """Verify that the main simulation runner imports succeed without broker packages."""

    def test_headless_runner_importable_without_brokers(self):
        """HeadlessRunner should import cleanly without broker dependencies."""
        with patch.dict(os.environ, {"DISABLE_RABBITMQ": "1", "DISABLE_KAFKA": "1"}):
            from src.testing.headless_regression_runner import HeadlessRunner
            assert HeadlessRunner is not None

    def test_action_system_importable_without_brokers(self):
        """ActionSystem should import without triggering broker imports."""
        with patch.dict(os.environ, {"DISABLE_RABBITMQ": "1", "DISABLE_KAFKA": "1"}):
            from src.systems.gameplay.action_system import ActionSystem
            assert ActionSystem is not None


import os
import sys
from unittest import mock
import pytest

def test_rabbitmq_disabled_no_crash():
    """Verify that rabbitmq_client handles missing pika gracefully when disabled."""
    with mock.patch.dict(os.environ, {"DISABLE_RABBITMQ": "1"}):
        # We must clear the module from sys.modules if it was already imported
        if "src.api.rabbitmq_client" in sys.modules:
            del sys.modules["src.api.rabbitmq_client"]
        
        # Mock pika as missing
        with mock.patch.dict(sys.modules, {"pika": None}):
            from src_legacy.api.rabbitmq_client import get_rabbitmq, HAS_PIKA
            assert HAS_PIKA is False
            assert get_rabbitmq() is None

def test_kafka_disabled_no_crash():
    """Verify that kafka_client handles missing confluent_kafka gracefully when disabled."""
    with mock.patch.dict(os.environ, {"DISABLE_KAFKA": "1"}):
        if "src.api.kafka_client" in sys.modules:
            del sys.modules["src.api.kafka_client"]
            
        with mock.patch.dict(sys.modules, {"confluent_kafka": None}):
            from src_legacy.api.kafka_client import get_kafka_producer, HAS_KAFKA
            assert HAS_KAFKA is False
            assert get_kafka_producer() is None

def test_redis_disabled_no_crash():
    """Verify that redis_client handles missing redis gracefully when disabled."""
    with mock.patch.dict(os.environ, {"DISABLE_REDIS": "1"}):
        if "src.api.redis_client" in sys.modules:
            del sys.modules["src.api.redis_client"]
            
        with mock.patch.dict(sys.modules, {"redis": None}):
            from src_legacy.api.redis_client import get_async_redis, HAS_REDIS_PKG
            assert HAS_REDIS_PKG is False
            assert get_async_redis() is None

def test_regression_runner_with_disabled_brokers():
    """Verify that the headless runner can initialize without brokers."""
    # This is a smoke test for the runner's bootstrapping logic
    with mock.patch.dict(os.environ, {
        "DISABLE_RABBITMQ": "1",
        "DISABLE_KAFKA": "1",
        "DISABLE_REDIS": "1"
    }):
        # We don't need to mock sys.modules here, just prove it returns None and doesn't crash
        from src_legacy.api.rabbitmq_client import get_rabbitmq
        from src_legacy.api.kafka_client import get_kafka_producer
        
        assert get_rabbitmq() is None
        assert get_kafka_producer() is None

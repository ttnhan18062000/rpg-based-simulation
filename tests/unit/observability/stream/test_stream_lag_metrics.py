"""ai_worker serves consumer-group lag and pending count as Prometheus gauges (TCK-20261014-AI-WORKER-EXPOSES-STREAM-CONSUMER-LAG-AND-PENDING-METRICS)."""
from __future__ import annotations

import socket
import subprocess
import sys
import urllib.request

import pytest
from prometheus_client import CollectorRegistry, generate_latest

from src.observability.stream import lag_metrics
from src.observability.stream.lag_metrics import StreamLagCollector, metrics_port_from_env


class FakeRedis:
    def __init__(self, groups_by_stream):
        self.groups_by_stream = groups_by_stream
        self.down = False

    def xinfo_groups(self, stream):
        if self.down:
            raise ConnectionError("redis is down")
        return self.groups_by_stream[stream]


def _scrape(collector):
    registry = CollectorRegistry()
    registry.register(collector)
    return generate_latest(registry).decode()


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_lag_and_pending_are_reported_per_stream_and_group():
    fake = FakeRedis({"simulation:events": [
        {"name": "observatory:consumers", "pending": 7, "lag": 120},
        {"name": "audit", "pending": 0, "lag": 3},
    ]})
    text = _scrape(StreamLagCollector(lambda: fake, ["simulation:events"]))
    assert 'sim_stream_consumer_up 1.0' in text
    assert 'sim_stream_consumer_lag{group="observatory:consumers",stream="simulation:events"} 120.0' in text
    assert 'sim_stream_pending_messages{group="observatory:consumers",stream="simulation:events"} 7.0' in text
    assert 'sim_stream_consumer_lag{group="audit",stream="simulation:events"} 3.0' in text
    assert 'sim_stream_pending_messages{group="audit",stream="simulation:events"} 0.0' in text


def test_values_are_read_at_scrape_time():
    fake = FakeRedis({"s": [{"name": "g", "pending": 1, "lag": 10}]})
    collector = StreamLagCollector(lambda: fake, ["s"])
    assert 'sim_stream_consumer_lag{group="g",stream="s"} 10.0' in _scrape(collector)
    fake.groups_by_stream["s"][0].update(lag=99, pending=4)
    text = _scrape(collector)
    assert 'sim_stream_consumer_lag{group="g",stream="s"} 99.0' in text
    assert 'sim_stream_pending_messages{group="g",stream="s"} 4.0' in text


def test_a_group_with_unknown_lag_reports_pending_and_no_lag_sample():
    fake = FakeRedis({"s": [{"name": "g", "pending": 2, "lag": None}]})
    text = _scrape(StreamLagCollector(lambda: fake, ["s"]))
    assert 'sim_stream_pending_messages{group="g",stream="s"} 2.0' in text
    assert 'sim_stream_consumer_lag{' not in text


def test_redis_down_reports_up_zero_and_no_stale_gauges():
    fake = FakeRedis({"s": [{"name": "g", "pending": 5, "lag": 50}]})
    collector = StreamLagCollector(lambda: fake, ["s"])
    assert 'sim_stream_consumer_lag{group="g",stream="s"} 50.0' in _scrape(collector)
    fake.down = True
    text = _scrape(collector)
    assert 'sim_stream_consumer_up 0.0' in text
    assert 'sim_stream_consumer_lag{' not in text
    assert 'sim_stream_pending_messages{' not in text
    fake.down = False
    assert 'sim_stream_consumer_up 1.0' in _scrape(collector)


def test_a_client_that_cannot_be_built_reports_up_zero():
    def refuse():
        raise ConnectionError("no redis")

    text = _scrape(StreamLagCollector(refuse, ["s"]))
    assert 'sim_stream_consumer_up 0.0' in text
    assert 'sim_stream_consumer_lag{' not in text


def test_the_port_defaults_to_9108_and_the_env_overrides_it():
    assert metrics_port_from_env({}) == 9108
    assert metrics_port_from_env({"AI_WORKER_METRICS_PORT": "9300"}) == 9300
    assert metrics_port_from_env({"AI_WORKER_METRICS_PORT": ""}) == 9108


@pytest.mark.parametrize("bad", ["abc", "0", "70000", "-5"])
def test_an_unusable_port_value_falls_back_to_the_default(bad):
    assert metrics_port_from_env({"AI_WORKER_METRICS_PORT": bad}) == 9108


def test_metrics_endpoint_serves_the_gauges_on_the_env_port(monkeypatch):
    fake = FakeRedis({"simulation:events": [{"name": "observatory:consumers", "pending": 3, "lag": 8}]})
    monkeypatch.setattr(lag_metrics, "redis_client_factory", lambda url: (lambda: fake))
    port = _free_port()
    monkeypatch.setenv("AI_WORKER_METRICS_PORT", str(port))
    lag_metrics.start_lag_metrics_server("redis://unused", "simulation:events")
    body = urllib.request.urlopen(f"http://127.0.0.1:{port}/metrics", timeout=5).read().decode()
    assert 'sim_stream_consumer_lag{group="observatory:consumers",stream="simulation:events"} 8.0' in body
    assert 'sim_stream_pending_messages{group="observatory:consumers",stream="simulation:events"} 3.0' in body


def test_the_lag_module_does_not_import_the_engine():
    code = (
        "import sys; import src.observability.stream.lag_metrics; "
        "bad = sorted(m for m in sys.modules if m == 'src.engine' or m.startswith('src.engine.')); "
        "print(bad); sys.exit(1 if bad else 0)"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr

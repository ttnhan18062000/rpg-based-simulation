"""The request-duration histogram (issue #622, R2): labelled by method, route TEMPLATE and status class, with bounded cardinality."""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from prometheus_client import CollectorRegistry

from src.api.http_metrics import (
    METRIC_NAME, UNMATCHED_ROUTE, HttpRequestMetrics, RequestDurationMiddleware, activate, deactivate, status_class,
)


class _Manager:
    def __init__(self) -> None:
        self.registry = CollectorRegistry()
        self.http_metrics = HttpRequestMetrics(self.registry)


@pytest.fixture
def served(monkeypatch):
    manager = _Manager()
    activate(manager.http_metrics)
    app = FastAPI()
    app.add_middleware(RequestDurationMiddleware)

    @app.get("/items/{item_id}")
    def item(item_id: str):
        return {"id": item_id}

    @app.get("/boom")
    def boom():
        raise RuntimeError("boom")

    yield TestClient(app, raise_server_exceptions=False), manager.registry
    deactivate(manager.http_metrics)


def _series(registry: CollectorRegistry):
    """Every (method, route, status_class) the histogram holds, with its request count."""
    out = {}
    for family in registry.collect():
        for sample in family.samples:
            if sample.name == f"{METRIC_NAME}_count":
                out[(sample.labels["method"], sample.labels["route"], sample.labels["status_class"])] = sample.value
    return out


def test_a_parameterised_path_is_one_series_labelled_by_its_template(served):
    client, registry = served
    for item_id in ("1", "2", "abc", "a-very-long-and-unique-identifier-0001"):
        assert client.get(f"/items/{item_id}").status_code == 200
    assert _series(registry) == {("GET", "/items/{item_id}", "2xx"): 4.0}


def test_an_unmatched_route_gets_one_fixed_label_whatever_the_raw_path(served):
    client, registry = served
    for path in ("/nope", "/nope/deeper", "/items", "/x/" + "y" * 200):
        assert client.get(path).status_code == 404
    assert _series(registry) == {("GET", UNMATCHED_ROUTE, "4xx"): 4.0}


def test_a_failing_handler_is_counted_as_a_5xx_on_its_route(served):
    client, registry = served
    assert client.get("/boom").status_code == 500
    assert _series(registry) == {("GET", "/boom", "5xx"): 1.0}


def test_the_label_set_stays_bounded_over_many_distinct_raw_paths(served):
    client, registry = served
    for i in range(200):
        client.get(f"/items/{i}")
        client.get(f"/missing/{i}")
    assert len(_series(registry)) == 2


def test_status_classes_and_unknown_methods_are_bucketed():
    assert [status_class(c) for c in (101, 204, 301, 404, 503)] == ["1xx", "2xx", "3xx", "4xx", "5xx"]
    assert status_class(0) == status_class(700) == "other"
    registry = CollectorRegistry()
    metrics = HttpRequestMetrics(registry)
    metrics.observe("BREW", "/pot", 200, 0.01)
    metrics.observe("PROPFIND", "/pot", 200, 0.01)
    assert set(_series(registry)) == {("OTHER", "/pot", "2xx")}


def test_a_request_with_no_active_histogram_still_succeeds():
    app = FastAPI()
    app.add_middleware(RequestDurationMiddleware)

    @app.get("/ok")
    def ok():
        return {}

    assert TestClient(app).get("/ok").status_code == 200

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from web import app


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def test_create_order(client: TestClient) -> None:
    response = client.post("/orders", json={"total": 100})
    assert response.status_code == 201
    data = response.json()
    assert "order_id" in data
    assert data["total"] == 100


def test_create_order_with_invalid_total(client: TestClient) -> None:
    response = client.post("/orders", json={"total": -10})
    assert response.status_code == 422
    assert "PositiveTotal" in response.json()["detail"]


def test_get_order_not_found(client: TestClient) -> None:
    response = client.get(f"/orders/{uuid4()}")
    assert response.status_code == 404


def test_get_order(client: TestClient) -> None:
    create_response = client.post("/orders", json={"total": 42})
    order_id = create_response.json()["order_id"]

    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    assert response.json()["order_id"] == order_id
    assert response.json()["total"] == 42

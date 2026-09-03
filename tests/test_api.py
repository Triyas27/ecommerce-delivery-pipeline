import numpy as np
import pytest
from fastapi.testclient import TestClient

from api import main

VALID_ORDER = {
    "promised_days": 20,
    "purchase_day_of_week": 2,
    "purchase_month": 11,
    "item_count": 1,
    "distinct_product_count": 1,
    "distinct_seller_count": 1,
    "total_price": 124.99,
    "total_freight_value": 21.88,
    "customer_state": "SP",
}


class StubModel:
    """Stands in for the real trained model - CI has no registry to load one from."""

    def predict_proba(self, X):
        return np.array([[0.7, 0.3]] * len(X))


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main.mlflow.sklearn, "load_model", lambda uri: StubModel())
    with TestClient(main.app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model_loaded": True}


def test_predict_valid_order(client):
    response = client.post("/predict", json=VALID_ORDER)
    assert response.status_code == 200
    body = response.json()
    assert body["is_late_probability"] == pytest.approx(0.3)
    assert body["is_late_prediction"] is False


def test_predict_missing_required_field(client):
    incomplete_order = {k: v for k, v in VALID_ORDER.items() if k != "customer_state"}
    response = client.post("/predict", json=incomplete_order)
    assert response.status_code == 422

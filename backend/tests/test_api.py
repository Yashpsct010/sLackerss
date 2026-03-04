import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.models.domain import ForecastHorizon

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_get_forecast():
    response = client.get("/api/v1/forecasts/ELEC-100?horizon=DAILY")
    assert response.status_code == 200
    data = response.json()
    assert data["sku"] == "ELEC-100"
    assert data["horizon"] == ForecastHorizon.DAILY.value
    assert len(data["predictions"]) == 30

def test_get_recommendations():
    response = client.get("/api/v1/recommendations/LOC-1")
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0
    # Ensure sorted by priority
    recs = data["recommendations"]
    assert recs[0]["priority_score"] >= recs[-1]["priority_score"]

def test_ingest_sales_data_empty():
    response = client.post("/api/v1/sales-data", json={"records": []})
    assert response.status_code == 400

def test_ingest_sales_data_valid():
    payload = {
        "records": [
            {
                "sku": "TEST-SKU",
                "date": "2024-03-01",
                "location": "LOC-1",
                "quantity_sold": 10,
                "revenue": 100.0,
                "price": 10.0,
                "promotion_active": False
            }
        ]
    }
    response = client.post("/api/v1/sales-data", json=payload)
    assert response.status_code == 200
    assert response.json()["result"]["status"] == "success"
    assert response.json()["result"]["valid_count"] == 1

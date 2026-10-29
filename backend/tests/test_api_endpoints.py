import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["models"]["crop_suitability"]["selected_model"].startswith("Support Vector Machine")
    assert data["models"]["crop_yield"]["selected_model"].startswith("Random Forest")
    assert "AMBALA" in data["metadata"]["supported_districts"]

def test_api_weather_endpoint():
    response = client.get("/api/weather?latitude=30.3782&longitude=76.7767&district=Ambala")
    assert response.status_code == 200
    data = response.json()
    assert "temperature" in data
    assert "humidity" in data
    assert "rainfall" in data
    assert data["temperature"] > 0

def test_api_crop_recommendation_endpoint():
    payload = {
        "N": 90.0,
        "P": 42.0,
        "K": 43.0,
        "temperature": 25.0,
        "humidity": 80.0,
        "ph": 6.5,
        "rainfall": 200.0
    }
    response = client.post("/api/crop-recommendation", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "recommended_crop" in data
    assert data["probability_supported"] is False
    assert len(data["candidate_ranking"]) > 0

def test_api_yield_prediction_endpoint():
    payload = {
        "state": "Haryana",
        "district": "Ambala",
        "crop": "Rice",
        "season": "Kharif",
        "year": 2024,
        "area": 4.0
    }
    response = client.post("/api/yield-prediction", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_yield_tonnes_per_ha"] > 0
    assert data["estimated_production_tonnes"] > 0
    assert data["estimated_production_quintals"] == round(data["estimated_production_tonnes"] * 10.0, 2)

def test_api_mandi_analysis_endpoint():
    payload = {
        "crop": "Maize",
        "state": "Haryana"
    }
    response = client.post("/api/mandi-analysis", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["selected_price_quintal"] > 0
    assert data["experimental_forecast"]["chronological_baseline_mae"] == 161.09
    assert data["experimental_forecast"]["hgb_test_mae"] == 389.71

def test_api_plan_endpoint():
    payload = {
        "state": "Haryana",
        "district": "Ambala",
        "area_ha": 2.5,
        "season": "Kharif",
        "N": 90.0,
        "P": 42.0,
        "K": 43.0,
        "temperature": 25.0,
        "humidity": 80.0,
        "ph": 6.5,
        "rainfall": 220.0,
        "storage_months": 0
    }
    response = client.post("/api/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "primary_crop" in data
    assert "selected_plan" in data
    assert data["selected_plan"]["gross_production_tonnes"] > 0
    assert data["selected_plan"]["net_return_rs"] is not None

def test_api_what_if_endpoint():
    # First generate a plan to get a valid CropPlan
    plan_payload = {
        "state": "Haryana",
        "district": "Ambala",
        "area_ha": 2.0,
        "season": "Kharif",
        "N": 90.0,
        "P": 42.0,
        "K": 43.0,
        "temperature": 25.0,
        "humidity": 80.0,
        "ph": 6.5,
        "rainfall": 200.0,
        "storage_months": 0
    }
    plan_res = client.post("/api/plan", json=plan_payload).json()
    base_plan = plan_res["selected_plan"]

    what_if_payload = {
        "base_plan": base_plan,
        "price_change_pct": 10.0,
        "yield_shock_pct": -5.0,
        "storage_months": 1
    }
    response = client.post("/api/what-if", json=what_if_payload)
    assert response.status_code == 200
    data = response.json()
    assert "simulated_plan" in data
    assert data["simulated_plan"]["gross_revenue_rs"] > 0

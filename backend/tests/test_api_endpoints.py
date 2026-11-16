import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["models"]["crop_suitability"]["selected_model"].startswith(
        "Support Vector Machine"
    )
    assert data["models"]["crop_yield"]["selected_model"].startswith("Random Forest")
    assert "AMBALA" in data["metadata"]["supported_districts"]


def test_api_weather_endpoint():
    response = client.get(
        "/api/weather?latitude=30.3782&longitude=76.7767&district=Ambala"
    )
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
        "rainfall": 200.0,
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
        "area": 4.0,
    }
    response = client.post("/api/yield-prediction", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_yield_tonnes_per_ha"] > 0
    assert data["estimated_production_tonnes"] > 0
    assert data["estimated_production_quintals"] == round(
        data["estimated_production_tonnes"] * 10.0, 2
    )


def test_api_mandi_analysis_endpoint():
    payload = {"crop": "Maize", "state": "Haryana"}
    response = client.post("/api/mandi-analysis", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["selected_price_quintal"] > 0
    assert data["sample_size"] > 0
    assert data["forecast_price_quintal"] > 0
    assert "Historical" in data["price_source"]


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
        "storage_months": 0,
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
        "storage_months": 0,
    }
    plan_res = client.post("/api/plan", json=plan_payload).json()
    base_plan = plan_res["selected_plan"]

    what_if_payload = {
        "base_plan": base_plan,
        "price_change_pct": 10.0,
        "yield_shock_pct": -5.0,
        "storage_months": 1,
    }
    response = client.post("/api/what-if", json=what_if_payload)
    assert response.status_code == 200
    data = response.json()
    assert "simulated_plan" in data
    assert data["simulated_plan"]["gross_revenue_rs"] > 0


@pytest.mark.parametrize('patch', [
    {'temperature': 100}, {'rainfall': 5000}, {'area_ha': 1001},
    {'state': 'Atlantis'}, {'area_ha': 0}, {'humidity': -1}, {'user_price_override': 0.001},
])
def test_plan_rejects_out_of_range_inputs(patch):
    assert client.post('/api/plan', json=patch).status_code == 422


def test_dataset_price_location_override_and_forecast():
    from app.services.mandi_service import mandi_service, dataset_prices
    result = mandi_service.get_mandi_analysis('Maize', 'Haryana', district='Ambala')
    raw = dataset_prices('Maize')
    local = raw[raw['State Name'].eq('Haryana') & raw['District Name'].str.upper().eq('AMBALA')]
    recent = local[local.date.dt.to_period('M').eq(local.date.max().to_period('M'))]
    assert result.selected_price_quintal == round(float(recent.price.median()), 2)
    assert result.market_scope == 'Ambala, Haryana'
    assert result.forecast_price_quintal > 0
    override = mandi_service.get_mandi_analysis('Maize', 'Haryana', 7777, 'Ambala')
    assert override.selected_price_quintal == 7777
    assert override.historical_median == result.historical_median
    assert override.is_user_override

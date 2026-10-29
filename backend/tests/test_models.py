import pytest
from app.services.model_service import model_service

def test_crop_suitability_pipeline_loaded():
    assert model_service.crop_pipeline is not None
    assert len(model_service.crop_pipeline.classes_) == 27
    assert "rice" in model_service.crop_pipeline.classes_
    assert "maize" in model_service.crop_pipeline.classes_

def test_crop_suitability_prediction_known_sample():
    # Standard rice profile
    res = model_service.predict_crop_suitability(
        N=90.0, P=42.0, K=43.0,
        temperature=20.9, humidity=82.0,
        ph=6.5, rainfall=202.0
    )
    assert res.recommended_crop == "rice"
    assert res.probability_supported is False
    assert len(res.candidate_ranking) > 0
    assert res.candidate_ranking[0].crop == "rice"
    assert res.candidate_ranking[0].is_top_choice is True

def test_yield_random_forest_pipeline_loaded():
    assert model_service.yield_pipeline is not None
    # The full cleaned 1997-2019 dataset includes the post-2015 district split.
    assert "AMBALA" in model_service.supported_districts
    assert "SHAHID BHAGAT SINGH NAGAR" in model_service.supported_districts
    assert "Rice" in model_service.supported_crops
    assert "Wheat" in model_service.supported_crops

def test_yield_prediction_supported_sample():
    res = model_service.predict_yield(
        state="Haryana",
        district="Ambala",
        crop="Rice",
        season="Kharif",
        year=2024,
        area=5.0
    )
    assert res.is_supported_crop is True
    assert res.is_supported_district is True
    assert res.predicted_yield_tonnes_per_ha > 0
    # Estimated production: yield * area
    assert abs(res.estimated_production_tonnes - (res.predicted_yield_tonnes_per_ha * 5.0)) < 0.05
    # Conversion: 1 tonne = 10 quintals
    assert abs(res.estimated_production_quintals - (res.estimated_production_tonnes * 10.0)) < 0.05

def test_yield_prediction_unsupported_crop_fallback():
    # Crop outside Haryana/Punjab training set
    res = model_service.predict_yield(
        state="Haryana",
        district="Ambala",
        crop="Exotic Dragonfruit",
        season="Kharif",
        year=2024,
        area=2.0
    )
    assert res.is_supported_crop is False
    assert res.predicted_yield_tonnes_per_ha > 0
    assert res.validation_message is not None

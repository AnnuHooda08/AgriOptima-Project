import logging
import warnings
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from app.core.config import CROP_SUITABILITY_MODEL_PATH, YIELD_RANDOM_FOREST_MODEL_PATH
from app.schemas.crop import CandidateCrop, CropRecommendationResponse
from app.schemas.yield_pred import YieldPredictionResponse

logger = logging.getLogger(__name__)

# Bridge mapping from Suitability Model crop names (lowercase/mixed) to Yield Model crop names
SUITABILITY_TO_YIELD_MAP: Dict[str, str] = {
    "rice": "Rice",
    "maize": "Maize",
    "cotton": "Cotton(lint)",
    "chickpea": "Gram",
    "blackgram": "Urad",
    "mungbean": "Moong(Green Gram)",
    "pigeonpeas": "Arhar/Tur",
    "lentil": "Masoor",
    "groundnuts": "Groundnut",
    "Soyabeans": "Soyabean",
    "peas": "Peas & beans (Pulses)",
    "mothbeans": "Moth",
    "wheat": "Wheat",
    "bajra": "Bajra",
    "barley": "Barley",
    "sugarcane": "Sugarcane",
    "sunflower": "Sunflower",
    "onion": "Onion",
    "potato": "Potato",
}

class ModelService:
    def __init__(self):
        self.crop_pipeline = None
        self.yield_pipeline = None
        self.supported_districts: List[str] = []
        self.supported_crops: List[str] = []
        self.supported_states: List[str] = []
        self.supported_seasons: List[str] = []
        self._load_models()

    def _load_models(self):
        """Loads saved ML pipelines and extracts category vocabularies."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # 1. Crop Suitability Model (SVM)
            if Path(CROP_SUITABILITY_MODEL_PATH).exists():
                self.crop_pipeline = joblib.load(CROP_SUITABILITY_MODEL_PATH)
                logger.info(
                    f"Loaded Crop Suitability Pipeline from {CROP_SUITABILITY_MODEL_PATH}"
                )
            else:
                logger.error(f"Crop model not found at {CROP_SUITABILITY_MODEL_PATH}")

            # 2. Crop Yield Model (Random Forest)
            if Path(YIELD_RANDOM_FOREST_MODEL_PATH).exists():
                self.yield_pipeline = joblib.load(YIELD_RANDOM_FOREST_MODEL_PATH)
                logger.info(
                    f"Loaded Yield Random Forest Pipeline from {YIELD_RANDOM_FOREST_MODEL_PATH}"
                )

                # Extract known training categories from OneHotEncoder inside ColumnTransformer
                try:
                    preproc = self.yield_pipeline.named_steps["preprocessor"]
                    encoder = preproc.named_transformers_["categorical"].named_steps[
                        "encoder"
                    ]
                    cats = encoder.categories_
                    self.supported_states = list(cats[0])
                    self.supported_districts = list(cats[1])
                    self.supported_crops = list(cats[2])
                    self.supported_seasons = list(cats[3])
                except Exception as e:
                    logger.warning(f"Could not extract yield categories: {e}")
            else:
                logger.error(
                    f"Yield model not found at {YIELD_RANDOM_FOREST_MODEL_PATH}"
                )

    def predict_crop_suitability(
        self,
        N: float,
        P: float,
        K: float,
        temperature: float,
        humidity: float,
        ph: float,
        rainfall: float,
    ) -> CropRecommendationResponse:
        """
        Runs the saved SVM pipeline.
        Matches exact training columns: ['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']
        Note: Model has probability=False; uses decision_function for ranking alternatives.
        """
        if self.crop_pipeline is None:
            raise RuntimeError("Crop suitability model is not loaded.")

        input_df = pd.DataFrame(
            [[N, P, K, temperature, humidity, ph, rainfall]],
            columns=["N", "P", "K", "temperature", "humidity", "ph", "rainfall"],
        )

        # Predict primary crop
        pred = self.crop_pipeline.predict(input_df)[0]

        # Use decision_function to score candidates
        classes = self.crop_pipeline.classes_
        decision_scores = self.crop_pipeline.decision_function(input_df)[0]

        # Order candidates by decision boundary distance
        ranked_indices = np.argsort(decision_scores)[::-1]

        candidates = []
        for rank, idx in enumerate(ranked_indices):  # Full ranking lets planning filter unsupported crops
            candidates.append(
                CandidateCrop(
                    crop=str(classes[idx]),
                    decision_score=round(float(decision_scores[idx]), 3),
                    is_top_choice=(rank == 0),
                )
            )

        primary_score = float(decision_scores[ranked_indices[0]])

        return CropRecommendationResponse(
            recommended_crop=str(pred),
            decision_boundary_score=round(primary_score, 3),
            probability_supported=False,
            evaluation_note="SVM pipeline trained with probability=False. Historical test accuracy ~79.87%. Secondary rankings represent decision boundary margin heuristics, not calibrated probabilities.",
            candidate_ranking=candidates,
            input_features={
                "N": N,
                "P": P,
                "K": K,
                "temperature": temperature,
                "humidity": humidity,
                "ph": ph,
                "rainfall": rainfall,
            },
        )

    def predict_yield(
        self, state: str, district: str, crop: str, season: str, year: int, area: float
    ) -> YieldPredictionResponse:
        """
        Runs the saved Random Forest pipeline.
        Features match: State, District, Crop, Season (Categorical), YearStart, Area (Numerical).
        Yield target is in tonnes per hectare.
        """
        if self.yield_pipeline is None:
            raise RuntimeError("Yield model pipeline is not loaded.")

        # Normalization
        norm_state = state.strip().title()
        norm_district = district.strip().upper()
        norm_season = season.strip().title()
        norm_crop = crop.strip()

        # Check support
        is_supported_crop = norm_crop in self.supported_crops
        is_supported_district = norm_district in self.supported_districts

        # Build DataFrame with exact expected feature names
        input_df = pd.DataFrame(
            [
                {
                    "State": norm_state,
                    "District": norm_district,
                    "Crop": norm_crop,
                    "Season": norm_season,
                    "YearStart": year,
                    "Area": float(area),
                }
            ]
        )

        validation_message = None
        predicted_yield = 0.0

        # Unsupported inputs should not receive an invented yield.
        if not is_supported_crop or not is_supported_district or norm_state not in self.supported_states or norm_season not in self.supported_seasons:
            raise ValueError('Choose a state, district, crop and season covered by the yield model.')
        prediction = float(self.yield_pipeline.predict(input_df)[0])
        if not np.isfinite(prediction):
            raise ValueError('The yield model could not produce a valid estimate.')
        predicted_yield = round(max(0.0, prediction), 2)

        # Calculations
        est_production_tonnes = round(predicted_yield * area, 2)
        est_production_quintals = round(est_production_tonnes * 10.0, 2)

        return YieldPredictionResponse(
            state=norm_state,
            district=norm_district,
            crop=norm_crop,
            season=norm_season,
            year=year,
            area_ha=area,
            predicted_yield_tonnes_per_ha=predicted_yield,
            estimated_production_tonnes=est_production_tonnes,
            estimated_production_quintals=est_production_quintals,
            model_name="Random Forest Regressor (200 trees, max_depth=15)",
            evaluation_rationale="Selected for lowest recorded MAE of 2.10 t/ha (outperforming Linear Regression MAE 3.04 and Decision Tree MAE 2.99) to minimize absolute forecasting error for farmers.",
            is_supported_crop=is_supported_crop,
            is_supported_district=is_supported_district,
            validation_message=validation_message,
        )


# Global singleton instance
model_service = ModelService()

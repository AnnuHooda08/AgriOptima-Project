"""Saved study-value model. Reject inputs the fitted encoder has never seen."""
from functools import lru_cache
import joblib
import pandas as pd
import numpy as np
from app.core.config import BASE_DIR

LOSS_ALIASES = {"Rice": "Paddy", "Gram": "Chickpea", "Arhar/Tur": "Pigeon Pea",
    "Moong(Green Gram)": "Green gram", "Urad": "Black gram", "Cotton(lint)": "Cottonseed",
    "Rapeseed &Mustard": "Mustard", "Soyabean": "Soybean", "Peas & beans (Pulses)": "Green Pea"}

@lru_cache(maxsize=1)
def loss_bundle():
    return joblib.load(BASE_DIR / "backend/saved_models/post_harvest_loss.joblib")


def model_loss(crop, state):
    bundle = loss_bundle()
    model = bundle["model"]
    row = pd.DataFrame([[state, LOSS_ALIASES.get(crop, crop), "Total", "Overall total loss"]], columns=bundle["features"])
    encoder = model.named_steps["preprocessor"].named_transformers_["categories"].named_steps["encoder"]
    for name, known in zip(bundle["features"], encoder.categories_):
        matches = [value for value in known if str(value).casefold() == str(row.loc[0, name]).casefold()]
        if not matches:
            return None
        row.loc[0, name] = matches[0]
    value = float(model.predict(row)[0])
    return round(value, 3) if np.isfinite(value) and 0 <= value <= 100 else None

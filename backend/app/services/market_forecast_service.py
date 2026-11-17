"""Predict commodity prices from the saved multi-commodity model and monthly history."""
from functools import lru_cache
import joblib
import pandas as pd
from app.core.config import BASE_DIR

@lru_cache(maxsize=1)
def market_data():
    bundle = joblib.load(BASE_DIR/'backend/saved_models/market_prices.joblib')
    data = pd.read_csv(BASE_DIR/'results/mandi_prices/monthly_crop_prices.csv',parse_dates=['date'])
    return bundle, data

@lru_cache(maxsize=1)
def market_options():
    bundle, data = market_data()
    complete = data.dropna(subset=bundle['features'])
    excluded={'Bull','Butter','Calf','Cock','Cow','Duck','Egg','Fish','Ghee','Goat','He Buffalo','Hen','Khoya','Ox','Pigs','Ram','She Buffalo','She Goat','Sheep','Skin And Hide'}
    counts = data[data.state.isin(['Haryana','Punjab'])].dropna(subset=['price']).groupby(['crop','state']).size().unstack(fill_value=0)
    both = counts[(counts.get('Haryana',0) >= 30) & (counts.get('Punjab',0) >= 30)]
    trained = set(complete.crop)
    return {crop:['Haryana','Punjab'] for crop in sorted(both.index) if crop not in excluded and crop in trained}

def predict_market(crop,state):
    bundle,data = market_data()
    if crop not in market_options():
        raise ValueError("This crop has insufficient model-ready training history.")
    rows = data[(data.crop == crop) & (data.state == state)].sort_values('date')
    if rows.empty: raise ValueError('No recorded history for this crop and region.')
    row = rows.tail(1).copy()
    # Only prices observed before the forecast month enter this estimate.
    # Gaps in a lag use the region's recent observed median, never a fixed rate.
    recent = rows.loc[rows.date.lt(row.date.iloc[0]), 'price'].dropna().tail(12)
    if recent.empty:
        raise ValueError('No usable recorded price history for this region.')
    missing = False
    for feature in bundle['features']:
        if feature.startswith('lag_') and row[feature].isna().any():
            row.loc[:,feature] = float(recent.median())
            missing = True
    value = float(bundle['model'].predict(row[bundle['features']])[0])
    return {'crop':crop,'state':state,'predicted_price':round(value,2),
            'unit':'Rs per quintal','scope':'Next month after the available recorded history',
            'history':[{'price':round(float(v),2)} for v in rows.price.dropna().tail(12)],
            'source':'Model trained on recorded AGMARKNET commodity reports. This is a historical forecast, not a live quote.' + (' Missing past months use the recent regional price pattern.' if missing else '')}

# AgriOptima ML models

Each model folder contains commented preprocessing, training, evaluation, inference, tests, documentation, clean intermediate data, measured reports, and its saved artifact. The source datasets remain in DataSets/.

| Model | Cleaning and validation | Current measured result |
|---|---|---|
| Crop suitability | 3,130 clean rows, 27 labels | 626-row stratified holdout: accuracy 79.87%, weighted F1 78.66% |
| Crop yield | 9,882 of 12,447 raw rows pass documented checks | 2015–2019 holdout (2,712 rows): MAE 2.0995 t/ha, RMSE 9.2745, R² 0.7723; median baseline MAE 8.4960 |
| Soil clustering | 5,000 random records sampled per each of six depth layers | Coordinate-group holdout silhouette 0.3910; selected k=2 |
| Soil anomaly detection | Same 30,000 balanced soil sample | 160 of 6,000 held-out rows flagged (2.67%); no ground-truth labels exist |
| Mandi maize price | 1,077,217 raw rows reduced to 265 valid monthly records; missing months are not filled | 14-month test: persistence MAE 49.214, seasonal MAE 122.893, HGB MAE 306.140 Rs/quintal |
| Post-harvest loss | 1,865 valid 2022 records | Group holdout (490 rows): RF MAE 0.3612 percentage points vs median baseline 0.9937 |

Mandi HGB is experimental and loses to persistence. Soil anomaly flags are review candidates, not confirmed errors. Post-harvest has only one year of target data, so its better single split is not independent validation. Clusters are descriptive groups, not agronomic advice.

Install with python -m pip install -r requirements.txt. For each model, run its preprocessing script, then evaluation, then training, then inference; the individual README files include exact commands and interpretation. Run all automated checks with python -m pytest models/*/tests backend/tests.

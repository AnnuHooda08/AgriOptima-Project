# Crop yield

**Task:** estimate tonnes per hectare from state, district, crop, season, year, and area using a Random Forest regression pipeline.

Preprocessing reads the preserved raw CSV at DataSets/Yeild/crop_production_haryana_punjab_1997_2019.csv. It removes duplicate rows, parses year labels, validates area/yield values and measurement units, writes an exclusion audit, and keeps 9,882 of 12,447 rows. Evaluation holds out every year from 2015 through 2019: Random Forest MAE 2.0995 t/ha, RMSE 9.2745, R² 0.7723, versus training-median baseline MAE 8.4960. Training refits the inference artifact on all 9,882 clean rows.

Run from repository root:
- python models/crop_yield/preprocessing/prepare_data.py
- python models/crop_yield/evaluation/evaluate.py
- python models/crop_yield/training/train.py
- python models/crop_yield/inference/predict.py
- python -m pytest models/crop_yield/tests backend/tests

Older diagnostic reports remain under reports/legacy. The API reads the maintained artifact from this folder.

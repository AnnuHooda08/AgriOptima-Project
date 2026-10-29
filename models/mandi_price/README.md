# Mandi price

**Task:** experimental forecast of monthly median maize modal price (Rs/quintal) from a national aggregate series. The 1,077,217 raw market rows yield 265 valid monthly model rows after date/price validation and calendar-lag construction. Missing months are left missing; a lag always means the actual prior calendar month.

Evaluation trains before 2021 and tests 14 observed months from 2023 onward. MAE: previous-calendar-month baseline 49.214; same-month-last-year baseline 122.893; HistGradientBoosting 306.140. The learned model loses badly, so the artifact is for comparison only. Prefer the persistence baseline on this dataset, and do not present it as reliable market advice.

Run from repository root:
- python models/mandi_price/preprocessing/prepare_data.py
- python models/mandi_price/evaluation/evaluate.py
- python models/mandi_price/training/train.py
- python models/mandi_price/inference/predict.py
- python -m pytest models/mandi_price/tests

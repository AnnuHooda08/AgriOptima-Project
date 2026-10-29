# Soil anomaly screening

**Task:** use Isolation Forest to flag unusual SoilGrids rows for human review. The feature set includes soil properties and depth, while coordinates are reserved for making an independent spatial holdout.

Preprocessing samples 5,000 valid records from each of six depth layers (30,000 total). Evaluation fits only on 24,000 training rows and scores 6,000 rows from held-out locations. It flagged 160 rows (2.67%). The dataset has no verified anomaly labels, so precision, recall, and accuracy cannot be calculated. A flag is not proof that a measurement is wrong.

Run from repository root:
- python models/anomaly_detection/preprocessing/prepare_data.py
- python models/anomaly_detection/evaluation/evaluate.py
- python models/anomaly_detection/training/train.py
- python models/anomaly_detection/inference/predict.py
- python -m pytest models/anomaly_detection/tests

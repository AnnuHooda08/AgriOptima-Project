# Soil clustering

**Task:** group soil profiles with K-means. The model uses soil properties plus depth, scales units through its saved pipeline, and does not use latitude/longitude as cluster features.

Preprocessing samples 5,000 valid rows from each of six SoilGrids depth files (30,000 total), using a fixed random seed. Evaluation holds out whole coordinate locations, chooses k on training locations using silhouette score, and reports holdout silhouette 0.3910; k=2 was selected. Silhouette measures geometric separation only; it cannot tell us whether clusters are agronomically useful.

Run from repository root:
- python models/clustering/preprocessing/prepare_data.py
- python models/clustering/evaluation/evaluate.py
- python models/clustering/training/train.py
- python models/clustering/inference/predict.py
- python -m pytest models/clustering/tests

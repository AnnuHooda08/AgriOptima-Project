# Crop suitability

**Task:** classify one of 27 crop labels from N/P/K, temperature, humidity, pH, and rainfall using a scaled RBF SVC.

Preprocessing reads the preserved DataSets/crop_suitability.csv, converts measurements to numeric, removes invalid and duplicate rows, and writes a clean model-local copy. It kept all 3,130 rows. Evaluation uses a fixed stratified 80/20 split (seed 42): accuracy 79.87%, weighted F1 78.66%, on 626 held-out rows. Training refits the selected pipeline on all 3,130 clean rows for inference. The saved pipeline includes its scaler.

From the repository root run:
- python models/crop_suitability/preprocessing/prepare_data.py
- python models/crop_suitability/evaluation/evaluate.py
- python models/crop_suitability/training/train.py
- python models/crop_suitability/inference/predict.py
- python -m pytest models/crop_suitability/tests

The distinct earlier suitability CSV and exploratory notebooks are retained under this model’s data/raw and notebooks folders. Predictions come from historical data and are not agronomic guarantees.

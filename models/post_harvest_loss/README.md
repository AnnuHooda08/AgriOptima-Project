# Post-harvest loss

**Task:** estimate loss percentage from state, crop, loss type, and stage using a categorical Random Forest. The source table contains one year (2022); all 1,865 records passed cleaning.

Evaluation holds out complete state/crop groups (1,375 training rows, 490 test rows, 35 held-out groups). Random Forest MAE was 0.3612 percentage points and RMSE 0.6097; the training-median baseline MAE was 0.9937. This is one grouped split, not year-forward validation. Keep the existing deterministic lookup as the operational fallback until independent years or measurements confirm the result.

Run from repository root:
- python models/post_harvest_loss/preprocessing/prepare_data.py
- python models/post_harvest_loss/evaluation/evaluate.py
- python models/post_harvest_loss/training/train.py
- python models/post_harvest_loss/inference/predict.py
- python -m pytest models/post_harvest_loss/tests

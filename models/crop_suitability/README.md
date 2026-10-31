# Crop Suitability Classification

This module predicts one of 27 crop labels from seven numeric inputs: N, P, K,
temperature, humidity, pH, and rainfall. It is a dataset-label classifier, not a
verified agronomic decision system. The source file does not identify farms,
locations, seasons, sampling methods, or the meaning and units of each record.

## Current model and review state

- Production remains the existing scaled RBF SVM at
  `artifacts/crop_suitability_pipeline.pkl`. It was not changed in this audit.
- A grouped validation comparison selected Random Forest as the best candidate
  by validation macro F1. It is saved separately as
  `artifacts/crop_suitability_grouped_split_challenger_040c3feeea2b.joblib` for review.
- Do not promote the challenger until its limitations and class-level results,
  especially chickpea recall, have been reviewed.
- The SVM does not provide calibrated crop probabilities. Backend decision
  scores are margin-based ranking hints, not probabilities.

## Reproduce the audit

From the repository root, using the project environment:

```bash
MPLCONFIGDIR=/private/tmp/agrioptima-mpl-cache ./.venv/bin/python models/crop_suitability/evaluation/audit_and_benchmark.py
MPLCONFIGDIR=/private/tmp/agrioptima-mpl-cache ./.venv/bin/python -m pytest -q models/crop_suitability/tests
PYTHONPATH=backend MPLCONFIGDIR=/private/tmp/agrioptima-mpl-cache ./.venv/bin/python -m pytest -q backend/tests/test_models.py -k crop_suitability
PYTHONPATH=backend MPLCONFIGDIR=/private/tmp/agrioptima-mpl-cache ./.venv/bin/python -m pytest -q backend/tests/test_api_endpoints.py -k crop_recommendation
```

The audit script reads `DataSets/crop_suitability.csv`, writes reports and plots
under `evaluation/data_audit/`, compares five baseline classifiers, then checks
the validation-selected candidate and a refitted SVM reference on one untouched
grouped test set. The test results do not select or tune the model. An existing
challenger artifact is preserved rather than overwritten.

## Module map

- `preprocessing/prepare_data.py`: validates and writes a cleaned model-local
  copy; it never writes to the source dataset.
- `preprocessing/feature_validation.py`: checks single and batch inference
  values and fixes feature order.
- `training/train.py`: refits the SVM on all cleaned rows and writes the
  production artifact. Do not run it when the artifact must remain unchanged.
- `evaluation/evaluate.py`: historical random 80/20 evaluation. Its old score is
  retained for reference, but it does not group repeated feature profiles.
- `evaluation/audit_and_benchmark.py`: current data audit and grouped comparison.
- `inference/predict.py`: validates input and sends it to the saved pipeline.
- `tests/test_crop_suitability.py`: preprocessing and inference checks.
- `evaluation/reports/`: dataset, EDA, comparison, intended-use, and final
  evaluation notes.
- `evaluation/data_audit/`: generated CSV/JSON evidence and visualizations.
- `data/raw/` and `notebooks/`: preserved historical copies and experiments.
  They are not authoritative data sources for current training.

## Reports

- [Dataset audit](evaluation/reports/dataset_audit_report.md)
- [Exploratory data analysis](evaluation/reports/eda_report.md)
- [Model comparison](evaluation/reports/model_comparison_report.md)
- [Final evaluation](evaluation/reports/final_evaluation_report.md)
- [Intended use and limitations](evaluation/reports/intended_use.md)
- [Data dictionary](evaluation/reports/data_dictionary.md)

No dataset, production artifact, existing experiment, backend file, or frontend
file was deleted or moved during this review.

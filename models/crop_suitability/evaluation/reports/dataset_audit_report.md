# Crop Suitability Dataset Audit

## Verified source-file facts

The source used by the module is `DataSets/crop_suitability.csv`. It has 3,130
rows, seven numeric inputs, and one target (`label`), with 27 labels. All 3,130
rows have finite numeric inputs and a non-empty label. There are no missing
values, exact duplicate rows, or records outside the deliberately broad physical
screening ranges used in this audit. The source dataset was read only; no source
rows were removed or edited.

The category counts run from 100 (`beans`, `chickpea`, `peas`, and other labels)
to 176 (`rice`), a largest-to-smallest ratio of 1.76. This is imbalance, but not
the severe long-tail distribution often seen in operational data. Labels are
case-sensitive in the file: `Soyabeans` is capitalized while most other labels
are lowercase. The audit preserves that label instead of silently renaming it.

## Repeated and conflicting observations

There are 2,776 distinct seven-feature profiles. Another 354 rows repeat a
feature profile already present. Every one of those 354 repeated profiles has a
different crop label attached to the same seven measurements, affecting 708
rows. This is not an exact duplicated row; it is a contradictory target for an
identical input. A classifier cannot distinguish those labels from the
available inputs.

We also screened near profiles by dividing each feature by its fixed broad
input-range width and connecting profiles at Euclidean distance at most 0.005.
This descriptive rule
found 896 close pairs, including 530 pairs with different labels. The connected
components contain 2,264 groups; 836 groups contain more than one row, 500 of
those contain conflicting labels, and the largest has three rows. This
threshold is an explicit sensitivity rule, not a claim that nearby records are
the same farm or measurement event. It is used conservatively to keep similar
profiles together during model evaluation.

Detailed evidence is saved in:

- `../data_audit/dataset_audit_summary.json`
- `../data_audit/crop_class_counts.csv`
- `../data_audit/repeated_feature_profiles.csv`
- `../data_audit/conflicting_feature_profiles.csv`
- `../data_audit/near_feature_profile_pairs.csv`
- `../data_audit/suspicious_and_outlier_screen.csv`

## Plausibility and source limitations

The broad screening ranges were N/P/K 0–300, temperature −10–60, relative
humidity 0–100, pH 0–14, and rainfall 0–2,000. No row fell outside them. The
IQR screen flags 550 rows as statistically unusual in at least one feature; an
IQR flag is not evidence of an error, and none were removed. N, P, and K units
are not stated in the CSV itself. The backend request schema describes them as
kg/ha, temperature as °C, humidity as percent, and rainfall as mm; that is an
application contract, not verified source metadata.

No source URL, collection date, farm/district identifier, sampling procedure,
label-generation rule, license, or record-level provenance is included with the
CSV or model module. The project overview makes a general ICAR/agricultural
survey statement, but it supplies no citation that establishes the origin of
this exact file. The schema resembles the familiar public Crop Recommendation
benchmark: published descriptions identify a Kaggle dataset with 2,200 rows,
22 crops, and the same seven inputs, and describe it as compiled/augmented from
other data sources ([Sensors paper](https://www.mdpi.com/1424-8220/22/16/6299),
[Kaggle dataset](https://www.kaggle.com/datasets/atharvaingle/crop-recommendation-dataset)).
The repository file has 3,130 rows and 27 classes, so this resemblance does not
prove that it is the same source or that its labels represent field outcomes.
The exact file provenance remains unverified.

The processed model-local CSV and the preserved legacy CSV contain the same
records and values as the source, although the source uses a different text
format. Both copies were preserved. No raw or legacy data file was moved,
renamed, duplicated, or deleted by this audit.

## Existing artifact compatibility

The existing production pickle loads under the project virtual environment
(scikit-learn 1.9.1), contains a `StandardScaler` followed by an SVC, accepts
the seven fields in the configured order, and predicted `rice` for the first
source row in a direct compatibility check. Its 27 model classes match the
dataset's 27 target labels. The scaler is part of the pipeline, so inputs must
not be scaled a second time.

`config.py` records scikit-learn 1.7.2, while loading the artifact under that
system version emitted a warning that its estimators were serialized with
1.9.1. The project `.venv` uses 1.9.1 and loads the artifact successfully. Keep
training and inference package versions aligned and update the version metadata
when the artifact is next intentionally retrained.

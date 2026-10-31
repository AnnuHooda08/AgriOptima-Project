# Crop Suitability: Intended Use and Limitations

## What the current data supports

The dataset supports a reproducible exercise in classifying one of 27 labels
from seven numeric columns. With the grouped holdout, the selected Random Forest
candidate scored 0.8357 accuracy and 0.8016 macro F1. This is evidence of
performance on held-out rows from this same file under its label conventions.
It is not independent field validation.

The current module can be described as a **historical/curated dataset-label
classifier**. “Historical” here means the model is fit to an existing table; the
table itself has no dates, so it cannot estimate yield or crop conditions in a
particular year.

## What it does not establish

- **Farm-specific suitability:** unsupported. No farm identifier, location,
  measured soil context, irrigation, management, crop variety, or farm outcome
  is present.
- **District or regional recommendations:** unsupported. There are no state,
  district, or coordinates.
- **Crop-season recommendations:** unsupported. There is no planting season,
  sowing date, or local growing window.
- **Yield, profit, fertilizer dose, or guaranteed outcome:** outside the
  classifier's target and not derivable from these labels.
- **Real-world probability of success:** unsupported. The SVM has no calibrated
  probabilities; its margin scores are ranking hints. Any RF probability is
  also uncalibrated and tied to this dataset's labels.

The input fields omit additional soil properties, soil depth and texture,
irrigation/water availability, locally resolved climate and forecasts, season,
planting calendar, pests, crop variety, management practices, and economics.
Recommendation quality cannot be established without those contexts and
independent, well-documented field outcomes.

## Reliability and user-facing behavior

The same seven measured values occur with different crop labels 354 times.
Chickpea recall is 0.10 for the Random Forest challenger and 0.00 for the SVM
reference on the grouped test. A single top label can therefore be wrong even
for data that looks like this file. The application should identify the result
as an experimental dataset-based suggestion, avoid certainty language, and
allow users to consult qualified local agronomy guidance. Do not show decision
scores or uncalibrated class scores with a percent sign.

Input validation rejects missing, non-numeric, and broad-range-invalid values,
but it currently accepts some values well outside the observed data range.
Until an out-of-distribution policy is agreed, applications should not imply
that such inputs are supported.

The false-positive cost (recommending a crop that is not suitable) and the
false-negative cost (failing to suggest a suitable crop) cannot be compared
from this dataset: it contains crop labels but no crop outcome or cost. The
current macro metrics treat every crop equally; weighted metrics reflect row
counts. Neither one encodes agronomic consequences.

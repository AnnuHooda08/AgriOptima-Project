# Mandi Price Prediction — Linear Regression

## What this model estimates

This beginner-friendly example predicts the **next month's national median maize modal price**, in rupees per quintal. It combines market reports from many mandis into one monthly number. It is not a quote for a particular state, market, variety, or farmer, and it does not guarantee a future selling price.

The raw market collection is stored as one CSV per commodity under `DataSets/india_mandi_prices_2000_2024/`. The existing module focuses on the available maize file, `Maize.csv`, and retains an older HistGradientBoosting experiment separately for comparison.

## Source and dataset

Project documentation attributes the market files to AGMARKNET and the Directorate of Marketing & Inspection (DMI). The Government of India's [OGD catalog for daily mandi prices](https://www.data.gov.in/catalog/current-daily-price-various-commodities-various-markets-mandi) says the dataset is generated through AGMARKNET and includes daily wholesale minimum, maximum, and modal prices. In this maize file, the column names state prices in **Rs/quintal** and arrivals in **tonnes**.

The folder has 325 CSV entries: 306 contain data, 9 are Git LFS pointer files without the underlying data in this checkout, and 10 are empty placeholders. The available files contain about 38.1 million market records in total. Some commodity files do not state the price unit in their column names, so the all-commodity inventory records that uncertainty instead of assuming a unit.

The maize file has 1,077,217 rows covering 30 states, 428 districts, 1,640 markets and 34 varieties from 10 January 2001 through 2 February 2024. Prices and arrivals are reported at market level. The modal price is used as the target because it is the market's reported representative price for the day; the model aggregates those values to a monthly national median.

Detailed findings, file-by-file inventory and plots are in [`evaluation/reports/linear_regression/`](evaluation/reports/linear_regression/). The raw data is never edited.

## Data cleaning and features

1. Parse each reported date and modal price. Missing or non-numeric prices and zero/negative prices cannot provide a meaningful price target, so those records are written to a rejection log with reasons.
2. Remove exact repeated rows from the derived modeling input only. Every extra copy is saved in the rejection log; the raw CSV remains unchanged. Rows with the same market/date/variety but different values are flagged for review and are not silently merged.
3. Take the median of the valid market-reported modal prices for each calendar month. This gives each source record one vote; it is not weighted by arrivals.
4. Create lag features for the exact previous 1, 2, 3, and 12 calendar months. Missing calendar months remain missing, so the model never treats an older available month as if it were the previous month.
5. Use the calendar year as a simple trend and one-hot encode month as a season category. A scikit-learn `Pipeline` fits the imputer and encoder only on the training rows.

State, district, market and variety are not features because the target is a national aggregate rather than a mandi-specific price. Same-month arrivals and minimum/maximum prices are excluded: they are reported with the target and would not be known before the month being predicted. The lag prices are available for a **rolling one-month-ahead** estimate; predicting several months ahead would require forecasts for the missing future lags.

## Linear Regression in plain language

Linear Regression learns a weighted sum of its inputs. In this model the estimate is:

`price = intercept + (lag_1 × weight_1) + (lag_2 × weight_2) + (lag_3 × weight_3) + (lag_12 × weight_12) + (year × year_weight) + month_adjustment`

The training algorithm chooses the weights that minimize the squared differences between its predictions and the known training prices. Month is encoded as categories, so the model can learn a seasonal adjustment without pretending that December is numerically close to January. A positive or negative coefficient describes the direction of a feature's relationship in this fitted equation; it is not proof that the feature causes prices to move.

## Evaluation method and actual result

Rows are sorted by date, never shuffled:

- Training for the first validation check: 2002–2019 (215 monthly rows).
- Validation: 2020–2022 (36 rows).
- Final test: January 2023–February 2024 (14 rows). This period is not used to fit or preprocess the model.
- The final saved model is fitted on all pre-test months (251 rows), after evaluation settings are fixed.

Validation results (Rs/quintal):

| Method | MAE | RMSE | R² |
|---|---:|---:|---:|
| Linear Regression | 51.86 | 62.87 | 0.956 |
| Previous-month price | 64.67 | 83.65 | 0.923 |
| Same month last year | 431.78 | 463.94 | -1.376 |

Final test results (Rs/quintal):

| Method | MAE | RMSE | R² |
|---|---:|---:|---:|
| Linear Regression | 58.84 | 70.57 | 0.411 |
| Previous-month price | 49.21 | 71.32 | 0.398 |
| Same month last year | 122.89 | 160.30 | -2.039 |

The test result is mixed. Linear Regression has a slightly lower RMSE and slightly higher R² than the previous-month baseline, but its MAE is about ₹9.63/quintal higher. The previous-month estimate has the lower typical absolute error in this small test period. Therefore, the evidence does **not** show that Linear Regression is consistently better than the simple baseline. The test has only 14 months, so these results are uncertain.

MAE is the average absolute size of an error, in rupees per quintal. RMSE uses squared errors and penalizes a few large misses more. R² compares the prediction error with a constant average-price estimate; a negative value means it performed worse than that reference. The saved predictions, residual plot, actual-vs-predicted plot and error tables are in the evaluation report folder.

## Run it

Run commands from the repository root:

```bash
python models/mandi_price/evaluation/audit_dataset.py
python models/mandi_price/preprocessing/prepare_linear_data.py
python models/mandi_price/evaluation/evaluate_linear.py
python models/mandi_price/training/train_linear.py
python models/mandi_price/inference/predict_linear.py
python -m pytest models/mandi_price/tests
```

The first command scans the 3.17 GB commodity folder in chunks and can take a few minutes. It writes inventory and EDA outputs in the report folder. The other commands use only the maize file and the new Linear Regression paths. Existing HistGradientBoosting files and reports remain available.

## Example prediction

After training, call the inference function with the target month/year and the actual observed monthly national median maize prices from the required prior calendar months:

```python
from models.mandi_price.inference.predict_linear import predict

estimate = predict(
    lags={"lag_1": 2090, "lag_2": 2090, "lag_3": 1980, "lag_12": 2100},
    month=1,
    year=2024,
)
print(f"Estimated price: ₹{estimate:.2f} per quintal")
```

The function validates the inputs and loads the saved scikit-learn pipeline. These example values are illustrative, not a recommendation or guaranteed market price.

## Main files

- `preprocessing/prepare_linear_data.py`: cleaning, duplicate log, monthly target and exact calendar lags.
- `training/train_linear.py`: Linear Regression pipeline and saved artifact.
- `evaluation/audit_dataset.py`: collection inventory and maize exploratory analysis.
- `evaluation/evaluate_linear.py`: chronological validation/test metrics, baselines, plots and error tables.
- `inference/predict_linear.py`: validated prediction function.
- `tests/test_linear_mandi_price.py`: preprocessing, artifact and input-validation tests.
- `artifacts/maize_price_linear_regression.joblib`: new Linear Regression model; the older HGB artifact is preserved.

## Limitations

- A national monthly median hides local market, state, variety, grade and quality differences.
- The newest test period is only 14 months and ends in February 2024; later market changes are not evaluated.
- Some source rows have missing/nonpositive prices, repeated records, extreme values and inconsistent minimum/modal/maximum ordering. The audit logs these; it does not prove every remaining price is correct.
- The source is a historical record of reported wholesale market prices, not a forecast of a farmer's realized transaction price.
- Lag-based estimates are only one month ahead when actual previous-month observations are supplied. Multi-month forecasts need another evaluation design.
- Linear Regression is deliberately simple and may not capture sudden policy, weather, supply or demand shocks.

The previous HistGradientBoosting experiment remains in `training/train.py`, `evaluation/evaluate.py`, and `artifacts/maize_price_hgb.joblib`; it is preserved as a historical comparison and is not the main model described here.

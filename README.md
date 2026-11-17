# AgriOptima

Agricultural machine-learning experiments and a React application for crop
suitability, yield, market prices and post-harvest loss.

## Team

| Member | Main component |
| --- | --- |
| [Abhinav Sharma](https://github.com/abhinav20january-a11y) | Crop suitability classification |
| [Annu](https://github.com/AnnuHooda08) | Crop yield prediction |
| [Ananya Upadhyay](https://github.com/uananya2502) | Mandi and market price forecasting |
| [Aditya Narayan](https://github.com/darksoul2406) | Post-harvest loss estimation |

## Project structure

- `models/`: complete ML notebooks with data preparation, training and evaluation.
- `DataSets/`: input datasets and source attribution.
- `results/`: machine-readable evaluation outputs and model plots.
- `backend/`: FastAPI application, required application model bundles and API tests.
- `frontend/`: React and CSS application.

## Machine learning components

| Notebook | Experiment |
| --- | --- |
| `01_crop_suitability.ipynb` | Compare Logistic Regression and RBF SVM for crop labels |
| `02_crop_yield.ipynb` | Compare Linear Regression, Ridge, Decision Tree and Random Forest |
| `03_mandi_price.ipynb` | Predict monthly prices across available commodities |
| `04_post_harvest_loss.ipynb` | Estimate published loss percentages with Random Forest |

Run notebook cells from top to bottom with the project root or `models/` as
the working directory. Research outputs are saved separately and do not
replace the application model bundles automatically.

## Run locally

Install Python dependencies with `python3 -m pip install -r requirements.txt -r requirements-dev.txt`, then run `npm install --prefix frontend`.
Run `./start.sh`. Open http://127.0.0.1:5174 in Chrome or another browser.
Set AGRI_PYTHON to your environment Python path if needed.
The frontend uses same-origin /api requests, proxied to port 8000.

## Data and predictions

The website has four independent prediction screens: crop suitability, yield,
market prices and post-harvest loss. No fixed numerical fallback predictions are used.
The price notebook reads all available commodity CSVs. 295 commodities have
sufficient model-ready monthly history. Regional forecasts use the selected region’s recorded history. Missing lag months
use its recent observed price median, with a source note. A region with no usable
history returns an unavailable response. There are 32 recorded regions plus the
national aggregate in the prepared table. These forecasts concern the next month after recorded
history, not a current market quote.

The chronological test compares Random Forest MAE 822.13 Rs/quintal with
previous-month MAE 683.49 across 69,641 monthly records. The baseline performs
better on this aggregate test. Errors combine commodities with different price scales.
The model is refitted on recorded history after evaluation for application inference.

Loss prediction uses the saved NABCONS study-value model. Unsupported categories
return an error. The yield model also rejects unsupported crops instead of using
fixed regional values. Soil datasets, maize-only extensions and unused source
workbooks are excluded from the current four-component workflow.

## Verification

Run `python3 -m pytest` and `npm run build --prefix frontend`.
Reports, presentations and study materials are excluded from GitHub.

The market selector lists 95 crops with at least 30 observed monthly prices in
each of Haryana and Punjab. Coverage counts are recorded in
`results/mandi_prices/haryana_punjab_coverage.csv`. Broader commodity inputs
remain necessary for reproducing the pooled model training.

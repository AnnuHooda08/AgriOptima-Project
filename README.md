# AgriOptima

Agricultural machine-learning experiments and a React application for crop
planning, yield estimates and market scenarios.

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
- `saved_models/`: research bundles generated locally by the notebooks.
- `results/`: machine-readable evaluation outputs and model plots.
- `backend/`: FastAPI application, required application model bundles and API tests.
- `frontend/`: React and CSS application.

## Machine learning components

| Notebook | Experiment |
| --- | --- |
| `01_crop_suitability.ipynb` | Compare Logistic Regression and RBF SVM for crop labels |
| `02_crop_yield.ipynb` | Compare Linear Regression, Ridge, Decision Tree and Random Forest |
| `03_mandi_price.ipynb` | Forecast next-month national maize median prices |
| `04_post_harvest_loss.ipynb` | Estimate published loss percentages with Random Forest |
| `05_soil_clustering.ipynb` | Group similar soil records with K-means |
| `06_soil_anomalies.ipynb` | Flag unusual soil records with Isolation Forest |

Run notebook cells from top to bottom with the project root or `models/` as
the working directory. Research outputs are saved separately and do not
replace the application model bundles automatically.

## Run locally

Create and activate a Python environment, then run from the project root:

```sh
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m uvicorn app.main:app --app-dir backend --reload
```

In a second terminal:

```sh
cd frontend
npm install
npm run dev
```

The Vite application normally opens at `http://localhost:5173` and proxies
API requests to the local backend. The backend normally runs on port 8000.

Some existing large dataset files use Git LFS. Install Git LFS and run
`git lfs pull` after cloning to download their contents.

## Verification

```sh
python -m pytest
cd frontend
npm run build
```

## Evaluation notes

Classification and yield use separate training, validation and test groups.
Price forecasts use only earlier months, and grouped splits keep related loss
and soil records together. Preprocessing is fitted inside model pipelines.

The extended price experiment reports 2025 MAE of Rs 47.61/quintal versus
Rs 76.67 for repeating the previous month. The baseline performs better during
2023-2024 validation. Incomplete November 2025 reporting is shown in both the
full-year and coverage-screened results. This experiment forecasts a national
maize aggregate, rather than a live quote for each mandi.

Crop labels and yield estimates require local agronomic verification. Published
loss values are study aggregates. Soil anomaly flags request review and do not
prove measurement errors. Notebook evaluation results and the application’s
original pipeline metrics describe different model versions.

Study materials, submission reports and presentation files are not included.

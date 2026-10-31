# AgriOptima — Technical System Documentation

**Connected Machine Learning & Full-Stack Agricultural Decision Support System**

---

## 1. Executive Summary & Project Architecture

AgriOptima is a connected, beginner-friendly agricultural intelligence platform designed to eliminate disjointed predictions and give farmers end-to-end operational clarity. Rather than presenting isolated machine learning predictions across disconnected screens, AgriOptima links every agronomic and economic stage into a single continuous pipeline:

$$\text{Farm Profile} \longrightarrow \text{Crop Suitability (SVM)} \longrightarrow \text{Yield Prediction (RF)} \longrightarrow \text{Production \& Losses} \longrightarrow \text{Market Mandi Economics} \longrightarrow \text{Net Profit P\&L} \longrightarrow \text{What-If Risk Simulation}$$

### Architecture Diagram

```
+----------------------------------------------------------------------------------------------------+
|                                    REACT FRONTEND (Vite Dashboard)                                 |
|  [1. Farm Profile] -> [2. Crop Suitability] -> [3. Yield & Prod] -> [4. Market/Loss] -> [5. Plan]  |
|                                       [6. What-If Scenarios]                                       |
+----------------------------------------------------------------------------------------------------+
                                                 |  HTTP REST JSON
                                                 v
+----------------------------------------------------------------------------------------------------+
|                                    FASTAPI BACKEND (/api)                                          |
|  /health | /weather | /crop-recommendation | /yield-prediction | /mandi-analysis | /plan | /what-if |
+----------------------------------------------------------------------------------------------------+
        |                                   |                                   |
        v                                   v                                   v
+-----------------------+       +-----------------------+       +------------------------------------+
| CROP SUITABILITY (ML) |       |  YIELD PREDICTION(ML) |       |   PLANNING & FINANCIAL ENGINE      |
| Pipeline: SVM (SVC)   |       |  Pipeline: RF Regr.   |       |   Pure Python Deterministic Logic  |
| Inputs: N,P,K,pH,Rain |       |  Inputs: State, Dist, |       |   • 1 Tonne = 10 Quintals          |
| Scaler: Embedded      |       |          Crop, Season,|       |   • CIPHET 2022 Post-Harvest Loss  |
| Accuracy: ~79.87%     |       |          Year, Area   |       |   • Itemized CACP Cultivation Cost |
| Decision Hyperplane   |       |  Target: Tonnes/Ha    |       |   • AGMARKNET Median Mandi Price   |
| Margin Heuristic      |       |  MAE: 2.10 Tonnes/Ha  |       |   • Net Return = Revenue - Costs   |
+-----------------------+       +-----------------------+       +------------------------------------+
                                                                                |
                                                                                v
                                                                +------------------------------------+
                                                                | EXPERIMENTAL MANDI BENCHMARK       |
                                                                | HistGradientBoostingRegressor      |
                                                                | • Naive Lag-1 Baseline: 161.09 Rs. |
                                                                | • HGB Model Test MAE:   389.71 Rs. |
                                                                | • Excluded from production plan    |
                                                                +------------------------------------+
```

---

## 2. Selected Models & Technical Justification

In accordance with strict ML engineering principles, **only one selected model is used per prediction module**, avoiding unnecessary model loading or confusing multi-model exposure.

### Module A: Crop Suitability — Support Vector Machine (SVM)
- **Artifact Path:** `models/crop_suitability/artifacts/crop_suitability_pipeline.pkl`
- **Architecture:** `Pipeline(steps=[('scaler', StandardScaler()), ('svm', SVC(C=1, probability=False))])`
- **Input Features (7):**
  1. `N`: Nitrogen in soil (kg/ha)
  2. `P`: Phosphorus in soil (kg/ha)
  3. `K`: Potassium in soil (kg/ha)
  4. `temperature`: Surface temperature (°C)
  5. `humidity`: Relative air humidity (%)
  6. `ph`: Soil acidity / alkalinity (0–14)
  7. `rainfall`: Annual/seasonal precipitation (mm)
- **Output:** Predicted suitable crop label (27 supported classes).
- **Honest Model Representation:**
  - The pipeline was trained with `probability=False`. The application **does not fabricate pseudo-confidence percentages**.
  - Alternative candidate crops are ranked strictly by their geometric distance from the SVM decision boundary (`decision_function`), labelled transparently as a **hyperplane margin heuristic**, not model confidence.
- **Historical Performance:** Preserved historical test accuracy is **~79.87%**.

---

### Module B: Crop Yield Prediction — Random Forest production artifact; Decision Tree challenger under review
- **Production Artifact:** `models/crop_yield/artifacts/random_forest.joblib` (kept in place pending review).
- **Challenger Artifact:** `models/crop_yield/artifacts/challenger_decision_tree_crop_season.joblib` (validation-selected; not wired into the API).
- **Production inputs:** State, District, Crop, Season, YearStart, and Area (hectares). The selected challenger uses Crop and Season only. Production is excluded to prevent target leakage.
- **Target:** Yield in tonnes per hectare.
- **Current chronological comparison:** `models/crop_yield/evaluation/model_comparison.csv` reports five candidates selected using 2012–2014 validation, then refit on all pre-2015 records and tested on 2015–2019. Crop-season-only Decision Tree led validation MAE (2.5300 t/ha); on the final test its MAE/RMSE/R² were 2.4032/6.2134/0.8978. The existing Random Forest test metrics were 2.0995/9.2745/0.7723. These trade-offs and temporal instability are documented in `models/crop_yield/README.md` and `models/crop_yield/reports/current/academic_evaluation.md`.
- **Review status:** The production artifact has not been replaced. Review the Decision Tree challenger and dataset limitations before promoting it.
- **Preserved Archive:** Prior candidate artifacts/reports remain archived for reproducibility and are not loaded at runtime.
---

### Module C: Mandi Price Forecasting — Experimental HistGradientBoosting Benchmark
- **Dataset:** 1,077,217 raw maize market records, aggregated into 265 valid monthly observations with calendar-correct lag features.
- **Methodology:** Monthly median modal price (Rs/quintal); missing calendar months are not filled. Training uses pre-2021 rows and the out-of-time test uses 2023 onward (14 months).
- **Measured test MAE:** previous-month persistence 49.214 Rs/quintal; same-month-last-year 122.893 Rs/quintal; HistGradientBoosting 306.140 Rs/quintal.
- **Engineering verdict:** HistGradientBoosting loses to the simple previous-month baseline and remains experimental. Planning uses historical mandi prices and an editable price field rather than this model.

---

### Module D: Planning Engine — Pure Python Deterministic Logic
- No black-box machine learning models are used for financial planning, storage decisions, or what-if analysis.
- Connects predictions to real-world economics using documented formulas and published agricultural cost statistics.

---

## 3. Mathematical Formulas & Explicit Units

Every financial and agronomic calculation in AgriOptima adheres to strict physical and economic accounting:

1. **Estimated Production (Tonnes):**
   $$\text{Production}_{\text{tonnes}} = \text{Yield}_{\text{tonnes/ha}} \times \text{Cultivated Area}_{\text{ha}}$$

2. **Quintals Conversion:**
   $$\text{Production}_{\text{quintals}} = \text{Production}_{\text{tonnes}} \times 10 \quad (1\text{ Tonne} = 10\text{ Quintals})$$

3. **Post-Harvest Loss Accounting (Applied Exactly Once):**
   $$\text{Marketable Quantity}_{\text{quintals}} = \text{Production}_{\text{quintals}} \times \left(1 - \frac{\text{Loss Percentage}}{100}\right)$$
   *(Loss stages from ICAR-CIPHET 2022: Harvesting, Threshing, Winnowing, Storage, Transport, Market)*

4. **Gross Market Revenue:**
   $$\text{Gross Revenue}_{\text{Rs.}} = \text{Marketable Quantity}_{\text{quintals}} \times \text{Mandi Price}_{\text{Rs./quintal}}$$

5. **Itemized Operational Costs:**
   $$\text{Cultivation Cost} = \text{CACP Cost per Hectare} \times \text{Area}_{\text{ha}}$$
   $$\text{Transport Cartage} = \text{Marketable Quintals} \times 35.0\text{ Rs./quintal}$$
   $$\text{Storage Warehousing} = \text{Marketable Quintals} \times \text{Storage Months} \times 45.0\text{ Rs./quintal/month}$$
   $$\text{Packaging \& Bagging} = \text{Marketable Quintals} \times 20.0\text{ Rs./quintal}$$
   $$\text{Total Costs} = \text{Cultivation} + \text{Transport} + \text{Storage} + \text{Packaging}$$

6. **Net Return (Profit) & ROI:**
   $$\text{Net Return}_{\text{Rs.}} = \text{Gross Revenue} - \text{Total Costs}$$
   $$\text{Net Return per Hectare} = \frac{\text{Net Return}}{\text{Area}_{\text{ha}}}$$
   $$\text{ROI (\%)} = \left(\frac{\text{Net Return}}{\text{Total Costs}}\right) \times 100$$

---

## 4. Dataset Inventory & Provenance

| Logical Dataset | Source & Scope | Records / Size | Variables Used in AgriOptima |
|---|---|---|---|
| `crop_suitability.csv` | ICAR & agricultural soil survey normal | 2,200 rows | Soil N, P, K, pH, climate temp, humidity, rainfall, crop label |
| `crop_production_haryana_punjab_1997_2019.csv` | Ministry of Agriculture & Farmers Welfare, DES | 12,447 rows | State, District, Crop, Season, Year, Area, Production, Yield |
| `post_harvest_loss_2022_haryana_punjab.csv` | ICAR-CIPHET National Study (2022) | 164 records | Crop-specific physical loss percentages by supply chain stage |
| `india_mandi_prices_2000_2024/*.csv` | AGMARKNET Directorate of Marketing & Inspection | 316 CSVs (over 10M rows) | Modal Price, Date, Market, State, District |
| NASA POWER API | NASA Langley Research Center Agroclimatology | Live REST API | Daily & climatological temperature, relative humidity, precipitation |

---

## 5. Verification & Test Execution Results

### 1. Automated Test Suite (`pytest`)
All 14 unit and integration tests executed cleanly:

```
platform darwin -- Python 3.14.5, pytest-9.2.0, pluggy-1.7.0
rootdir: /Users/ananyaupadhyay/Documents/AgriOptima-Project

backend/tests/test_api_endpoints.py::test_api_health_endpoint PASSED     [  7%]
backend/tests/test_api_endpoints.py::test_api_weather_endpoint PASSED    [ 14%]
backend/tests/test_api_endpoints.py::test_api_crop_recommendation_endpoint PASSED [ 21%]
backend/tests/test_api_endpoints.py::test_api_yield_prediction_endpoint PASSED [ 28%]
backend/tests/test_api_endpoints.py::test_api_mandi_analysis_endpoint PASSED [ 35%]
backend/tests/test_api_endpoints.py::test_api_plan_endpoint PASSED       [ 42%]
backend/tests/test_api_endpoints.py::test_api_what_if_endpoint PASSED    [ 50%]
backend/tests/test_models.py::test_crop_suitability_pipeline_loaded PASSED [ 57%]
backend/tests/test_models.py::test_crop_suitability_prediction_known_sample PASSED [ 64%]
backend/tests/test_models.py::test_yield_random_forest_pipeline_loaded PASSED [ 71%]
backend/tests/test_models.py::test_yield_prediction_supported_sample PASSED [ 78%]
backend/tests/test_models.py::test_yield_prediction_unsupported_crop_fallback PASSED [ 85%]
backend/tests/test_planning_engine.py::test_full_plan_generation_math PASSED [ 92%]
backend/tests/test_planning_engine.py::test_what_if_price_and_yield_shocks PASSED [100%]

======================== 14 passed in 2.37s =========================
```

### 2. Frontend Production Build (`Vite`)
The React dashboard compiled with zero errors in 1.30s:

```
vite v6.4.5 building for production...
✓ 2051 modules transformed.
dist/index.html                   0.74 kB │ gzip:  0.43 kB
dist/assets/index-B7ztADya.css    4.99 kB │ gzip:  1.51 kB
dist/assets/index-CROonlLJ.js   279.14 kB │ gzip: 82.70 kB
✓ built in 1.30s
```

### 3. Realistic End-to-End Demonstration Case
- **Profile:** Haryana, District Ambala, Kharif Season, Area = 3.0 Hectares, N=90, P=42, K=43, pH=6.5, Rainfall=220mm.
- **Crop Suitability (SVM):** Classified as **Rice** (Decision Boundary Score: +2.45).
- **Yield (Random Forest):** **4.66 Tonnes/Hectare**.
- **Gross Production:** $4.66 \times 3.0 = \mathbf{13.98\text{ Tonnes}} = \mathbf{139.8\text{ Quintals}}$.
- **Post-Harvest Loss (ICAR-CIPHET Rice: 4.2%):** Net Marketable = $\mathbf{133.93\text{ Quintals}}$.
- **Mandi Price (MSP/AGMARKNET):** ₹2,183.0 / quintal.
- **Gross Revenue:** $133.93 \times 2,183 = \mathbf{₹2,92,369.19}$.
- **Itemized Costs:** Cultivation (₹1,35,000) + Cartage (₹4,687.55) + Packaging (₹2,678.60) = $\mathbf{₹1,42,366.15}$.
- **Net Return:** $₹2,92,369.19 - ₹1,42,366.15 = \mathbf{₹1,50,003.04}$ ($\mathbf{ROI: 105.4\%}$).

---

## 6. How to Run the Application

### Prerequisites
- Python 3.10+ with active `.venv`
- Node.js 18+ and npm

### Terminal 1: Start Backend (FastAPI)
```bash
cd /Users/ananyaupadhyay/Documents/AgriOptima-Project
source .venv/bin/activate
export PYTHONPATH=backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API docs available at: `http://127.0.0.1:8000/docs`

### Terminal 2: Start Frontend (React + Vite)
```bash
cd /Users/ananyaupadhyay/Documents/AgriOptima-Project/frontend
npm run dev
```
Open your browser at: `http://localhost:5173`

---

## 7. Known Limitations & College Defense Notes

1. **Geographic Scope of Direct Yield Model:**
   The saved Random Forest yield model is trained on 44 districts of Haryana and Punjab. For requests in other states, the system provides transparent state-level regional baseline estimates rather than hallucinating unseen categorical weights.
2. **Crop Name Vocabulary Alignment:**
   Crop Suitability outputs lowercase agronomic labels (e.g. `rice`, `pigeonpeas`), while the Yield Model uses administrative labels (e.g. `Rice`, `Arhar/Tur`). AgriOptima incorporates an explicit bidirectional bridge dictionary (`SUITABILITY_TO_YIELD_MAP`). Horticulture crops without commercial field data (e.g. `apple`, `banana`) are explicitly labelled as "regional yield data unavailable".
3. **Mandi Price Non-Stationarity:**
   Agricultural commodity spot prices fluctuate due to unexpected weather, export bans, and global geopolitical factors. As demonstrated by our benchmark, complex time-series ML models can overfit and fail against simple persistence baselines during regime shifts. AgriOptima resolves this by giving farmers a transparent baseline with direct price override capability.

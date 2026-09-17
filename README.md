# AgriOptima Large Dataset EDA

Put all CSV files in `DataSets/`.

Run:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python eda/run_eda.py
```

The pipeline is designed for large CSVs: it reads in chunks and keeps a bounded reservoir sample for plots. It creates reports and plots for every CSV automatically.

Outputs:
- `reports/dataset_inventory.csv`
- `reports/<dataset>/overview.json`
- `reports/<dataset>/column_summary.csv`
- `reports/<dataset>/missing_values.csv`
- `reports/<dataset>/numeric_summary.csv`
- `reports/<dataset>/categorical_summary.csv`
- `reports/<dataset>/outlier_summary.csv`
- `reports/<dataset>/correlation_pairs.csv`
- `reports/<dataset>/agriculture_checks.csv`
- `reports/<dataset>/dataset_specific_analysis.json`
- `reports/<dataset>/eda_summary.txt`
- `plots/<dataset>/...`

Important: if yield = production / area, production must not be used as an input feature for yield prediction (target leakage).

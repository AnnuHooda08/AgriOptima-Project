from pathlib import Path
import pandas as pd

data = Path("DataSets")
files = sorted(data.glob("*.csv"))
print("CSV files found:", len(files))
for p in files:
    print("\n", p.name, f"{p.stat().st_size/1024**2:.2f} MB")
    df = pd.read_csv(p, nrows=5, low_memory=False)
    print("Columns:", list(df.columns))
    print(df.head().to_string(index=False))

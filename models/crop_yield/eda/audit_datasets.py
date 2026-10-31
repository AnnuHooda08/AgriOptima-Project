"""Audit potentially relevant local crop yield, soil, and weather data sources."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "models/crop_yield/reports/current"
YIELD_DIR = ROOT / "DataSets/Yeild"
SOIL_GRID = ROOT / "DataSets/Soil Grid"
SOIL_NUTRIENT = ROOT / "DataSets/Soil nutrient"


def inspect_csv(path, use_chunks=False):
    """Collect facts from CSV headers and rows without modifying any source."""
    sample = pd.read_csv(path, nrows=10, low_memory=False)
    columns = list(sample.columns)
    year_column = next((c for c in ("Year", "Crop_Year", "year") if c in columns), None)
    state_column = next((c for c in ("State", "State_Name", "State Name", "state_name") if c in columns), None)
    district_column = next((c for c in ("District", "District_Name", "Dist Name", "district_name") if c in columns), None)
    observed_years, states, districts = set(), set(), set()
    if use_chunks:
        rows, null_counts = 0, pd.Series(0, index=columns, dtype="int64")
        # Stream large shards so the audit does not need to hold them in memory.
        for chunk in pd.read_csv(path, chunksize=100_000, low_memory=False):
            rows += len(chunk)
            null_counts = null_counts.add(chunk.isna().sum(), fill_value=0)
            for col, bucket in ((year_column, observed_years), (state_column, states),
                                (district_column, districts)):
                if col:
                    bucket.update(chunk[col].dropna().astype(str).unique())
        null_cells = int(null_counts.sum())
    else:
        frame = pd.read_csv(path, low_memory=False)
        rows = len(frame)
        null_cells = int(frame.isna().sum().sum())
        for col, bucket in ((year_column, observed_years), (state_column, states),
                            (district_column, districts)):
            if col:
                bucket.update(frame[col].dropna().astype(str).unique())

    # Report year labels as stored; keep crop-year labels intact rather than inventing dates.
    if observed_years:
        years_sorted = sorted(observed_years)
        time_coverage = f"{years_sorted[0]} to {years_sorted[-1]}"
    else:
        time_coverage = "No date field"
    geography_counts = {
        "states": len(states) if states else None,
        "districts": len(districts) if districts else None,
    }
    if "latitude" in columns and "longitude" in columns:
        coordinates = pd.read_csv(path, usecols=["latitude", "longitude"])
        geography_counts["coordinate_bounds"] = {
            "latitude_min": float(coordinates.latitude.min()),
            "latitude_max": float(coordinates.latitude.max()),
            "longitude_min": float(coordinates.longitude.min()),
            "longitude_max": float(coordinates.longitude.max()),
        }
    return {
        "filename": path.name,
        "path": str(path.relative_to(ROOT)),
        "records": rows,
        "feature_count": len(columns),
        "columns": columns,
        "missing_cells": null_cells,
        "missing_percent_of_cells": round(100 * null_cells / max(rows * len(columns), 1), 4),
        "time_coverage": time_coverage,
        "geographic_counts": geography_counts,
        "source_provenance": "Not documented in repository metadata; filename/schema only.",
    }


def run_audit():
    """Inventory plausible local sources and record fit/exclusion rationale."""
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(YIELD_DIR.glob("*.csv"))
    files += sorted(SOIL_GRID.glob("*.csv"))
    # Nutrient data is split into shards; audit each shard using streaming counts.
    files += sorted(SOIL_NUTRIENT.glob("*.csv"))
    records = []
    for path in files:
        record = inspect_csv(path, use_chunks=path.parent == SOIL_NUTRIENT)
        columns = set(record["columns"])
        lower_path = str(path).lower()
        if "soilgrids" in lower_path:
            record.update({
                "geography": "Latitude/longitude grid",
                "target_available": False,
                "intended_use": "Candidate soil features; not integrated without documented spatial join to production districts.",
            })
        elif "soil nutrient" in lower_path:
            record.update({
                "geography": "State/district/block/village fields",
                "target_available": False,
                "intended_use": "Not integrated: recent survey timing and field identifiers do not align with historical crop-year rows.",
            })
        elif "icrisat" in lower_path:
            frame = pd.read_csv(path, low_memory=False, usecols=["Year", "State Name", "Dist Name"])
            record.update({
                "geography": "India district-level; separate wide schema",
                "target_available": True,
                "intended_use": "Reference/possible external validation after sentinel handling and crop-triplet reshaping; excluded from current model.",
            })
        elif "1997.csv" in lower_path:
            record.update({
                "geography": "India district-level",
                "target_available": "Production and area; yield can be derived after unit validation",
                "intended_use": "Not integrated: despite the filename, the data spans multiple years; units and source provenance are not documented, so yield derivation and combination are not defensible yet.",
            })
        elif "1997_2014" in lower_path:
            record.update({
                "geography": "Haryana and Punjab district-level",
                "target_available": "Production and area; yield can be derived, but units are not explicit",
                "intended_use": "Historical overlapping extract; excluded because current source has 1997-2019 coverage and explicit yield/unit fields.",
            })
        else:
            record.update({
                "geography": "Haryana and Punjab district-level",
                "target_available": True,
                "intended_use": "Primary training dataset: explicit yield and units, longer coverage, and compatible model fields.",
            })
        records.append(record)
    inventory = pd.DataFrame([{k: v for k, v in r.items() if k != "columns"} for r in records])
    inventory.to_csv(OUT / "yield_dataset_inventory.csv", index=False)
    (OUT / "yield_dataset_schemas.json").write_text(json.dumps(records, indent=2) + "\n")
    # Weather is absent if no local dataset or repository integration is found.
    weather = [p for p in (ROOT / "DataSets").rglob("*") if p.is_file()
               and any(token in p.name.lower() for token in ("weather", "rainfall", "temperature", "climate"))]
    weather_service = ROOT / "backend/app/services/weather_service.py"
    summary = {
        "primary_dataset": "DataSets/Yeild/crop_production_haryana_punjab_1997_2019.csv",
        "weather_files_found_by_filename": [str(p.relative_to(ROOT)) for p in weather],
        "weather_integration": (
            "A NASA POWER climatology endpoint exists in backend/app/services/weather_service.py "
            "with district baseline fallbacks. It returns climatological/annual summaries, not historical "
            "year- and season-aligned weather for 1997-2019, so it cannot be joined to training rows."
            if weather_service.exists()
            else "No local weather file or weather service was found."
        ),
        "weather_service_path": str(weather_service.relative_to(ROOT)) if weather_service.exists() else None,
        "dataset_count_audited": len(records),
        "candidate_decisions": {
            "primary": "Explicit yield in tonnes/ha plus area, crop, season, year, district, state, and Haryana/Punjab coverage.",
            "not_combined": "The remaining files have incompatible geography/time/schema, are overlapping/shorter extracts, or require source semantics/spatial matching not provided by the repository.",
        },
    }
    (OUT / "yield_dataset_audit.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Audited {len(records)} local yield/soil CSV files; wrote inventory and schema report.")
    return inventory


if __name__ == "__main__":
    run_audit()

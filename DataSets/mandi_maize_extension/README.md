# Additional maize price records

These are real downloaded records, not generated or duplicated training examples.
The three CSVs contain 159,336 maize records after exact duplicate removal:

| File | Records | Available dates |
| --- | ---: | --- |
| maize_2024.csv | 76,948 | 2024-01-01 to 2024-12-31 |
| maize_2025.csv | 72,768 | 2025-01-01 to 2025-12-31 |
| maize_2026.csv | 9,620 | 2026-01-01 to 2026-04-20 |

Source: [India Mandi Daily Prices archive on Hugging Face](https://huggingface.co/datasets/DHIVAKARNAIDUSUNKARI/mandi-india-daily-prices-2001-2026), uploaded by DHIVAKARNAIDUSUNKARI. Its card attributes the compilation to Manas Khandelwal's [Kaggle dataset](https://www.kaggle.com/datasets/khandelwalmanas/daily-commodity-prices-india), DOI 10.34740/kaggle/dsv/15888319, and the underlying data to [AGMARKNET / data.gov.in](https://www.data.gov.in/resource/variety-wise-daily-market-prices-data-commodity).

The publisher states Government Open Data License – India for the original data.
This is a third-party processed archive. We have not independently verified every
record with the government. Preserve this attribution and the source manifest.

`source_manifest.json` records the immutable archive revision, download URLs,
row counts, date ranges and SHA-256 checksums of the saved CSVs. These files have
price fields but no arrivals-quantity field. The model uses modal prices as
rupees per quintal, consistent with the original project and reported source
conventions; it does not use these values as live price quotes.

To repeat the download/extraction, run from any folder:

```sh
python /absolute/path/to/AgriOptima-GitHub-Latest/DataSets/mandi_maize_extension/download_data.py
```

Dependencies are already listed in the project requirements: requests, pandas,
and pyarrow. Downloading all-commodity annual Parquet files temporarily uses
about 147 MB in the system temporary folder; only the maize rows are kept here.

## Important coverage findings

The archive's November 2025 maize rows cover only 1–5 November. It must not be
presented as a full month. December's forecast also uses this sparse November
as a lag. We retain the original 12-month test and also show a coverage-screened
10-month sensitivity comparison. A month having 20 reporting days does not
prove that all mandis or varieties are represented.

The older file and extension overlap in January 2024: medians are 2111 and 2120
respectively. The new source has 4,945 January records, versus 4,916 in the old
file. The modeling join uses the old source only before 2024 and the new source
from January 2024 onward. It does not append both copies of the overlap.

All 2026 rows are retained for review but excluded from the current training,
validation and test. April is incomplete, and 2026 market coverage has not been
validated for a new prospective experiment.

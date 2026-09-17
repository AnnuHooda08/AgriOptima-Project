# India historical mandi prices

Source: [India Commodity Wise Mandi Dataset on Kaggle](https://www.kaggle.com/datasets/vandeetshah/india-commodity-wise-mandi-dataset), version 1, downloaded 2026-09-17. The uploader describes coverage from 2000-01-01 to 2024-02-01 and lists the license as Apache 2.0. These are historical records, not a live feed.

Files:

- `india_mandi_prices_2000_2024_kaggle.zip`: original, unmodified download (423,298,799 bytes). ZIP integrity check passed.
- `india_mandi_prices_2000_2024/`: extracted commodity CSVs (325 files, about 4.4 GB).

Local checks: 56,879,397 total lines across the files, of which 315 are headers and 56,879,082 are data rows. Ten CSVs are empty. Haryana occurs in 3,682,255 rows across 193 commodity files; Punjab occurs in 5,456,235 rows across 191 commodity files. Counts are based on state names at the start of each data row. The 315 nonempty files have two header variants: 293 specify `Arrivals (Tonnes)` and prices in `Rs./Quintal`; 22 omit units in the header. Check units before combining those files. The commodity name is the CSV filename, not a data column.

Fields: state, district, market, variety, group, arrivals, minimum price, maximum price, modal price, and reported date. For price forecasting, keep commodity and variety separate, account for missing market days, and split train/test by date. Use a daily government API separately to show the latest reported prices on the website.

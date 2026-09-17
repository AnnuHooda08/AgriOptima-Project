# Reconstruct the India mandi-price dataset

These `part-*` files are consecutive 40,000,000-byte pieces of the original Kaggle ZIP. This keeps each Git file below GitHub's 100 MB single-file limit. The archive was downloaded from [India Commodity Wise Mandi Dataset](https://www.kaggle.com/datasets/vandeetshah/india-commodity-wise-mandi-dataset), version 1. See `../../raw/README_india_mandi_prices.md` for coverage and caveats.

From the repository root on macOS/Linux:

```sh
cat data/shared/mandi_archive/part-* > data/raw/india_mandi_prices_2000_2024_kaggle.zip
shasum -a 256 data/raw/india_mandi_prices_2000_2024_kaggle.zip
unzip -q data/raw/india_mandi_prices_2000_2024_kaggle.zip -d data/raw/india_mandi_prices_2000_2024
```

Expected SHA-256: `982be7cf392c949aafd0328907347bb8b4a883adf202c5415ba8b84b3e9aa7b0`.

The reconstructed ZIP is 423,298,799 bytes; the extracted data is about 4.4 GB. Do not commit the reconstructed ZIP or extracted files, which are ignored by Git.

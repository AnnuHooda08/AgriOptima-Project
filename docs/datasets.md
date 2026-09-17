# AgriOptima datasets

Shared project data for the Haryana and Punjab AI/ML project. The downloaded source data, processed regional subsets, and scripts are under `data/` and `scripts/`.

| Dataset | Location | Notes |
| --- | --- | --- |
| Historical India mandi prices | `data/shared/mandi_archive/` | Reassemble the 11 parts into the original ZIP using its README; 56.9 million reported rows in 325 commodity CSVs. |
| SoilGrids predictions | `data/raw/soilgrids_haryana_punjab_bbox/` and `data/processed/soilgrids_haryana_punjab_bbox/` | Nine soil properties at six depths; 1,494,006 sampled location-depth rows in the CSVs. See `data/processed/README_soilgrids.md`. |
| District crop production | `data/raw/india_district_crop_production_1997_2019.csv` and `data/processed/crop_production_haryana_punjab_1997_2019.csv` | Historical production records. See `data/processed/README_crop_recommendation_data.md`. |
| Post-harvest losses | `data/raw/fao_food_loss_export_2026-09-17.csv`, `data/raw/nabcons_post_harvest_loss_2022.pdf`, and `data/processed/post_harvest_loss_2022_haryana_punjab.csv` | Published aggregates and estimates. See `data/processed/README_post_harvest_loss.md`. |

The SoilGrids CSVs include a rectangular area around Haryana and Punjab, including neighboring territory. SoilGrids values are mapped estimates, not field tests. Mandi prices are historical observations; showing current reported prices requires a separately configured daily feed.

The full extracted mandi directory (about 4.4 GB) is ignored by Git. Reconstruct it from the shared ZIP parts when needed. Keep model experiments and contributions in separate branches and cite the source notes above in reports.

# Crop recommendation data

Preferred historical crop-production source: [India Agriculture Crop Production on Kaggle](https://www.kaggle.com/datasets/pyatakov/india-agriculture-crop-production), a third-party mirror of Indian district crop statistics. The project files are:

- `../raw/india_district_crop_production_1997_2019.csv`: 345,407 records for India.
- `crop_production_haryana_punjab_1997_2019.csv`: 12,447 records (8,305 Haryana; 4,142 Punjab), 1997–98 through 2019–20.

Fields are state, district, crop, year, season, area, area unit, production, production unit, and yield. In the two-state subset, 1,418 rows lack production or yield. Cotton production is reported in **bales** in 626 rows; other production is in tonnes, so do not pool their yield values without a unit conversion or crop-specific model.

These records show what farmers grew and the resulting production. They do **not** label the best or most suitable crop, and they lack measured soil nutrients and weather. A defensible recommendation model would add aligned soil and climate data, estimate crop-specific performance, evaluate on later years, then rank viable crops within a season. Historical cultivation alone must not be treated as proof of suitability.

The source is older than the current growing seasons. For a direct agro-ecological suitability layer, consider the [FAO/IIASA GAEZ database](https://www.fao.org/gaez/gaezv4/en), which reports suitability and attainable yields for 51 crops on a 5-arc-minute grid. Such layers represent modelled potential rather than observed yields.

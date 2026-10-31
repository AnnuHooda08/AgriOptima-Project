# Crop Suitability Data Dictionary

Source: `DataSets/crop_suitability.csv`. The CSV contains no unit or provenance
metadata. The API currently labels N/P/K as kg/ha, temperature as °C, humidity
as percent, and rainfall as mm; these are interface descriptions, not
independently verified units for this source file.

| Field | Role | Meaning / unit status | Observed range |
| --- | --- | --- | ---: |
| `N` | Input | Nitrogen measurement; CSV does not state unit | 0–140 |
| `P` | Input | Phosphorus measurement; CSV does not state unit | 5–145 |
| `K` | Input | Potassium measurement; CSV does not state unit | 5–205 |
| `temperature` | Input | Temperature; API describes degrees Celsius | 8.826–43.675 |
| `humidity` | Input | Humidity; API describes relative humidity percent | 14.258–99.982 |
| `ph` | Input | pH; dimensionless pH scale | 3.505–9.935 |
| `rainfall` | Input | Rainfall; API describes millimetres | 5.315–298.560 |
| `label` | Target | Crop class name as stored in source; 27 case-sensitive labels | Not numeric |

All numeric ranges above are observed extrema in this file, not safe agronomic
limits. The source does not identify the place, time window, sample method, or
label definition for any row. Preserve label spelling and capitalization when
comparing against saved model classes.

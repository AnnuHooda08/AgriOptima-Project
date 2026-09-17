# AgriOptima: Haryana and Punjab dataset shortlist

Checked: 2026-09-07. Scope: Indian states Haryana and Punjab.

## Status

Sources identified; no crop dataset has been downloaded or row-audited yet. Do not treat catalog dates as data coverage dates. Government resource opened in the browser; download requires a purpose form and CAPTCHA. Direct government and ICRISAT requests failed/timed out. ICRISAT browser navigation also timed out.

## CropCast repository audit

- Candidate repository: https://github.com/RitikOnWork/CropCast
- Audited commit: `1beec29c43db55366e3a8f6fbd8182b464d54bfc` (2026-04-11).
- The repository contains React 19 + Vite + plain CSS, a small FastAPI service, an XGBoost training script, serialized model files, and `backend/crop_production.csv` (246,091 records).
- No LICENSE/COPYING file was present and GitHub API reported `license: null`. Do not copy its code into the assessed project without permission or a later explicit license.
- Its README calls the data a 10-year ICAR dataset, but the included file spans more years and contains no embedded provenance/license. Treat the source attribution as unverified.
- Its current model is not acceptable evidence for our ML submission: random row splitting, encoders fitted before the split, ordinal label encoding for nominal geography/crops, area used to predict per-hectare yield, and an unexplained global removal of yields above 15.
- The API exposes all districts independently of state, so invalid state-district combinations are selectable. The UI also says "Live Data Stream", "Satellite imagery", and "Telemetry tracking" without implementing those feeds.
- It has no expert inference engine, CSP implementation, reasoning trace, or disruption replanning. It cannot satisfy the planned AI contribution.

### Included Haryana/Punjab data

All counts below are from the repository file and require provenance/unit confirmation against an authoritative source.

| State | Rows | Years | District labels | Production missing | Core-crop observations |
|---|---:|---|---:|---:|---|
| Haryana | 5,875 | 1997-2012 (16 years) | 21 | 1,335 | Wheat 317/317 usable; rice 300/305; maize 148/267; rapeseed & mustard 272/277 |
| Punjab | 3,173 | 1997-2014 (18 years) | 22 | 30 | Wheat 338/338 usable; rice 338/338; maize 219/219; rapeseed & mustard 288/288 |

The file includes district-boundary changes: Haryana Mewat begins in 2005 and Palwal in 2008; Punjab Barnala begins in 2007, Fazilka and Pathankot in 2012, and S.A.S Nagar and Tarn Taran in 2006. Preserve this history during temporal evaluation.

Some included Haryana records produce zero yield for maize, rice, and mustard. Audit these rather than silently dropping them. The file can support a historical classroom experiment, especially for wheat and rice, but it cannot by itself validate present-day or farm-level forecasts.

## Preferred ML source

- Government district-wise, season-wise crop production statistics from 1997:
  https://www.data.gov.in/resource/district-wise-season-wise-crop-production-statistics-1997
- Catalog: https://www.data.gov.in/catalog/district-wise-season-wise-crop-production-statistics-0
- Published metadata describes district, crop, season, year, area (hectares), and production (tonnes). Actual file schema and crop-specific units require verification.
- The resource was marked updated 16 October 2024; this does not establish the latest observation year.
- Download UI: Non Commercial; Academia; CAPTCHA; Download. Optional name/mobile/email fields are present; do not assume personal information is required. File is hosted by the source department; completing this form may lead to another page.
- Alternative government query/export portal: https://data.desagri.gov.in/website/apy-query-report-web

## Research-data alternative

- ICRISAT/TCI District Level Database: https://data.icrisat.org/dld/
- Crop data: https://data.icrisat.org/dld/src/crops.html
- Additional data: https://data.icrisat.org/dld/src/additional.html
- Documentation describes annual district area, production and yield for 20 major crops. Additional data lists district/season area and production for 1997-2019. Actual Haryana/Punjab completeness is unverified.
- Boundary systems differ: apportioned 1966 boundaries versus unapportioned 2015 boundaries. Choose and document one; do not merge them naively or call historic districts current districts.
- Supporting candidate variables: irrigation, rainfall, temperature, fertilizer and farm harvest prices. Check availability dates before use as prediction features.

## Weather extension

- NASA POWER: https://power.larc.nasa.gov/
- API guide: https://power.larc.nasa.gov/docs/tutorials/service-data-request/api/
- Candidate temperature and precipitation features from gridded products. Point values are not district-wide or field sensor measurements.
- Pre-planting models can only use information available before planting. Same-season realized weather requires a different, explicitly dated prediction task.

## AI knowledge sources

- Punjab Agricultural University publications: https://pau.edu/index.php?DO=subSubLink&_act=manageLink&intMainID=3&intSubID=13&intSubSubID=61
- Haryana Agricultural University publication unit: https://hau.ac.in/page/publication-unit
- Extract cited crop/season/sowing/irrigation guidance after reviewing relevant editions and pages. These are rule sources, not labelled ML datasets. No numeric agronomic rules have been validated yet.
- Farm area, budget and water budget can initially be labelled demonstration inputs.

## Initial crop shortlist (provisional)

Inspect wheat, rice, maize and rapeseed/mustard first. Keep a crop only where state/district/year coverage supports evaluation. Do not assume all crops are suitable in every district or season.

## Audit after download

1. Preserve the raw file and record source, retrieval date, license, and checksum.
2. Inspect schema, unit conventions and missing-value sentinels.
3. Filter India/Haryana/Punjab; normalize whitespace and crop names without erasing meaningful categories.
4. Report rows, districts, crops, seasons, earliest/latest year and gaps by state/crop.
5. Check duplicate state/district/crop/season/year keys and administrative-boundary changes.
6. Quarantine missing production, nonpositive area and implausible units; do not silently replace missing production with zero.
7. Derive tonnes/hectare only when area and production units justify it. Production must not be an input to yield prediction.
8. Prefer at least 10 usable years where available; this is a target, not verified coverage or a guarantee of model quality.
9. Split by complete agricultural years into chronological training, validation and held-out test periods; dates chosen only after coverage audit.
10. Compare a training-only historical baseline against regression models. Report district-level limitations and do not claim farm-level validation.

## User action

Open the government resource and complete its download CAPTCHA yourself. Save the original CSV/Excel/ZIP in the project's data/raw directory, or leave it in Downloads and provide its filename. Do not clean or edit it first. If the download leads to an unavailable external site, report that message; dataset acquisition remains pending.

# Post-harvest loss CSVs

These CSVs were extracted from Appendix 6 (state-level tables, PDF pages 267–286) of the [NABCONS 2022 report published by India's Ministry of Food Processing Industries](https://www.mofpi.gov.in/sites/default/files/phl_study_final_report_07.12.2022_2.pdf). The local source copy is `../raw/nabcons_post_harvest_loss_2022.pdf`.

- `post_harvest_loss_2022_state_stage.csv`: 1,865 readable numeric loss estimates from 19 states.
- `post_harvest_loss_2022_haryana_punjab.csv`: 164 of those estimates, restricted to Haryana (89) and Punjab (75).

Each row reports a loss percentage for one state, crop, and farm or market stage. `Overall total loss` and stage totals are reported estimates, so **do not sum them again with their component stages**. `source_pdf_page`, `source_table`, and `source_row` identify the PDF location used by `../../scripts/extract_post_harvest_loss.py`.

The source study surveyed the 2020–22 period and published results in 2022. These rows are **aggregated estimates**, not independent farmer records or an annual time series. They should be used as reference values or descriptive comparisons; row count alone does not make them sufficient training data for a Haryana–Punjab loss prediction model.

The PDF has irregular table layouts. The extractor omits unreadable cells and tables rather than filling them in, and excludes four crop-state groups whose extracted totals failed consistency checks. Therefore the CSV is a verified subset of the published appendix, not a complete transcription of every state table.

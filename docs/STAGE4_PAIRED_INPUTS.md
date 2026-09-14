# Paired V5 inputs and experimental inference

The manual **Pair scenes and prepare V5 inputs (review only)** workflow searches new Landsat 8 scenes and looks for Sentinel-2 within the historical `[-5 days, +5 days)` window. It never uses the independently selected Stage 3 Sentinel date without checking the temporal match.

## Gates and bounded search

- Initial midnight state dates represent whole processed days, preventing reprocessing May 3 as a new observation just because the satellite overpass occurred after midnight.
- Search the latest 10 new Landsat L2SP scenes with scene cloud <20%. For each, inspect up to 10 Sentinel scenes with scene cloud <20% within the matching window. Limits are explicit: no result means no pair among these bounded candidates, not proof that no possible imagery exists.
- Require at least 80% jointly valid area across the entire canonical study footprint. Masked/uncovered pixels count as invalid. The Landsat mask includes the surface-temperature band, making the coverage gate conservative where thermal retrieval is missing.
- Preserve all 1,320 IDs. Only cells with at least 70% valid coverage and all 25 finite, in-range features are eligible for inference. These are initial review thresholds, not calibrated confidence levels.
- Preserve the historical scientific formulas and report missing data rather than imputing old values into new dates.

No-compatible-pair runs produce a successful, explicit **no compatible pair** report with candidate diagnostics and zero inference-eligible cells. Such a result must not advance state or trigger predictions/publication.

## Completed feature contract

`v5_schema.py` freezes all 25 ordered features from script 30. Tests compare it directly to that original script.

Spatial inputs use the Landsat/Sentinel formulas from Stage 3 plus SRTM elevation, script 36's JRC occurrence >=50% water-distance transform (100 m UTM grid, 250-pixel neighbourhood, capped at 25 km), and Dynamic World mean tree/built probabilities within Landsat +/-5 days.

The 11 non-overpass weather features reproduce script 22's transformations and UTC windows:

- Air temperature, wind magnitude of mean components, relative humidity and soil moisture: acquisition to acquisition +24 hours.
- Precipitation: sums over the preceding 1, 3 and 7 days, metres to millimetres.
- Solar radiation: previous-day hourly accumulations summed, J/m² to MJ/m².
- Cloud cover: previous-day ERA5 mean, fraction to percent.
- Air temperature history: preceding 3/7-day means, kelvin to Celsius.

Every hourly window must contain the expected unique consecutive timestamps. Because four inputs use the 24 hours **after** acquisition, this is retrospective inference, not a live forecast. The five overpass variables retain script 28's +/-90-minute/AOI averaging method.

To reproduce script 37's date-level weather summaries, weather is sampled at 30 m over the original weather AOI using up to 750 requested samples under the valid feature mask, then median-aggregated. New dates use deterministic seed 42. Historical scripts used scene-loop-dependent seeds and somewhat different masks; this sampling difference must be checked before operational use. No scaler is applied. Historical script 37 imputed missing spatial values; this workflow deliberately excludes incomplete cells instead and documents that change.

## Inference helper

All new runs enforce a previous-calendar-month UTC cutoff for acquisitions and their complete ancillary windows. For example, September runs query only data before September 1. The full Dynamic World +5-day window must fit, so some late-August Landsat scenes are deferred until October. This also keeps forward 24-hour weather and overpass windows within the cutoff without changing the trained feature definitions. Status files and prediction summaries record `data_through`, `data_cutoff_exclusive` and `data_date_policy`. Older artifacts without this metadata must be regenerated before using the updated validator/inference helper.

Use **Run workflow** on `main` with `validation_date` empty for a fresh monthly check. This searches eligible unprocessed scenes up to the cutoff; it does not calculate a calendar-month composite or automatically publish predictions.

`predict_v5_review.py` accepts a validated input artifact and a local model path. Before loading the pickle, it checks the original V5 SHA-256 against `MODEL_MANIFEST.json`, checks the recorded scikit-learn/numpy/joblib versions, and verifies the serialized feature order. It predicts eligible cells only and writes an experimental result and observed-LST comparison inside the review artifact.

```sh
python automation/predict_v5_review.py latest_data/v5-inputs --model /trusted/path/urban_heat_model_v5.pkl
```

No model is downloaded automatically. No model is retrained. Predictions are not added to the historical website or labeled operationally validated. Comparing predicted grid means with observed grid means is a diagnostic; it is not an independent accuracy certification of a model trained on pixel samples.

State advancement, rolling heat scores, hotspot recalculation and public latest-conditions deployment remain outside this workflow.

## Verified runs and current readiness

- [New-date check, run 34883806840](https://github.com/Rohan-Ktksu/bengaluru-heat-atlas/actions/runs/34883806840): succeeded with `no_compatible_pair`. The only new Landsat scene meeting the bounded search's metadata criteria was June 4, 2026. No Sentinel candidate within +/-5 days passed scene cloud <20%. Zero new input rows were produced; no inference or state advancement occurred.
- [Explicit historical replay, run 34884034505](https://github.com/Rohan-Ktksu/bengaluru-heat-atlas/actions/runs/34884034505): May 3 Landsat paired with April 29 Sentinel. Joint satellite-valid area was 99.58%. All hourly weather windows were complete; 734 valid meteorological samples contributed to the date-level medians. All 1,320 grid records were preserved and 1,268 passed the combined-feature coverage/input gates. The other 52 were excluded without imputation.
- Local inference with the original manifest-verified V5 model succeeded for those 1,268 cells in the recorded runtime. Comparison against observed grid-mean LST: MAE 2.1854 C, RMSE 2.7223 C, prediction-minus-observation bias +1.3043 C. These are historical replay diagnostics on a date already in the original evaluation period; they must not be advertised as a new independent accuracy result.

The workflow now accepts an optional `validation_date` for one of the seven historical study dates. Leaving it blank searches only new acquisitions. Replay outputs carry `run_kind: historical_validation_replay`; the state and public atlas are never updated by a replay.

The code is ready to prepare new-date inputs when an eligible pair exists. Current evidence does not support new-date predictions or automatic public latest-conditions publication. New feature extraction and the local inference helper have both been exercised; automated model artifact delivery, rolling scores/clusters and a public latest mode remain separate future work.
